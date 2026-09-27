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
  'cash-reset': 'Money Reset Tool',
  'finance-fridays': 'Finance Fridays',
  sequences: 'Welcome emails',
};

function label(magnetKey) {
  return MAGNET_LABELS[magnetKey] || magnetKey || 'unknown magnet';
}

// Joel, 27 Sep: alerts go to Fred (Telegram), where every other robot already reports. Slack is only used if
// Fred's variables are missing and a Slack webhook is set.
async function post(body) {
  const { TELEGRAM_BOT_TOKEN: tg, TELEGRAM_CHAT_ID: chat } = process.env;
  if (tg && chat) {
    try {
      const res = await fetch(`https://api.telegram.org/bot${tg}/sendMessage`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: chat, text: body.text, disable_web_page_preview: true }),
      });
      if (!res.ok) console.error(`[fred] ${res.status}: ${(await res.text()).slice(0, 200)}`);
      return { ok: res.ok };
    } catch (err) {
      console.error('[fred] network error:', err.message);
      return { ok: false, error: err.message };
    }
  }
  const url = process.env.SLACK_WEBHOOK_URL;
  if (!url) {
    console.warn('[alerts] Neither Fred nor Slack is set, skipping notification.');
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
    text: `⚠️ ${magnetName} FAILED for ${email || 'unknown email'}
Reason: ${reason}
Detail: ${String(detail || '—').slice(0, 400)}`,
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
