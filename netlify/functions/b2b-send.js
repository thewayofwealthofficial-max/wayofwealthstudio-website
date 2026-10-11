// Netlify function: GET /api/b2b/send?week=<yyyy-mm-dd>&id=<card id or "all">&sig=<hmac16>
//
// The Friday big swing (scripts/b2b-friday.mjs) saves each pitch that has an
// email address to scripts/state/b2b/pending.json and puts a "✅ Send" link
// under it in Fred's Telegram message (Joel, 11 Oct 2026: send from
// joel@wayofwealthcoaching.com once he taps yes). This function checks the link
// is genuine and recent, sends exactly the saved draft from
// joel@wayofwealthcoaching.com (replies forward to Joel's Gmail, a blind copy
// goes there too), and marks it sent so a second tap can't send it twice.
// Pitches with only a contact form never get a link.
//
// Same signing pattern as fred-approve.js. Netlify env: FRED_SECRET,
// GITHUB_DISPATCH_PAT, GITHUB_REPO, RESEND_API_KEY.
// Signature: hmac16 = HMAC-SHA256(FRED_SECRET, `b2b:${week}:${id}`).slice(0, 16)

const crypto = require('crypto');

const TTL_MS = 6 * 24 * 60 * 60 * 1000; // a week's batch stays sendable until the next Friday
const FROM = 'Joel Ezekiel <joel@wayofwealthcoaching.com>';
const REPLY_TO = 'joel@wayofwealthcoaching.com';
const COPY_TO = 'joeleezekiel@gmail.com';
const FILE = 'scripts/state/b2b/pending.json';

const { FRED_SECRET, GITHUB_DISPATCH_PAT, GITHUB_REPO, RESEND_API_KEY } = process.env;

const escapeHtml = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function html(status, body) {
  return {
    statusCode: status,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
    body: `<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fred</title><style>body{font-family:-apple-system,Segoe UI,sans-serif;max-width:30rem;margin:4rem auto;padding:0 1rem;color:#222;line-height:1.5}h1{font-size:1.25rem;margin-bottom:.5rem}p,li{margin:.4rem 0}</style>${body}`,
  };
}

function sign(week, id) {
  return crypto.createHmac('sha256', FRED_SECRET).update(`b2b:${week}:${id}`).digest('hex').slice(0, 16);
}

function sigOk(week, id, sig) {
  const a = Buffer.from(String(sig || ''));
  const b = Buffer.from(sign(week, id));
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

async function github(method, body) {
  const res = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/contents/${FILE}`, {
    method,
    headers: {
      Authorization: `Bearer ${GITHUB_DISPATCH_PAT}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`GitHub ${method} ${res.status}`);
  return res.json();
}

async function sendOne(item, week) {
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${RESEND_API_KEY}`,
      'Content-Type': 'application/json',
      // Two quick taps on the same link send once.
      'Idempotency-Key': `b2b-${week}-${item.id}`,
    },
    body: JSON.stringify({ from: FROM, to: [item.to], bcc: [COPY_TO], reply_to: REPLY_TO, subject: item.subject, text: item.body }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || `Resend ${res.status}`);
  return data.id;
}

exports.handler = async (event) => {
  if (!FRED_SECRET || !GITHUB_DISPATCH_PAT || !GITHUB_REPO || !RESEND_API_KEY) {
    return html(500, '<h1>Not set up</h1><p>A Netlify environment variable is missing.</p>');
  }
  const { week, id, sig } = event.queryStringParameters || {};
  if (!week || !id || !sigOk(week, id, sig)) {
    return html(400, '<h1>⛔ This link isn\'t valid</h1><p>Nothing was sent.</p>');
  }
  if (Date.now() - Date.parse(`${week}T00:00:00Z`) > TTL_MS) {
    return html(400, '<h1>⛔ This link has expired</h1><p>Nothing was sent. Send it yourself from the text in Telegram.</p>');
  }

  let file;
  try {
    file = await github('GET');
  } catch (err) {
    return html(502, `<h1>Couldn't reach GitHub</h1><p>Nothing was sent. ${escapeHtml(err.message)}</p>`);
  }
  const pending = JSON.parse(Buffer.from(file.content, 'base64').toString('utf8'));
  if (pending.week !== week) {
    return html(400, '<h1>⛔ A newer batch has replaced this one</h1><p>Nothing was sent.</p>');
  }

  const chosen = (pending.items || []).filter((it) => it.to && (id === 'all' || it.id === id));
  const toSend = chosen.filter((it) => !it.sent_at);
  if (!chosen.length) return html(404, '<h1>Not found</h1><p>Nothing was sent.</p>');
  if (!toSend.length) {
    return html(200, `<h1>Already sent</h1><ul>${chosen.map((it) => `<li>${escapeHtml(it.name)}: sent ${escapeHtml(it.sent_at)}</li>`).join('')}</ul>`);
  }

  const sent = [];
  const failed = [];
  for (const it of toSend) {
    try {
      await sendOne(it, week);
      it.sent_at = new Date().toISOString();
      sent.push(it);
    } catch (err) {
      failed.push(`${it.name}: ${err.message}`);
    }
  }

  // Remember what went, so the same link can't send it again next week.
  if (sent.length) {
    try {
      await github('PUT', {
        message: `b2b: sent ${sent.map((s) => s.id).join(', ')} (${week})`,
        content: Buffer.from(JSON.stringify(pending, null, 1)).toString('base64'),
        sha: file.sha,
      });
    } catch (err) {
      failed.push(`(sent, but couldn't record it: ${err.message})`);
    }
  }

  return html(failed.length && !sent.length ? 502 : 200,
    `<h1>${sent.length ? '✅ Sent' : '❌ Not sent'}</h1>` +
      (sent.length ? `<p>From joel@wayofwealthcoaching.com, with a copy to your Gmail:</p><ul>${sent.map((s) => `<li>${escapeHtml(s.name)} (${escapeHtml(s.to)})</li>`).join('')}</ul>` : '') +
      (failed.length ? `<p>Problems:</p><ul>${failed.map((f) => `<li>${escapeHtml(f)}</li>`).join('')}</ul>` : '') +
      '<p>Replies come to your Gmail.</p>');
};
