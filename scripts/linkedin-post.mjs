#!/usr/bin/env node
// Writes ONE native LinkedIn post (no link, no ask) from Joel's own words. Mon/Wed/Fri/Sun (Joel, 2026-09-27).
//   1. Joel's story passages come from his recent Fathom calls (scripts/daily-email/fathom.mjs), in memory only.
//   2. The model picks ONE passage and ONE of the bridge angles it truly supports, then writes the post in that
//      angle's shape (research/2026-09-25-linkedin/v2/LINKEDIN_BRIDGE.md §5, SCRIPTING.md §7).
//   3. Automatic checks (below), then a SEPARATE audit call that compares every claim with Joel's words.
//      Fails are fed back; after 5 fails nothing is posted and Fred says why.
//
// PRIVACY: this repo and its Action logs are PUBLIC. The draft and the passages are never written to a file or
// printed, except with DRY_RUN=1 on Joel's own computer. State keeps only a hash of the passage used.
//
// ENV: FATHOM_API_KEY, ANTHROPIC_API_KEY. DRY_RUN=1 prints the draft instead of sending it on.

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { recentJoelWords } from './daily-email/fathom.mjs';
import { JOEL_FACTS } from './daily-email/voice.mjs';
import { READER_PHRASES } from './voice/reader-phrases.mjs';
import { BRAND_VOICE_BLOCK } from './voice/joel-voice.mjs';
import { talkPassages, openBox } from './voice/talk.mjs';
import { joelShare } from './voice/own-words.mjs';
import { readOwn, ranking as ownRanking } from './linkedin-own.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const STATE = join(ROOT, 'scripts', 'state', 'linkedin-native.json');
const DRY = process.env.DRY_RUN === '1';
const MODEL = process.env.LINKEDIN_MODEL || 'claude-sonnet-4-6';
const { FATHOM_API_KEY, ANTHROPIC_API_KEY, FRED_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID } = process.env;
const SITE = 'https://wayofwealthcoaching.com';

async function telegram(text, reply_markup) {
  const r = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text, parse_mode: 'HTML', disable_web_page_preview: true, ...(reply_markup ? { reply_markup } : {}) }),
  });
  if (!r.ok) throw new Error(`Telegram ${r.status}`);
}

// The bridge angles (LINKEDIN_BRIDGE.md §5). Shape and length only; no competitor wording.
// Angle 7 is left out: its format is a short video of Joel, which a robot can't make.
const ANGLES = {
  1: { name: 'The month after the big payment', hook: 'a confession: the moment the account was lower than expected', shape: 'before → what happened, shown as 3–4 "→" lines of real figures → one small fix → no shame, no blame. If it is a client, tell their feelings, not just the numbers.', words: [230, 340] },
  2: { name: 'Full diary, empty account', hook: 'a personal or client story: how it looked from the outside', shape: 'outside vs inside → the warning signs → what actually changed', words: [280, 550] },
  3: { name: 'The money moment with no tidy lesson', hook: 'a confession that he has avoided telling this', shape: 'Joel\'s own low point with money, dated, specific moments, says outright there is no neat takeaway. No ask.', words: [280, 550] },
  4: { name: 'Why a 60-minute session isn\'t 60 minutes of work', hook: 'a question comparing two prices', shape: 'explainer comparing two ways of working, step by step, no lecture', words: [350, 450] },
  5: { name: '"I can\'t pay myself, my income isn\'t consistent"', hook: 'the objection they carry, said as a plain "you" line, never in quote marks (their words become "you" lines, never quotes)', shape: 'the line → the reply → short reframe lines, one per paragraph → end on a line that lands. Never a "5 signs" list.', words: [150, 230] },
  6: { name: 'Mindset and behaviour', hook: 'a myth line', shape: 'myth → "In reality..." → 4–5 short lines on what else has to happen → one-line close. Take manifesting seriously; never claim it works.', words: [40, 90] },
  8: { name: 'Why a money person works with small business owners (Joel\'s origin)', hook: 'personal: why he walked away from something', shape: 'origin story with a lesson: the win, the loss, then the MSc and QFP (in that order), then why small business owners', words: [300, 400] },
  9: { name: 'How a money coach looks after his own money', hook: 'a plain statement of the topic', shape: 'his personal routine, the why behind it, who taught him', words: [230, 290] },
  10: { name: 'Emergency fund vs runway for income that swings', hook: 'a call-out to fellow small business owners with a question', shape: 'why standard advice doesn\'t fit → a simple everyday comparison → how to work out your runway. Budgeting education only, no products.', words: [270, 340] },
  11: { name: 'Proud of a client\'s small behaviour win', hook: 'personal: proud of someone he works with', shape: 'short client win → it doesn\'t have to be a big number → what the win really was', words: [80, 130] },
  12: { name: '"Pay me when you can"', hook: 'a call-out plus his own story', shape: 'call-out → what happened → how it felt → 3 changes. Tone hurt, not angry.', words: [270, 340] },
};

