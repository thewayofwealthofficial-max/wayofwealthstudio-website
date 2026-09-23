#!/usr/bin/env node
// Daily subscriber email, fully automatic, sent through Resend.
//
//   1. (live only) sync MailerLite -> Resend so opt-outs are always respected
//   2. pull competitor email angles from Gmail (optional; angles only, never copied)
//   3. draft in Joel's voice with Anthropic, then run automatic safety checks
//      (regenerate with the problems fed back, up to 3 tries; if it still fails, skip the day)
//   4. send as a Resend broadcast, with a proper unsubscribe link
//   5. tell Joel on Telegram exactly what went out
//
// MODES (DAILY_EMAIL_MODE):  dry  = draft + check, send nothing
//                            test = send to the private "Test" audience only (Joel)
//                            live = send to the "General" audience (the real list)
//
// ENV: RESEND_API_KEY, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
//      MAILERLITE_API_KEY (live sync), GMAIL_* (optional intel), TEST_EMAIL (test mode)
// OPTIONAL: DAILY_EMAIL_MODEL, DAILY_CALL_URL, DAILY_EMAIL_FOOTER_ADDRESS, RESEND_AUDIENCE_NAME

import process from 'node:process';
import { fetchCompetitorEmails, parseSenderName } from '../gmail-client.mjs';
import { buildFunnelhackQuery } from '../funnelhack-senders.mjs';
import { SYSTEM_PROMPT, buildUserPrompt, FROM_NAME, FROM_EMAIL } from './voice.mjs';
import { draftEmail } from './anthropic.mjs';
import { checkDraft, clean } from './safety.mjs';
import { findOrCreateAudience, addContact, listContacts, listBroadcasts, createBroadcast, sendBroadcast } from './resend.mjs';
import { syncList } from './sync-list.mjs';

const MODE = (process.env.DAILY_EMAIL_MODE || 'dry').toLowerCase();
const MODEL = process.env.DAILY_EMAIL_MODEL || 'claude-sonnet-4-6';
const CTA_URL = process.env.DAILY_CALL_URL || 'https://calendly.com/thewayofwealth-official/20min';
const MAX_TRIES = 3;

function need(name) {
  const v = process.env[name];
  if (!v) { console.error('FATAL: missing env var ' + name); process.exit(1); }
  return v;
}

async function telegram(text) {
  const token = process.env.TELEGRAM_BOT_TOKEN, chat = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chat) return;
  try {
    await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chat, text: text.slice(0, 3900), disable_web_page_preview: true }),
    });
  } catch (e) { console.error('Telegram notify failed:', e.message); }
}

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function toHtml(body, footerAddress) {
  const paras = body.split(/\n{2,}/).map((p) => {
    let h = esc(p).replace(/\n/g, '<br>');
    h = h.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1">$1</a>');
    return `<p style="margin:0 0 16px;line-height:1.6;">${h}</p>`;
  }).join('\n');
  const foot = [
    'You are getting this because you signed up at thewayofwealth.shop.',
    footerAddress ? esc(footerAddress) : '',
    '<a href="{{{RESEND_UNSUBSCRIBE_URL}}}">Unsubscribe</a>',
  ].filter(Boolean).join(' &nbsp;·&nbsp; ');
  return `<div style="font-family:Georgia,'Times New Roman',serif;font-size:17px;color:#2D2D2D;max-width:560px;margin:0 auto;padding:8px;">\n${paras}\n<hr style="border:none;border-top:1px solid #ddd;margin:28px 0 12px;">\n<p style="font-size:12px;color:#777;line-height:1.5;">${foot}</p>\n</div>`;
}

function toText(body, footerAddress) {
  return `${body}\n\n--\nYou are getting this because you signed up at thewayofwealth.shop.${footerAddress ? '\n' + footerAddress : ''}\nUnsubscribe: {{{RESEND_UNSUBSCRIBE_URL}}}`;
}

