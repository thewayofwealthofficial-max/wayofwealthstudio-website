// Signup + lead-magnet form handler.
//
// Every signup is saved to RESEND (the main email list, audience "General").
// While MailerLite is still in use for old sequences, it is ALSO saved there (a second copy).
// If either one succeeds the visitor sees success; Joel is pinged on Slack if both fail.
//
// Env vars (Netlify site settings):
//   RESEND_API_KEY                    Resend key, used for the email list only
//   RESEND_AUDIENCE_ID                optional, defaults to the "General" audience
//   MAILERLITE_API_TOKEN              optional second copy while MailerLite still runs sequences
//   MAILERLITE_GROUP_<MAGNET>         optional group id per magnet (see MAGNET_GROUP_MAP)
//   SLACK_WEBHOOK_URL                 optional, Slack pings skip quietly if unset
//
// Rules: nobody who has unsubscribed is ever re-subscribed by a form.

const { notifyLeadCaptured, notifyCaptureFailed } = require('./lib/slack');

const ML_API = 'https://connect.mailerlite.com/api/subscribers';
const RESEND_API = 'https://api.resend.com';
const DEFAULT_AUDIENCE = 'ed40086b-fccc-4755-8744-72085ceac3e7'; // "General"

const MAGNET_GROUP_MAP = {
  'finance-fridays': 'MAILERLITE_GROUP_FINANCE_FRIDAYS',
  'budget-tracker': 'MAILERLITE_GROUP_BUDGET_TRACKER',
  'cashflow-model': 'MAILERLITE_GROUP_CASHFLOW_MODEL',
  // The Cashflow Shield at /reset. Gates the annual leak figure only.
  'cash-reset': 'MAILERLITE_GROUP_CASH_RESET',
};

const BAD_DOMAINS = new Set([
  'mailinator.com', 'guerrillamail.com', 'guerrillamail.info', 'guerrillamail.biz',
  '10minutemail.com', '10minutemail.net', 'tempmail.com', 'temp-mail.org',
  'yopmail.com', 'throwaway.email', 'maildrop.cc', 'getnada.com', 'sharklasers.com',
  'mintemail.com', 'mohmal.com', 'fakeinbox.com', 'trashmail.com', 'mailcatch.com',
  'spamgourmet.com', 'dispostable.com', 'tempinbox.com', 'mailnesia.com',
  'discard.email', 'spambog.com', 'tempmailo.com', 'emailondeck.com',
  'example.com', 'test.com', 'asdf.com', 'a.com', 'b.com',
]);

function validateEmail(s) {
  if (typeof s !== 'string') return { ok: false, error: 'Email is required.' };
  const email = s.trim().toLowerCase();
  if (email.length > 254) return { ok: false, error: 'That email is too long.' };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return { ok: false, error: 'Please enter a valid email.' };
  const domain = email.split('@')[1];
  if (!domain || !domain.includes('.')) return { ok: false, error: 'That domain looks invalid.' };
  if (BAD_DOMAINS.has(domain)) return { ok: false, error: "I can't send to a temp/disposable address. Use your real email." };
  return { ok: true, email };
}

async function addToResend({ email, name }) {
  const key = process.env.RESEND_API_KEY;
  if (!key) return { ok: false, skipped: true, detail: 'RESEND_API_KEY not set' };
  const audience = process.env.RESEND_AUDIENCE_ID || DEFAULT_AUDIENCE;
  const headers = { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' };
  try {
    // Never re-subscribe someone who opted out.
    const found = await fetch(`${RESEND_API}/audiences/${audience}/contacts/${encodeURIComponent(email)}`, { headers });
    if (found.ok) {
      const c = await found.json().catch(() => ({}));
      if (c && c.unsubscribed) return { ok: true, note: 'previously unsubscribed, left as is' };
      return { ok: true, note: 'already on the list' };
    }
    const res = await fetch(`${RESEND_API}/audiences/${audience}/contacts`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ email, first_name: name ? String(name).trim().split(/\s+/)[0].slice(0, 60) : undefined, unsubscribed: false }),
    });
    if (res.ok) return { ok: true };
    const text = await res.text().catch(() => '');
    return { ok: false, detail: `Resend ${res.status} ${text.slice(0, 160)}` };
  } catch (e) {
    return { ok: false, detail: 'Resend request failed: ' + e.message };
  }
}

async function addToMailerLite({ email, name, magnetKey }) {
  const token = process.env.MAILERLITE_API_TOKEN;
  const groupId = process.env[MAGNET_GROUP_MAP[magnetKey]];
  if (!token || !groupId) return { ok: false, skipped: true, detail: 'MailerLite not configured for this magnet' };
  const body = { email, groups: [groupId], fields: { source: `lead-magnet:${magnetKey}` } };
  if (name) body.fields.name = String(name).trim().slice(0, 80);
  try {
    const res = await fetch(ML_API, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.status === 200 || res.status === 201) return { ok: true };
    const text = await res.text().catch(() => '');
    return { ok: false, detail: `MailerLite ${res.status} ${text.slice(0, 160)}` };
  } catch (e) {
    return { ok: false, detail: 'MailerLite request failed: ' + e.message };
  }
}

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  let payload;
  try {
    payload = JSON.parse(event.body || '{}');
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: 'Invalid JSON' }) };
  }

  const { email, name, magnet, honeypot } = payload;

  // Honeypot: if filled, silently drop (return 200 so the bot thinks it worked)
  if (honeypot) return { statusCode: 200, body: JSON.stringify({ ok: true }) };

  const v = validateEmail(email);
  if (!v.ok) return { statusCode: 400, body: JSON.stringify({ error: v.error }) };

  const magnetKey = (magnet || '').toString();
  if (!MAGNET_GROUP_MAP[magnetKey]) return { statusCode: 400, body: JSON.stringify({ error: 'Unknown magnet.' }) };

  const cleanName = name && typeof name === 'string' ? name.trim().slice(0, 80) : '';
  const [resend, mailerlite] = await Promise.all([
    addToResend({ email: v.email, name: cleanName }),
    addToMailerLite({ email: v.email, name: cleanName, magnetKey }),
  ]);

  if (resend.ok || mailerlite.ok) {
    if (!resend.ok && !resend.skipped) {
      await notifyCaptureFailed({ email: v.email, magnet: magnetKey, reason: 'Saved to MailerLite but NOT to Resend', detail: resend.detail });
    }
    await notifyLeadCaptured({ email: v.email, name: cleanName, magnet: magnetKey });
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  }

  console.error('[lead-magnet-subscribe] both saves failed', resend.detail, mailerlite.detail);
  await notifyCaptureFailed({ email: v.email, magnet: magnetKey, reason: 'Could not save the signup anywhere', detail: `${resend.detail} | ${mailerlite.detail}` });
  return {
    statusCode: 503,
    body: JSON.stringify({ error: "Something went wrong on my side. Please email joel@thewayofwealth.shop and I'll add you by hand." }),
  };
};
