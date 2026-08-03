// Slack notifications for the lead magnets. Mirrors the Money Story Diagnostic's
// lib/slack.js, but CommonJS to match the website's functions.
//
// Env var required (Netlify → wow-website site → Environment variables):
//   SLACK_WEBHOOK_URL — same incoming webhook the diagnostic uses.
//
// Both helpers are best-effort: they never throw, and a Slack outage must never
// stop a lead being saved. If the webhook isn't set, they skip quietly.

const MAGNET_LABELS = {
  'cashflow-model': 'Cash Flow Model',
  'budget-tracker': 'Budget Tracker',
};

function label(magnetKey) {
  return MAGNET_LABELS[magnetKey] || magnetKey || 'unknown magnet';
}

async function post(body) {
  const url = process.env.SLACK_WEBHOOK_URL;
  if (!url) {
    console.warn('[slack] SLACK_WEBHOOK_URL not set — skipping notification.');
    return { ok: false, skipped: true };
  }
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      console.error(`[slack] ${res.status}: ${(await res.text()).slice(0, 200)}`);
      return { ok: false, error: `slack ${res.status}` };
    }
    return { ok: true };
  } catch (err) {
    console.error('[slack] network error:', err.message);
    return { ok: false, error: err.message };
  }
}

// Fires when someone hands over their email and MailerLite accepted it.
async function notifyLeadCaptured({ email, name, magnet }) {
  const magnetName = label(magnet);
  const who = name ? `${name} (${email})` : email;
  return post({
    text: `New ${magnetName} lead: ${email}`,
    blocks: [
      { type: 'header', text: { type: 'plain_text', text: `📥 New ${magnetName} lead` } },
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Who:*\n${who}` },
          { type: 'mrkdwn', text: `*Magnet:*\n${magnetName}` },
        ],
      },
    ],
  });
}

// Fires when a real person tried to hand over their email and we failed to save it.
// This is the one that matters: the front end ignores the response, so without
// this the lead is lost silently.
async function notifyCaptureFailed({ email, magnet, reason, detail }) {
  const magnetName = label(magnet);
  return post({
    text: `⚠️ ${magnetName} capture FAILED for ${email || 'unknown email'}`,
    blocks: [
      { type: 'header', text: { type: 'plain_text', text: `⚠️ ${magnetName} capture failed` } },
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Email:*\n${email || '—'}` },
          { type: 'mrkdwn', text: `*Reason:*\n${reason}` },
        ],
      },
      {
        type: 'section',
        text: { type: 'mrkdwn', text: `*Detail:*\n\`${String(detail || '—').slice(0, 400)}\`` },
      },
      {
        type: 'context',
        elements: [{ type: 'mrkdwn', text: 'They still got their report. You did not get the lead.' }],
      },
    ],
  });
}

module.exports = { notifyLeadCaptured, notifyCaptureFailed };
