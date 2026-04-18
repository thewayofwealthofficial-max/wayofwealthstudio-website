#!/usr/bin/env node
// Fred — autonomous optimization loop, propose step (daily cron).
//
// Collects the last 24h of signal from Airtable (quiz events), MailerLite
// (subscribers + automations), GitHub (commits + workflow runs), and the
// local repo (reddit queue + recent blog posts). Sends the bundle to Claude
// Sonnet with a strict voice + behaviour prompt. Gets 3 proposals back.
// Validates them against a safety blocklist, HMAC-signs each one, stores
// the batch in .github/state/fred-proposals.json, commits + pushes that
// state file, and sends a Telegram message with approve links.
//
// APPROVAL FLOW:
//   Telegram link → Netlify function (netlify/functions/fred-approve.js)
//     → GitHub repository_dispatch (event_type: fred-apply)
//       → .github/workflows/fred-apply.yml runs scripts/fred-apply.mjs
//
// ENV VARS REQUIRED (GitHub Actions secrets):
//   TELEGRAM_BOT_TOKEN         — Fred bot (BotFather)
//   TELEGRAM_CHAT_ID           — Joel's chat id
//   ANTHROPIC_API_KEY          — Claude API
//   AIRTABLE_TOKEN             — quiz events base
//   AIRTABLE_BASE_ID
//   AIRTABLE_QUIZ_TABLE_ID
//   MAILERLITE_API_KEY         — subscribers + automations
//   FRED_SECRET                — HMAC secret for approve tokens
//                                generate locally via: openssl rand -hex 32
//                                rotate quarterly (architecture doc default)
//   GITHUB_TOKEN               — provided automatically by Actions
//                                (used for workflow-run lookup + push)
//
// NETLIFY ENV VARS (separate set, configured in Netlify UI):
//   FRED_SECRET                — same value as the GitHub secret
//   GITHUB_DISPATCH_PAT        — personal access token, scope: repo
//                                (used by netlify/functions/fred-approve.js
//                                to trigger repository_dispatch)
//   GITHUB_REPO                — e.g. "joel-way/wayofwealthstudio-website"
//                                (owner/name the dispatch targets)
//
// TEST: trigger manually via Actions tab → "Fred Propose" → Run workflow.

import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import { createHmac, randomBytes } from 'node:crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const STATE_DIR = join(REPO_ROOT, '.github', 'state');
const STATE_FILE = join(STATE_DIR, 'fred-proposals.json');
const BLOG_DIR = join(REPO_ROOT, 'src', 'content', 'blog');
const QUEUE_PATH = join(REPO_ROOT, 'src', 'content', 'reddit-queue.md');

const {
  TELEGRAM_BOT_TOKEN,
  TELEGRAM_CHAT_ID,
  ANTHROPIC_API_KEY,
  AIRTABLE_TOKEN,
  AIRTABLE_BASE_ID,
  AIRTABLE_QUIZ_TABLE_ID,
  MAILERLITE_API_KEY,
  FRED_SECRET,
  GITHUB_TOKEN,
  GITHUB_REPOSITORY, // provided by Actions, format "owner/repo"
} = process.env;

const MODEL = process.env.CLAUDE_MODEL ?? 'claude-sonnet-4-6';
const APPROVE_BASE_URL = 'https://thewayofwealth.shop/api/fred/approve';
const PROPOSAL_TTL_MS = 24 * 60 * 60 * 1000; // 24h
const DAY_MS = 24 * 60 * 60 * 1000;

// Required-at-minimum. Fred can still run if data-source envs are missing
// (Claude will just see fewer signals), but we need the core three.
for (const [k, v] of Object.entries({ TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ANTHROPIC_API_KEY, FRED_SECRET })) {
  if (!v) {
    console.error(`FATAL: ${k} not set.`);
    // Best-effort failure notify before exiting.
    await safeFailNotify(`Fred propose aborted: missing env var ${k}.`).catch(() => {});
    process.exit(1);
  }
}

const FUNNEL_STEPS = [
  'intro_load', 'quiz_start',
  'q1_shown', 'q1', 'q2_shown', 'q2', 'q3_shown', 'q3',
  'q4_shown', 'q4', 'q5_shown', 'q5', 'q6_shown', 'q6', 'q7_shown', 'q7',
  'email_shown', 'completed',
];

