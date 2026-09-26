#!/usr/bin/env node
// List emails, sent through Resend on the rhythm Joel approved (2026-09-24):
//   Sun + Tue  letter   (shape: Denise Duffield-Thomas's Tue/Sun emails)
//   Thu        post     (shape: Denise's Thursday episode email, pointing at this week's blog post)
//   Fri        fridays  (Finance Fridays, shape: Mind Money Balance's weekly newsletter)
// Monthly cycle (Denise): open the theme, teach, check in, then push the free call in the last 9 days.
//
//   1. work out today's email type and month phase
//   2. shape: the latest matching competitor email from Gmail (structure only)
//   3. words: Joel's own passages from recent Fathom calls; facts only from voice.mjs + input
//   4. draft, then automatic checks (up to 3 tries, problems fed back); skip the send if it still fails
//   5. send: review = to Joel only; live = to the list. Joel gets the full text on Telegram.
//
// PRIVACY: this repo and its logs are public. Never print Fathom passages or draft bodies to the log.
//
// MODES (DAILY_EMAIL_MODE): dry = draft + check, Telegram only · review = email Joel only · live = the list
// EMAIL_TYPE (optional): letter | post | fridays, overrides the weekday.

import process from 'node:process';
import { readdir, readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { getAccessToken, listMessages, getMessageFull } from '../gmail-client.mjs';
import { systemPrompt, userPrompt, FROM_NAME, FROM_EMAIL, LINKS, THEMES, DEFAULT_THEME, JOEL_FACTS } from './voice.mjs';
import { draftEmail } from './anthropic.mjs';
import { checkDraft, clean } from './safety.mjs';
import { recentJoelWords } from './fathom.mjs';
import { findOrCreateAudience, addContact, listContacts, listBroadcasts, createBroadcast, sendBroadcast } from './resend.mjs';
import { syncList } from './sync-list.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const MODE = (process.env.DAILY_EMAIL_MODE || 'dry').toLowerCase().replace('test', 'review');
const MODEL = process.env.DAILY_EMAIL_MODEL || 'claude-sonnet-4-6';
const MAX_TRIES = 3;
const DENISE = 'denisedt@c.kajabimail.net';
const MMB = 'lindsay@mindmoneybalance.com';

// Public testimonials: the only client names and words any email may use.
const TESTIMONIALS = [
  { who: 'Josh, yacht chef', quote: "You've taken money off the pedestal. Now it's just a tool. I'm in control of it, not it in control of me." },
  { who: 'Josh, yacht chef', quote: 'Book that first call with Joel. Just do it. One call is all it takes.' },
];

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
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chat, text: text.slice(0, 3900), disable_web_page_preview: true }),
    });
  } catch (e) { console.error('Telegram notify failed:', e.message); }
}

function ukParts(d = new Date()) {
  const f = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/London', weekday: 'short', year: 'numeric', month: '2-digit', day: '2-digit' });
  const p = Object.fromEntries(f.formatToParts(d).map((x) => [x.type, x.value]));
  return { weekday: p.weekday, year: +p.year, month: +p.month, day: +p.day, iso: `${p.year}-${p.month}-${p.day}` };
}

function pickType(weekday) {
  if (process.env.EMAIL_TYPE) return process.env.EMAIL_TYPE;
  return { Sun: 'letter', Tue: 'letter', Thu: 'post', Fri: 'fridays' }[weekday] || null;
}

function pickPhase({ year, month, day, weekday }) {
  const dim = new Date(Date.UTC(year, month, 0)).getUTCDate();
  if (day >= dim - 8) return weekday === 'Sun' ? 'push_pitch' : weekday === 'Tue' ? 'push_case' : 'push';
  if (day >= 15) return 'checkin';
  if (day <= 4) return 'open';
  return 'teach';
}

// Latest competitor email for this slot, as a structure reference.
async function shapeReference(type) {
  if (!process.env.GMAIL_REFRESH_TOKEN) return null;
  const accessToken = await getAccessToken({ clientId: process.env.GMAIL_CLIENT_ID, clientSecret: process.env.GMAIL_CLIENT_SECRET, refreshToken: process.env.GMAIL_REFRESH_TOKEN });
  const from = type === 'fridays' ? MMB : DENISE;
  const refs = await listMessages({ accessToken, query: `from:${from} newer_than:35d`, maxResults: 25 });
  const msgs = [];
  for (const r of refs) msgs.push(await getMessageFull({ accessToken, id: r.id, maxChars: 6000 }));
  msgs.sort((a, b) => (Date.parse(b.date) || 0) - (Date.parse(a.date) || 0));
  const dow = (m) => new Date(m.date).toLocaleDateString('en-GB', { weekday: 'short', timeZone: 'Europe/London' });
  const isEpisode = (m) => /\bepisode\b/i.test(m.body);
  let pick;
  if (type === 'fridays') pick = msgs[0];
  else if (type === 'post') pick = msgs.find((m) => dow(m) === 'Thu' && isEpisode(m)) || msgs.find(isEpisode);
  else pick = msgs.find((m) => ['Tue', 'Sun'].includes(dow(m)) && !isEpisode(m)) || msgs.find((m) => !isEpisode(m));
  return pick ? { subject: pick.subject, body: pick.body, date: String(pick.date).slice(0, 16) } : null;
}

