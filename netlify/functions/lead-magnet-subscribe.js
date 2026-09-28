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
const { connectLambda, getStore } = require('@netlify/blobs');
const seq = require('./lib/sequence-core');

const ML_API = 'https://connect.mailerlite.com/api/subscribers';
const RESEND_API = 'https://api.resend.com';
const DEFAULT_AUDIENCE = 'ed40086b-fccc-4755-8744-72085ceac3e7'; // "General"

const MAGNET_GROUP_MAP = {
  'finance-fridays': 'MAILERLITE_GROUP_FINANCE_FRIDAYS',
  'budget-tracker': 'MAILERLITE_GROUP_BUDGET_TRACKER',
  'cashflow-model': 'MAILERLITE_GROUP_CASHFLOW_MODEL',
  // The Cashflow Shield at /reset. Gates the annual leak figure only.
  'cash-reset': 'MAILERLITE_GROUP_CASH_RESET',
  // Money Story Diagnostic: no MailerLite copy (these env vars are deliberately not set on this site).
  diagnostic: 'MAILERLITE_GROUP_DIAGNOSTIC',
  'diagnostic-qualified': 'MAILERLITE_GROUP_DIAGNOSTIC',
  'diagnostic-avoidance': 'MAILERLITE_GROUP_DIAGNOSTIC',
  'diagnostic-worship': 'MAILERLITE_GROUP_DIAGNOSTIC',
  'diagnostic-status': 'MAILERLITE_GROUP_DIAGNOSTIC',
  'diagnostic-vigilance': 'MAILERLITE_GROUP_DIAGNOSTIC',
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

// The Money Reset Tool (/reset). The person may tick "Email me my numbers too"; only then do figures arrive here.
// They are turned into text for email 1 and never stored anywhere (Joel, 27 Sep).
const CURRENCIES = new Set(['£', '$', '€', 'C$', 'R', '₪']);
function breakdownText(b) {
  if (!b || typeof b !== 'object') return null;
  const cur = CURRENCIES.has(b.cur) ? b.cur : '£';
  const n = (k) => (Number.isFinite(Number(b[k])) && Number(b[k]) >= 0 && Number(b[k]) < 1e8 ? Math.round(Number(b[k])) : null);
  const [rev, tax, run, buffer, payMonth, payWeek, taxPct] = ['rev', 'tax', 'run', 'buffer', 'payMonth', 'payWeek', 'taxPct'].map(n);
  if ([rev, tax, run, buffer, payMonth, payWeek, taxPct].some((x) => x === null)) return null;
  const m = (x) => `${cur}${x.toLocaleString('en-GB')}`;
  return [
    'Each month, roughly:',
    `- **Coming in:** ${m(rev)}`,
    `- **Tax (${taxPct}%):** ${m(tax)}. Swept the day money lands, so the tax money is put aside before you can spend it.`,
    `- **Work bills:** ${m(run)}. What your work costs to run, ring-fenced.`,
    `- **Slow-month buffer:** ${m(buffer)}. Builds up during strong months to protect your pay when you take time off.`,
    `- **Yours to keep:** ${m(payWeek)} a week (${m(payMonth)} a month). A steady wage that stays the same whether you had a big month or a quiet one.`,
  ].join('\n').replace(/\n- /, '\n\n- ');
}

// Sends /reset email 1 on its own: to people already on the list, or running the tool again. They asked for it.
async function sendResetEmail({ email, name, vars }) {
  const def = seq.SEQUENCES['money-reset'];
  try {
    await seq.sendEmail({ to: email, email: def.emails[0], firstName: name, footerReason: def.footerReason, tagSeq: 'money-reset_01-your-numbers', vars });
  } catch (e) {
    // The sign-up itself is saved; tell Joel the email didn't go.
    await notifyCaptureFailed({ email, magnet: 'cash-reset', reason: 'Saved, but the breakdown email did not send', detail: e.message });
  }
}

// New person on a form that has a welcome sequence: enrol them and send email 1 now.
// They join the main list when the sequence ends (see lib/sequence-core.js).
async function startSequence({ event, email, name, seqId, vars = {} }) {
  connectLambda(event);
  const store = getStore('sequences');
  const key = `${seqId}/${email}`;
  // Enrolment lives in Blobs; all sequences share one Resend list (see sequenceAudienceId).
  if (await store.get(key, { type: 'json' })) {
    if (seqId === 'money-reset') await sendResetEmail({ email, name, vars });
    return { ok: true, note: 'already in this sequence' };
  }
  const aud = await seq.sequenceAudienceId();
  if (!(await seq.getContact(aud, email))) {
    const made = await seq.rs(`/audiences/${aud}/contacts`, {
      method: 'POST',
      body: { email, first_name: name ? String(name).trim().split(/\s+/)[0].slice(0, 60) : undefined, unsubscribed: false },
    });
    if (!made.ok) return { ok: false, detail: `Resend enrol ${made.status} ${made.text.slice(0, 160)}` };
  }
  const enrolledAt = new Date().toISOString();
  await store.setJSON(key, { sent: [], enrolledAt });
  const def = seq.SEQUENCES[seqId];
  const first = def.emails[0];
  try {
    await seq.sendEmail({ to: email, email: first, firstName: name, footerReason: def.footerReason, tagSeq: `${seqId}_${first.id}`, vars });
    await store.setJSON(key, { sent: [first.id], lastSentAt: new Date().toISOString(), enrolledAt });
  } catch (e) {
    // They are enrolled; the hourly runner will send email 1 if this failed.
    console.error('[lead-magnet-subscribe] email 1 not sent now:', e.message);
  }
  return { ok: true, note: `enrolled in ${seqId}` };
}

async function addToResend({ email, name, magnetKey, event, vars = {} }) {
  const isReset = magnetKey === 'cash-reset';
  const key = process.env.RESEND_API_KEY;
  if (!key) return { ok: false, skipped: true, detail: 'RESEND_API_KEY not set' };
  const audience = process.env.RESEND_AUDIENCE_ID || DEFAULT_AUDIENCE;
  const headers = { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' };
  try {
    // Never re-subscribe someone who opted out.
    const found = await fetch(`${RESEND_API}/audiences/${audience}/contacts/${encodeURIComponent(email)}`, { headers });
    if (found.ok) {
      const c = await found.json().catch(() => ({}));
      // They asked for their breakdown, so /reset email 1 goes even to people already on the list (no re-enrolling,
      // and an unsubscribed person stays unsubscribed).
      if (isReset) await sendResetEmail({ email, name, vars });
      if (c && c.unsubscribed) return { ok: true, note: 'previously unsubscribed, left as is' };
      // The diagnostic's series is their report and what it means, so it runs even for people already on the list.
      // (Its safety-net capture adds them to the list seconds before this call.)
      if (!magnetKey.startsWith('diagnostic-')) return { ok: true, note: 'already on the list' };
    }
    // Kill switch: sequences only start once SEQUENCES_ENABLED=true is set on Netlify.
    // A test address can be enrolled early with SEQUENCES_TEST_EMAIL.
    const seqId = seq.MAGNET_TO_SEQUENCE[magnetKey];
    const seqOn = process.env.SEQUENCES_ENABLED === 'true' || email === (process.env.SEQUENCES_TEST_EMAIL || '').toLowerCase();
    if (seqId && seqOn) return await startSequence({ event, email, name, seqId, vars });
    const res = await fetch(`${RESEND_API}/audiences/${audience}/contacts`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ email, first_name: name ? String(name).trim().split(/\s+/)[0].slice(0, 60) : undefined, unsubscribed: false }),
    });
    if (res.ok) {
      if (isReset) await sendResetEmail({ email, name, vars });
      return { ok: true };
    }
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

  const { email, name, magnet, honeypot, breakdown } = payload;
  // Only present when the person ticked "Email me my numbers too" on /reset. Used for email 1, never stored.
  const bd = magnet === 'cash-reset' ? breakdownText(breakdown) : null;
  const vars = bd ? { breakdown: bd } : {};
  // The diagnostic sends the person's own report link for its day-1 email. Only its own report links are accepted.
  if (typeof payload.report_url === 'string' && payload.report_url.startsWith('https://discover.thewayofwealth.shop/.netlify/functions/report?') && payload.report_url.length < 600) {
    vars.report_line = `Your full Money Story Report is ready, the whole thing in one place: [open your report](${payload.report_url})`;
  }

  // Honeypot: if filled, silently drop (return 200 so the bot thinks it worked)
  if (honeypot) return { statusCode: 200, body: JSON.stringify({ ok: true }) };

  const v = validateEmail(email);
  if (!v.ok) return { statusCode: 400, body: JSON.stringify({ error: v.error }) };

  const magnetKey = (magnet || '').toString();
  if (!MAGNET_GROUP_MAP[magnetKey]) return { statusCode: 400, body: JSON.stringify({ error: 'Unknown magnet.' }) };

  const cleanName = name && typeof name === 'string' ? name.trim().slice(0, 80) : '';
  const [resend, mailerlite] = await Promise.all([
    addToResend({ email: v.email, name: cleanName, magnetKey, event, vars }),
    addToMailerLite({ email: v.email, name: cleanName, magnetKey }),
  ]);

  if (resend.ok || mailerlite.ok) {
    if (!resend.ok && !resend.skipped) {
      await notifyCaptureFailed({ email: v.email, magnet: magnetKey, reason: 'Saved to MailerLite but NOT to Resend', detail: resend.detail });
    }
    // The diagnostic calls twice (a safety net, then the routed one); one alert per lead is enough.
    if (magnetKey !== 'diagnostic') await notifyLeadCaptured({ email: v.email, name: cleanName, magnet: magnetKey });
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  }

  console.error('[lead-magnet-subscribe] both saves failed', resend.detail, mailerlite.detail);
  await notifyCaptureFailed({ email: v.email, magnet: magnetKey, reason: 'Could not save the signup anywhere', detail: `${resend.detail} | ${mailerlite.detail}` });
  return {
    statusCode: 503,
    body: JSON.stringify({ error: "Something went wrong on my side. Please email joel@wayofwealthcoaching.com and I'll add you by hand." }),
  };
};
