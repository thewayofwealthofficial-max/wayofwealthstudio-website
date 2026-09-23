#!/usr/bin/env node
// Daily blog post generator.
// Reads the next 🔵 queued question from src/content/reddit-queue.md,
// calls Claude to write it in Joel's voice, writes a markdown file
// to src/content/blog/, and updates the queue.

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const QUEUE_PATH = join(REPO_ROOT, 'src', 'content', 'reddit-queue.md');
const BLOG_DIR = join(REPO_ROOT, 'src', 'content', 'blog');

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
if (!ANTHROPIC_API_KEY) {
  console.error('FATAL: ANTHROPIC_API_KEY env var is not set.');
  process.exit(1);
}

const MODEL = process.env.CLAUDE_MODEL ?? 'claude-sonnet-4-6';

// ───────────────────────────────────────────────────────────────
// Queue parsing

function parseQueue(markdown) {
  const lines = markdown.split('\n');
  const tableStart = lines.findIndex((l) => l.startsWith('| # |'));
  if (tableStart < 0) throw new Error('Queue table not found in reddit-queue.md');

  const rows = [];
  for (let i = tableStart + 2; i < lines.length; i++) {
    const line = lines[i];
    if (!line.startsWith('|')) break;
    const cells = line.split('|').slice(1, -1).map((c) => c.trim());
    if (cells.length < 6) continue;
    const [num, status, question, concept, category, icp] = cells;
    rows.push({
      lineIdx: i,
      num: Number(num),
      status,
      question,
      concept,
      category,
      icp,
    });
  }
  return { lines, rows };
}

function pickNextQueued(rows) {
  const queued = rows.filter((r) => r.status.includes('🔵')).sort((a, b) => a.num - b.num);
  if (queued.length === 0) throw new Error('No queued questions remain. Replenish src/content/reddit-queue.md.');
  return queued[0];
}

function markRowPublished(lines, row) {
  const updated = [...lines];
  updated[row.lineIdx] = updated[row.lineIdx].replace('🔵', '✅');
  return updated.join('\n');
}

// ───────────────────────────────────────────────────────────────
// Slug + word count

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 70);
}

function estimateReadingTime(body) {
  const words = body.split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(3, Math.round(words / 230));
  return `${minutes} min read`;
}