// Safety blocklist — Fred cannot autonomously touch anything here.
// Anything that matches gets marked requires_manual: true (PR instead of auto-apply).
const BLOCKED_PATHS = [
  /^wow-coaching-portal\//,
  /^\/wow-coaching-portal\//,
  /(^|\/)astro\.config\.mjs$/,
  /(^|\/)package\.json$/,
  /(^|\/)package-lock\.json$/,
  /^\.github\/workflows\//,
  /(^|\/)src\/content\.config\.ts$/,
];
const PRICING_TOKENS = ['£597', '£847', '£997', '£299', '£219'];

function isBlockedPath(filePath) {
  if (!filePath || typeof filePath !== 'string') return true;
  const normalised = filePath.replace(/^\.?\//, '').replace(/\\/g, '/');
  return BLOCKED_PATHS.some((re) => re.test(normalised));
}

function touchesPricing(proposal) {
  const path = (proposal.file || '').replace(/\\/g, '/');
  if (!path.endsWith('src/pages/coaching.astro')) return false;
  const haystack = `${proposal.current_text ?? ''}\n${proposal.new_text ?? ''}`;
  return PRICING_TOKENS.some((tok) => haystack.includes(tok));
}

// ─────────────────────────────────────────────────────────────
// 1. Airtable — quiz events (last 48h)

async function pullQuizData() {
  if (!AIRTABLE_TOKEN || !AIRTABLE_BASE_ID || !AIRTABLE_QUIZ_TABLE_ID) {
    return { available: false, reason: 'Airtable env vars missing.' };
  }

  const records = [];
  let offset = '';
  for (let i = 0; i < 10; i++) {
    const url = new URL(`https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_QUIZ_TABLE_ID}`);
    url.searchParams.set('pageSize', '100');
    if (offset) url.searchParams.set('offset', offset);
    const res = await fetch(url, { headers: { Authorization: `Bearer ${AIRTABLE_TOKEN}` } });
    if (!res.ok) {
      return { available: false, reason: `Airtable ${res.status}` };
    }
    const data = await res.json();
    records.push(...(data.records ?? []));
    if (!data.offset) break;
    offset = data.offset;
  }

  const now = Date.now();
  const t48h = now - 2 * DAY_MS;

  const sessions = new Map();
  const sources = new Map();
  const stepCounts = new Map();

  for (const r of records) {
    const f = r.fields ?? {};
    const sid = f['Session ID'];
    const step = f['Step'];
    const ts = new Date(f['Timestamp'] || r.createdTime).getTime();
    if (!sid || !step || ts < t48h) continue;

    const rank = FUNNEL_STEPS.indexOf(step);
    const cur = sessions.get(sid) ?? { max: -1, step: null, source: null };
    if (rank > cur.max) {
      cur.max = rank;
      cur.step = step;
    }
    if (!cur.source && (f['Source'] || f['source'] || f['Referrer'])) {
      cur.source = f['Source'] || f['source'] || f['Referrer'];
    }
    sessions.set(sid, cur);
    stepCounts.set(step, (stepCounts.get(step) ?? 0) + 1);
  }

  const starts = [...sessions.values()].filter((v) => v.max >= FUNNEL_STEPS.indexOf('quiz_start')).length;
  const completions = [...sessions.values()].filter((v) => v.step === 'completed').length;

  const furthestDist = {};
  for (const { step } of sessions.values()) {
    furthestDist[step] = (furthestDist[step] ?? 0) + 1;
  }

  for (const { source } of sessions.values()) {
    if (!source) continue;
    sources.set(source, (sources.get(source) ?? 0) + 1);
  }
  const topSources = [...sources.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, count]) => ({ name, count }));

  return {
    available: true,
    window_hours: 48,
    sessions: sessions.size,
    starts,
    completions,
    completion_rate_pct: sessions.size ? Math.round((completions / sessions.size) * 100) : null,
    furthest_step_distribution: furthestDist,
    top_sources: topSources,
  };
}

// ─────────────────────────────────────────────────────────────
// 2. MailerLite

