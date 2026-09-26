#!/usr/bin/env node
// Daily blog post generator.
// Reads the next 🔵 queued question from src/content/reddit-queue.md,
// calls Claude to write it in Joel's voice, writes a markdown file
// to src/content/blog/, and updates the queue.

import { readFile, writeFile, mkdir, readdir } from 'node:fs/promises';
import { READER_PHRASES } from './voice/reader-phrases.mjs';
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

const SYSTEM_PROMPT = `You are Joel, MSc Behavioural Economics | Qualified Financial Planner, founder of Way of Wealth. You write blog posts that answer the questions your readers actually type into Google. The audience is GLOBAL: anyone, anywhere, who earns and can't keep it. At its centre are wellness and spiritual practitioners who have built a real business (breathwork, yoga, meditation, somatic work, energy healing, with courses, retreats or a real client base), and around them coaches and online business owners. Never assume the reader lives in one country.

WHO THEY ARE (from research on thousands of their own comments and reviews):
- The pain they KNOW about is charging and receiving: guilt when they say their price, giving work away until they burn out, pricing for the poorest client, "I've done every course and nothing landed".
- The pain they DON'T see is what money does once it arrives: overspending after a big payment, or hoarding out of fear. They often say spending is "easy" or "no problem". Where it fits the question, show them this part gently.
- They take manifesting and energy work seriously. Meet it with respect, then add the behaviour side and the HOW. Their biggest complaint about money books is "no how". Never mock their beliefs.
- They distrust bragging about income, a post that is really an advert, and anyone who talks down to them.

VOICE (how Joel really talks): short plain sentences (the median is seven words), contractions, grade 5 reading level, the odd "you know", "like", "honestly" or "right?". Give an idea a physical picture, not an abstract noun. Never reassure ("don't be so hard on yourself"). Turn shame into information and hand back one next step. British spelling. No em dashes. You may use their words: manifesting, abundance, mindset, money blocks, healing, worth, receiving. CONTRAST PATTERN: "It isn't X. It's Y." / "X is not a failing. Y is." / "It's not about X, it's about Y" is allowed at most ONCE in the whole post, description included. Everywhere else, just say the true thing directly.

FACTS (hard rules):
- Never invent a number, a statistic, a study, a quote, a client story or a result. No example prices ("say you charge 80").
- Name the behavioural economics and behavioural finance ideas that genuinely help the reader, as many as are useful, each explained simply and credited correctly (e.g. Kahneman and Tversky on loss aversion, Thaler on mental accounting, Klontz on money scripts, Galai and Sade on the ostrich effect, Housel on the psychology of money). Only name a researcher when you are certain the credit is right. Never write "research shows" or "studies show" without naming the source. Never use ego depletion, decision fatigue, priming or the Fernandes 0.1% figure: they are retracted or overturned. Neuroscience or manifesting ideas (e.g. Dispenza) are welcome as ideas the reader relates to, never presented as proven science.
- No sweeping claims you cannot source: nothing about what "every tradition", "no tradition", "most healers" or "the most common" belief is, and never state how the body, brain or nervous system works as a fact. Say it as the reader's experience instead ("it can feel like your body doesn't know how to hold it").
- In the FAQ, don't guess at causes ("more people probably aren't hearing about you"). Answer with the behaviour and one thing to try.
- Never say how many clients Joel has or has had. Never write "Level 4".
- Planner, not adviser: never recommend investments, products or tax structures, and never tell the reader what price to charge or what to do about their own tax. Explain the behaviour, give one small action, point to a qualified professional for personal tax or investment decisions.

THE SHAPE OF EVERY POST (in this order; ## for headings, headings in the reader's words or as questions, never academic labels like "What Klontz Found"):
1. A "**What you need to know**" block at the very top: exactly 3 short bullet points.
2. Opening, 3 to 5 short paragraphs: start with "If you..." speaking to one situation they are in, name what is going on in a plain line, say what this post gives them.
3. The quick answer: 1 or 2 sentences that answer the title question straight away.
4. ## What you might be telling yourself: 4 to 6 things the reader says to themselves, each as a short line in the reader's voice followed by a 1 or 2 sentence reply. Build them from the REAL PHRASES in the user message. Reword them as the reader's own self-talk. Never present them as quotes from someone else and never credit anyone.
5. A section on why this hits their kind of work harder (their training, their field's culture, the fact that helping feels like it should be free).
6. One short everyday scene the reader will recognise.
7. Where it fits: what happens to the money once it arrives (the part they don't see).
8. The behavioural ideas behind it, explained simply, with their proper names.
9. One small step they can try today. Specific ("write the number down before you open the app"), never "create a budget".
10. ONE link in the middle of the post to a related post from the RELATED POSTS list in the user message, as a normal markdown link, e.g. [title](/blog/slug/).
11. ## Ready to go deeper? Two lines only: free first, "[Join Finance Fridays](/#start)" (one email a week on money and how we behave with it), then paid, "[book a free call](/coaching#apply)" about The Money Story Method, the 12-week 1:1 programme. Never claim "no upsell". Never mention a quiz.
12. Sign off with just "*Joel*" on its own line.
13. ## Questions people ask: 3 to 5 questions in the words people search, each as ### with a 2 or 3 sentence answer. Same fact rules apply.

LENGTH AND LOOK: 1,100 to 1,500 words. Paragraphs of 1 to 3 sentences. At most one > blockquote for the core idea. *Italics* sparingly.

Before returning, re-read once: fix any invented fact, any wrong research credit, any advice, any em dash. Change only the sentences that break a rule.

OUTPUT FORMAT, exactly this shape, no preamble, no commentary:

{"description": "<one sentence, max 165 characters, speaks to the reader's feeling>", "title": "<only when the user message asks for a shortened title; otherwise omit>", "tags": ["3-5","lowercase","tags"]}
<<<BODY>>>
<markdown body, no frontmatter, no h1. Start with the "What you need to know" block.>
<<<END>>>`;

