#!/usr/bin/env node
// Trending-topic blog engine.
//   1. Gather what people are reading and searching for right now (sources.mjs)
//   2. Claude picks the ONE story that is most talked about AND that self-employed people, coaches and
//      wellness practitioners will feel in their own money life. If nothing fits, no post is written.
//   3. Fetch that article so the post only states facts that are in the source
//   4. Claude writes the post in Joel's voice; automatic checks must pass (retry with feedback, then skip)
//   5. Write src/content/blog/<slug>.md. The workflow commits it and Netlify deploys it.
//
// ENV: ANTHROPIC_API_KEY. Optional: CLAUDE_MODEL. DRY_RUN=1 prints the post instead of writing it.

import { readFile, writeFile, readdir, mkdir, appendFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gatherItems, fetchArticleText } from './sources.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BLOG_DIR = join(__dirname, '..', '..', 'src', 'content', 'blog');
const KEY = process.env.ANTHROPIC_API_KEY;
const MODEL = process.env.CLAUDE_MODEL ?? 'claude-sonnet-4-6';
const DRY = process.env.DRY_RUN === '1';
if (!KEY) { console.error('FATAL: ANTHROPIC_API_KEY is not set'); process.exit(1); }

const CATEGORIES = ['Spending & shame', 'Anxiety & avoidance', 'ADHD & money', 'Self-employed', 'Budgeting that sticks', 'Behavioural basics'];
const TITLE_MAX = 100;

async function claude(system, user, maxTokens = 6000) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: MODEL, max_tokens: maxTokens, system, messages: [{ role: 'user', content: user }] }),
  });
  if (!r.ok) throw new Error(`Anthropic API ${r.status}: ${(await r.text()).slice(0, 300)}`);
  const d = await r.json();
  const text = (d.content || []).map((b) => b.text || '').join('').trim();
  if (!text) throw new Error('Empty response from Claude');
  return text;
}