// THE MIX (IDEATION.md: 3 reach / 2 positioning / 1 nurture / 1 convert), fitted to 4 LinkedIn days (Joel, 2026-09-27):
// Mon reach · Wed positioning · Fri reach · Sun nurture and convert in turn. Each job has its own angles.
const JOBS = {
  reach: { angles: [5, 2, 4, 12], brief: 'REACH (attract): mindset through psychology: money stress, avoiding the numbers, always feeling behind, not paying yourself, working hard with nothing left. Told through their situation (a small business owner who earns decent money: clients, invoices, a slow month, the tax bill) and Joel\'s words. Carries ONE research line from RESEARCH IDEAS.' },
  positioning: { angles: [6, 10], brief: 'POSITIONING: "there\'s a name for this". A money habit they recognise, the research name for it (ONE idea from RESEARCH IDEAS), and the practical how: real tactics and expertise, not just the insight.' },
  nurture: { angles: [3, 8, 9], brief: 'NURTURE: Joel\'s own story. If it is the £150k story: £3,000 → £150,000 → lost it all → that sent him to study why (MSc, then QFP), always in that order, and always say what changed. Or his own current struggle or routine, warts and all.' },
  convert: { angles: [1, 11], brief: 'CONVERT: where the money goes once it lands (the month after a big payment, the tax bill that comes later, business and home money mixed together), then the practical fix (separate pots, a tax pot, paying yourself a steady wage). No link, no ask, no product name.' },
};
const jobOf = (angle) => Object.keys(JOBS).find((j) => JOBS[j].angles.includes(Number(angle)));

// Research ideas the robot may name: ONLY these, said the way TEACHING_SCOPE.md allows (it owns what is true).
const RESEARCH = [
  { key: /mental account/i, line: 'Mental accounting (Thaler): we put money into mental boxes, and money in one box gets spent differently from money in another.' },
  { key: /earmark/i, line: 'Earmarking (Soman & Cheema): money that is labelled for something is spent less. No numbers.' },
  { key: /default/i, line: 'Defaults (Madrian & Shea): people tend to stick with whatever happens automatically.' },
  { key: /save more tomorrow/i, line: 'Save More Tomorrow (Thaler & Benartzi): people commit to saving more later, out of money they haven\'t got yet.' },
  { key: /commitment device/i, line: 'Commitment devices (Ashraf, Karlan & Yin): making it harder for your future self to touch the money helps more of it stay.' },
  { key: /if[- ]then|implementation intention/i, line: 'If-then plans (implementation intentions): "when an invoice lands, 30% moves to the tax pot" beats a goal. Name no effect size.' },
  { key: /loss aversion/i, line: 'Loss aversion: losses tend to hit harder than the same-sized gain, about twice as hard. Never "exactly twice" or "proven".' },
  { key: /money script|klontz/i, line: 'Money scripts (Klontz): the beliefs about money we picked up young. A conversation opener, never a diagnosis.' },
  { key: /positive fantas|oettingen|mental contrast/i, line: 'Positive fantasies (Oettingen): picturing only the dream outcome can drain the energy to act on it. Pair the dream with the obstacle.' },
  { key: /ostrich/i, line: 'The ostrich effect (Karlsson, Loewenstein & Seppi): people look at their accounts less when things are bad. "You check on payday. You stop checking when you owe."' },
];

// Story angles follow Problem → Pursuit → Payoff (SCRIPTING.md §4; Joel, 2026-09-27: "any storytelling posts should follow the three Ps").
const STORY = new Set([1, 2, 3, 8, 9, 11, 12]);

