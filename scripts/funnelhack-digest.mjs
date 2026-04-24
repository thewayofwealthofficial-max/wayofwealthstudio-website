#!/usr/bin/env node
// Once-daily digest of new emails from competitors in Joel's funnel-hack inbox.
// Reads Gmail (competitor sender list OR label:Funnel-Hack, last 24h)
// → groups by sender → Telegrams summary.
//
// Primary match: `from:` any address in funnelhack-senders.mjs.
// Secondary (supplementary) match: any email manually labeled Funnel-Hack.
// This means the digest works without relying on a Gmail filter being configured.
//
// ENV VARS REQUIRED:
//   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID   (consumed by telegram-notify.mjs)
//   GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN

import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { fetchDigest, parseSenderName } from './gmail-client.mjs';
import { buildFunnelhackQuery, COMPETITOR_SENDERS } from './funnelhack-senders.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const NOTIFY_SCRIPT = join(REPO_ROOT, 'scripts', 'telegram-notify.mjs');

const GMAIL_CLIENT_ID = process.env.GMAIL_CLIENT_ID;
const GMAIL_CLIENT_SECRET = process.env.GMAIL_CLIENT_SECRET;
const GMAIL_REFRESH_TOKEN = process.env.GMAIL_REFRESH_TOKEN;

if (!GMAIL_CLIENT_ID || !GMAIL_CLIENT_SECRET || !GMAIL_REFRESH_TOKEN) {
  console.error('FATAL: missing GMAIL_* env vars. Check GitHub repo secrets.');
  process.exit(1);
}

function notify({ emoji, title, body }) {
  const result = spawnSync(
    'node',
    [NOTIFY_SCRIPT, '--emoji', emoji, '--title', title, '--body', body],
    { stdio: 'inherit', env: process.env }
  );
  if (result.status !== 0) {
    console.error(`telegram-notify exited with code ${result.status}`);
    process.exit(result.status ?? 1);
  }
}

async function main() {
  const query = buildFunnelhackQuery({ days: 1 });
  console.log(`Query: ${query}`);
  console.log(`Tracking ${COMPETITOR_SENDERS.length} competitor senders`);

  const messages = await fetchDigest({
    clientId: GMAIL_CLIENT_ID,
    clientSecret: GMAIL_CLIENT_SECRET,
    refreshToken: GMAIL_REFRESH_TOKEN,
    query,
  });

  if (messages.length === 0) {
    notify({
      emoji: '📮',
      title: 'Funnel-hack digest',
      body: `No new competitor emails in the last 24h.\n\nTracking ${COMPETITOR_SENDERS.length} senders. If you expected emails, verify sender address in scripts/funnelhack-senders.mjs matches the actual "From:" address in Gmail.`,
    });
    return;
  }

  // Group by sender name
  const bySender = new Map();
  for (const m of messages) {
    const name = parseSenderName(m.from);
    const list = bySender.get(name) ?? [];
    list.push(m);
    bySender.set(name, list);
  }

  const lines = [];
  lines.push(`${messages.length} new email${messages.length === 1 ? '' : 's'} across ${bySender.size} sender${bySender.size === 1 ? '' : 's'}:`);
  lines.push('');

  // Show top 8 senders (keep digest compact)
  const sorted = [...bySender.entries()].sort((a, b) => b[1].length - a[1].length);
  for (const [sender, list] of sorted.slice(0, 8)) {
    lines.push(`• ${sender} — ${list.length}`);
    // Show up to 3 subject lines per sender
    for (const m of list.slice(0, 3)) {
      lines.push(`   · ${m.subject || '(no subject)'}`);
    }
  }

  if (sorted.length > 8) {
    lines.push('');
    lines.push(`+ ${sorted.length - 8} more sender(s) · open Gmail to view all`);
  }

  notify({
    emoji: '📮',
    title: 'Funnel-hack digest',
    body: lines.join('\n'),
  });
}

main().catch((e) => {
  console.error('Fatal:', e);
  // Send failure ping so Joel sees something went wrong
  notify({
    emoji: '❌',
    title: 'Funnel-hack digest FAILED',
    body: `${e.message}\n\nCheck workflow logs.`,
  });
  process.exit(1);
});
