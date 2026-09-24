#!/usr/bin/env node
// Weekly blog topic top-up. Keeps src/content/reddit-queue.md from running dry.
//
// Where the questions come from (both free, public, no login):
//   1. Google search suggestions, UK / US / Australia / Canada: what people actually type.
//   2. Personal Finance & Money Stack Exchange: questions asked in the last 14 days.
// Claude then picks the best ones for Joel, drops duplicates and anything that needs
// regulated advice, and tags each with a behavioural concept, category and segment.
// Question wording stays as the person typed it (only capitalisation and a "?" added).
//
// Usage: ANTHROPIC_API_KEY=... node scripts/topup-blog-queue.mjs [--dry]
// Env: TARGET_QUEUED (default 28), MAX_ADD (default 14)

import { readFile, writeFile, readdir } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { appendFileSync } from 'node:fs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const QUEUE_PATH = join(ROOT, 'src', 'content', 'reddit-queue.md');
const BLOG_DIR = join(ROOT, 'src', 'content', 'blog');
const DRY = process.argv.includes('--dry');
const TARGET = Number(process.env.TARGET_QUEUED || 28);
const MAX_ADD = Number(process.env.MAX_ADD || 14);
const KEY = process.env.ANTHROPIC_API_KEY;
const MODEL = 'claude-sonnet-4-6';

// Must match the category enum in src/content.config.ts (see generate-daily-post.mjs).
const CATEGORIES = ['Spending & shame', 'Anxiety & avoidance', 'ADHD & money', 'Self-employed', 'Budgeting that sticks', 'Behavioural basics'];

const SEEDS = [
  'why do i spend money when', 'why do i always spend', 'why can i not save money', 'why can\'t i save money',
  'why do i feel guilty spending', 'why do i feel guilty charging', 'why am i so bad with money', 'why do i avoid',
  'how to stop impulse spending', 'how to stop overspending', 'why is money so stressful', 'money anxiety',
  'why do i hate looking at my bank', 'scared to check bank account', 'why do i sabotage', 'money blocks',
  'how to manifest money', 'why does money make me anxious', 'how to stop living paycheck to paycheck',
  'why do i spend all my money', 'how to feel safe with money', 'why do i undercharge', 'how to charge more for',
  'how much should i charge for', 'self employed money', 'irregular income', 'how to pay yourself self employed',
  'wellness practitioner money', 'yoga teacher income', 'how to price my coaching', 'how to price reiki',
  'breathwork facilitator', 'is it wrong to charge for', 'why do i feel broke', 'lifestyle creep',
  'emotional spending', 'money shame', 'money mindset', 'why do i give money away', 'how to stop being bad with money',
  'why do i buy things i don\'t need', 'money and adhd', 'why do i never have money',
];
const LOCALES = [['en-GB', 'uk'], ['en-US', 'us'], ['en-AU', 'au'], ['en-CA', 'ca']];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function googleSuggestions() {
  const out = new Set();
  for (const seed of SEEDS) {
    for (const [hl, gl] of LOCALES) {
      try {
        const url = `https://suggestqueries.google.com/complete/search?client=firefox&hl=${hl}&gl=${gl}&q=${encodeURIComponent(seed)}`;
        const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
        if (!res.ok) continue;
        const [, list] = await res.json();
        for (const s of list || []) out.add(String(s).trim().toLowerCase());
      } catch { /* one failed lookup is fine */ }
      await sleep(120);
    }
  }
  // Keep the ones that read like a real question or a problem someone has.
  return [...out].filter((s) => s.split(' ').length >= 4 && /^(why|how|what|is|am|can|should|do|does|i |my |when|where)/.test(s));
}

async function stackExchangeQuestions() {
  try {
    const from = Math.floor(Date.now() / 1000) - 14 * 86400;
    const url = `https://api.stackexchange.com/2.3/questions?order=desc&sort=votes&site=money&pagesize=60&fromdate=${from}`;
    const res = await fetch(url);
    if (!res.ok) return [];
    const j = await res.json();
    const decode = (s) => s.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    return (j.items || []).map((q) => decode(q.title));
  } catch {
    return [];
  }
}

function parseQueue(raw) {
  const lines = raw.split('\n');
  const rows = [];
  for (const line of lines) {
    const m = line.match(/^\|\s*(\d+)\s*\|\s*([^|]*)\|\s*([^|]*)\|/);
    if (m) rows.push({ num: Number(m[1]), status: m[2].trim(), question: m[3].trim() });
  }
  return { lines, rows };
}