const SYSTEM = `You write ONE LinkedIn post for Joel Ezekiel (Way of Wealth), in his voice, built only from his own words.

WHO JOEL IS: ${JOEL_FACTS}
He is a planner, not an adviser: never recommend investments, products, pensions, debt choices or tax moves.

WHO READS IT: small business owners with a service business (coaches, therapists, consultants, freelancers, creatives, trades). Global, UK first in tone. They earn decent money, but their money feels chaotic. Their pains, most common first: money stress, income that swings, not paying themselves, not knowing where the money goes, the tax bill shock, working hard with nothing left, burnout, and home bills tangled up with the business. What they want: calm first, then a steady wage, then a buffer, then tax sorted. Their own words: "pay myself", "struggle", "confused", "take home", "where my money is going", "always behind". If they take mindset or manifesting seriously, so does Joel, and he adds the behaviour side. Never mock it, never claim it works.
Joel has NOT coached wellness practitioners yet. Never say or imply that a client of his is a healer, yoga teacher, breathwork facilitator or practitioner unless his own words say so.

THE SHAPE COMES FROM ONE REAL POST (Joel, 6 Oct 2026: the reel built by copying a real outlier, "yes love this script"; the LinkedIn post built from written "shapes", "terrible"). You get ONE OUTLIER POST: a real LinkedIn post that did well with self-employed and small-business readers. Copy it the way SCRIPTING.md copies a reel:
- KEEP ITS HOOK: its first line(s), changed only enough to fit Joel's topic (swap the topic words, keep the build).
- FOLLOW ITS STRUCTURE BEAT FOR BEAT: the same number of paragraphs and roughly the same number of sentences, each about the same length. If its list stacks, yours stacks. If it ends on a question, yours ends on a question. If it tells a story, yours tells Joel's story in the same beats.
- EVERY OTHER LINE IS JOEL'S: where their line does a job (a confession, a scene, a list item, the turn, the lesson), Joel's line does the same job, taken from his_lines.
- Never more than 15% of their wording outside the hook, never 12 of their words in a row, and never their facts, story, numbers, names or claims.
- No link. No hashtags. No ask, or at most one soft question at the very end. Never their call to action.

JOEL'S VOICE (measured from his real speech): plain, warm, direct. Short words. A long sentence carries the reasoning, a short one lands the point. He says "like", "honestly", "you know", "right?" now and then. He uses everyday comparisons. British spelling. No em dashes. No "It's not X, it's Y". No three-item filler lists. No delve, unpack, tapestry, journey, unlock, "here's the thing", "the truth is".

HARD RULES (a draft that breaks any is rejected):
- THE VOICE RULE THAT OVERRIDES EVERYTHING (Joel's email prompt, EMAIL_COPY.md, 2026-10-05): every post must sound like Joel, not like a generic coach and not like the top LinkedIn posts. The test: "Does this sound like Joel talking, or like a coach trying to sound like Joel?"
- This is a transcript-to-post job: keep Joel's words and rhythm, and tidy only the filler ("um", "so basically", repeated phrases, false starts). MOST of the post must be his own sentences from the ONE passage you pick, in his words. Your own words only to join or trim his. If the passage doesn't hold enough of his words for an angle, pick a different angle or passage. Add nothing that happened that he didn't say.
- No invented facts, numbers, dates, studies or quotes. Numbers only from the passage or JOEL'S FACTS.
- "I/me/my" in a passage is Joel's own story: tell it as his. Never turn his story into a client's or a client's into his.
- Never name or describe anyone else in the passage (clients, partners, family, friends, firms, places). Say "someone I work with" for a client.
- Never mention anyone else's health, drinking, drugs, self-harm or legal trouble.
- Never mention drugs at all, including Joel's own past (Joel, 2026-09-27).
- Never mention the price, how many people he works with, or places left.
- No research claims except ONE idea from RESEARCH IDEAS when the job asks for it, worded as given there ("there's a name for this", "researchers call this"). Never "studies show", "research shows" or "a recent study", and never add a number or detail that isn't written there.

THEIR WORDS: the READER PHRASES are real things strangers in this market have written. You may turn one into a "you" line. Never quote them, never credit them.

HOW TO BUILD IT (three steps, in this order):
1. "his_lines": copy out 12 to 25 of Joel's own sentences from the ONE passage, word for word, with only the filler taken out (um, like, you know, so basically, repeats, false starts). Do not reword them. Pick the ones that carry the story and the point.
2. "map": for each paragraph of the OUTLIER, one short line: what job it does, and which of his_lines fills it.
3. "post": write it, paragraph for paragraph. At least half the words are his lines as copied. Your own words only for the adapted hook, short joins, and at most one research line.
${BRAND_VOICE_BLOCK}

OUTPUT: only valid JSON, no fences:
{"passage": <number of the passage you used>, "angle": <angle number>, "his_lines": ["...", "..."], "map": ["...", "..."], "post": "paragraphs separated by \\n\\n"}`;

