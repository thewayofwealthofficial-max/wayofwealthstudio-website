#!/usr/bin/env node
// Writes ONE native LinkedIn post (no link, no ask) from Joel's own words. Mon/Wed/Fri/Sun (Joel, 2026-09-27).
// Rebuilt 6 Nov 2026 because the posts read as AI-written: stitched call lines, smoothed by ~20 rules.
//   1. Joel's passages come from his recent Fathom calls (scripts/daily-email/fathom.mjs) and his solo camera talk,
//      in memory only.
//   2. The model picks ONE real story, moment or point from them and tells it in his voice (scripts/voice/BRAND_VOICE.md),
//      using the SHAPE of one top watchlist outlier (scripts/state/linkedin-monitor/latest.json): its hook pattern,
//      its length, its layout. Only the shape and first line are ever given, never the rest of their post.
//   3. Hard checks only (check() below): nothing invented (figure check + a SEPARATE fact check), no private names,
//      no links, no asks, no prices, no regulated advice, nothing about drugs, under the word limit.
//   4. A separate short "human" pass rewrites only the lines that read like AI into plain spoken lines, adding no
//      facts. The hard checks and the fact check run again on the result; if it fails, the checked draft is kept.
//   5. Joel's choices are logged per draft (scripts/linkedin-outcomes.mjs: posted unchanged, rewritten, ignored),
//      shape and topic only, and the shapes he posted unchanged in the last month are fed back as preferred.
//
// PRIVACY: this repo and its Action logs are PUBLIC. The draft and the passages are never written to a file or
// printed, except with DRY_RUN=1 on Joel's own computer. State keeps only hashes, shapes and labels.
//
// ENV: FATHOM_API_KEY, ANTHROPIC_API_KEY, VOICE_KEY. LINKEDIN_MODEL overrides the model. DRY_RUN=1 prints the draft
// instead of sending it on.

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { recentJoelWords } from './daily-email/fathom.mjs';
import { JOEL_FACTS } from './daily-email/voice.mjs';
import { BRAND_VOICE_BLOCK } from './voice/joel-voice.mjs';
import { talkPassages, openBox } from './voice/talk.mjs';
import { shapeOf } from './linkedin-bank.mjs';
import { markOutcomes, preferredShapes } from './linkedin-outcomes.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const STATE = join(ROOT, 'scripts', 'state', 'linkedin-native.json');
const POSTED = join(ROOT, 'scripts', 'state', 'linkedin-posted.json');
const LATEST = join(ROOT, 'scripts', 'state', 'linkedin-monitor', 'latest.json');
const DRY = process.env.DRY_RUN === '1';
const MODEL = process.env.LINKEDIN_MODEL || 'claude-sonnet-5-5';
const { FATHOM_API_KEY, ANTHROPIC_API_KEY, FRED_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID } = process.env;
const SITE = 'https://wayofwealthcoaching.com';
const MAX_WORDS = 250;

async function telegram(text, reply_markup) {
  const r = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text, parse_mode: 'HTML', disable_web_page_preview: true, ...(reply_markup ? { reply_markup } : {}) }),
  });
  if (!r.ok) throw new Error(`Telegram ${r.status}`);
}

// Topic labels only (what the post is about), shown to Joel and scored by linkedin-own.mjs (which reads this list
// from the source, so keep the `n: { name: '...' }` form). The numbers are kept because old state uses them.
const ANGLES = {
  3: { name: 'The money moment with no tidy lesson' },
  6: { name: 'Mindset and behaviour' },
  8: { name: 'Joel\'s origin: how he came to money' },
  9: { name: 'How a money coach looks after his own money' },
  11: { name: 'Proud of a client\'s small behaviour win' },
  13: { name: 'Small saving habits that add up' },
  14: { name: 'Where the money sits: the accounts, and how much in each' },
  15: { name: 'No good or bad spending: what to cut and what to keep' },
  16: { name: 'The order to do money in' },
  17: { name: 'Looking rich vs becoming rich' },
  18: { name: 'What a money book taught Joel' },
};