async function pullMailerLite() {
  if (!MAILERLITE_API_KEY) {
    return { available: false, reason: 'MAILERLITE_API_KEY missing.' };
  }

  const headers = {
    Authorization: `Bearer ${MAILERLITE_API_KEY}`,
    Accept: 'application/json',
  };

  let total = null;
  let signups7d = null;
  let automations = [];

  // Total subscribers.
  try {
    const res = await fetch('https://connect.mailerlite.com/api/subscribers?limit=1', { headers });
    if (res.ok) {
      const data = await res.json();
      total = data.meta?.total ?? null;
    }
  } catch (err) {
    console.error('MailerLite subscribers error:', err.message);
  }

  // Last 7d signups — filter by date_from (ISO date, YYYY-MM-DD).
  try {
    const since = new Date(Date.now() - 7 * DAY_MS).toISOString().slice(0, 10);
    const url = `https://connect.mailerlite.com/api/subscribers?limit=1&filter[status]=active&filter[date_from]=${since}`;
    const res = await fetch(url, { headers });
    if (res.ok) {
      const data = await res.json();
      signups7d = data.meta?.total ?? null;
    }
  } catch (err) {
    console.error('MailerLite 7d signups error:', err.message);
  }

  // Automations — MailerLite returns stats blobs. Field names vary by account
  // (opens_count vs opens_rate etc); we try a few and fall back gracefully.
  try {
    const res = await fetch('https://connect.mailerlite.com/api/automations?limit=25', { headers });
    if (res.ok) {
      const data = await res.json();
      const rows = (data.data ?? []).map((a) => {
        const stats = a.stats ?? {};
        const opens = stats.opens_count ?? stats.unique_opens_count ?? 0;
        const sent = stats.sent ?? stats.sent_count ?? stats.emails_sent ?? 0;
        const openRate = stats.open_rate ?? (sent ? opens / sent : 0);
        return {
          id: a.id,
          name: a.name,
          enabled: a.enabled,
          sent,
          opens,
          open_rate: typeof openRate === 'number' ? Math.round(openRate * 10000) / 100 : openRate,
        };
      });
      automations = rows
        .filter((r) => r.sent > 0)
        .sort((a, b) => (b.open_rate ?? 0) - (a.open_rate ?? 0))
        .slice(0, 3);
    }
  } catch (err) {
    console.error('MailerLite automations error:', err.message);
  }

  return { available: true, total, signups_7d: signups7d, top_automations: automations };
}

// ─────────────────────────────────────────────────────────────
// 3. GitHub repo activity

function pullGitCommits() {
  try {
    const out = execSync('git log --since="1 day ago" --format="%H %s"', {
      cwd: REPO_ROOT,
      encoding: 'utf8',
    }).trim();
    if (!out) return [];
    return out.split('\n').map((line) => {
      const [sha, ...rest] = line.split(' ');
      return { sha: sha.slice(0, 7), message: rest.join(' ') };
    });
  } catch (err) {
    console.error('git log failed:', err.message);
    return [];
  }
}

async function pullWorkflowRuns() {
  if (!GITHUB_TOKEN || !GITHUB_REPOSITORY) return { available: false };

  const since = new Date(Date.now() - DAY_MS).toISOString();
  try {
    const url = `https://api.github.com/repos/${GITHUB_REPOSITORY}/actions/runs?created=%3E%3D${encodeURIComponent(since)}&per_page=50`;
    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
    });
    if (!res.ok) return { available: false, reason: `GitHub API ${res.status}` };
    const data = await res.json();
    const runs = (data.workflow_runs ?? []).map((r) => ({
      name: r.name,
      status: r.status,
      conclusion: r.conclusion,
      created_at: r.created_at,
    }));
    const failed = runs.filter((r) => r.conclusion && r.conclusion !== 'success' && r.conclusion !== 'skipped');
    return {
      available: true,
      total: runs.length,
      failed_count: failed.length,
      failed_runs: failed.slice(0, 5),
    };
  } catch (err) {
    return { available: false, reason: err.message };
  }
}

// ─────────────────────────────────────────────────────────────
// 4. Reddit queue + recent blog posts