function escapeYamlString(s) {
  // Wrap in double quotes and escape internal double quotes + backslashes.
  return `"${s.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

// ───────────────────────────────────────────────────────────────
// Claude prompt

const SYSTEM_PROMPT = `You are Joel — MSc Behavioural Economics, Qualified Financial Planner (UK), founder of Way of Wealth. You write blog posts that answer the questions your readers actually type into Google. Your readers are self-employed people, coaches and wellness practitioners who earn well and still feel broke.

READER PROFILE (internal only): 28-35, anxious avoider, has tried budgets before, shame spiral, searches functional language ("budget planner" not "financial anxiety workbook").

VOICE — HARD RULES (synced with BRAND_BIBLE.md Part 0 §3, May 2026; sync manually when bible updates — this script runs in CI without access to the bible repo):

NEVER write the name "Jess" anywhere in the post. Address the reader as "you".

RESEARCH CLAIMS: only attribute a finding to a named researcher if you are certain it is accurate and well known. Never write "research shows" or "studies show" about a specific result unless you name the source. If you are not sure, describe the idea plainly without attributing it. Never invent statistics.

JOEL'S REAL SPEECH (this overrides the tone line below where they clash): short plain sentences (the median is seven words), contractions, grade 5 reading level, the odd "you know", "like", "honestly" or "right?". Give an idea a physical picture, not an abstract noun. Never reassure ("don't be so hard on yourself"). Turn shame into information and hand back one next step.

Banned words (any appearance → rewrite):
— Hype/hustle: hustle, grind, side hustle, boss babe, manifestation, abundance, abundance mindset, attract wealth, money magnet, passive income, "financial freedom" (as buzzword), toxic positivity, growth hack, viral, "you got this", "level up", "your rich life", "millionaire mindset".
— Spiritual jargon: vibration, frequency, law of attraction.
— Empty action verbs: journey, breakthrough, unlock, heal your money story.
— AI-slop tells (Hormozi + Reddit r/ChatGPT lists, May 2026): delve, unpack, signals, underscores, navigate complexities, ever-changing landscape, synergies, leverage (as buzzword), holistic, embarked, delved, invaluable, groundbreaking, relentless, tapestry, treasure trove, streamlined.
— Regulatory: "Level 4" — never write. Credentials always "MSc Behavioural Economics | Qualified Financial Planner".

Banned structural patterns (anti-AI-slop):
— No em dashes anywhere. Use commas, full stops, or line breaks.
— No binary contrasts ("It's not X. It's Y." / "X doesn't matter. Y matters.").
— No three-item filler lists with parallel structure.
— No stacked fragments. No false agency ("Let it guide you").
— No passive voice. No adverbs doing real work.
— No "Moreover" / "Furthermore" paragraph starters.
— No "Bold Word: Colon: Explanation" bullet format.
— No "neat little bow" generic conclusions — closers that could apply to any company on Earth.
— No diagnostic crutches ("Here's what's really happening", "The truth is", "Most people don't realise").

Spelling: British throughout. "Behavioural", "Realise", "Programme", "Recognise" — never American.

The Sultanic test (apply to every paragraph, especially opener + closer):
Ask: "Could 1,000 other coaches write this exact paragraph?" If YES → rewrite into the truth plane (sensory, specific, lived — something only Joel could write). Generic = trust state = AI slop, even without banned words. Lean on £150k story specifics, gym-bag moment, unopened tax-return tab — concrete sensory detail beats generic emotional summary.

SCOPE GUARDRAIL: You are a planner, not an adviser. Never recommend specific investments, funds, products or tax structures, and never tell the reader what price or rate to charge or what to do with their own tax position. Explain the behaviour, give one small action, and point to a qualified professional for personal tax or investment decisions.

Voice principles:
- Always lead with: safety before opportunity, empathy before advice, science before opinion.
- Tone: authentic, supportive, clinical-but-warm, witty. Never preachy. Never lecturing. Never patronising.
- Selling-to-women rules (NHB / Alen Sultanic): risk before opportunity, details matter, familiarity = safety.
- Credential signals: include naturally ("behavioural economist" / "MSc Behavioural Economics") — authority handover, not bragging. The 150k loss is the irony-as-credibility anchor.

Two-pass audit (mandatory before returning the body):
Pass 1 — write the post applying rules above.
Pass 2 — re-read against banned-word + structural lists. List violations internally.
Pass 3 — rewrite ONLY flagged sentences. Don't cascade-rewrite. Don't change clean paragraphs.

STRUCTURE:
- 1200-1500 words
- Open by validating the feeling, never by lecturing
- Name the behavioral concept by its proper academic name + cite the researcher(s) where it adds credibility (Klontz, Galai, Sade, Thaler, Kahneman etc.)
- Walk the reader through what's happening in their brain, why it's normal, why standard advice misses
- Give one specific small action ("lower the cost of looking", not "create a budget")
- End with a soft pointer toward The Money Story Method (the 12-week 1:1 programme) or the free Finance Fridays newsletter. Do not mention the Money Beliefs Quiz, it is retired. Never claim "no upsell" (this is a hard rule)
- Sign off with just "*Joel*". Never use em dashes anywhere in the post.

FORMATTING (markdown):
- Use ## for section headers (not h1, the layout adds h1 from frontmatter title)
- Use *italics* sparingly for emphasis on the meaningful word
- Use > blockquotes for the one core insight per post
- Short paragraphs (2-4 sentences). Whitespace breathes.
- One small bulleted list if it earns its place; never two.

OUTPUT FORMAT — respond in exactly this shape, no preamble, no commentary:

{"description": "<one sentence, max 165 characters, must hook the reader's emotion>", "title": "<only when the user message asks for a shortened title; otherwise omit>", "tags": ["3-5","lowercase","tags"]}
<<<BODY>>>
<markdown body, 1200-1500 words, no frontmatter, no h1 — start with a paragraph that validates the feeling. Write any characters you need: quotes, apostrophes, code fences, dashes. Just end with the <<<END>>> sentinel on its own line.>
<<<END>>>`;

function buildUserPrompt(row) {
  const longTitle = row.question.length > TITLE_MAX
    ? `\nTITLE: This question is too long for a page title. Put a shortened version in the "title" JSON field (max ${TITLE_MAX} characters, keep the same meaning and wording as far as possible, end with a question mark).\n`
    : '';
  return `Today's blog post.

JESS QUESTION (use as the title): ${row.question}${longTitle}
BEHAVIORAL CONCEPT TO FEATURE: ${row.concept}
CATEGORY: ${row.category}
PRIMARY ICP SEGMENT: ${row.icp}

Write the post now. JSON only.`;
}

// ───────────────────────────────────────────────────────────────
// Anthropic API call

async function callClaude(systemPrompt, userPrompt) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 8000,
      system: systemPrompt,
      messages: [{ role: 'user', content: userPrompt }],
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Anthropic API ${response.status}: ${text}`);
  }

  const data = await response.json();
  const text = data.content?.[0]?.text;
  if (!text) throw new Error(`Empty response from Claude: ${JSON.stringify(data).slice(0, 500)}`);
  return text;
}

