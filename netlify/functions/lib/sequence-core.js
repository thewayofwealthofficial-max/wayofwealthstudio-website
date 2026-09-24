// Email sequences on Resend (replaces MailerLite automations).
//
// How it works:
//   - Each sequence has its own Resend audience, "Seq · <id>". Joining it is the enrolment;
//     the contact's created_at is the start time.
//   - Email 1 is sent straight from the signup function. The hourly runner sends the rest.
//   - What each person has been sent is kept in Netlify Blobs (store "sequences").
//   - When the last email is sent, the person joins the main "General" list and gets the weekly emails.
//     Keeping them off General until then means nobody gets a welcome email and a weekly email on the same day.
//
// Env: RESEND_API_KEY, UNSUBSCRIBE_SECRET, optional RESEND_AUDIENCE_ID (General).

const { createHmac } = require('node:crypto');

const RESEND = 'https://api.resend.com';
const GENERAL_AUDIENCE = process.env.RESEND_AUDIENCE_ID || 'ed40086b-fccc-4755-8744-72085ceac3e7';
const SITE = 'https://thewayofwealth.shop';
const FROM = 'Joel from Way of Wealth <joel@thewayofwealth.shop>';
const REPLY_TO = 'joel@thewayofwealth.shop';
const COMPANY_LINE = 'Way of Wealth LTD · Registered in England and Wales, company no. 17214427';

const SEQUENCES = {
  'welcome-newsletter': require('./sequences/welcome-newsletter'),
};

// Which sign-up form starts which sequence.
const MAGNET_TO_SEQUENCE = {
  'finance-fridays': 'welcome-newsletter',
};

let lastCall = 0;
async function rs(path, { method = 'GET', body } = {}) {
  const key = process.env.RESEND_API_KEY;
  if (!key) throw new Error('RESEND_API_KEY not set');
  for (let attempt = 0; attempt < 4; attempt++) {
    const wait = lastCall + 550 - Date.now();
    if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    lastCall = Date.now();
    const res = await fetch(RESEND + path, {
      method,
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 429) { await new Promise((r) => setTimeout(r, 1200 * (attempt + 1))); continue; }
    const text = await res.text();
    let json = null;
    try { json = text ? JSON.parse(text) : null; } catch { /* not json */ }
    return { ok: res.ok, status: res.status, json, text };
  }
  return { ok: false, status: 429, json: null, text: 'rate limited' };
}

const audienceCache = {};
async function sequenceAudienceId(seqId) {
  if (audienceCache[seqId]) return audienceCache[seqId];
  const name = `Seq · ${seqId}`;
  const list = await rs('/audiences');
  if (!list.ok) throw new Error(`Resend audiences ${list.status}`);
  let hit = (list.json.data || []).find((a) => a.name === name);
  if (!hit) {
    const made = await rs('/audiences', { method: 'POST', body: { name } });
    if (!made.ok) throw new Error(`Resend create audience ${made.status} ${made.text.slice(0, 120)}`);
    hit = made.json;
  }
  audienceCache[seqId] = hit.id;
  return hit.id;
}

async function getContact(audienceId, email) {
  const r = await rs(`/audiences/${audienceId}/contacts/${encodeURIComponent(email)}`);
  return r.ok ? r.json : null;
}

async function listContacts(audienceId) {
  const out = [];
  let after = null;
  for (let page = 0; page < 50; page++) {
    const r = await rs(`/audiences/${audienceId}/contacts?limit=100${after ? `&after=${after}` : ''}`);
    if (!r.ok) throw new Error(`Resend list contacts ${r.status}`);
    const rows = r.json.data || [];
    out.push(...rows);
    if (!r.json.has_more || !rows.length) break;
    after = rows[rows.length - 1].id;
  }
  return out;
}

function unsubToken(email) {
  const secret = process.env.UNSUBSCRIBE_SECRET;
  if (!secret) throw new Error('UNSUBSCRIBE_SECRET not set');
  return createHmac('sha256', secret).update(String(email).trim().toLowerCase()).digest('hex').slice(0, 32);
}

function unsubUrl(email) {
  const e = String(email).trim().toLowerCase();
  return `${SITE}/api/unsubscribe?e=${encodeURIComponent(e)}&t=${unsubToken(e)}`;
}

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// Email bodies are written in a tiny markdown: blank line = new paragraph, "- " = bullet,
// **bold**, *italic*, [text](url). {{name}} becomes the first name, or "there" if we don't have one.
function inlineHtml(s) {
  return esc(s)
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, t, u) => `<a href="${u}" style="color:#1C2A3A;font-weight:bold;text-decoration:underline;">${t}</a>`)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>');
}
function inlineText(s) {
  return s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '$1 ( $2 )').replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1');
}