async function pullQueueAndPosts() {
  let queueStatus = { queued: null, published: null };
  try {
    const raw = await readFile(QUEUE_PATH, 'utf8');
    queueStatus = {
      queued: (raw.match(/🔵/g) || []).length,
      published: (raw.match(/✅/g) || []).length,
    };
  } catch (err) {
    console.error('reddit-queue read failed:', err.message);
  }

  let recentPosts = [];
  try {
    const files = (await readdir(BLOG_DIR)).filter((f) => f.endsWith('.md'));
    const entries = await Promise.all(files.map(async (f) => {
      const content = await readFile(join(BLOG_DIR, f), 'utf8');
      const title = content.match(/^title:\s*"?([^"\n]+)"?/m)?.[1] ?? f;
      const pubDate = content.match(/^pubDate:\s*(\S+)/m)?.[1] ?? '';
      return { file: f, title: title.replace(/"$/, ''), pubDate };
    }));
    entries.sort((a, b) => b.pubDate.localeCompare(a.pubDate));
    recentPosts = entries.slice(0, 3);
  } catch (err) {
    console.error('blog read failed:', err.message);
  }

  return { queue: queueStatus, recent_posts: recentPosts };
}

// ─────────────────────────────────────────────────────────────
// Claude prompt

const SYSTEM_PROMPT = `You are Fred, an autonomous optimization assistant for Way of Wealth — Joel's UK behavioural-money-coaching business. Review the last 24 hours of data below. Identify the 3 highest-leverage actions Joel could take in the next 24 hours to improve conversion, reduce drop-offs, or publish better content.

Voice rules (strict — banned words):
abundance, manifest, money magnet, lucky, money blocks, release, rich life, first class, chill, chillpreneur, somatic, sacred, body check-in, holding space, un-shaming, hustle, grind, side hustle, boss babe.
In-bounds: quiet awareness, turning toward, the story beneath the money, honest reckoning, the work underneath, the thing you won't look at, grounded, steady.

ICP: ambitious self-development-focused earners 25-35 (gender-neutral) who earn well but don't build.

Each proposal must be:
- Small enough to ship in ONE file edit
- Specific enough that the change can be described as a single file path + diff
- Grounded in the DATA, not opinion

Return JSON only, format:
{"proposals": [{"id": "short-slug", "observation": "...", "proposal": "...", "file": "relative/path.ext", "current_text": "...", "new_text": "...", "impact": "short phrase", "risk": "low|medium|high"}, ...]}`;

function buildUserPrompt(ctx) {
  return `DATA FOLLOWS:\n\n${JSON.stringify(ctx, null, 2)}\n\nReturn JSON only — no preamble, no markdown fencing.`;
}

async function callClaude(systemPrompt, userPrompt) {
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 4000,
      system: systemPrompt,
      messages: [{ role: 'user', content: userPrompt }],
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Anthropic API ${res.status}: ${text.slice(0, 400)}`);
  }

  const data = await res.json();
  const text = data.content?.[0]?.text;
  if (!text) throw new Error(`Empty response from Claude.`);
  return text;
}

function parseClaudeJson(text) {
  const cleaned = text.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '').trim();
  return JSON.parse(cleaned);
}

// ─────────────────────────────────────────────────────────────
// Proposal handling

function signId(rawId, createdAt) {
  const payload = `${rawId}:${createdAt}`;
  const mac = createHmac('sha256', FRED_SECRET).update(payload).digest('hex').slice(0, 16);
  // Include createdAt so the approve function can verify + check expiry without lookup order.
  return `${mac}.${createdAt}`;
}

function validateProposals(list) {
  const valid = [];
  const createdAt = Date.now();
  for (const p of list) {
    if (!p || !p.id || !p.file || !p.proposal) continue;
    const blocked = isBlockedPath(p.file) || touchesPricing(p);
    // Short slug id for humans; signed token for HMAC.
    const signed = signId(p.id, createdAt);
    valid.push({
      ...p,
      id: p.id,
      signed_id: signed,
      created_at: createdAt,
      requires_manual: Boolean(blocked),
      block_reason: blocked ? (touchesPricing(p) ? 'pricing' : 'path') : null,
    });
    if (valid.length >= 3) break;
  }
  return valid;
}

async function writeStateFile(proposals) {
  await mkdir(STATE_DIR, { recursive: true });
  const payload = {
    generated_at: new Date().toISOString(),
    ttl_ms: PROPOSAL_TTL_MS,
    proposals,
  };
  await writeFile(STATE_FILE, JSON.stringify(payload, null, 2) + '\n', 'utf8');
}

function commitAndPushState() {
  try {
    execSync('git config user.name "Fred Bot"', { cwd: REPO_ROOT });
    execSync('git config user.email "fred@thewayofwealth.shop"', { cwd: REPO_ROOT });
    execSync(`git add .github/state/fred-proposals.json`, { cwd: REPO_ROOT });
    const status = execSync('git diff --staged --name-only', { cwd: REPO_ROOT, encoding: 'utf8' }).trim();
    if (!status) {
      console.log('No state changes to commit.');
      return;
    }
    execSync('git commit -m "fred: daily proposals" -m "Auto-generated by fred-propose.mjs."', { cwd: REPO_ROOT });
    execSync('git push', { cwd: REPO_ROOT });
    console.log('Committed + pushed state file.');
  } catch (err) {
    console.error('Commit/push failed (non-fatal):', err.message);
  }
}

// ─────────────────────────────────────────────────────────────
// Telegram

function escMd(text) {
  return String(text ?? '').replace(/[_*\[\]()~`>#+\-=|{}.!\\]/g, (c) => '\\' + c);
}

function riskEmoji(risk) {
  if (risk === 'low') return '🟢';
  if (risk === 'medium') return '🟡';
  if (risk === 'high') return '🔴';
  return '⚪';
}

function buildTelegramMessage(proposals) {
  const today = new Date();
  const dateStr = today.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });

  let msg = `🦊 *Fred's daily proposals — ${escMd(dateStr)}*\n\n`;

  if (proposals.length === 0) {
    msg += `_No proposals today — all signals quiet or no high\\-leverage moves found\\._`;
    return msg;
  }

  proposals.forEach((p, i) => {
    const n = i + 1;
    const tag = p.requires_manual ? 'NEEDS PR' : (p.risk ?? 'low').toUpperCase();
    msg += `${n}\\. ${riskEmoji(p.risk)} *${escMd(p.impact || p.id)}* \\[${escMd(tag)}\\]\n`;
    msg += `_Observation:_ ${escMd(p.observation)}\n`;
    msg += `_Proposal:_ ${escMd(p.proposal)}\n`;
    msg += `_File:_ \`${escMd(p.file)}\`\n`;
    const approveUrl = `${APPROVE_BASE_URL}?id=${encodeURIComponent(p.signed_id)}&slug=${encodeURIComponent(p.id)}`;
    msg += `→ [APPROVE](${approveUrl})\n\n`;
  });

  msg += `_Skip all → no action taken\\. I'll generate 3 new ones tomorrow\\._\n— Fred`;
  return msg;
}