async function publishedTitles() {
  const titles = [];
  for (const f of await readdir(BLOG_DIR)) {
    if (!f.endsWith('.md') && !f.endsWith('.mdx')) continue;
    const t = (await readFile(join(BLOG_DIR, f), 'utf8')).match(/^title:\s*["']?(.+?)["']?\s*$/m);
    if (t) titles.push(t[1]);
  }
  return titles;
}

async function askClaude(candidates, existing, need) {
  const system = `You pick blog topics for Joel Ezekiel (Way of Wealth): MSc Behavioural Economics, Qualified Financial Planner, a behavioural money coach. The blog is global money psychology. Its centre is wellness and spiritual practitioners who have built a real business, and around them coaches and online business owners who earn money and can't keep it.

Choose questions a real person typed, that Joel can answer with money psychology plus one practical step.

REJECT anything that:
- needs regulated advice: which investment, fund, pension, mortgage, ISA, debt to clear first, tax structure, or a specific product;
- is a pure calculation or country-specific rules question (tax codes, benefits, US-only paperwork);
- is a near-duplicate of an existing topic (same underlying question in other words);
- is hustle or get-rich content.

For each pick:
- "question": the person's wording exactly. You may only fix capitalisation, spelling of "i" to "I", apostrophes, and add a question mark. Do not rephrase.
- "concept": one or two established behavioural science concepts that genuinely explain it (e.g. ostrich effect, mental accounting, present bias, loss aversion, money scripts (Klontz), status quo bias, social comparison, hedonic adaptation, pain of paying, implementation intentions, law of least effort). Never use ego depletion, decision fatigue, priming or willpower as a resource.
- "category": exactly one of ${CATEGORIES.join(' | ')}.
- "segment": a short reader label, e.g. "Wellness practitioners", "Self-employed", "Anxious avoider", "ADHD", "All segments".
- "source": "google" or "stackexchange".

Return ONLY a JSON array, no prose.`;
  const user = `Pick up to ${need} topics.

EXISTING TOPICS (never duplicate these):
${existing.map((t) => `- ${t}`).join('\n')}

CANDIDATES:
${candidates.map((c) => `- [${c.source}] ${c.text}`).join('\n')}`;

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: MODEL, max_tokens: 4000, system, messages: [{ role: 'user', content: user }] }),
  });
  if (!res.ok) throw new Error(`Anthropic ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const text = (await res.json()).content?.[0]?.text || '';
  const json = text.slice(text.indexOf('['), text.lastIndexOf(']') + 1);
  return JSON.parse(json);
}

const clean = (s) => String(s).replace(/\|/g, '/').replace(/\s*—\s*/g, ', ').replace(/\s+/g, ' ').trim();

async function main() {
  if (!KEY) throw new Error('ANTHROPIC_API_KEY not set');
  const raw = await readFile(QUEUE_PATH, 'utf8');
  const { lines, rows } = parseQueue(raw);
  const queued = rows.filter((r) => r.status.includes('🔵')).length;
  const need = Math.min(MAX_ADD, TARGET - queued);
  console.log(`Queue: ${rows.length} rows, ${queued} waiting. Target ${TARGET}, adding up to ${Math.max(need, 0)}.`);
  if (need <= 0) { output(0); return; }

  const [google, se] = await Promise.all([googleSuggestions(), stackExchangeQuestions()]);
  console.log(`Candidates: ${google.length} from Google suggestions, ${se.length} from Stack Exchange.`);
  const existingQs = rows.map((r) => r.question);
  const existing = [...existingQs, ...(await publishedTitles())];
  const seen = new Set(existing.map((q) => q.toLowerCase().replace(/[^a-z ]/g, '').trim()));
  const candidates = [
    ...google.map((text) => ({ source: 'google', text })),
    ...se.map((text) => ({ source: 'stackexchange', text })),
  ].filter((c) => !seen.has(c.text.toLowerCase().replace(/[^a-z ]/g, '').trim())).slice(0, 400);
  if (!candidates.length) throw new Error('No candidate questions found this week.');

  const picks = await askClaude(candidates, existing, need);
  const valid = [];
  for (const p of picks) {
    if (!p || !p.question || !CATEGORIES.includes(p.category)) continue;
    const key = p.question.toLowerCase().replace(/[^a-z ]/g, '').trim();
    if (seen.has(key)) continue;
    seen.add(key);
    valid.push(p);
    if (valid.length >= need) break;
  }

  let next = Math.max(0, ...rows.map((r) => r.num)) + 1;
  const newLines = valid.map((p) => `| ${next++} | 🔵 | ${clean(p.question)} | ${clean(p.concept)} | ${p.category} | ${clean(p.segment || 'All segments')} |`);
  const lastRowIdx = lines.map((l) => /^\|\s*\d+\s*\|/.test(l)).lastIndexOf(true);
  lines.splice(lastRowIdx + 1, 0, ...newLines);

  console.log(`Adding ${newLines.length}:`);
  newLines.forEach((l) => console.log('  ' + l));
  if (!DRY) await writeFile(QUEUE_PATH, lines.join('\n'));
  output(newLines.length);
}

function output(n) {
  if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, `count=${n}\n`);
}

main().catch((e) => { console.error('FATAL:', e.message); process.exit(1); });