function userPrompt(passages, angles, feedback, last, job, outlier) {
  // Angles are now only WHAT the post is about; the outlier decides how it is built (6 Oct 2026).
  const a = Object.entries(angles).map(([n, x]) => `${n}. ${x.name}`).join('\n');
  const p = passages.map((x, i) => `[${i}] (${x.date})\n${x.text}`).join('\n\n');
  const research = ['reach', 'positioning'].includes(job) ? `\n\nRESEARCH IDEAS (use exactly ONE, as worded here):\n${RESEARCH.map((r) => '- ' + r.line).join('\n')}` : '';
  // What's working on LinkedIn (scripts/linkedin-monitor.mjs, monthly on the 1st). Patterns only, never their words.
  // Used for 35 days so it covers the whole month (was 14, which left Fred with nothing from about the 15th; 1 Oct 2026).
  let working = '';
  try {
    const m = JSON.parse(readFileSync(join(ROOT, 'scripts', 'state', 'linkedin-monitor', 'latest.json'), 'utf8'));
    if (Date.now() - Date.parse(m.date) < 35 * 864e5 && m.posts?.length) {
      working = `\n\nWHAT'S WORKING ON LINKEDIN THIS MONTH (top public posts in Joel's space; copy the pattern if it fits, never their words):\n${m.posts.slice(0, 5).map((x) => `- ${x.topic ? `[${x.topic}] ` : ''}${x.hook} · ${x.structure}: ${x.why}`).join('\n')}`;
    }
  } catch { /* no monitor data yet */ }
  // Proven over months (scripts/linkedin-bank.mjs): won in 2+ months from 3+ different people. Stronger than the above.
  try {
    const b = JSON.parse(readFileSync(join(ROOT, 'scripts', 'state', 'linkedin-monitor', 'bank.json'), 'utf8'));
    const { patterns = [], topics = [] } = b.promoted || {};
    if (patterns.length || topics.length) {
      working += `\n\nPROVEN IN JOEL'S SPACE (won across several months, from different people; lean on these):${patterns.length ? `\n- Shapes: ${patterns.join('; ')}` : ''}${topics.length ? `\n- Topics: ${topics.join('; ')}` : ''}`;
    }
  } catch { /* no bank yet */ }
  // Joel's OWN results (scripts/linkedin-own.mjs): post types and topics with 3+ scored posts, vs his average.
  try {
    const r = ownRanking(readOwn());
    const line = (xs, name) => xs.map((x) => `${name(x.key)} ${x.avg} per 1k over ${x.n} posts (${x.avg >= r.overall ? 'above' : 'below'} his average)`).join('; ');
    if (r.angles.length || r.topics.length) {
      working += `\n\nJOEL'S OWN RESULTS (his average: ${r.overall} reactions+comments per 1k followers):${r.angles.length ? `\n- Angles: ${line(r.angles, (k) => `angle ${k}`)}` : ''}${r.topics.length ? `\n- Topics: ${line(r.topics, (k) => k)}` : ''}\nWhen a passage fits more than one angle or topic, prefer the one that has done better for HIM. His own results count for more than the market's.`;
    }
  } catch { /* no own results yet */ }
  // Only when a topic is actually named above. On 2 Oct 2026 this line went out with no topics in the prompt, and the
  // model spent all 2,000 tokens hunting for them out loud, so all 5 attempts were cut off before the JSON.
  if (/\[[a-z ]+\] |- Topics: /.test(working)) working += `\n\nTOPICS: if one of Joel's passages below genuinely speaks to a topic named above, prefer that passage. Never stretch a passage to fit a topic, and never add a claim he didn't make.`;
  if (working) working += `\n\nUse all of the above quietly: decide in your head, then reply with the JSON only. No working shown.`;
  return `THIS POST'S JOB: ${JOBS[job].brief}${research}${working}\n\nTHE OUTLIER POST TO COPY (${outlier.words} words, ${outlier.paragraphs} paragraphs, ${outlier.per1k} reactions+comments per 1k followers). Copy its build, never its content:\n<<<\n${outlier.body}\n>>>\n\nANGLES (what it's about; pick the one the passage truly supports):\n${a}\n\nJOEL'S OWN WORDS (pick ONE passage):\n${p}\n\nREADER PHRASES:\n${READER_PHRASES.map((r) => '- ' + r).join('\n')}${feedback ? `\n\nYOUR LAST DRAFT (angle ${last.angle}, passage ${last.passage}) WAS REJECTED. Keep what works and fix only these:\n- ${feedback.join('\n- ')}\n\nLAST DRAFT:\n${last.post}` : ''}`;
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

const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9£$€% ]+/g, ' ').replace(/\s+/g, ' ').trim();
const hash = (s) => createHash('sha256').update(s).digest('hex').slice(0, 16);

// How much of a post is Joel's own words (0 to 1). Filler is removed from both sides so tidying it doesn't count against him.
// Joel, 5 Oct 2026: "as high as possible without breaking". 50% blocked every draft (best tries 25-31%), so: below
// 15% never reaches him (hard; 4 test runs on 5 Oct: best tries 31, 25, 18 and 30%, worst run 18%); below 35% keeps the repairs pushing for more of his words; of all tries he gets the
// one with the most of his words.
const MIN_OWN = 0.15;
const TARGET_OWN = 0.35;

// Joel's copying rule (SCRIPTING.md 1b): outside the hook (the first paragraph), at most 15% of their wording and never
// 12 of their words in a row. Words count as copied inside any 6-word run that also appears in the outlier.
function copiedFromOutlier(post, body) {
  const rest = post.split(/\n\s*\n/).slice(1).join(' ');
  const b = norm(rest).split(' ').filter(Boolean), s = ` ${norm(body)} `;
  if (b.length < 6) return null;
  const cov = new Array(b.length).fill(false);
  for (let i = 0; i + 6 <= b.length; i++) if (s.includes(` ${b.slice(i, i + 6).join(' ')} `)) for (let k = i; k < i + 6; k++) cov[k] = true;
  let longest = 0, cur = 0;
  for (const c of cov) { cur = c ? cur + 1 : 0; longest = Math.max(longest, cur); }
  const share = cov.filter(Boolean).length / b.length;
  if (longest > 12) return `a ${longest}-word stretch`;
  if (share > 0.15) return `${Math.round(share * 100)}% of the words`;
  return null;
}

