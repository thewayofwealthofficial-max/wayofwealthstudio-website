#!/usr/bin/env node
// Fred — apply step. Triggered by repository_dispatch (event_type: fred-apply)
// from netlify/functions/fred-approve.js, which passes the proposal as
// client_payload.proposal.
//
// Behaviour:
//   - requires_manual=false: opens proposal.file, replaces current_text with
//     new_text, commits + pushes to default branch as Fred Bot.
//   - requires_manual=true: creates a new branch `fred/<id>`, applies the
//     edit, pushes, opens a PR via the GitHub API.
//
// After apply: wait 2 minutes, re-fetch the affected page, grep for the new
// text as a canary. If missing or 5xx, auto-revert and notify.
//
// ENV VARS (provided by .github/workflows/fred-apply.yml):
//   TELEGRAM_BOT_TOKEN
//   TELEGRAM_CHAT_ID
//   GITHUB_TOKEN        — provided by Actions, used for push + PR create
//   GITHUB_REPOSITORY   — owner/name
//   GITHUB_EVENT_PATH   — path to event payload JSON

import { readFile, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const SITE_URL = 'https://thewayofwealth.shop';
const CANARY_DELAY_MS = 2 * 60 * 1000; // 2 minutes

const {
  TELEGRAM_BOT_TOKEN,
  TELEGRAM_CHAT_ID,
  GITHUB_TOKEN,
  GITHUB_REPOSITORY,
  GITHUB_EVENT_PATH,
} = process.env;

for (const [k, v] of Object.entries({ TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GITHUB_TOKEN, GITHUB_REPOSITORY, GITHUB_EVENT_PATH })) {
  if (!v) { console.error(`FATAL: ${k} not set.`); process.exit(1); }
}

function escMd(text) {
  return String(text ?? '').replace(/[_*\[\]()~`>#+\-=|{}.!\\]/g, (c) => '\\' + c);
}

async function telegram(text) {
  try {
    await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text,
        parse_mode: 'MarkdownV2',
        disable_web_page_preview: true,
      }),
    });
  } catch (err) {
    console.error('Telegram notify failed:', err.message);
  }
}

function sh(cmd, opts = {}) {
  return execSync(cmd, { cwd: REPO_ROOT, encoding: 'utf8', stdio: 'pipe', ...opts }).trim();
}

function configFredBot() {
  sh('git config user.name "Fred Bot"');
  sh('git config user.email "fred@thewayofwealth.shop"');
}

async function readProposal() {
  const raw = await readFile(GITHUB_EVENT_PATH, 'utf8');
  const event = JSON.parse(raw);
  const proposal = event?.client_payload?.proposal;
  if (!proposal) throw new Error('No proposal in client_payload.');
  return proposal;
}

async function applyEdit(filePath, currentText, newText) {
  const abs = join(REPO_ROOT, filePath);
  const original = await readFile(abs, 'utf8');
  if (!original.includes(currentText)) {
    throw new Error(`current_text not found in ${filePath}.`);
  }
  if (original.split(currentText).length - 1 > 1) {
    throw new Error(`current_text is not unique in ${filePath}.`);
  }
  const updated = original.replace(currentText, newText);
  await writeFile(abs, updated, 'utf8');
  return abs;
}

function autoApply(proposal) {
  const { file, current_text, new_text, id } = proposal;
  configFredBot();

  // Make sure we're on the default branch and up to date.
  const defaultBranch = sh('git rev-parse --abbrev-ref HEAD') || 'main';

  return applyEdit(file, current_text, new_text).then(() => {
    sh(`git add "${file}"`);
    const diff = sh('git diff --staged --name-only');
    if (!diff) throw new Error('Edit made but no diff staged.');
    sh(`git commit -m "fred: apply ${id}" -m "Auto-applied via Fred approve link."`);
    sh('git push');
    const sha = sh('git rev-parse HEAD');
    return { mode: 'commit', sha, branch: defaultBranch };
  });
}

async function prApply(proposal) {
  const { file, current_text, new_text, id } = proposal;
  configFredBot();

  const branch = `fred/${id}-${Date.now().toString(36)}`;
  sh(`git checkout -b "${branch}"`);
  await applyEdit(file, current_text, new_text);
  sh(`git add "${file}"`);
  sh(`git commit -m "fred: propose ${id}" -m "Auto-drafted via Fred approve link — needs human review."`);
  sh(`git push --set-upstream origin "${branch}"`);
  const sha = sh('git rev-parse HEAD');

  const body = [
    `**Fred proposal \`${id}\`** — auto-drafted, needs human review.`,
    '',
    `**Observation:** ${proposal.observation ?? '(none provided)'}`,
    `**Proposal:** ${proposal.proposal ?? '(none provided)'}`,
    `**Impact:** ${proposal.impact ?? '(unstated)'}`,
    `**Risk:** ${proposal.risk ?? 'unstated'}`,
    `**Block reason:** ${proposal.block_reason ?? '(blocked path)'}`,
    '',
    `File: \`${file}\``,
  ].join('\n');

  const res = await fetch(`https://api.github.com/repos/${GITHUB_REPOSITORY}/pulls`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: `fred: ${id}`,
      head: branch,
      base: 'main',
      body,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PR create ${res.status}: ${text.slice(0, 300)}`);
  }
  const pr = await res.json();
  return { mode: 'pr', sha, branch, pr_url: pr.html_url, pr_number: pr.number };
}

function fileToPublicUrl(file) {
  const p = file.replace(/\\/g, '/');
  // Homepage
  if (p === 'src/pages/index.astro') return `${SITE_URL}/`;
  // Blog post
  const blogMatch = p.match(/^src\/content\/blog\/(.+)\.mdx?$/);
  if (blogMatch) return `${SITE_URL}/blog/${blogMatch[1]}`;
  // Generic page
  const pageMatch = p.match(/^src\/pages\/(.+)\.astro$/);
  if (pageMatch) return `${SITE_URL}/${pageMatch[1].replace(/\/index$/, '')}`;
  return null;
}

async function canary(proposal) {
  const url = fileToPublicUrl(proposal.file);
  if (!url) {
    console.log('No public URL inferred for', proposal.file, '— skipping canary.');
    return { ok: true, skipped: true };
  }
  console.log(`Canary: waiting ${CANARY_DELAY_MS / 1000}s then checking ${url}`);
  await sleep(CANARY_DELAY_MS);
  try {
    const res = await fetch(url, { headers: { 'User-Agent': 'Fred-Canary/1.0' } });
    if (res.status >= 500) return { ok: false, reason: `HTTP ${res.status}` };
    const html = await res.text();
    // Look for a short, meaningful slice of the new text (first 40 chars,
    // HTML-unsafe but good enough for a sanity check).
    const needle = (proposal.new_text || '').trim().slice(0, 40);
    if (needle && !html.includes(needle)) {
      return { ok: false, reason: 'new_text not visible on page' };
    }
    return { ok: true, url };
  } catch (err) {
    return { ok: false, reason: err.message };
  }
}

async function revert(sha) {
  configFredBot();
  try {
    sh(`git revert --no-edit ${sha}`);
    sh('git push');
    return true;
  } catch (err) {
    console.error('Revert failed:', err.message);
    return false;
  }
}

async function main() {
  const proposal = await readProposal();
  console.log(`Applying proposal ${proposal.id} (requires_manual=${proposal.requires_manual})`);

  let result;
  try {
    if (proposal.requires_manual) {
      result = await prApply(proposal);
    } else {
      result = await autoApply(proposal);
    }
  } catch (err) {
    console.error('Apply failed:', err);
    await telegram(`❌ *Fred apply FAILED* — \`${escMd(proposal.id)}\`\n\n${escMd(err.message)}`);
    process.exit(1);
  }

  if (result.mode === 'pr') {
    await telegram(`✅ *Fred opened PR* for \`${escMd(proposal.id)}\`\n\n[PR \\#${result.pr_number}](${result.pr_url})\n\nNeeds your review before merge\\.`);
    return;
  }

  // Auto-applied commit — send confirmation, then canary.
  await telegram(`✅ *Fred applied* \`${escMd(proposal.id)}\`\n\nCommit \`${escMd(result.sha.slice(0, 7))}\` pushed\\. Canary check in 2m\\.`);

  const check = await canary(proposal);
  if (check.ok) {
    if (!check.skipped) {
      await telegram(`🟢 Canary OK — \`${escMd(proposal.id)}\` live at ${escMd(check.url)}`);
    }
    return;
  }

  // Canary failed — revert + notify.
  const reverted = await revert(result.sha);
  if (reverted) {
    await telegram(`🔴 *Canary failed* — \`${escMd(proposal.id)}\`\n\nReason: ${escMd(check.reason)}\n\nAuto\\-reverted \\(\`${escMd(result.sha.slice(0, 7))}\`\\)\\.`);
  } else {
    await telegram(`🔴 *Canary failed, revert also failed* — \`${escMd(proposal.id)}\`\n\nReason: ${escMd(check.reason)}\n\nManual intervention needed on commit \`${escMd(result.sha.slice(0, 7))}\`\\.`);
  }
  process.exit(1);
}

main().catch(async (err) => {
  console.error('FATAL:', err);
  await telegram(`❌ *Fred apply crashed* — ${escMd(err.message ?? String(err))}`);
  process.exit(1);
});