function render(email, { firstName, to, footerReason }) {
  const name = (firstName || '').trim().split(/\s+/)[0] || 'there';
  const fill = (s) => s.replace(/\{\{name\}\}/g, name);
  const blocks = fill(email.body).trim().split(/\n\s*\n/);
  const P = 'margin:0 0 18px;';
  const html = blocks.map((b) => {
    const lines = b.split('\n');
    if (lines.every((l) => l.trim().startsWith('- '))) {
      return `<ul style="margin:0 0 18px;padding-left:22px;">${lines.map((l) => `<li style="margin:0 0 6px;">${inlineHtml(l.trim().slice(2))}</li>`).join('')}</ul>`;
    }
    return `<p style="${P}">${lines.map(inlineHtml).join('<br>')}</p>`;
  }).join('\n');
  const unsub = unsubUrl(to);
  const footer = `You're getting this because ${footerReason}. <a href="${unsub}" style="color:#888;">Unsubscribe</a><br>${esc(COMPANY_LINE)}`;
  const preheader = email.preheader
    ? `<div style="display:none;max-height:0;overflow:hidden;opacity:0;">${esc(fill(email.preheader))}</div>`
    : '';
  const fullHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#ffffff;">${preheader}
<div style="max-width:560px;margin:0 auto;padding:24px 20px;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;color:#2D2D2D;">
${html}
<p style="margin:32px 0 0;font-size:12px;line-height:1.5;color:#888;">${footer}</p>
</div></body></html>`;
  const text = blocks.map((b) => b.split('\n').map((l) => inlineText(l)).join('\n')).join('\n\n')
    + `\n\n---\nYou're getting this because ${footerReason}. Unsubscribe: ${unsub}\n${COMPANY_LINE}`;
  return { subject: fill(email.subject), html: fullHtml, text, unsub };
}

async function sendEmail({ to, email, firstName, footerReason, tagSeq }) {
  const r = render(email, { firstName, to, footerReason });
  const res = await rs('/emails', {
    method: 'POST',
    body: {
      from: FROM,
      to: [to],
      reply_to: REPLY_TO,
      subject: r.subject,
      html: r.html,
      text: r.text,
      headers: { 'List-Unsubscribe': `<${r.unsub}>`, 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click' },
      tags: tagSeq ? [{ name: 'sequence', value: tagSeq.replace(/[^a-zA-Z0-9_-]/g, '_') }] : undefined,
    },
  });
  if (!res.ok) throw new Error(`Resend send ${res.status} ${res.text.slice(0, 200)}`);
  return res.json.id;
}

function parseResendDate(s) {
  // Resend returns "2026-09-23 21:24:02.212483+00"
  return Date.parse(String(s).replace(' ', 'T').replace(/\+00$/, 'Z'));
}

// UK hour right now (handles BST/GMT).
function ukHour(d = new Date()) {
  return Number(new Intl.DateTimeFormat('en-GB', { hour: 'numeric', hour12: false, timeZone: 'Europe/London' }).format(d));
}

module.exports = {
  SEQUENCES, MAGNET_TO_SEQUENCE, GENERAL_AUDIENCE,
  rs, sequenceAudienceId, getContact, listContacts,
  unsubToken, unsubUrl, render, sendEmail, parseResendDate, ukHour,
};