// The only research ideas a post may name (TEACHING_SCOPE.md owns what is true). Optional; most posts need none.
const RESEARCH = [
  'Mental accounting (Thaler): we put money into mental boxes, and money in one box gets spent differently from money in another.',
  'Earmarking (Soman & Cheema): money that is labelled for something is spent less. No numbers.',
  'Defaults (Madrian & Shea): people tend to stick with whatever happens automatically.',
  'Commitment devices (Ashraf, Karlan & Yin): making it harder for your future self to touch the money helps more of it stay.',
  'Loss aversion: losses tend to hit harder than the same-sized gain, about twice as hard. Never "exactly twice" or "proven".',
  'Money scripts (Klontz): the beliefs about money we picked up young. A conversation opener, never a diagnosis.',
  'The ostrich effect (Karlsson, Loewenstein & Seppi): people look at their accounts less when things are bad.',
];

const CLIENT_LABEL = 'CLIENT (a client said this on a call, not Joel):';
// The £150k story (Joel, 2 Nov 2026: "use other stories of mine not just the 150k story"): if one of the last
// RECENT_150 posts told it, passages that mention it are left out today. A passage filter, not a rule on the draft.
const IS_150 = /150[,.]?000|150\s?k\b|hundred and fifty (?:grand|thousand)/i;
const RECENT_150 = 4;
const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9£$€% ]+/g, ' ').replace(/\s+/g, ' ').trim();
const hash = (s) => createHash('sha256').update(s).digest('hex').slice(0, 16);
const NUM_WORDS = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12, thirty: 30, sixty: 60, ninety: 90 };
const digits = (s) => String(s).replace(/\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirty|sixty|ninety)\b/gi, (w) => NUM_WORDS[w.toLowerCase()]);

// "Day 1 to day 90 with real numbers": only offered when a passage holds a real timeline AND real figures.
const TIMELINE = /\b(?:day|week|month)\s(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|thirty|sixty|ninety)\b|\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|thirty|sixty|ninety)\s(?:days?|weeks?|months?)\s(?:in|later|on|after)\b/gi;
export const hasTimeline = (t) => (String(t).match(TIMELINE) || []).length >= 2 && /(?:£|\$|€)\s?\d|\d\s?(?:%|k\b|grand|thousand)/i.test(t);

const SYSTEM = `You write ONE LinkedIn post for Joel Ezekiel (Way of Wealth), in his voice.

WHO JOEL IS: ${JOEL_FACTS}
He is a behavioural money coach, not a regulated adviser.

WHO READS IT: people interested in personal finance and money behaviour: saving, spending, where the money goes, why we do what we do with it. UK first in tone.

WHAT TO DO:
1. Read Joel's passages. Pick ONE real story, moment or point from them. Just one.
2. Tell it the way Joel would say it out loud, written down, following his voice file below. Use his own words and phrases where they work. Plain everyday words everywhere else.
3. Use the SHAPE you are given: its kind of hook, its length and its layout (how many paragraphs, how short the lines are). Never its words, its topic or its claims.

HARD LIMITS:
- Nothing invented. No fact, number, date, timeline, person, quote or event that isn't in the passage you picked or in WHO JOEL IS. "I" is Joel's own story only. A passage marked CLIENT is a client's words: never tell it as Joel's, quote it only word for word (filler out), never name or describe the client. A research idea only from this list, as worded: ${RESEARCH.join(' | ')}
- Nobody else's name or place from the calls.
- No links, no hashtags, no ask (one soft question at the very end at most), nothing about his prices or places, no financial advice (no investment, product, pension, debt or tax picks), nothing about drugs.
- Under ${MAX_WORDS} words.
${BRAND_VOICE_BLOCK}

OUTPUT: only valid JSON, no fences:
{"passage": <number of the passage you used>, "angle": <angle number>, "post": "the post, paragraphs separated by \\n\\n"}`;

