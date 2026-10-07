#!/usr/bin/env node
// Daily morning brief — runs 07:00 UTC every day via GitHub Actions.
// Pulls yesterday's free-tool numbers from the website, email list size from Resend,
// latest blog post from the repo, and composes a Telegram message for Joel.
//
// ENV VARS REQUIRED (GitHub Actions secrets):
//   TELEGRAM_BOT_TOKEN
//   TELEGRAM_CHAT_ID
//   FRED_SECRET
//   RESEND_API_KEY

import { readdir, readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { rs, listContacts } from './daily-email/resend.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');

const {
  TELEGRAM_BOT_TOKEN,
  TELEGRAM_CHAT_ID,
  FRED_SECRET,
  RESEND_API_KEY,
} = process.env;

const required = { TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID };
for (const [k, v] of Object.entries(required)) {
  if (!v) { console.error(`FATAL: ${k} not set`); process.exit(1); }
}

// Free tools (Money Reset Tool, Masterclass, Money Story Diagnostic): yesterday's numbers from the website's
// tracker (netlify/functions/magnet-track.js). Replaced the retired quiz's Airtable funnel (7 Oct 2026).

async function pullFreeTools() {
  if (!FRED_SECRET) throw new Error('FRED_SECRET not set');
  const day = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/London', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(Date.now() - 864e5));
  const res = await fetch(`https://wayofwealthcoaching.com/api/magnet/track?counts=${day}`, { headers: { 'x-fred-secret': FRED_SECRET } });
  if (!res.ok) throw new Error(`Free tool numbers: ${res.status}`);
  return { day, counts: await res.json() };
}

// ───────────────────────────────────────────────────────────────
// Email list — people subscribed in Resend's "General" audience, the one the list emails go to
// (scripts/daily-email/send-daily.mjs). Was MailerLite, which the list emails no longer use (7 Oct 2026).

async function pullEmailList() {
  if (!RESEND_API_KEY) throw new Error('RESEND_API_KEY not set');
  const { data: audiences = [] } = await rs(RESEND_API_KEY, '/audiences');
  const general = audiences.find((a) => a.name === (process.env.RESEND_AUDIENCE_NAME || 'General'));
  if (!general) throw new Error('No "General" audience in Resend');
  const contacts = await listContacts(RESEND_API_KEY, general.id);
  return { subscribed: contacts.filter((c) => !c.unsubscribed).length };
}

// ───────────────────────────────────────────────────────────────
// Latest blog post

async function pullLatestPost() {
  const BLOG_DIR = join(REPO_ROOT, 'src', 'content', 'blog');
  try {
    const files = (await readdir(BLOG_DIR)).filter((f) => f.endsWith('.md'));
    if (files.length === 0) return null;
    const entries = await Promise.all(files.map(async (f) => {
      const content = await readFile(join(BLOG_DIR, f), 'utf8');
      const title = content.match(/^title:\s*"?([^"\n]+)"?/m)?.[1] ?? f;
      const pubDate = content.match(/^pubDate:\s*(\S+)/m)?.[1] ?? '';
      return { file: f, title, pubDate };
    }));
    entries.sort((a, b) => b.pubDate.localeCompare(a.pubDate));
    return entries[0];
  } catch {
    return null;
  }
}

// ───────────────────────────────────────────────────────────────
// Telegram send

function esc(s) {
  return String(s ?? '').replace(/[_*\[\]()~`>#+\-=|{}.!\\]/g, (c) => '\\' + c);
}

async function sendTelegram(text) {
  const res = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text, parse_mode: 'MarkdownV2' }),
  });
  const json = await res.json();
  if (!json.ok) { console.error('Telegram error:', json.description); process.exit(1); }
  console.log(`✓ Sent (message_id: ${json.result.message_id})`);
}

// ───────────────────────────────────────────────────────────────
// Compose + send

async function main() {
  console.log('Pulling data...');
  const [tools, list, post] = await Promise.all([pullFreeTools().catch((e) => ({ error: e.message })), pullEmailList().catch((e) => ({ error: e.message })), pullLatestPost()]);

  const today = new Date();
  const dateStr = today.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });

  let msg = `☕ *Morning brief — ${esc(dateStr)}*\n\n`;

  // What shipped yesterday / overnight
  msg += `🚀 *Shipped overnight*\n`;
  if (post) msg += `• Latest post: ${esc(post.title)}\n`;
  msg += '\n';

  // Free tools, yesterday (UK day). Same numbers as the 20:00 round-up, one line each.
  const NAMES = { reset: 'Money Reset Tool', masterclass: 'Masterclass', diagnostic: 'Money Story Diagnostic' };
  if (tools.error) {
    msg += `📊 *Free tools yesterday*\n• Couldn't read the numbers: ${esc(tools.error)}\n\n`;
  } else {
    msg += `📊 *Free tools yesterday \\(${esc(tools.day)}\\)*\n`;
    for (const [k, name] of Object.entries(NAMES)) {
      const c = tools.counts[k] || {};
      msg += `• ${esc(name)}: ${c.opened || 0} opened · ${c.email || 0} gave email · ${c.book || 0} clicked book\n`;
    }
    msg += '\n';
  }

  // Email list (Resend)
  msg += list.error ? `📧 *Email list*\n• Couldn't read it: ${esc(list.error)}\n\n` : `📧 *Email list*\n• ${list.subscribed} subscribed\n\n`;

  msg += `_Reply here with 'status', 'flags', 'ideas', or a specific question — I check these when you open Claude Code next\\._\n— Fred`;

  console.log(msg);
  await sendTelegram(msg);
}

main().catch((e) => { console.error('Fatal:', e); process.exit(1); });
