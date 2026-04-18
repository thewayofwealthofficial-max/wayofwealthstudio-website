#!/usr/bin/env node
//
// ╔═══════════════════════════════════════════════════════════════════════╗
// ║ TODO — Gmail wiring pending                                           ║
// ╠═══════════════════════════════════════════════════════════════════════╣
// ║ This script is a STUB for v1. It emits a single Telegram message so   ║
// ║ Joel sees the workflow is alive + scheduled correctly. Once a data    ║
// ║ source is connected, replace the stub() function with a real fetch.   ║
// ║                                                                       ║
// ║ Options to wire Gmail (pick one, then remove this block):             ║
// ║                                                                       ║
// ║  (a) OAuth2 refresh token                                             ║
// ║      - Create a Google Cloud project, enable Gmail API, generate an   ║
// ║        OAuth client (type: desktop).                                  ║
// ║      - Run a one-off script locally that performs the consent flow    ║
// ║        and prints a refresh token.                                    ║
// ║      - Store as GitHub secret GMAIL_REFRESH_TOKEN (+ CLIENT_ID /      ║
// ║        CLIENT_SECRET).                                                ║
// ║      - Add scripts/gmail-client.mjs helper that exchanges refresh     ║
// ║        token → access token, then calls users.messages.list with      ║
// ║        q=`label:funnel-hack newer_than:1d`.                           ║
// ║                                                                       ║
// ║  (b) Zapier / IFTTT forwarder                                         ║
// ║      - Trigger: "New email matching search in Gmail" (label:funnel-   ║
// ║        hack).                                                         ║
// ║      - Action: POST the message body/subject to a Telegram channel    ║
// ║        or to a tiny webhook bucket (e.g. webhook.site, or an Astro    ║
// ║        API route on wayofwealthstudio.shop).                          ║
// ║      - This script reads the bucket and summarises.                   ║
// ║                                                                       ║
// ║  (c) Manual — skip automation, Joel paste-forwards to Fred ad-hoc.    ║
// ║                                                                       ║
// ║ Recommended: (a). Cleanest, no third-party dependency. One-time       ║
// ║ setup, then forget.                                                   ║
// ╚═══════════════════════════════════════════════════════════════════════╝
//
// Once-daily digest of new emails from competitors in Joel's funnel-hack inbox.
// Schedule is currently workflow_dispatch only (see funnelhack-digest.yml header).
//
// ENV VARS REQUIRED (v1 stub):
//   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID   (consumed by telegram-notify.mjs)
// ENV VARS FUTURE (when Gmail wired):
//   GMAIL_REFRESH_TOKEN, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET
//   ANTHROPIC_API_KEY   (for summarisation step)

import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const NOTIFY_SCRIPT = join(REPO_ROOT, 'scripts', 'telegram-notify.mjs');

// ───────────────────────────────────────────────────────────────
// Telegram helper (via existing script — do not re-implement)

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

// ───────────────────────────────────────────────────────────────
// Stub data source — replace with real Gmail fetch when wired

async function stub() {
  // Returns [] for now. When Gmail is wired, this function should return:
  //   [{ from, subject, receivedAt, snippet, bodyText }, ...]
  // filtered to the last 24h + label:funnel-hack.
  return [];
}

// ───────────────────────────────────────────────────────────────
// Main

async function main() {
  const messages = await stub();

  if (messages.length === 0) {
    notify({
      emoji: '📮',
      title: 'Funnel-hack digest',
      body: 'Stub ran OK. Gmail integration pending — see scripts/funnelhack-digest.mjs TODO block for the 3 wiring options.',
    });
    return;
  }

  // Future: summarise + group by sender
  const bySender = new Map();
  for (const m of messages) {
    const list = bySender.get(m.from) ?? [];
    list.push(m);
    bySender.set(m.from, list);
  }

  const lines = [];
  lines.push(`${messages.length} new email(s) in the last 24h across ${bySender.size} sender(s).`);
  lines.push('');
  for (const [sender, list] of bySender) {
    lines.push(`• ${sender} — ${list.length}`);
    for (const m of list.slice(0, 3)) {
      lines.push(`   - ${m.subject}`);
    }
  }

  notify({
    emoji: '📮',
    title: 'Funnel-hack digest',
    body: lines.join('\n'),
  });
}

main().catch((e) => {
  console.error('Fatal:', e);
  process.exit(1);
});