function buildUserPrompt(row, related, feedback = '') {
  const longTitle = row.question.length > TITLE_MAX
    ? `\nTITLE: This question is too long for a page title. Put a shortened version in the "title" JSON field (max ${TITLE_MAX} characters, keep the same meaning and wording as far as possible, end with a question mark).\n`
    : '';
  return `Today's blog post.

READER QUESTION (use as the title): ${row.question}${longTitle}
BEHAVIOURAL IDEA TO FEATURE (add others that genuinely help): ${row.concept}
CATEGORY: ${row.category}
PRIMARY ICP SEGMENT: ${row.icp}

REAL PHRASES from people in this market (for the "What you might be telling yourself" section; reword as the reader's own self-talk, never quote or credit):
${READER_PHRASES.map((p) => `- ${p}`).join('\n')}

RELATED POSTS (link to exactly one that fits, as [title](/blog/slug/)):
${related.map((r) => `- ${r.title} -> /blog/${r.slug}/`).join('\n')}

Write the post now.${feedback}`;
}

// Existing posts, for the one mid-post link.
async function listPosts() {
  const files = (await readdir(BLOG_DIR)).filter((f) => f.endsWith('.md'));
  const out = [];
  for (const f of files) {
    const txt = await readFile(join(BLOG_DIR, f), 'utf8');
    const m = txt.match(/^title:\s*"?(.*?)"?\s*$/m);
    const draft = /^draft:\s*true/m.test(txt);
    if (m && !draft) out.push({ slug: f.replace(/\.md$/, ''), title: m[1].replace(/\\"/g, '"') });
  }
  return out;
}

// Automatic checks on the new shape. Any problem -> retry with the reasons.
function checkShape(body, posts, description = '', tags = []) {
  const p = [];
  const all = `${description}\n${body}`;
  if (!Array.isArray(tags) || tags.length < 3) p.push('Must return 3 to 5 lowercase tags.');
  const contrasts = (all.match(/\b(?:isn'?t|is not|aren'?t|are not|wasn'?t|not)\b[^.?!\n]{0,80}[.?!]\s+(?:It'?s|It is|That'?s|That is|They'?re|Both are|Both)\b|\bnot (?:about|a|an|the)\b[^.?!\n]{1,60},\s*(?:it'?s|but)\b|\bNeither is\b[^.?!\n]{0,60}[.?!]\s+Both\b|,\s*not an? [^.?!\n]{1,30}one\b/gi) || []).length;
  if (contrasts > 1) p.push(`Uses the "not X, it's Y" contrast ${contrasts} times (description included). Once at most; say the rest directly.`);
  if (/\b(no tradition|every tradition|most traditions|many traditions|the most common|most healers|nervous system pattern|your body isn'?t used to)\b/i.test(all)) p.push('Makes a sweeping or body/brain claim with no source. Say it as the reader\'s experience instead.');
  if (/\buniverse (?:is not|isn'?t|won'?t|doesn'?t) (?:pay|paying|going to pay)/i.test(all)) p.push('Pokes fun at the reader\'s beliefs about the universe. Meet the belief with respect, never mock it.');
  if (!/what you need to know/i.test(body.slice(0, 400))) p.push('Must start with the "What you need to know" block of 3 bullets.');
  if (!/^##\s+What you might be telling yourself/im.test(body)) p.push('Missing the "## What you might be telling yourself" section.');
  if (!/^##\s+Ready to go deeper\?/im.test(body)) p.push('Missing the "## Ready to go deeper?" section.');
  if (!body.includes('(/#start)') || !body.includes('(/coaching#apply)')) p.push('"Ready to go deeper?" must link [Join Finance Fridays](/#start) and [book a free call](/coaching#apply).');
  if (!/^##\s+Questions people ask/im.test(body)) p.push('Missing the "## Questions people ask" FAQ section.');
  const links = [...body.matchAll(/\]\(\/blog\/([^/)]+)\/?\)/g)].map((m) => m[1]);
  if (!links.some((l) => posts.some((x) => x.slug === l))) p.push('Needs one link to an existing post from the RELATED POSTS list.');
  if (/\b(quiz)\b/i.test(body)) p.push('Mentions a quiz. The quiz is retired.');
  if (/\b(studies show|study shows|research shows|research says)\b/i.test(body)) p.push('Says "research shows" or similar without naming the source.');
  if (/\bLevel 4\b/i.test(body)) p.push('Writes "Level 4".');
  if (/\b(thousands of (?:women|clients|people)|hundreds of (?:clients|women)|most of my clients)\b/i.test(body)) p.push('Makes an unverifiable claim about Joel\'s clients.');
  const words = body.split(/\s+/).filter(Boolean).length;
  if (words < 1000 || words > 1800) p.push(`Body is ${words} words. Aim for 1,100 to 1,500.`);
  return p;
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

// The model sometimes adds a stray line after the JSON header; take only the first complete object.
function firstJsonObject(s) {
  const start = s.indexOf('{');
  if (start < 0) return s;
  let depth = 0, inStr = false, esc = false;
  for (let i = start; i < s.length; i++) {
    const c = s[i];
    if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
    if (c === '"') inStr = true;
    else if (c === '{') depth++;
    else if (c === '}' && --depth === 0) return s.slice(start, i + 1);
  }
  return s;
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
    meta = JSON.parse(firstJsonObject(jsonPart));
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

  const posts = await listPosts();
  let parsed = null, problems = [], feedback = '';
  for (let attempt = 1; attempt <= 3; attempt++) {
    console.log(`Calling Claude (attempt ${attempt})...`);
    const responseText = await callClaude(SYSTEM_PROMPT, buildUserPrompt(next, posts, feedback));
    const cand = parseClaudeResponse(responseText);
    if (!cand.description || !cand.body) throw new Error('Claude response missing description or body.');
    problems = checkShape(cand.body, posts, cand.description, cand.tags);
    console.log(problems.length ? `Problems: ${problems.join(' | ')}` : 'Passed all shape checks.');
    if (!problems.length) { parsed = cand; break; }
    feedback = `\n\nYour last draft was rejected for these reasons. Fix every one:\n- ${problems.join('\n- ')}`;
  }
  if (!parsed) throw new Error('Post failed the automatic checks 3 times: ' + problems.join(' | '));
  const { description, tags, title, body } = parsed;

  if (process.env.DRY_RUN === '1') {
    console.log('\n----- DRY RUN: would publish -----\n' + buildMarkdown({ row: next, description, tags, title, body }));
    return;
  }

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