function describeShape(s) {
  const from = s.source === 'watchlist' ? `a real post by ${s.author}${s.x_median ? ` that did ${s.x_median}x their usual` : ''}`
    : s.source === 'own' ? 'one of Joel\'s own best posts (its story is already on his page: tell a DIFFERENT moment)'
    : `a real post by a money creator${s.x ? ` that did ${s.x}x their usual` : ''}`;
  return `THE SHAPE TO USE (from ${from}; you get its shape only):
- Hook: ${s.hook || 'see its first line'}${s.firstLine ? `. Its first line was: "${s.firstLine}". Copy how that line works (the kind of opening), never its words.` : ''}
- Structure: ${s.structure || (s.story ? 'a story' : 'an idea post')}${s.endsOnQuestion ? ', ends on a question' : ''}
- Length: about ${Math.min(s.words || 200, MAX_WORDS - 10)} words, ${s.paragraphs || '?'} paragraphs${s.wordsPerLine ? `, about ${s.wordsPerLine} words a line` : ''}${s.oneLineParas ? `, ${Math.round(s.oneLineParas * 100)}% of paragraphs are a single short line` : ''}.`;
}

function userPrompt({ passages, angles, shape, preferred, no150, feedback, last }) {
  const a = Object.entries(angles).map(([n, x]) => `${n}. ${x.name}`).join('\n');
  const p = passages.map((x, i) => `[${i}] (${x.date})${x.client ? ` ${CLIENT_LABEL}` : ''}\n${x.text}`).join('\n\n');
  const timeline = passages.some((x) => hasTimeline(x.text))
    ? `\n\nOPTIONAL SHAPE: one of the passages holds a real timeline with real numbers. If you pick it, you may instead tell it as "day 1 to day 90": short dated beats, each with the real number from the passage, then where it landed. Only the days, weeks and figures he actually said.`
    : '';
  const pref = preferred.length
    ? `\n\nJOEL POSTED THESE SHAPES WITHOUT CHANGES THIS MONTH (lean towards them when the given shape leaves room): ${preferred.slice(0, 5).map((x) => `${x.hook || 'any hook'} · ${x.structure || 'any structure'}, about ${x.words} words in ${x.paragraphs} paragraphs`).join('; ')}`
    : '';
  const avoid150 = no150 ? `\n\nNot the £150k story today: it was in one of his last ${RECENT_150} posts.` : '';
  const fix = feedback ? `\n\nYOUR LAST DRAFT WAS REJECTED. Fix only these:\n- ${feedback.join('\n- ')}\n\nLAST DRAFT:\n${last.post}` : '';
  return `${describeShape(shape)}${timeline}${pref}${avoid150}\n\nANGLES (a label for Joel; pick the one that fits the moment):\n${a}\n\nJOEL'S PASSAGES (pick ONE):\n${p}${fix}`;
}