const slugify = (t) => t.toLowerCase().replace(/['’]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);
const yamlStr = (s) => JSON.stringify(String(s));
const clean = (s) => String(s || '').replace(/\s*—\s*/g, ', ').replace(/\s*–\s*/g, ', ');

// ---------- 1 + 2: gather and pick ----------

const PICKER_SYSTEM = `You choose the single best story for a money-psychology blog written by Joel: MSc Behavioural Economics, Qualified Financial Planner (UK).

READERS: self-employed people, coaches and wellness practitioners (yoga, breathwork, meditation, energy work) who earn well and still feel broke. They feel guilty charging what they are worth, avoid their tax and statements, and live in feast-or-famine months.

PICK the ONE item that (a) is genuinely talked about right now (it shows up in several sources or is trending) and (b) these readers will feel in their own money life, so Joel can honestly connect it to a well-known behavioural idea. Good: tax and HMRC changes, interest rates, energy and living costs, a cost or price shock, savings, pensions for the self-employed, AI changing freelance work, big spending events.

SKIP: war, partisan politics, crime, deaths, disasters, celebrity, sport, health emergencies, anything you could only discuss by giving personal tax or investment advice. If nothing fits, return null. Never force a weak fit.

Reply with ONLY JSON: {"choice": <number or null>, "why": "<one sentence>", "concept": "<one well-established behavioural concept, e.g. loss aversion, present bias, mental accounting, anchoring, money scripts, the ostrich effect>", "category": "<one of: ${CATEGORIES.join(' | ')}>"}`;

async function pickStory(items) {
  const list = items.slice(0, 90).map((it, i) => `${i}. [${it.source}${it.traffic ? ' · trending ' + it.traffic : ''}] ${it.title}${it.summary ? ' :: ' + it.summary.slice(0, 140) : ''}`).join('\n');
  const text = await claude(PICKER_SYSTEM, `Today's items:\n\n${list}\n\nChoose now. JSON only.`, 600);
  const m = text.match(/\{[\s\S]*\}/);
  if (!m) throw new Error('Picker returned no JSON: ' + text.slice(0, 200));
  const j = JSON.parse(m[0]);
  if (j.choice === null || j.choice === undefined) return null;
  const item = items[Number(j.choice)];
  if (!item) throw new Error('Picker chose an item that does not exist: ' + j.choice);
  const category = CATEGORIES.includes(j.category) ? j.category : 'Self-employed';
  return { item, why: j.why, concept: j.concept, category };
}

// ---------- 3 + 4: write and check ----------

const BANNED = ['hustle', 'grind', 'manifest', 'abundance', 'money magnet', 'passive income', 'financial freedom', 'vibration', 'law of attraction', 'journey', 'breakthrough', 'unlock', 'delve', 'unpack', 'tapestry', 'holistic', 'mindset', 'level 4', 'game changer', 'quiz'];

const WRITER_SYSTEM = `You are Joel: MSc Behavioural Economics, Qualified Financial Planner (UK), founder of Way of Wealth. You write a short blog post that connects something in the news right now to a well-known behavioural money idea, for self-employed people, coaches and wellness practitioners. Address the reader as "you". NEVER write the name "Jess".

FACTS: You will be given the SOURCE TEXT of one article. State a news fact ONLY if it is in that source text, and say who reported it ("The Guardian reports..."). Never invent a number, a date, a quote or a study. Paraphrase; never copy more than a short phrase. Use quotation marks ONLY around exact words that appear in the source text. If the source is thin, say less. Do not add facts from memory about the news event.

RESEARCH: name a researcher or idea only if you are certain it is accurate and well known (Kahneman and Tversky on loss aversion, Thaler on mental accounting, Klontz on money scripts, Galai and Sade on the ostrich effect). Never write "studies show" about a specific result. Do not use anything retracted (ego depletion, decision fatigue, priming, the Fernandes 0.1% figure).

SCOPE: you are a planner, not an adviser. Never recommend investments, products, tax steps or what someone should do with their own tax or money. Explain what is happening in their head, give ONE small behavioural action, and point to a qualified professional for personal decisions.

VOICE (this is how Joel really talks): short plain sentences, contractions, grade 5 reading level, the odd "you know", "like", "honestly" or "right?". Give ideas a physical picture, not an abstract noun. Never reassure ("don't be so hard on yourself"). Turn shame into information. No em dashes. British spelling. No "It's not X, it's Y" pairs. No wellness jargon (healing, alignment, nervous system, abundance, manifest, mindset). Banned: ${BANNED.join(', ')}.

STRUCTURE (700 to 1000 words, ## headings, short paragraphs): open with the news in one plain sentence from the source; why it lands on you; the behavioural idea by its proper name; one small action for this week; a soft pointer to The Money Story Method (12-week 1:1 programme) OR the free Finance Fridays newsletter; then a line "*Source: [Publication](URL)*"; then sign off with just *Joel*.

OUTPUT, exactly this shape, no preamble:
{"title": "<max ${TITLE_MAX} characters, plain, speaks to the reader's feeling, no clickbait>", "description": "<one sentence, max 160 characters>", "tags": ["3-5","lowercase","tags"]}
<<<BODY>>>
<markdown body, no frontmatter, no h1>
<<<END>>>`;

function parse(text) {
  const cleaned = text.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '').trim();
  const s = cleaned.indexOf('<<<BODY>>>'), e = cleaned.lastIndexOf('<<<END>>>');
  if (s < 0 || e <= s) throw new Error('Writer response missing body sentinels');
  const meta = JSON.parse(cleaned.slice(0, s).trim().match(/\{[\s\S]*\}/)[0]);
  return { title: clean(meta.title).trim(), description: clean(meta.description).trim(), tags: meta.tags || [], body: clean(cleaned.slice(s + 10, e)).trim() };
}

function check(post, source, url) {
  const p = [];
  const all = `${post.title}\n${post.description}\n${post.body}`;
  const lower = all.toLowerCase();
  if (/\bJess\b/.test(all)) p.push('Mentions the internal persona name "Jess".');
  if (all.includes('—')) p.push('Contains an em dash.');
  for (const w of BANNED) if (lower.includes(w)) p.push(`Uses banned word "${w}".`);
  if (/\b(studies show|study shows|research shows|research says|scientists (?:say|found)|a recent study)\b/i.test(post.body)) p.push('Makes a research claim without naming a source.');
  const figs = post.body.match(/(?:£|\$|€)\s?\d[\d,.]*\s?(?:bn|m|k|billion|million)?|\d[\d,.]*\s?(?:%|per ?cent)/gi) || [];
  for (const f of figs) if (!source.includes(f.trim())) p.push(`Figure "${f.trim()}" is not in the source text.`);
  const norm = (s) => s.toLowerCase().replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/\s+/g, ' ');
  const quotes = (post.body.match(/["“]([^"”]{12,}?)["”]/g) || []).map((q) => q.slice(1, -1));
  for (const q of quotes) if (!norm(source).includes(norm(q))) p.push(`Quoted text "${q.slice(0, 50)}" is not in the source. Only quote exact words from the source.`);
  if (!post.body.includes(url)) p.push('Must link to the source article URL.');
  if (post.title.length > TITLE_MAX || post.title.length < 15) p.push(`Title must be 15 to ${TITLE_MAX} characters.`);
  if (post.description.length > 165) p.push('Description over 165 characters.');
  const words = post.body.split(/\s+/).length;
  if (words < 600 || words > 1200) p.push(`Body is ${words} words, need 600 to 1200.`);
  if (/\b(you should (?:buy|invest|sell|switch|move your)|invest in|put your money in|pay less tax|avoid tax|tax loophole)\b/i.test(all)) p.push('Reads like regulated financial or tax advice.');
  if (/\b(I read every|thousands of|hundreds of|most of my clients|guaranteed?)\b/i.test(all)) p.push('Unverifiable claim about Joel, clients or results.');
  if (!/\*Joel\*\s*$/.test(post.body.trim()) && !/\bJoel\s*$/.test(post.body.trim())) p.push('Must end with the sign-off *Joel*.');
  return p;
}

// ---------- main ----------

async function main() {
  console.log(`[${new Date().toISOString()}] News engine. Model: ${MODEL}${DRY ? ' (DRY RUN)' : ''}`);
  const { items, report } = await gatherItems();
  console.log('Sources: ' + report.join(' | '));
  if (items.length < 10) throw new Error('Too few items gathered (' + items.length + '). Feeds may be down.');

  const existing = existsSync(BLOG_DIR) ? await readdir(BLOG_DIR) : [];
  const usedText = (await Promise.all(existing.map((f) => readFile(join(BLOG_DIR, f), 'utf8').catch(() => '')))).join('\n');
  const fresh = items.filter((i) => !(i.link && usedText.includes(i.link)));
  console.log(`${items.length} items, ${fresh.length} not yet written about.`);

  const pick = await pickStory(fresh);
  if (!pick) { console.log('No story today is a genuine fit for the readers. No post written.'); return; }
  console.log(`Picked: [${pick.item.source}] ${pick.item.title}\nWhy: ${pick.why}\nConcept: ${pick.concept}`);

  const url = pick.item.link;
  let source = await fetchArticleText(url);
  if (source.length < 600) source = `${pick.item.title}. ${pick.item.summary}`;
  if (source.length < 200) throw new Error('Could not get enough source text to write from safely.');
  console.log(`Source text: ${source.length} characters from ${url}`);

  let post = null, problems = [], feedback = '';
  for (let attempt = 1; attempt <= 3; attempt++) {
    const user = `NEWS ITEM: ${pick.item.title}\nPUBLISHER: ${pick.item.source}\nURL: ${url}\nBEHAVIOURAL IDEA TO USE: ${pick.concept}\nWHY IT MATTERS TO THE READER: ${pick.why}\n\nSOURCE TEXT (the only facts you may state about the news):\n${source}\n\nWrite the post now.${feedback}`;
    const cand = parse(await claude(WRITER_SYSTEM, user));
    problems = check(cand, source, url);
    console.log(`Attempt ${attempt}: "${cand.title}" -> ${problems.length ? problems.join(' | ') : 'passed all checks'}`);
    if (!problems.length) { post = cand; break; }
    feedback = `\n\nYour last draft was rejected for these reasons. Fix every one:\n- ${problems.join('\n- ')}`;
  }
  if (!post) throw new Error('Post failed the automatic checks 3 times: ' + problems.join(' | '));

  const slug = slugify(post.title);
  const target = join(BLOG_DIR, `${slug}.md`);
  if (existsSync(target)) throw new Error('A post with this slug already exists: ' + slug);
  const words = post.body.split(/\s+/).length;
  const md = `---\ntitle: ${yamlStr(post.title)}\ndescription: ${yamlStr(post.description)}\npubDate: ${new Date().toISOString().slice(0, 10)}\ncategory: ${yamlStr(pick.category)}\ntags: [${post.tags.map((t) => yamlStr(String(t).toLowerCase())).join(', ')}]\nreadingTime: ${yamlStr(Math.max(3, Math.round(words / 230)) + ' min read')}\n---\n\n${post.body}\n`;

  if (DRY) { console.log('\n----- DRY RUN: would publish -----\n' + md); return; }
  await mkdir(BLOG_DIR, { recursive: true });
  await writeFile(target, md, 'utf8');
  console.log('Wrote ' + target);
  if (process.env.GITHUB_OUTPUT) await appendFile(process.env.GITHUB_OUTPUT, `slug=${slug}\ntitle=${post.title}\nsource=${url}\n`);
}

main().catch((e) => { console.error('FATAL:', e); process.exit(1); });
