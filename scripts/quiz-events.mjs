#!/usr/bin/env node
// Quiz events — polls Airtable for new quiz activity and notifies Joel via Fred (Telegram).
//
// Cadence: "Quiet"
//   • Quiz completions → IMMEDIATE Telegram ping (hot signal)
//   • Starts + drop-offs → rolled into a daily 20:00 UK summary
//
// Runs every 15 min (via quiz-events.yml). Same script decides what to send based on UTC time:
//   • EVERY run: scan for new quiz_complete events since last cursor → instant ping
//   • 19:00–20:00 UTC window (once/day): also emit daily rollup (starts / drop-offs / top source)
//
// State: .github/state/quiz-last-seen.json holds the highest createdTime we've processed.
// The workflow commits the diff so state survives across runs without external storage.
//
// ENV VARS REQUIRED:
//   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID   (consumed by telegram-notify.mjs)
//   AIRTABLE_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_QUIZ_TABLE_ID

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const STATE_DIR = join(REPO_ROOT, '.github', 'state');
const STATE_FILE = join(STATE_DIR, 'quiz-last-seen.json');
const NOTIFY_SCRIPT = join(REPO_ROOT, 'scripts', 'telegram-notify.mjs');

const {
  AIRTABLE_TOKEN,
  AIRTABLE_BASE_ID,
  AIRTABLE_QUIZ_TABLE_ID,
} = process.env;

if (!AIRTABLE_TOKEN || !AIRTABLE_BASE_ID || !AIRTABLE_QUIZ_TABLE_ID) {
  console.error('FATAL: Airtable env vars missing (TOKEN / BASE_ID / QUIZ_TABLE_ID).');
  process.exit(1);
}

// ───────────────────────────────────────────────────────────────
// State

async function loadState() {
  if (!existsSync(STATE_FILE)) {
    // Default: 24h ago, so first run after deploy doesn't flood with backfill.
    const iso = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    return { lastSeen: iso, lastRollupDate: null };
  }
  try {
    const raw = await readFile(STATE_FILE, 'utf8');
    const parsed = JSON.parse(raw);
    return {
      lastSeen: parsed.lastSeen || new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      lastRollupDate: parsed.lastRollupDate || null,
    };
  } catch (e) {
    console.error('State file unreadable, defaulting to 24h ago:', e.message);
    return { lastSeen: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), lastRollupDate: null };
  }
}

async function saveState(state) {
  if (!existsSync(STATE_DIR)) await mkdir(STATE_DIR, { recursive: true });
  await writeFile(STATE_FILE, JSON.stringify(state, null, 2) + '\n', 'utf8');
}

// ───────────────────────────────────────────────────────────────
// Airtable

