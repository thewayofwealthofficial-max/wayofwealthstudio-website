// Lead-magnet form handler. Adds subscriber to a MailerLite group.
//
// Env vars required (Netlify → Site settings → Environment variables):
//   MAILERLITE_API_TOKEN              — from MailerLite → Integrations → API
//   MAILERLITE_GROUP_BUDGET_TRACKER   — group ID for the Budget Tracker magnet
//   (Add MAILERLITE_GROUP_<MAGNET_NAME> for each future magnet.)
//   SLACK_WEBHOOK_URL                 — same incoming webhook the diagnostic uses.
//                                       Optional: if unset, Slack pings skip quietly.
//
// Flow:
//   1. Validate payload (email + magnet key + honeypot)
//   2. Resolve MailerLite group ID from MAGNET_GROUP_MAP
//   3. POST to https://connect.mailerlite.com/api/subscribers
//      with the email, optional name, group ID, and source field
//   4. Return { ok: true } so the frontend redirects to /thanks/<magnet>

const { notifyLeadCaptured, notifyCaptureFailed } = require('./lib/slack');

const ML_API = 'https://connect.mailerlite.com/api/subscribers';

// Map magnet keys → env var that holds the MailerLite group ID for that magnet.
const MAGNET_GROUP_MAP = {
  'budget-tracker': 'MAILERLITE_GROUP_BUDGET_TRACKER',
  'cashflow-model': 'MAILERLITE_GROUP_CASHFLOW_MODEL',
  // Add more as we ship them, e.g. 'mindset-workbook': 'MAILERLITE_GROUP_MINDSET_WORKBOOK'
};

// Disposable / temp / obvious-junk domains. Mirrors the client-side list.
// MailerLite catches the rest server-side via bounce checks — this just
// stops the worst offenders before we make the API call.
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

  // Honeypot — if filled, silently drop (return 200 so bot thinks it worked)
  if (honeypot) {
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  }

  const v = validateEmail(email);
  if (!v.ok) {
    return { statusCode: 400, body: JSON.stringify({ error: v.error }) };
  }

  const magnetKey = (magnet || '').toString();
  const envVarName = MAGNET_GROUP_MAP[magnetKey];
  if (!envVarName) {
    return { statusCode: 400, body: JSON.stringify({ error: 'Unknown magnet.' }) };
  }

  const apiToken = process.env.MAILERLITE_API_TOKEN;
  const groupId = process.env[envVarName];

  if (!apiToken || !groupId) {
    await notifyCaptureFailed({
      email: v.email,
      magnet: magnetKey,
      reason: 'Email setup missing',
      detail: !apiToken ? 'MAILERLITE_API_TOKEN not set' : `${envVarName} not set`,
    });
    return {
      statusCode: 503,
      body: JSON.stringify({
        error: "I'm finalising the email setup. Please email joel@thewayofwealth.shop and I'll send the tracker directly.",
      }),
    };
  }

  const subBody = {
    email: v.email,
    groups: [groupId],
    fields: {
      source: `lead-magnet:${magnetKey}`,
    },
  };
  if (name && typeof name === 'string') {
    subBody.fields.name = name.trim().slice(0, 80);
  }

  try {
    const res = await fetch(ML_API, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(subBody),
    });

    // MailerLite returns 200/201 for new + existing subscribers (idempotent add to group)
    if (res.status === 200 || res.status === 201) {
      await notifyLeadCaptured({ email: v.email, name: subBody.fields.name, magnet: magnetKey });
      return { statusCode: 200, body: JSON.stringify({ ok: true }) };
    }

    // 422 = validation issue, e.g. bouncing email. Treat as user error.
    if (res.status === 422) {
      const body = await res.json().catch(() => ({}));
      const msg = body?.message || 'That email looks invalid. Try another?';
      await notifyCaptureFailed({ email: v.email, magnet: magnetKey, reason: 'MailerLite rejected the email (422)', detail: msg });
      return { statusCode: 400, body: JSON.stringify({ error: msg }) };
    }

    // Anything else — log + return generic error
    const text = await res.text().catch(() => '');
    console.error('[lead-magnet-subscribe] MailerLite error', res.status, text);
    await notifyCaptureFailed({ email: v.email, magnet: magnetKey, reason: `MailerLite error ${res.status}`, detail: text });
    return {
      statusCode: 502,
      body: JSON.stringify({ error: 'Email service failed. Email joel@thewayofwealth.shop and I will send the tracker directly.' }),
    };
  } catch (err) {
    console.error('[lead-magnet-subscribe] fetch failed', err);
    await notifyCaptureFailed({ email: v.email, magnet: magnetKey, reason: 'Network error talking to MailerLite', detail: err.message });
    return {
      statusCode: 502,
      body: JSON.stringify({ error: 'Network error talking to email service. Try again or email joel@thewayofwealth.shop.' }),
    };
  }
};