async function claude(system, user, maxTokens) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: MODEL, max_tokens: maxTokens, system, messages: [{ role: 'user', content: user }] }),
  });
  if (!r.ok) throw new Error(`Anthropic ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const text = ((await r.json()).content || []).map((b) => b.text || '').join('').trim();
  // Take the first complete {...} object, so any words the model adds after it are ignored.
  const s = text.indexOf('{');
  let depth = 0, inStr = false, esc = false;
  for (let i = s; s >= 0 && i < text.length; i++) {
    const c = text[i];
    if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
    if (c === '"') inStr = true;
    else if (c === '{') depth++;
    else if (c === '}' && --depth === 0) return JSON.parse(text.slice(s, i + 1));
  }
  throw new Error('No complete JSON object in the reply');
}

// The model names the passage it used. Accepts a number, "7,8" or [7,8] (up to 2, in case one moment spans two).
function pickedPassages(d, passages) {
  const ids = [...new Set(String(d.passage ?? d.passages ?? '').match(/\d+/g) || [])].map(Number).filter((i) => passages[i]).slice(0, 2);
  return ids.length ? { ids, text: ids.map((i) => (passages[i].client ? `${CLIENT_LABEL}\n` : '') + passages[i].text).join('\n\n'), hashes: ids.map((i) => hash(passages[i].text)).join(','), date: passages[ids[0]].date } : null;
}

const FIGURE = /(?:£|\$|€)\s?\d[\d,.]*k?|\d[\d,.]*\s?(?:%|per ?cent)|\b(?:day|week|month)\s\d+\b|\b\d+\s(?:days?|weeks?|months?|years?)\b/gi;

// THE HARD CHECKS. Nothing else: no style rules (6 Nov 2026). Every problem here blocks the draft.
export function check(d, passages, names, shape) {
  const source = pickedPassages(d, passages);
  if (!source) return ['No passage picked. Give the number of the passage you used.'];
  d.source = source;
  const post = String(d.post || '').trim();
  const problems = [];
  // Nothing invented: every figure, day, week or month count must be in the passage or JOEL'S FACTS.
  const src = norm(digits(source.text + ' ' + JOEL_FACTS)).replace(/[\s,]/g, '');
  for (const f of (post.match(FIGURE) || []).map((x) => x.replace(/[.,]+$/, ''))) {
    if (!src.includes(norm(f).replace(/[\s,]/g, ''))) problems.push(`Figure "${f.trim()}" is not in Joel's words or facts.`);
  }
  if (/\b(studies show|study shows|research shows|research says|according to|a recent study|scientists?)\b/i.test(post) && !/\b(study|research)\b/i.test(source.text)) problems.push('Makes a research claim that is not in the passage.');
  // No private names: other speakers and invitees on the calls, and capitalised names or places from the passage.
  for (const n of names) if (n.length > 2 && new RegExp(`\\b${n.replace(/[^A-Za-z'-]/g, '')}\\b`, 'i').test(post)) problems.push(`Contains the name "${n}" from a private call.`);
  const ALLOW = /^(Joel|Money|Story|Method|Way|Wealth|MSc|Behavioural|Economics|Qualified|Financial|Planner|The|And|But|So|When|Then|Now|Yeah|Right|Okay|Jesus|God|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|January|February|March|April|May|June|July|August|September|October|November|December|Uber|Instagram|LinkedIn|Christmas|Day|Week|Month)$/;
  const midSentence = (s) => new Set((s.match(/(?<=[a-z,] )[A-Z][a-z]{2,}\b/g) || []).filter((w) => !ALLOW.test(w)));
  const inCall = midSentence(source.text);
  for (const w of midSentence(post)) if (inCall.has(w)) problems.push(`Uses the name or place "${w}" from a private call.`);
  // No links, asks, prices, advice, drugs.
  if (/https?:\/\/|www\.|\.com\b|\.co\.uk\b|\.shop\b/i.test(post)) problems.push('Contains a link. LinkedIn native posts carry no link.');
  if (/\b(link in (?:my )?bio|book (?:a|your)|free (?:20[- ]minute )?call|DM me|message me|get in touch|sign up|comment below|drop a comment)\b/i.test(post)) problems.push('Contains an ask. At most one soft question at the end.');
  if (/£\s?(1,?000|500|334)\b|\b(?:5|five) (?:people|clients|places)\b|\b(?:spots?|places?)\b[^.\n]{0,20}\b(?:left|open|remaining)\b/i.test(post)) problems.push('Mentions the price or places. Never in a LinkedIn post.');
  if (/\b(you should invest|buy shares|investment advice|put your money in|pay less tax|avoid tax)\b/i.test(post)) problems.push('Reads like regulated advice.');
  if (/\b(drugs?|cocaine|weed)\b/i.test(post)) problems.push('Mentions drugs. Never, including Joel\'s own past (Joel, 2026-09-27).');
  // Under the word limit.
  const words = post.split(/\s+/).filter(Boolean).length;
  if (words > MAX_WORDS) problems.push(`Post is ${words} words; keep it under ${MAX_WORDS}.`);
  // Another creator's words never go out under Joel's name: no 8-word run from the shape's first line.
  if (shape?.firstLine && shape.source !== 'own') {
    const f = norm(shape.firstLine).split(' '), p = ` ${norm(post)} `;
    for (let i = 0; i + 8 <= f.length; i++) if (p.includes(` ${f.slice(i, i + 8).join(' ')} `)) { problems.push('Copies the outlier\'s first line word for word. Keep the kind of hook, use Joel\'s words.'); break; }
  }
  return problems;
}