function check(d, passages, names, recentAngles, outlier) {
  const problems = [];
  const angle = ANGLES[d.angle];
  const passage = passages[d.passage];
  if (!angle) return [`Angle ${d.angle} is not on the list.`];
  if (!passage) return [`Passage ${d.passage} does not exist.`];
  if (recentAngles.includes(Number(d.angle))) problems.push(`Angle ${d.angle} was used in the last 3 posts. Pick another.`);
  const post = String(d.post || '').trim();
  const words = post.split(/\s+/).length;
  // The outlier sets the length now (6 Oct 2026): within about a third of it either way.
  const lo = Math.max(60, Math.round(outlier.words * 0.65)), hi = Math.round(outlier.words * 1.35);
  if (words < lo || words > hi) problems.push(`Post is ${words} words; the outlier is ${outlier.words}, so keep it ${lo} to ${hi}.`);
  if (/\b(?:isn['’]t|wasn['’]t|not) (?:about |just |really |a |an )?[^.!?\n]{1,40}[.!?]\s+(?:It['’]s|It is|It was|That['’]s|You['’]re|You are|I['’]m|I am)\b/i.test(post)) problems.push('Uses the "That\'s not X. It\'s Y." pattern, which reads as AI. Say the point once, plainly.');
  // Joel, 2026-09-27: no neat three-part lines ("Not a plan. Not a pivot. Just honesty.").
  const triplet = post.split(/\n\s*\n/).find((para) => { const s = para.trim().split(/(?<=[.!?])\s+/); return s.length === 3 && s.every((x) => x.split(/\s+/).length <= 4); });
  if (triplet) problems.push(`Neat three-part line ("${triplet.trim()}"), which reads as AI. Say it once, in one plain sentence.`);
  if (/\b(drugs?|cocaine|weed)\b/i.test(post)) problems.push('Mentions drugs. Never, including Joel\'s own past (Joel, 2026-09-27).');
  if (/[—–]/.test(post)) problems.push('Contains an em or en dash.');
  if (/https?:\/\/|www\.|\.com\b|\.shop\b/i.test(post)) problems.push('Contains a link. LinkedIn native posts carry no link.');
  if (/#\w/.test(post)) problems.push('Contains a hashtag.');
  if (/\b(link in (?:my )?bio|book (?:a|your)|free (?:20[- ]minute )?call|DM me|message me|get in touch|sign up|comment below)\b/i.test(post)) problems.push('Contains an ask. LinkedIn native posts have no ask, at most one soft question.');
  const pl = post.split(/\n\s*\n/).map((p) => p.split(/\s+/).length);
  if (pl.some((l) => l > 85) || pl.filter((l) => l > 40).length > 2) problems.push('Paragraphs too long: mostly one sentence each, at most two longer ones, none over 80 words.');
  if (/£\s?(1,?000|500|334)\b|\b(?:5|five) (?:people|clients|places)\b|\b(?:spots?|places?)\b[^.\n]{0,20}\b(?:left|open|remaining)\b/i.test(post)) problems.push('Mentions the price or places. Never in a LinkedIn post.');
  if (/\b(here'?s the thing|the truth is|delve|unpack|tapestry|journey|unlock|game[- ]changer|level up|dopamine)\b/i.test(post)) problems.push('Uses an AI tell or an unsourced brain claim.');
  if (/\b(studies show|study shows|research shows|research says|according to|a recent study|scientists?)\b/i.test(post) && !/\b(study|research)\b/i.test(passage.text)) problems.push('Makes a research claim that is not in the passage.');
  if (/\b(most people|most of my clients|every client|everyone I work with|(?:the )?people I work with (?:now )?are|I see (?:this|it) all the time|I hear (?:this|it) (?:all the time|a lot))\b/i.test(post)) problems.push('Makes an unverifiable claim about "most people" or his clients.');
  if (/\b(you should invest|buy shares|investment advice|put your money in|pay less tax|avoid tax)\b/i.test(post)) problems.push('Reads like regulated advice.');
  const src = norm(passage.text + ' ' + JOEL_FACTS).replace(/[\s,]/g, '');
  for (const f of post.match(/(?:£|\$|€)\s?\d[\d,.]*k?|\d[\d,.]*\s?(?:%|per ?cent)/gi) || []) {
    if (!src.includes(norm(f).replace(/[\s,]/g, ''))) problems.push(`Figure "${f.trim()}" is not in Joel's words or facts.`);
  }
  for (const n of names) if (new RegExp(`\\b${n.replace(/[^A-Za-z'-]/g, '')}\\b`, 'i').test(post)) problems.push(`Contains the name "${n}" from a private call.`);
  // Capitalised names in the passage (partners, exes, friends, firms) must not reach the post. Same rule as the emails.
  const ALLOW = /^(Joel|Money|Story|Method|Way|Wealth|MSc|Behavioural|Economics|Qualified|Financial|Planner|The|And|But|So|When|Then|Now|Yeah|Right|Okay|Jesus|God|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|January|February|March|April|May|June|July|August|September|October|November|December|Uber|Instagram|LinkedIn|Christmas)$/;
  const midSentence = (s) => new Set((s.match(/(?<=[a-z,] )[A-Z][a-z]{2,}\b/g) || []).filter((w) => !ALLOW.test(w)));
  const inCall = midSentence(passage.text);
  for (const w of midSentence(post)) if (inCall.has(w)) problems.push(`Uses the name or place "${w}" from a private call.`);
  const practice = /\b(healer|yoga|breathwork|reiki|practitioner|therapist|retreat)s?\b/i;
  if ((post.match(/\b(clients?|someone I work with|people I work with)\b[\s\S]{0,120}/gi) || []).some((s) => practice.test(s)) && !practice.test(passage.text)) {
    problems.push('Implies a client of Joel\'s is a practitioner. His words don\'t say so.');
  }
  const used = RESEARCH.filter((r) => r.key.test(post)).length;
  if (used > 1) problems.push(`Uses ${used} research ideas. One at most.`);
  const copied = copiedFromOutlier(post, outlier.body);
  if (copied) problems.push(`Copies too much of the outlier's wording (${copied}). Keep its hook and its build; every other line is Joel's.`);
  if (/\b(?:exactly|precisely|proven to be) twice\b/i.test(post)) problems.push('Says "exactly twice". TEACHING_SCOPE.md §2.2: "about twice" is fine, "exactly twice" is not.');
  // Joel, 5 Oct 2026: "didn't actually use my fathom recordings… sounded too ai". The old check passed a post with
  // ONE 5-word phrase of his. Now: share of the post's words that sit in a 3-word run found in his passage, with
  // spoken filler taken out of both sides first. Too little = never reaches Joel (hard fail).
  const ownShare = joelShare(post, passage.text);
  d.ownShare = ownShare;
  if (ownShare < MIN_OWN) problems.push(`Too little of Joel's own words: ${Math.round(ownShare * 100)}% of the post is from his passage (needs ${Math.round(MIN_OWN * 100)}%). Use his sentences, tidy only the filler.`);
  else if (ownShare < TARGET_OWN) problems.push(`Could use more of Joel's own words: ${Math.round(ownShare * 100)}% of the post is from his passage (aim for ${Math.round(TARGET_OWN * 100)}%). Swap your own lines for his sentences, tidied only of filler.`);
  return problems;
}

// Separate pass: a fresh call that only compares claims with the source. Draft first, audit second.
async function audit(post, passage, isStory) {
  const system = `You are a strict fact checker. You get Joel's own words (a call transcript passage), Joel's fixed facts, and a LinkedIn post written from them. List every statement in the post about something that happened, a person, a number, a feeling Joel had, or what someone did, that is NOT supported by the passage or the facts. The FACTS are true and count as support. Where the passage and the FACTS differ on Joel's own credentials or story numbers, the FACTS win (a loose word on a call is not a problem). General reflections and questions to the reader are fine. Also flag if the post turns Joel's own story into a client's, or a client's into Joel's, or describes or hints at who anyone else in the passage is. ${isStory ? 'This is a story post: also flag if the opening is background rather than the problem, or if there is no payoff.' : 'This is NOT a story post (an explainer or myth post): never flag it for a missing payoff or a background opening.'} A named research idea that matches one of these is fine: ${RESEARCH.map((r) => r.line.split(':')[0]).join('; ')}. A payoff is what shifted for Joel (a realisation, a step, or honestly not knowing yet); it is NEVER an offer, a call or a link, and the post must have no ask. Leaving out a detail, or leaving someone unnamed, is never a problem. The post copies the BUILD of a real LinkedIn post (its hook pattern, its paragraph shape, its list or its questions): that framing is fine and needs no support, as long as every statement of fact, story or feeling comes from Joel. Also flag (issue starting "Not Joel's voice:", quote the exact words) any line that reads like a generic coach or AI rather than Joel talking, judged against how he speaks in the passage. The test (Joel's own, EMAIL_COPY.md): "Does this sound like Joel talking, or like a coach trying to sound like Joel?" Output only JSON: {"items": [{"issue": "short description", "real_problem": true or false}]}`;
  const r = await claude(system, `FACTS:\n${JOEL_FACTS}\n\nPASSAGE:\n${passage.text}\n\nPOST:\n${post}`, 1600);
  return (r.items || []).filter((i) => i.real_problem === true).map((i) => `Not in Joel's words: ${i.issue}`);
}

async function main() {
  if (!FATHOM_API_KEY || !ANTHROPIC_API_KEY) throw new Error('FATHOM_API_KEY / ANTHROPIC_API_KEY not set');
  if (!DRY && (!FRED_SECRET || !TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID)) throw new Error('FRED_SECRET / TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set');
  const state = existsSync(STATE) ? JSON.parse(await readFile(STATE, 'utf8')) : [];
  const { passages: calls, names } = await recentJoelWords({ key: FATHOM_API_KEY, days: 60, maxPassages: 500 });
  // Plus his 2.5-hour solo talk to camera (5 Oct 2026): 72 passages of him explaining money in his own words.
  let talk = [];
  try { talk = talkPassages(); } catch (e) { console.log(`Talk passages unavailable (${e.message}).`); }
  const all = calls.concat(talk);
  const fresh21 = (p) => !state.some((s) => s.passage === hash(p.text) && Date.now() - Date.parse(s.date) < 21 * 864e5);

  // REVISE_ID: Joel wrote what to fix on the approve page. Rewrite the SAME story and angle with his fixes first.
  const REVISE_ID = process.env.REVISE_ID;
  let orig = null;
  if (REVISE_ID) {
    if (!/^[0-9a-f]{16}$/.test(REVISE_ID)) throw new Error('bad REVISE_ID');
    // Netlify Blobs reads can lag a fresh save by up to ~60s, and this run starts seconds after Joel presses
    // "Rewrite it". So wait for his fixes to show up (every 10s, up to 2 min) before giving up.
    // 30 Sep 2026: the first rewrite failed because it read the draft 20s after the save and got the old copy.
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
  const passages = orig
    ? all.filter((p) => hash(p.text) === orig.passage)
    // A story can be reused once 3 weeks have passed since it was last used (Joel, 27 Sep). Filter BEFORE taking
    // the best 12, so used stories never crowd out unused ones (audit: the old top-30 cut would run dry by mid-Nov).
    // 7 call stories + 7 talk passages (rotating by day), so every post has plenty of his own sentences to build from.
    : (() => { const t = talk.filter(fresh21), k = t.length ? (Math.floor(Date.now() / 864e5) * 7) % t.length : 0; return calls.filter(fresh21).slice(0, 7).concat(t.slice(k, k + 7), t.slice(0, Math.max(0, k + 7 - t.length))); })();
  if (!passages.length) throw new Error(orig ? 'The story this draft came from is no longer in the last 60 days of calls.' : 'No unused story passages in the last 60 days of Fathom calls. Nothing written.');
  // Which job today: Mon reach, Wed positioning, Fri reach, Sun nurture/convert in turn. JOB=... overrides; other days reach.
  const lastSunday = [...state].reverse().find((s) => s.job === 'nurture' || s.job === 'convert');
  const byDay = { 1: 'reach', 3: 'positioning', 5: 'reach', 0: lastSunday?.job === 'nurture' ? 'convert' : 'nurture' };
  const job = orig ? jobOf(orig.angle) : (JOBS[process.env.JOB] ? process.env.JOB : byDay[new Date().getUTCDay()] || 'reach');
  const recentAngles = orig ? [] : state.slice(-3).map((s) => s.angle);
  const fresh = JOBS[job].angles.filter((n) => !recentAngles.includes(n));
  const pool = orig ? [Number(orig.angle)] : (fresh.length ? fresh : JOBS[job].angles);
  const angles = Object.fromEntries(pool.map((n) => [n, ANGLES[n]]));
  console.log(`Job: ${job}.`);
  // The post to copy (6 Oct 2026): the bank of real LinkedIn posts that did well with self-employed and small-business
  // readers (main project research/2026-10-06-linkedin-self-employed), encrypted because they are other people's posts.
  // Story posts for nurture and convert, idea posts for reach and positioning; the best one not used in 60 days.
  // A rewrite keeps the outlier its draft was built on.
  const bank = openBox('linkedin-outliers.enc');
  const usedRecently = (o) => state.some((s) => s.outlier === o.id && Date.now() - Date.parse(s.date) < 60 * 864e5);
  const wantStory = ['nurture', 'convert'].includes(job);
  const origOutlier = orig && state.find((s) => s.passage === orig.passage && s.outlier)?.outlier;
  const byScore = (a, b) => b.per1k - a.per1k;
  const outlier = (origOutlier && bank.find((o) => o.id === origOutlier))
    || bank.filter((o) => !usedRecently(o) && o.story === wantStory).sort(byScore)[0]
    || bank.filter((o) => !usedRecently(o)).sort(byScore)[0]
    || [...bank].sort(byScore)[0];
  console.log(`Copying outlier ${outlier.id} (${outlier.per1k} per 1k, ${outlier.words} words, ${outlier.story ? 'story' : 'idea'}).`);
  const joelFix = orig ? [`JOEL'S OWN FIXES (do these first, exactly as he asks; the hard rules still apply): ${orig.feedback}`] : [];

  // Hard safety fails never reach Joel. If no attempt passes everything, the closest draft with only style or
  // fact-check flags is sent with those flags on top: he approves every post anyway (first 2 weeks).
  const HARD = /^(Mentions drugs|Contains a link|Contains an ask|Mentions the price|Makes a research claim|Reads like regulated|Figure "|Contains the name|Uses the name or place|Implies a client|Angle .* is not|Passage \d+ does not|Story post is missing|Too little of Joel's own words|Copies too much of the outlier)/;
  let feedback = orig ? joelFix : null, draft = null, best = null, flags = [];
  let last = orig ? { angle: orig.angle, passage: 0, post: orig.text, problem: orig.text, pursuit: '', payoff: '' } : null;
  for (let attempt = 1; attempt <= 5; attempt++) {
    let d;
    try { d = await claude(SYSTEM, userPrompt(passages, angles, feedback, last, job, outlier), 4500); } catch (e) { console.log(`Attempt ${attempt}: bad reply (${e.message.slice(0, 80)}). Retrying.`); continue; }
    // One post now (the outlier sets the shape); stored in problem so the draft page and rewrites work as before.
    d.post = String(d.post || [d.problem, d.pursuit, d.payoff].filter(Boolean).join('\n\n')).replace(/\s*[—–]\s*/g, ', ').trim();
    d.problem = d.post; d.pursuit = ''; d.payoff = '';
    let problems = pool.includes(Number(d.angle))
      ? check(d, passages, names, fresh.length ? recentAngles : [], outlier)
      : [`Angle ${d.angle} is not on the list for today's ${job} post. Use one of: ${pool.join(', ')}.`];
    const hard = problems.some((p) => HARD.test(p));
    if (!hard) { try { problems = problems.concat(await audit(d.post, passages[d.passage], outlier.story)); } catch (e) { problems.push('The fact check could not read its own reply. Try again.'); } }
    if (!problems.length) { draft = d; break; }
    // A draft the fact check never finished on is unchecked, so it counts as unbacked too (6 Oct 2026: one slipped through).
    const unbacked = problems.some((p) => /^(Not in Joel's words|The fact check could not read)/.test(p));
    if (!hard && !unbacked && (!best || d.ownShare > best.d.ownShare || (d.ownShare === best.d.ownShare && problems.length < best.problems.length))) best = { d, problems };
    console.log(`Attempt ${attempt} rejected: ${problems.length} problem(s). Joel's own words: ${Math.round((d.ownShare || 0) * 100)}%.`);
    // Kinds of problem only, cut before any quote or detail: the logs are public.
    console.log('  kinds: ' + problems.map((p) => p.split(/[:("“]/)[0].trim().slice(0, 50)).join(' | '));
    if (DRY) console.log('  - ' + problems.join('\n  - ') + `\n  [angle ${d.angle}, passage ${d.passage}]\n${d.post}\n`);
    feedback = joelFix.concat(problems);
    last = d;
  }
  if (!draft && best) { draft = best.d; flags = best.problems; console.log(`No attempt passed everything. Sending the draft with the most of his words (${Math.round(draft.ownShare * 100)}%), ${flags.length} flag(s), for Joel to judge.`); }
  if (!draft) {
    // Joel, 6 Oct 2026: a draft with lines that aren't backed by his words never reaches him. Say so instead.
    console.log('No draft was safe to send: every try failed a hard check or had lines not backed by Joel\'s words.');
    if (!DRY) await telegram(`💼 LinkedIn draft skipped today (${job}). Five tries, and every one either broke a hard rule or had lines that weren't backed by your own words, so nothing was sent. The next one runs as normal.`);
    return;
  }

  const words = draft.post.split(/\s+/).length;
  console.log(`Draft ready: angle ${draft.angle} (${ANGLES[draft.angle].name}), ${words} words.`);
  if (DRY) {
    if (flags.length) console.log('FLAGS:\n  - ' + flags.join('\n  - '));
    console.log(`\n----- PASSAGE USED (${passages[draft.passage].date}) -----\n${passages[draft.passage].text}\n\n----- LINKEDIN POST -----\n` + draft.post + `\n-------------------------`);
    return;
  }
  // Store the draft privately on Netlify, then Fred sends it to Joel with the Approve button. Never logged.
  const r = await fetch(`${SITE}/api/linkedin/draft?action=create`, {
    method: 'POST', headers: { 'content-type': 'application/json', 'x-fred-secret': FRED_SECRET },
    body: JSON.stringify({ text: draft.post, angle: Number(draft.angle), passage: hash(passages[draft.passage].text), problem: draft.problem, pursuit: draft.pursuit, payoff: draft.payoff }),
  });
  if (!r.ok) throw new Error(`Draft store ${r.status}: ${(await r.text()).slice(0, 120)}`);
  const { id, sig } = await r.json();
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const shown = esc(draft.post);
  await telegram((orig ? '✏️ <b>Rewritten with your fixes</b>\n' : '') + `💼 <b>LinkedIn draft</b> · ${job} · angle ${draft.angle}: ${esc(ANGLES[draft.angle].name)} · ${words} words · copies a ${outlier.per1k}-per-1k post by ${esc(outlier.author)} · ${Math.round(draft.ownShare * 100)}% your own words\n<i>The labels are for you; they aren't posted.</i>\n\n` + (flags.length ? `⚠️ <b>Didn't pass every check. Read these first:</b>\n• ${flags.map(esc).join('\n• ')}\n\n` : '') + shown);
  await telegram('Tap below. On that page you can "Approve and post", or write what needs fixing and it gets rewritten. Ignore it and nothing is posted (expires in 48 hours).', {
    inline_keyboard: [[{ text: '✅ Review & approve', url: `${SITE}/api/linkedin/draft?id=${id}&sig=${sig}` }]],
  });
  console.log('Draft stored and sent to Joel on Telegram.');
  if (orig) return; // Same story as before; it's already recorded as used.
  state.push({ date: new Date().toISOString().slice(0, 10), job, angle: Number(draft.angle), passage: hash(passages[draft.passage].text), outlier: outlier.id });
  await mkdir(dirname(STATE), { recursive: true });
  await writeFile(STATE, JSON.stringify(state, null, 2) + '\n');
}

main().catch(async (e) => {
  console.error('FATAL:', e.message);
  // Tell Joel the actual reason, not just "failed". Our own messages carry no private words.
  if (!DRY && TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) { try { await telegram(`❌ <b>No LinkedIn draft this time</b>
${e.message.replace(/&/g, '&amp;').replace(/</g, '&lt;')}`); } catch {} }
  process.exit(1);
});