async function blogPosts() {
  const dir = join(ROOT, 'src', 'content', 'blog');
  const posts = [];
  for (const f of await readdir(dir)) {
    if (!/\.mdx?$/.test(f)) continue;
    const raw = await readFile(join(dir, f), 'utf8');
    const fm = raw.match(/^---\n([\s\S]*?)\n---/);
    if (!fm || /^draft:\s*true/m.test(fm[1])) continue;
    const title = (fm[1].match(/^title:\s*["']?(.+?)["']?\s*$/m) || [])[1];
    const date = (fm[1].match(/^pubDate:\s*["']?(.+?)["']?\s*$/m) || [])[1];
    if (!title || !date) continue;
    posts.push({ title, date: Date.parse(date) || 0, url: `${LINKS.blog}/${f.replace(/\.mdx?$/, '')}`, body: raw.slice(fm[0].length).trim() });
  }
  return posts.sort((a, b) => b.date - a.date);
}

// Joel's own domain takes over automatically once Resend has verified it.
async function senderEmail(key) {
  try {
    const res = await fetch('https://api.resend.com/domains', { headers: { Authorization: `Bearer ${key}` } });
    const j = await res.json();
    if ((j.data || []).some((d) => d.name === 'joelezekiel.com' && d.status === 'verified')) return 'joel@joelezekiel.com';
  } catch { /* fall back */ }
  return FROM_EMAIL;
}

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function toHtml(body, footerAddress) {
  const paras = body.split(/\n{2,}/).map((p) => {
    let h = esc(p).replace(/\n/g, '<br>');
    h = h.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" style="color:#1C2A3A;font-weight:bold;">$1</a>');
    return `<p style="margin:0 0 16px;line-height:1.6;">${h}</p>`;
  }).join('\n');
  const foot = [
    'You are getting this because you signed up at wayofwealthcoaching.com.',
    '<a href="{{{RESEND_UNSUBSCRIBE_URL}}}">Unsubscribe</a>',
    footerAddress ? esc(footerAddress) : '',
  ].filter(Boolean).join('<br>');
  return `<div style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:16px;color:#2D2D2D;max-width:560px;margin:0 auto;padding:8px;">\n${paras}\n<p style="margin:32px 0 0;font-size:12px;color:#888;line-height:1.5;">${foot}</p>\n</div>`;
}

function toText(body, footerAddress) {
  return `${body}\n\n--\nYou are getting this because you signed up at wayofwealthcoaching.com.\nUnsubscribe: {{{RESEND_UNSUBSCRIBE_URL}}}${footerAddress ? '\n' + footerAddress : ''}`;
}

async function main() {
  const resendKey = need('RESEND_API_KEY');
  const anthropicKey = need('ANTHROPIC_API_KEY');
  const uk = ukParts();
  const type = pickType(uk.weekday);
  if (!type) { console.log(`No list email on ${uk.weekday}.`); return; }
  const phase = type === 'fridays' ? 'teach' : pickPhase(uk);
  const theme = THEMES[`${uk.year}-${String(uk.month).padStart(2, '0')}`] || DEFAULT_THEME;
  console.log(`[${new Date().toISOString()}] ${uk.weekday} ${uk.iso} · type ${type} · phase ${phase} · mode ${MODE}`);

  if (MODE === 'live') {
    const already = (await listBroadcasts(resendKey)).find((b) => (b.name || '') === `List ${uk.iso}` && b.status !== 'draft');
    if (already) { console.log('Already sent today. Nothing to do.'); return; }
  }

  // Inputs.
  let shape = null;
  try { shape = await shapeReference(type); } catch (e) { console.error('Shape reference unavailable: ' + e.message); }
  console.log(shape ? `Shape reference: ${shape.date}, ${shape.body.split(/\s+/).length} words` : 'No shape reference found.');

  let passages = [], names = new Set();
  if (type !== 'post' && phase !== 'push_case') {
    try { ({ passages, names } = await recentJoelWords({ key: process.env.FATHOM_API_KEY })); } catch (e) { console.error('Fathom unavailable: ' + e.message); }
    console.log(`Joel passages: ${passages.length} (not printed: private).`);
    if (!passages.length && (type === 'fridays' || phase === 'teach')) {
      await telegram(`⏭ ${type} email for ${uk.iso} SKIPPED: no usable passages from your recent Fathom calls, and stories may only come from your own words.`);
      process.exit(1);
    }
  }

  const posts = await blogPosts();
  const post = type === 'post' ? posts[0] : type === 'fridays' ? (posts[1] || posts[0]) : null;
  const testimonials = phase === 'push_case' ? TESTIMONIALS : [];
  for (const t of testimonials) names.delete(t.who.split(/[ ,]/)[0]);

  const allowedLinks = [LINKS.call, LINKS.reset, LINKS.site, ...(post ? [post.url] : [])];
  const sourceText = [JOEL_FACTS, ...passages.map((p) => p.text), post ? `${post.title} ${post.body}` : '', ...testimonials.map((t) => t.quote)].join('\n');

  // Draft + checks.
  let draft = null, problems = [], feedback = '';
  for (let attempt = 1; attempt <= MAX_TRIES; attempt++) {
    const d = await draftEmail({
      apiKey: anthropicKey, model: MODEL, maxTokens: 2200,
      system: systemPrompt(type),
      user: userPrompt({ type, phase, theme, dateStr: uk.iso, shape, passages, post, testimonials }) + feedback,
    });
    const candidate = { subject: clean(d.subject), preview: clean(d.preview), body_plain: clean(d.body_plain) };
    problems = checkDraft(candidate, {
      type, allowedLinks, sourceText, blockedNames: names,
      shapeText: shape?.body || '', shapeSubject: shape?.subject || '',
      passagesText: passages.map((p) => p.text).join('\n'),
      requireJoelWords: passages.length > 0 && (type === 'fridays' || phase === 'teach'),
    });
    // Quoted parts can hold client names or private words, so they're blanked in the public log.
    console.log(`Attempt ${attempt}: ${problems.length ? problems.map((p) => p.replace(/"[^"]*"/g, '"…"').replace(/\(.*?\)/g, '(…)')).join(' | ') : 'passed all checks'}`);
    if (!problems.length) { draft = candidate; break; }
    feedback = `\n\nYour previous draft was rejected for these reasons. Fix every one and write a fresh email:\n- ${problems.join('\n- ')}`;
  }
  if (!draft) {
    await telegram(`⏭ ${type} email for ${uk.iso} SKIPPED. It failed the safety checks 3 times:\n- ${problems.join('\n- ')}\n\nNothing was sent.`);
    process.exit(1);
  }

  const label = `${type} · ${phase} · ${uk.weekday} ${uk.iso}`;
  if (MODE === 'dry') {
    await telegram(`📝 DRY RUN (nothing sent) — ${label}\n\nSubject: ${draft.subject}\nPreview: ${draft.preview}\n\n${draft.body_plain}`);
    console.log('Dry run done. Draft sent to Telegram only.');
    return;
  }

  // Send.
  const footerAddress = process.env.DAILY_EMAIL_FOOTER_ADDRESS || '';
  const audienceId = await findOrCreateAudience(resendKey, MODE === 'review' ? 'Test' : (process.env.RESEND_AUDIENCE_NAME || 'General'));
  let syncNote = '';
  if (MODE === 'review') {
    const to = need('TEST_EMAIL');
    const have = (await listContacts(resendKey, audienceId)).some((c) => String(c.email).toLowerCase() === to.toLowerCase());
    if (!have) await addContact(resendKey, audienceId, { email: to, firstName: 'Joel' });
  } else if (process.env.MAILERLITE_API_KEY) {
    try {
      const s = await syncList({ mlKey: process.env.MAILERLITE_API_KEY, resendKey, audienceId });
      syncNote = `List sync: +${s.added} new, ${s.markedUnsub + s.mlUnsubscribed} opt-outs applied. Sendable: ${s.sendableAfterSync}.`;
    } catch (e) { syncNote = 'List sync FAILED, sent to the list as it stood. ' + e.message.slice(0, 120); }
  }

  const id = await createBroadcast(resendKey, {
    audienceId,
    from: `${FROM_NAME} <${await senderEmail(resendKey)}>`,
    replyTo: 'joeleezekiel@gmail.com', // wayofwealthcoaching.com can't receive mail
    subject: (MODE === 'review' ? `[DRAFT ${uk.weekday}] ` : '') + draft.subject,
    previewText: draft.preview,
    html: toHtml(draft.body_plain, footerAddress),
    text: toText(draft.body_plain, footerAddress),
    name: MODE === 'review' ? `Review ${new Date().toISOString()}` : `List ${uk.iso}`,
  });
  await sendBroadcast(resendKey, id);
  console.log(`Broadcast sent (${MODE}).`);
  await telegram(`📧 ${MODE === 'review' ? 'DRAFT sent to you only' : 'Sent to the list'} — ${label}\n\nSubject: ${draft.subject}\n\n${draft.body_plain}\n\n${syncNote}`);
}

main().catch(async (e) => {
  console.error('Fatal:', String(e.message).split(/\r?\n/)[0].slice(0, 200));
  await telegram('❌ List email FAILED: ' + e.message.slice(0, 500));
  process.exit(1);
});