// Separate pass: a fresh call that only compares claims with the source. Draft first, audit second.
async function audit(post, sourceText) {
  const system = `You are a strict fact checker. You get Joel's own words (call transcript passages), Joel's fixed facts, and a LinkedIn post written from them. List every statement in the post about something that happened, a person, a number, a date or timeline, a feeling Joel had, or what someone did, that is NOT supported by the passages or the facts. The FACTS are true and count as support; where the passages and the FACTS differ on Joel's own credentials or story numbers, the FACTS win. General reflections and questions to the reader are fine. Also flag if the post turns Joel's own story into a client's or a client's into Joel's, or describes or hints at who anyone else in the passages is. A passage starting "${CLIENT_LABEL}" is a client's words: a quote from a client must be in that passage, word for word apart from filler. A named research idea from this list is fine: ${RESEARCH.map((r) => r.split(':')[0]).join('; ')}. Leaving out a detail is never a problem. The post's layout and kind of hook come from another post: that framing is fine. Keep every issue short. Output only JSON: {"items": [{"issue": "short description", "real_problem": true or false}]}`;
  const user = `FACTS:\n${JOEL_FACTS}\n\nPASSAGES:\n${sourceText}\n\nPOST:\n${post}`;
  let r;
  try { r = await claude(system, user, 2000); } catch { r = await claude(system, user, 2000); }
  return (r.items || []).filter((i) => i.real_problem === true).map((i) => `Not in Joel's words: ${i.issue}`);
}

// The human pass: a separate short call that rewrites only the lines that read like AI.
const HUMAN = `You edit a LinkedIn post so it reads like a real person talking, not like AI. Change ONLY the lines that read like AI writing. Leave every other line exactly as it is.
Signs of AI writing: neat lists of three; "here's the thing", "the truth is", "let that sink in", "the reality is", "here's what I learned", "and that's okay"; "it's not X, it's Y" set-ups; staged rhetorical set-ups ("The result? ...", "Why? Because ..."); a tidy moral or summary line at the end; em dashes or en dashes; colons used for drama; polished words a person wouldn't say out loud (journey, unlock, empower, navigate, game-changer, transformative, delve, profound); and words Joel never says per his voice file (mindset in the body, subconscious, framework, protocol, methodology, abundance, holistic).
Rewrite those lines as plain spoken lines the way Joel talks: short everyday words, "so", "now", "right?", his rhythm from the voice file. If the ending is a tidy moral, end on the moment or one plain line instead.
NEVER add a fact, number, date, name, event, feeling or claim. Never remove the story. Keep the hook, the layout and the length within about 10%. If nothing reads like AI, return the post unchanged.
${BRAND_VOICE_BLOCK}

OUTPUT: only valid JSON: {"post": "...", "changed": <number of lines you changed>}`;

const tidy = (s) => String(s || '').replace(/\s*[—–]\s*/g, ', ').replace(/\n{3,}/g, '\n\n').trim();

