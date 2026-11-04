// Netlify function: POST /.netlify/functions/fred-relay
//
// Resend calls this webhook when an email is sent. If the email is a check-in from
// Joel's agents (from fred@wayofwealthcoaching.com, subject starting "[Fred]"), it
// starts the fred-relay GitHub Action, which fetches the email from Resend and sends
// it to Joel on Telegram through Fred. Agents in scheduled runs can't push to GitHub,
// but they can send email, so this is how their check-ins reach Telegram.
//
// Required Netlify env vars:
//   RESEND_WEBHOOK_SECRET — the webhook's signing secret (whsec_...), from Resend
//   GITHUB_DISPATCH_PAT   — PAT with repo scope (already used by fred-approve)
//   GITHUB_REPO           — "owner/name" of this repo (already set)

const crypto = require('crypto');

const { RESEND_WEBHOOK_SECRET, GITHUB_DISPATCH_PAT, GITHUB_REPO } = process.env;
const FROM = 'fred@wayofwealthcoaching.com';

function verify(headers, raw) {
  const id = headers['svix-id'];
  const ts = headers['svix-timestamp'];
  const sigs = headers['svix-signature'];
  if (!id || !ts || !sigs || !RESEND_WEBHOOK_SECRET) return false;
  if (Math.abs(Date.now() / 1000 - Number(ts)) > 300) return false;
  const key = Buffer.from(RESEND_WEBHOOK_SECRET.replace(/^whsec_/, ''), 'base64');
  const expected = crypto.createHmac('sha256', key).update(`${id}.${ts}.${raw}`).digest('base64');
  return sigs.split(' ').some((s) => {
    const v = s.split(',')[1] || '';
    const a = Buffer.from(v);
    const b = Buffer.from(expected);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  });
}

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'POST only' };
  const raw = event.isBase64Encoded ? Buffer.from(event.body || '', 'base64').toString('utf8') : event.body || '';
  const headers = Object.fromEntries(Object.entries(event.headers || {}).map(([k, v]) => [k.toLowerCase(), v]));
  if (!verify(headers, raw)) return { statusCode: 401, body: 'bad signature' };

  let payload;
  try { payload = JSON.parse(raw); } catch { return { statusCode: 400, body: 'bad json' }; }
  const d = payload.data || {};
  const from = String(d.from || '').toLowerCase();
  const subject = String(d.subject || '');
  if (payload.type !== 'email.sent' || !from.includes(FROM) || !subject.startsWith('[Fred]') || !d.email_id) {
    return { statusCode: 200, body: 'ignored' };
  }

  const res = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/dispatches`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${GITHUB_DISPATCH_PAT}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ event_type: 'fred-relay', client_payload: { email_id: d.email_id } }),
  });
  if (!res.ok) return { statusCode: 502, body: `dispatch failed ${res.status}` };
  return { statusCode: 200, body: 'relayed' };
};