async function main() {
  const resendKey = need('RESEND_API_KEY');
  const anthropicKey = need('ANTHROPIC_API_KEY');
  const dateStr = new Date().toISOString().slice(0, 10);
  console.log(`[${new Date().toISOString()}] Daily email. Mode: ${MODE}. Model: ${MODEL}`);

  // Never send twice in one day (covers manual re-runs).
  if (MODE === 'live') {
    const already = (await listBroadcasts(resendKey)).find((b) => (b.name || '') === `Daily ${dateStr}` && b.status !== 'draft');
    if (already) { console.log('Already sent today. Nothing to do.'); return; }
  }

  // 1. Keep the list in step (live only).
  let syncNote = '';
  const audienceName = process.env.RESEND_AUDIENCE_NAME || 'General';
  const audienceId = await findOrCreateAudience(resendKey, MODE === 'test' ? 'Test' : audienceName);
  if (MODE === 'live') {
    const mlKey = need('MAILERLITE_API_KEY');
    try {
      const s = await syncList({ mlKey, resendKey, audienceId });
      syncNote = `List sync: +${s.added} new, ${s.markedUnsub + s.mlUnsubscribed} opt-outs applied. Sendable: ${s.sendableAfterSync}.`;
      console.log(syncNote);
    } catch (e) {
      console.error('List sync failed (sending to the list as it already stands):', e.message);
      syncNote = 'List sync FAILED, sent to the list as it stood. ' + e.message.slice(0, 120);
    }
  }

  // 2. Competitor angles (optional).
  let intel = [];
  if (process.env.GMAIL_REFRESH_TOKEN) {
    try {
      const msgs = await fetchCompetitorEmails({
        clientId: process.env.GMAIL_CLIENT_ID, clientSecret: process.env.GMAIL_CLIENT_SECRET,
        refreshToken: process.env.GMAIL_REFRESH_TOKEN, query: buildFunnelhackQuery({ days: 1 }), maxBodies: 20,
      });
      intel = msgs.map((m) => ({ sender: parseSenderName(m.from), subject: m.subject, snippet: (m.snippet || m.body || '').slice(0, 200) }));
      console.log(`Pulled ${intel.length} competitor email(s) for angle inspiration.`);
    } catch (e) { console.error('Gmail intel failed (drafting from core themes instead): ' + e.message); syncNote += ' Competitor intel unavailable today.'; }
  }
  const intelText = intel.map((m) => `${m.sender} ${m.subject} ${m.snippet}`).join(' ');

  // 3. Draft + safety check, with the problems fed back on each retry.
  let draft = null, problems = [], feedback = '';
  for (let attempt = 1; attempt <= MAX_TRIES; attempt++) {
    const d = await draftEmail({ apiKey: anthropicKey, model: MODEL, system: SYSTEM_PROMPT, user: buildUserPrompt({ intel, dateStr, ctaUrl: CTA_URL }) + feedback });
    const candidate = { subject: clean(d.subject), preview: clean(d.preview), body_plain: clean(d.body_plain) };
    problems = checkDraft(candidate, { ctaUrl: CTA_URL, intelText });
    console.log(`Attempt ${attempt}: "${candidate.subject}" -> ${problems.length ? problems.length + ' problem(s): ' + problems.join(' | ') : 'passed all checks'}`);
    console.log(`--- attempt ${attempt} text ---\n${candidate.body_plain}\n--- end ---`);
    if (!problems.length) { draft = candidate; break; }
    feedback = `\n\nYour previous draft was rejected for these reasons. Fix every one and write a fresh email:\n- ${problems.join('\n- ')}`;
  }
  if (!draft) {
    await telegram(`⏭ Daily email SKIPPED today. It failed the safety checks 3 times:\n- ${problems.join('\n- ')}\n\nNothing was sent.`);
    console.error('Skipped: draft failed safety checks.');
    process.exit(1);
  }

  if (MODE === 'dry') {
    console.log('\n----- DRY RUN: would send -----\nSubject: ' + draft.subject + '\nPreview: ' + draft.preview + '\n\n' + draft.body_plain + '\n-------------------------------');
    return;
  }

  // 4. Send.
  if (MODE === 'test') {
    const to = need('TEST_EMAIL');
    const have = (await listContacts(resendKey, audienceId)).some((c) => String(c.email).toLowerCase() === to.toLowerCase());
    if (!have) await addContact(resendKey, audienceId, { email: to, firstName: 'Joel' });
  }
  const footerAddress = process.env.DAILY_EMAIL_FOOTER_ADDRESS || '';
  const prefix = MODE === 'test' ? '[TEST] ' : '';
  const id = await createBroadcast(resendKey, {
    audienceId,
    from: `${FROM_NAME} <${FROM_EMAIL}>`,
    replyTo: FROM_EMAIL,
    subject: prefix + draft.subject,
    previewText: draft.preview,
    html: toHtml(draft.body_plain, footerAddress),
    text: toText(draft.body_plain, footerAddress),
    name: MODE === 'test' ? `Test ${new Date().toISOString()}` : `Daily ${dateStr}`,
  });
  await sendBroadcast(resendKey, id);
  console.log(`Broadcast ${id} sent (${MODE}).`);

  // 5. Tell Joel.
  await telegram(`📧 Daily email ${MODE === 'test' ? '(TEST to you only) ' : ''}sent.\n\nSubject: ${draft.subject}\n\n${draft.body_plain}\n\n${syncNote}\nTo pause the daily send, set the repo variable DAILY_EMAIL_ENABLED to false.`);
}

main().catch(async (e) => {
  console.error('Fatal:', e);
  await telegram('❌ Daily email FAILED: ' + e.message.slice(0, 500));
  process.exit(1);
});