// The shapes the writer may use, best first. Shape and first line only; never another creator's full post.
function shapeCandidates(state, preferred) {
  const list = [];
  try {
    const m = JSON.parse(readFileSync(LATEST, 'utf8'));
    if (Date.now() - Date.parse(m.date) < 14 * 864e5) {
      for (const p of m.posts || []) if (p.words) list.push({ ...p, ref: p.url, source: 'watchlist', rank: p.x_median ? 1000 + p.x_median : p.per1k || 0 });
    }
  } catch { /* no monitor data yet */ }
  try {
    for (const o of JSON.parse(readFileSync(join(ROOT, 'scripts', 'voice', 'linkedin-own-winners.json'), 'utf8')).posts) list.push({ ...shapeOf(o.body), ref: o.id, source: 'own', story: o.story, rank: -1 });
  } catch { /* none */ }
  try {
    for (const o of openBox('linkedin-outliers.enc')) list.push({ ...shapeOf(o.body), ref: o.id, source: 'bank', story: o.story, x: o.x_own, author: o.author, rank: -1000 + (o.x_own || 0) });
  } catch { /* no VOICE_KEY: watchlist and own posts only */ }
  const liked = new Set(preferred.map((x) => `${x.hook} · ${x.structure}`));
  const usedRecently = (c) => state.some((s) => s.outlier === c.ref && Date.now() - Date.parse(s.date) < 21 * 864e5);
  const score = (c) => c.rank + (liked.has(`${c.hook} · ${c.structure}`) ? 500 : 0);
  return list.sort((a, b) => score(b) - score(a)).map((c) => ({ ...c, used: usedRecently(c) }));
}