async function sendTelegram(text) {
  const res = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text,
      parse_mode: 'MarkdownV2',
      disable_web_page_preview: true,
    }),
  });
  const json = await res.json();
  if (!json.ok) throw new Error(`Telegram: ${json.description}`);
  return json.result.message_id;
}

async function safeFailNotify(reason) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) return;
  const text = `❌ *Fred propose FAILED*\n\n${escMd(reason).slice(0, 2000)}`;
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
  } catch {
    // already failing — swallow
  }
}

// ─────────────────────────────────────────────────────────────
// Main

async function main() {
  console.log(`[${new Date().toISOString()}] Fred propose — model: ${MODEL}`);

  console.log('Pulling signals...');
  const [quiz, mailerlite, runs, repoData] = await Promise.all([
    pullQuizData(),
    pullMailerLite(),
    pullWorkflowRuns(),
    pullQueueAndPosts(),
  ]);
  const commits = pullGitCommits();

  const context = {
    window: 'last 24h (quiz window 48h)',
    generated_at: new Date().toISOString(),
    quiz,
    mailerlite,
    github: {
      commits_24h: commits,
      workflow_runs: runs,
    },
    content: repoData,
    safety: {
      blocked_paths: [
        'wow-coaching-portal/*',
        'astro.config.mjs',
        'package.json / package-lock.json',
        '.github/workflows/*',
        'src/content.config.ts',
        'coaching.astro pricing lines (£597/£847/£997/£299/£219)',
      ],
    },
  };

  console.log('Calling Claude...');
  const raw = await callClaude(SYSTEM_PROMPT, buildUserPrompt(context));
  let parsed;
  try {
    parsed = parseClaudeJson(raw);
  } catch (err) {
    throw new Error(`Claude returned non-JSON: ${raw.slice(0, 400)}`);
  }

  const proposals = validateProposals(parsed.proposals ?? []);
  console.log(`Got ${proposals.length} valid proposals (${proposals.filter((p) => p.requires_manual).length} need PR).`);

  await writeStateFile(proposals);
  commitAndPushState();

  const message = buildTelegramMessage(proposals);
  await sendTelegram(message);
  console.log('Done.');
}

main().catch(async (err) => {
  console.error('FATAL:', err);
  await safeFailNotify(`Fred propose crashed: ${err.message ?? err}`);
  process.exit(1);
});