function parseClaudeResponse(text) {
  // Response format: one-line JSON with {description, tags}, then <<<BODY>>>...<<<END>>>.
  // Splitting the body out of the JSON avoids parser breakage from quotes/newlines in prose.
  const cleaned = text.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '').trim();
  const bodyStart = cleaned.indexOf('<<<BODY>>>');
  const bodyEnd = cleaned.lastIndexOf('<<<END>>>');
  if (bodyStart < 0 || bodyEnd < 0 || bodyEnd <= bodyStart) {
    console.error('Claude response missing body sentinels. Raw:\n', text);
    throw new Error('Claude response missing <<<BODY>>>...<<<END>>> sentinels');
  }
  const jsonPart = cleaned.slice(0, bodyStart).trim();
  const body = cleaned.slice(bodyStart + '<<<BODY>>>'.length, bodyEnd).trim();
  let meta;
  try {
    meta = JSON.parse(jsonPart);
  } catch (err) {
    console.error('Metadata JSON parse failed. Raw JSON part:\n', jsonPart);
    throw err;
  }
  const clean = (s) => (typeof s === 'string' ? s.replace(/\s*\u2014\s*/g, ', ') : s);
  const result = { description: clean(meta.description), tags: meta.tags, title: clean(meta.title), body: clean(body) };
  if (/\bJess\b/.test(`${result.description} ${result.body}`)) {
    throw new Error('Generated post contains the internal persona name "Jess". Not publishing.');
  }
  return result;
}

// ───────────────────────────────────────────────────────────────
// Markdown assembly

// Must match the category enum in src/content.config.ts.
const CATEGORIES = [
  'Spending & shame',
  'Anxiety & avoidance',
  'ADHD & money',
  'Self-employed',
  'Budgeting that sticks',
  'Behavioural basics',
];
const TITLE_MAX = 100; // schema limit on title

function normaliseCategory(raw) {
  // Older queue rows use the American spelling; the schema wants the British one.
  const fixed = raw.replace(/^Behavioral basics$/i, 'Behavioural basics');
  if (!CATEGORIES.includes(fixed)) {
    throw new Error(`Queue category "${raw}" is not in the schema enum: ${CATEGORIES.join(' | ')}`);
  }
  return fixed;
}

function pickTitle(row, modelTitle) {
  if (row.question.length <= TITLE_MAX) return row.question;
  const t = (modelTitle ?? '').trim();
  if (!t || t.length > TITLE_MAX) {
    throw new Error(`Question is ${row.question.length} chars (limit ${TITLE_MAX}) and Claude did not return a valid shortened "title".`);
  }
  return t;
}

function buildMarkdown({ row, description, tags, title, body }) {
  const today = new Date().toISOString().slice(0, 10);
  const readingTime = estimateReadingTime(body);
  const tagList = (tags ?? []).map((t) => `"${t}"`).join(', ');
  const desc = description.length > 165 ? description.slice(0, 162).trim() + '...' : description;

  return `---
title: ${escapeYamlString(pickTitle(row, title))}
description: ${escapeYamlString(desc)}
pubDate: ${today}
category: ${escapeYamlString(normaliseCategory(row.category))}
tags: [${tagList}]
redditQuestion: ${escapeYamlString(row.question)}
readingTime: ${escapeYamlString(readingTime)}
---

${body.trim()}
`;
}

// ───────────────────────────────────────────────────────────────
// Main

async function main() {
  console.log(`[${new Date().toISOString()}] Starting daily blog post generator. Model: ${MODEL}`);

  const queueRaw = await readFile(QUEUE_PATH, 'utf8');
  const { lines, rows } = parseQueue(queueRaw);
  const next = pickNextQueued(rows);
  console.log(`Picked queue row #${next.num}: "${next.question}"`);

  const slug = slugify(next.question);
  const targetPath = join(BLOG_DIR, `${slug}.md`);

  if (existsSync(targetPath)) {
    console.error(`Target file already exists: ${targetPath}. Aborting to avoid overwrite.`);
    process.exit(2);
  }

  console.log('Calling Claude...');
  const responseText = await callClaude(SYSTEM_PROMPT, buildUserPrompt(next));
  const { description, tags, title, body } = parseClaudeResponse(responseText);

  if (!description || !body) throw new Error('Claude response missing description or body.');

  const markdown = buildMarkdown({ row: next, description, tags, title, body });

  await mkdir(BLOG_DIR, { recursive: true });
  await writeFile(targetPath, markdown, 'utf8');
  console.log(`Wrote ${targetPath}`);

  const updatedQueue = markRowPublished(lines, next);
  await writeFile(QUEUE_PATH, updatedQueue, 'utf8');
  console.log(`Marked queue row #${next.num} as published.`);

  // Emit slug for downstream commit message
  if (process.env.GITHUB_OUTPUT) {
    const { appendFile } = await import('node:fs/promises');
    await appendFile(process.env.GITHUB_OUTPUT, `slug=${slug}\nquestion=${next.question}\n`);
  }

  console.log(`Done. New post slug: ${slug}`);
}

main().catch((err) => {
  console.error('FATAL:', err);
  process.exit(1);
});