async function fetchNewRecords(lastSeenIso) {
  const records = [];
  let offset = '';
  for (let page = 0; page < 10; page++) {
    const url = new URL(`https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_QUIZ_TABLE_ID}`);
    url.searchParams.set('pageSize', '100');
    url.searchParams.set('filterByFormula', `IS_AFTER(CREATED_TIME(), '${lastSeenIso}')`);
    if (offset) url.searchParams.set('offset', offset);
    const res = await fetch(url, { headers: { Authorization: `Bearer ${AIRTABLE_TOKEN}` } });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Airtable fetch failed: ${res.status} ${text.slice(0, 200)}`);
    }
    const data = await res.json();
    records.push(...(data.records ?? []));
    if (!data.offset) break;
    offset = data.offset;
  }
  // Sort ascending by createdTime so our cursor moves forward safely
  records.sort((a, b) => new Date(a.createdTime) - new Date(b.createdTime));
  return records;
}

async function fetch24hRecords() {
  // Separate pull used for the daily rollup summary — last 24h regardless of cursor
  const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  return fetchNewRecords(since);
}

// ───────────────────────────────────────────────────────────────
// Telegram (via existing helper — do not re-implement)

function notify({ emoji, title, body }) {
  const args = ['--emoji', emoji, '--title', title, '--body', body];
  const result = spawnSync('node', [NOTIFY_SCRIPT, ...args], {
    stdio: 'inherit',
    env: process.env,
  });
  if (result.status !== 0) {
    console.error(`telegram-notify exited with code ${result.status}`);
  }
}

// ───────────────────────────────────────────────────────────────
// Formatters

function ukTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString('en-GB', {
      hour: '2-digit', minute: '2-digit', timeZone: 'Europe/London',
    });
  } catch { return '??:??'; }
}

function normaliseSource(src) {
  if (!src) return 'unknown';
  const s = String(src);
  if (s === 'ig' || s === 'direct' || s === 'tt' || s === 'fb') return s;
  // URL → host
  try {
    const u = new URL(s);
    return u.hostname.replace(/^www\./, '');
  } catch {
    return s.slice(0, 30);
  }
}

// ───────────────────────────────────────────────────────────────
// Main

async function main() {
  const state = await loadState();
  console.log('Last seen cursor:', state.lastSeen);

  // 1. Pull new records since last cursor
  const newRecords = await fetchNewRecords(state.lastSeen);
  console.log(`Fetched ${newRecords.length} new records since cursor.`);

  // 2. For each completion → immediate ping
  const completions = newRecords.filter((r) => r.fields?.Step === 'quiz_complete' || r.fields?.Step === 'completed');
  for (const rec of completions) {
    const f = rec.fields || {};
    const source = normaliseSource(f.Source);
    const device = f.Device || 'unknown';
    const time = ukTime(f.Timestamp || rec.createdTime);
    notify({
      emoji: '🎯',
      title: 'Quiz completion',
      body: `Source: ${source} · Device: ${device} · Time: ${time} UK`,
    });
  }

  // 3. Update cursor to latest createdTime processed
  let newCursor = state.lastSeen;
  if (newRecords.length > 0) {
    newCursor = newRecords[newRecords.length - 1].createdTime;
  }

  // 4. Daily rollup window — 19:00–20:00 UTC, once per UTC date
  const now = new Date();
  const utcHour = now.getUTCHours();
  const todayUtc = now.toISOString().slice(0, 10);
  const inRollupWindow = utcHour === 19;
  const alreadyRolledUp = state.lastRollupDate === todayUtc;

  let newRollupDate = state.lastRollupDate;
  if (inRollupWindow && !alreadyRolledUp) {
    try {
      const recent = await fetch24hRecords();
      const sessions = new Map(); // sid → { steps: Set, source }
      for (const r of recent) {
        const f = r.fields || {};
        const sid = f['Session ID'];
        if (!sid) continue;
        const cur = sessions.get(sid) ?? { steps: new Set(), source: null };
        cur.steps.add(f.Step);
        if (!cur.source && f.Source) cur.source = normaliseSource(f.Source);
        sessions.set(sid, cur);
      }

      let starts = 0, completes = 0, dropoffs = 0;
      const sourceCounts = new Map();
      for (const { steps, source } of sessions.values()) {
        const started = steps.has('quiz_start') || [...steps].some((s) => s && s.startsWith('q'));
        const completed = steps.has('quiz_complete') || steps.has('completed');
        if (started) starts++;
        if (completed) completes++;
        if (started && !completed) dropoffs++;
        if (source) sourceCounts.set(source, (sourceCounts.get(source) || 0) + 1);
      }
      const topSource = [...sourceCounts.entries()].sort((a, b) => b[1] - a[1])[0];
      const topSourceLabel = topSource ? `${topSource[0]} (${topSource[1]})` : 'none';

      const body = [
        `Starts: ${starts}`,
        `Completions: ${completes}`,
        `Drop-offs: ${dropoffs}`,
        `Top source: ${topSourceLabel}`,
        `Sessions tracked: ${sessions.size}`,
      ].join('\n');

      notify({
        emoji: '📊',
        title: 'Daily quiz activity',
        body,
      });
      newRollupDate = todayUtc;
    } catch (e) {
      console.error('Rollup failed (non-fatal):', e.message);
    }
  }

  // 5. Persist state
  await saveState({ lastSeen: newCursor, lastRollupDate: newRollupDate });
  console.log('State saved. New cursor:', newCursor, 'Rollup date:', newRollupDate);
}

main().catch((e) => {
  console.error('Fatal:', e);
  process.exit(1);
});