async function main() {
  if (!FATHOM_API_KEY || !ANTHROPIC_API_KEY) throw new Error('FATHOM_API_KEY / ANTHROPIC_API_KEY not set');
  if (!DRY && (!FRED_SECRET || !TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID)) throw new Error('FRED_SECRET / TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set');
  const state = existsSync(STATE) ? JSON.parse(await readFile(STATE, 'utf8')) : [];
  const postedIds = existsSync(POSTED) ? JSON.parse(await readFile(POSTED, 'utf8')) : [];
  markOutcomes(state, postedIds);
  const preferred = preferredShapes(state, 30);
  const { passages: calls, clients = [], names } = await recentJoelWords({ key: FATHOM_API_KEY, days: 60, maxPassages: 500 });
  let talk = [];
  try { talk = talkPassages(); } catch (e) { console.log(`Talk passages unavailable (${e.message}).`); }
  const moments = clients.map((c) => ({ ...c, client: true }));
  const all = calls.concat(talk, moments);
  const usedHash = (s, h) => String(s.passage || '').split(',').includes(h);
  const fresh21 = (p) => !state.some((s) => usedHash(s, hash(p.text)) && Date.now() - Date.parse(s.date) < 21 * 864e5);
  const no150 = !process.env.REVISE_ID && state.slice(-RECENT_150).some((s) => s.told150);

  // REVISE_ID: Joel wrote what to fix on the approve page. Rewrite the SAME story with his fixes first.
  const REVISE_ID = process.env.REVISE_ID;
  let orig = null;
  if (REVISE_ID) {
    if (!/^[0-9a-f]{16}$/.test(REVISE_ID)) throw new Error('bad REVISE_ID');
    // Netlify Blobs reads can lag a fresh save by up to ~60s, so wait for his fixes to show up (every 10s, up to 2 min).
    for (let tries = 1; ; tries++) {
      const f = await fetch(`${SITE}/api/linkedin/draft?action=fetch&id=${REVISE_ID}`, { headers: { 'x-fred-secret': FRED_SECRET } });
      if (!f.ok) throw new Error(`Draft fetch ${f.status}`);
      orig = await f.json();
      if (orig.feedback) break;
      if (tries === 12) throw new Error('No fixes stored for this draft (still missing after 2 minutes of retries).');
      console.log(`Fixes not visible yet (try ${tries}/12). Waiting 10s for storage to catch up.`);
      await new Promise((r) => setTimeout(r, 10_000));
    }
  }
  // 7 call passages + 7 talk passages (rotating by day) + up to 5 client moments; a story can come back after 21 days.
  const passages = orig
    ? all.filter((p) => String(orig.passage).split(',').includes(hash(p.text)))
    : (() => { const ok = (p) => fresh21(p) && !(no150 && IS_150.test(p.text)); const t = talk.filter(ok), k = t.length ? (Math.floor(Date.now() / 864e5) * 7) % t.length : 0; return calls.filter(ok).slice(0, 7).concat(t.slice(k, k + 7), t.slice(0, Math.max(0, k + 7 - t.length)), moments.filter(ok).slice(0, 5)); })();
  if (!passages.length) throw new Error(orig ? 'The story this draft came from is no longer in the last 60 days of calls.' : 'No unused story passages in the last 60 days of Fathom calls. Nothing written.');
  const angles = orig && ANGLES[orig.angle] ? { [orig.angle]: ANGLES[orig.angle] } : ANGLES;

  // The shape: a rewrite keeps its draft's shape; otherwise the best watchlist outlier not used in 21 days.
  const cands = shapeCandidates(state, preferred);
  const origEntry = orig && (state.find((s) => s.id === REVISE_ID) || state.find((s) => s.passage === orig.passage && s.outlier));
  const shape = (process.env.OUTLIER && cands.find((c) => c.ref === process.env.OUTLIER))
    || (origEntry && (cands.find((c) => c.ref === origEntry.outlier) || (origEntry.shape && { ...origEntry.shape, ref: origEntry.outlier, source: 'saved' })))
    || cands.find((c) => !c.used) || cands[0];
  if (!shape) throw new Error('No shape to copy: no fresh watchlist outliers and no saved posts.');
  console.log(`Shape from ${shape.source} (${shape.x_median ? `${shape.x_median}x usual` : shape.x ? `${shape.x}x usual` : 'own post'}, ${shape.words} words, ${shape.paragraphs} paragraphs). ${preferred.length} preferred shape(s) from Joel.${no150 ? ' £150k story told recently: left out today.' : ''}`);

  const joelFix = orig ? [`JOEL'S OWN FIXES (do these first, exactly as he asks; the hard limits still apply): ${orig.feedback}`] : [];
  let feedback = orig ? joelFix : null, last = orig ? { post: orig.text } : null, draft = null, backup = null, flags = [];
  for (let attempt = 1; attempt <= 3 && !draft; attempt++) {
    let d;
    try { d = await claude(SYSTEM, userPrompt({ passages, angles, shape, preferred, no150, feedback, last }), 2500); } catch (e) { console.log(`Attempt ${attempt}: bad reply (${e.message.slice(0, 80)}). Retrying.`); continue; }
    d.post = tidy(d.post);
    if (!angles[d.angle]) d.angle = Number(Object.keys(angles)[0]);
    let problems = check(d, passages, names, shape);
    if (!problems.length) { try { problems = await audit(d.post, d.source.text); } catch { problems = ['The fact check could not read its own reply.']; } }
    if (!problems.length) { draft = d; break; }
    // Joel, 7 Oct 2026: if every try only has lines the fact check doubts, send the best one with those lines marked.
    const onlyDoubts = problems.every((p) => /^(Not in Joel's words|The fact check could not read)/.test(p));
    if (onlyDoubts && (!backup || problems.length < backup.problems.length)) backup = { d, problems };
    console.log(`Attempt ${attempt} rejected. Kinds: ${problems.map((p) => p.split(/[:("“]/)[0].trim().slice(0, 50)).join(' | ')}`); // kinds only: logs are public
    if (DRY) console.log('  - ' + problems.join('\n  - ') + `\n${d.post}\n`);
    feedback = joelFix.concat(problems);
    last = d;
  }
  if (!draft && backup) { draft = backup.d; flags = backup.problems; console.log(`Every try had doubted lines. Sending the one with the fewest (${flags.length}), marked for Joel.`); }
  if (!draft) {
    console.log('No draft was safe to send: every try failed a hard check.');
    if (!DRY) await telegram('💼 LinkedIn draft skipped today. Three tries, and every one broke a hard rule (a private name, a link, an ask, price, advice, or a made-up figure), so nothing was sent. The next one runs as normal.');
    return;
  }

  // The human pass, then every hard check again. If it breaks anything, the checked draft goes instead.
  try {
    const h = await claude(HUMAN, `POST:\n${draft.post}`, 2000);
    const hd = { ...draft, post: tidy(h.post) };
    if (hd.post && hd.post !== draft.post) {
      let problems = check(hd, passages, names, shape);
      if (!problems.length && !flags.length) { try { problems = await audit(hd.post, hd.source.text); } catch { problems = ['fact check unreadable']; } }
      if (!problems.length) { draft = hd; console.log(`Human pass: ${Number(h.changed) || 'some'} line(s) rewritten, checks passed.`); }
      else console.log(`Human pass broke a check (${problems.map((p) => p.split(/[:("“]/)[0].trim().slice(0, 40)).join(' | ')}); keeping the checked draft.`);
    } else console.log('Human pass: nothing changed.');
  } catch (e) { console.log(`Human pass failed (${e.message.slice(0, 80)}); keeping the checked draft.`); }

  const words = draft.post.split(/\s+/).length;
  console.log(`Draft ready: angle ${draft.angle} (${ANGLES[draft.angle].name}), ${words} words.`);
  if (DRY) {
    if (flags.length) console.log('FLAGS:\n  - ' + flags.join('\n  - '));
    console.log(`\n----- PASSAGE USED (${draft.source.date}) -----\n${draft.source.text}\n\n----- LINKEDIN POST -----\n` + draft.post + `\n-------------------------`);
    return;
  }
  // Store the draft privately on Netlify, then Fred sends it to Joel with the Approve button. Never logged.
  const r = await fetch(`${SITE}/api/linkedin/draft?action=create`, {
    method: 'POST', headers: { 'content-type': 'application/json', 'x-fred-secret': FRED_SECRET },
    body: JSON.stringify({ text: draft.post, angle: Number(draft.angle), passage: draft.source.hashes, problem: draft.post, pursuit: '', payoff: '' }),
  });
  if (!r.ok) throw new Error(`Draft store ${r.status}: ${(await r.text()).slice(0, 120)}`);
  const { id, sig } = await r.json();
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const from = shape.source === 'own' ? 'your own best post' : shape.author ? `a post by ${esc(shape.author)}${shape.x_median || shape.x ? ` that did ${shape.x_median || shape.x}x their usual` : ''}` : 'a saved post';
  await telegram((orig ? '✏️ <b>Rewritten with your fixes</b>\n' : '') + `💼 <b>LinkedIn draft</b> · angle ${draft.angle}: ${esc(ANGLES[draft.angle].name)} · ${words} words · shape from ${from}\n<i>The labels are for you; they aren't posted.</i>\n\n`
    + (flags.length ? `⛔ <b>The fact check thinks you never said some of this. Check these lines before you approve:</b>\n• ${flags.map(esc).join('\n• ')}\n\n` : '') + esc(draft.post));
  await telegram('Tap below. On that page you can "Approve and post", or write what needs fixing and it gets rewritten. Ignore it and nothing is posted (expires in 48 hours).', {
    inline_keyboard: [[{ text: '✅ Review & approve', url: `${SITE}/api/linkedin/draft?id=${id}&sig=${sig}` }]],
  });
  console.log('Draft stored and sent to Joel on Telegram.');
  // Logged per draft for learning: labels, shape and hashes only, never text. A rewrite is logged with revisedFrom.
  state.push({
    date: new Date().toISOString().slice(0, 10), sentAt: new Date().toISOString(), id, ...(orig ? { revisedFrom: REVISE_ID } : {}),
    angle: Number(draft.angle), topic: ANGLES[draft.angle].name, passage: draft.source.hashes, outlier: shape.ref,
    shape: { source: shape.source, hook: shape.hook || null, structure: shape.structure || null, words, paragraphs: draft.post.split(/\n\s*\n/).length },
    told150: IS_150.test(draft.post),
  });
  markOutcomes(state, postedIds);
  await mkdir(dirname(STATE), { recursive: true });
  await writeFile(STATE, JSON.stringify(state, null, 2) + '\n');
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  main().catch(async (e) => {
    console.error('FATAL:', e.message);
    // Tell Joel the actual reason, not just "failed". Our own messages carry no private words.
    if (!DRY && TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) { try { await telegram(`❌ <b>No LinkedIn draft this time</b>\n${e.message.replace(/&/g, '&amp;').replace(/</g, '&lt;')}`); } catch {} }
    process.exit(1);
  });
}
