#!/usr/bin/env node
// Writes ONE native LinkedIn post (no link, no ask) from Joel's own words. Mon/Wed/Fri/Sun (Joel, 2026-09-27).
//   1. Joel's story passages come from his recent Fathom calls (scripts/daily-email/fathom.mjs), in memory only.
//   2. The model picks 1 to 3 passages and a topic angle, and copies the build of one real outlier post.
//   3. Five simple rules (check() below; Joel, 7 Oct 2026: "KEEP RULES SIMPLE"), then a SEPARATE fact check that
//      compares every claim with Joel's words. Fails are fed back; after 5 fails nothing is posted and Fred says why.
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

// Angles are topic labels only (what the post is about). The outlier post decides the shape (6 Oct 2026).
// Numbers are kept because scripts/state and linkedin-own.json score by them.
const ANGLES = {
  1: { name: 'The month after the big payment' },
  2: { name: 'Full diary, empty account' },
  3: { name: 'The money moment with no tidy lesson' },
  4: { name: 'Why a 60-minute session isn\'t 60 minutes of work' },
  5: { name: '"I can\'t pay myself, my income isn\'t consistent"' },
  6: { name: 'Mindset and behaviour' },
  8: { name: 'Why a money person works with small business owners (Joel\'s origin)' },
  9: { name: 'How a money coach looks after his own money' },
  10: { name: 'Emergency fund vs runway for income that swings' },
  11: { name: 'Proud of a client\'s small behaviour win' },
  12: { name: '"Pay me when you can"' },
};

// THE MIX (IDEATION.md: 3 reach / 2 positioning / 1 nurture / 1 convert), fitted to 4 LinkedIn days (Joel, 2026-09-27):
// Mon reach · Wed positioning · Fri reach · Sun nurture and convert in turn. Each job has its own angles.
const JOBS = {
  reach: { angles: [5, 2, 4, 12], brief: 'REACH (attract): mindset through psychology: money stress, avoiding the numbers, always feeling behind, not paying yourself, working hard with nothing left. Told through their situation (a small business owner who earns decent money: clients, invoices, a slow month, the tax bill) and Joel\'s words. A research line only if it truly fits; most posts need none.' },
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

const SYSTEM = `You write ONE LinkedIn post for Joel Ezekiel (Way of Wealth), in his voice, built only from his own words.

WHO JOEL IS: ${JOEL_FACTS}
He is a planner, not an adviser: never recommend investments, products, pensions, debt choices or tax moves.

WHO READS IT: small business owners with a service business (coaches, therapists, consultants, freelancers, creatives, trades). Global, UK first in tone. They earn decent money, but their money feels chaotic. Their pains, most common first: money stress, income that swings, not paying themselves, not knowing where the money goes, the tax bill shock, working hard with nothing left, burnout, and home bills tangled up with the business. What they want: calm first, then a steady wage, then a buffer, then tax sorted. Their own words: "pay myself", "struggle", "confused", "take home", "where my money is going", "always behind". If they take mindset or manifesting seriously, so does Joel, and he adds the behaviour side. Never mock it, never claim it works.

THE SHAPE COMES FROM ONE REAL POST (Joel, 6 Oct 2026: the reel built by copying a real outlier, "yes love this script"; the LinkedIn post built from written "shapes", "terrible"). You get ONE OUTLIER POST: a real LinkedIn post that did well with self-employed and small-business readers. Copy it the way SCRIPTING.md copies a reel:
- KEEP ITS HOOK: its first line(s), changed only enough to fit Joel's topic (swap the topic words, keep the build).
- FOLLOW ITS STRUCTURE BEAT FOR BEAT: the same number of paragraphs and roughly the same number of sentences, each about the same length. If its list stacks, yours stacks. If it ends on a question, yours ends on a question. If it tells a story, yours tells Joel's story in the same beats.
- EVERY OTHER LINE IS JOEL'S: where their line does a job (a confession, a scene, a list item, the turn, the lesson), Joel's line does the same job, taken from his_lines.
- Never more than 15% of their wording outside the hook, never 12 of their words in a row, and never their facts, story, numbers, names or claims.
- No link. No hashtags. No ask, or at most one soft question at the very end. Never their call to action.

THE RULES (Joel, 7 Oct 2026: "it needs to sound like me more than anything else ... KEEP RULES SIMPLE"). Five, and that's all:
1. SOUND LIKE JOEL. Most of the post is his own sentences from the passages you pick, tidied only of filler ("um", "so basically", repeats, false starts). Your own words only to join or trim his. The test (EMAIL_COPY.md): "Does this sound like Joel talking, or like a coach trying to sound like Joel?"
2. NOTHING MADE UP. No fact, number, person, story or quote he didn't say. Numbers only from the passages or JOEL'S FACTS. "I/me/my" is Joel's own story; never turn his story into a client's or a client's into his. A research name only from RESEARCH IDEAS, worded as given, and only if it truly fits (most posts need none). Never "studies show".
3. NOTHING PRIVATE. Never name or describe anyone else in the passages (say "someone I work with").
4. NEVER: a link, an ask, his price or places, financial advice, or drugs.
5. SHORT: about 200 words, never more than 250.

THEIR WORDS: the READER PHRASES are real things strangers in this market have written. You may turn one into a "you" line. Never quote them, never credit them.

HOW TO BUILD IT (three steps, in this order):
1. "his_lines": copy out 12 to 25 of Joel's own sentences from up to 3 passages (one is fine), word for word, with only the filler taken out. Do not reword them. Pick the ones that carry the story and the point.
2. "map": for each paragraph of the OUTLIER, one short line: what job it does, and which of his_lines fills it.
3. "post": write it, paragraph for paragraph. At least half the words are his lines as copied.
${BRAND_VOICE_BLOCK}

OUTPUT: only valid JSON, no fences:
{"passages": [<numbers of the passages you used, 1 to 3>], "angle": <angle number>, "his_lines": ["...", "..."], "map": ["...", "..."], "post": "paragraphs separated by \\n\\n"}`;

function userPrompt(passages, angles, feedback, last, job, outlier) {
  // Angles are now only WHAT the post is about; the outlier decides how it is built (6 Oct 2026).
  const a = Object.entries(angles).map(([n, x]) => `${n}. ${x.name}`).join('\n');
  const p = passages.map((x, i) => `[${i}] (${x.date})\n${x.text}`).join('\n\n');
  const research = ['reach', 'positioning'].includes(job) ? `\n\nRESEARCH IDEAS (optional: at most ONE, as worded here, only if it truly fits):\n${RESEARCH.map((r) => '- ' + r.line).join('\n')}` : '';
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
  return `THIS POST'S JOB: ${JOBS[job].brief}${research}${working}\n\nLENGTH: about ${WIN_WORDS} words, never more than ${MAX_WORDS}. Keep every beat of the outlier, just say each one in fewer words.\n\nTHE OUTLIER POST TO COPY (${outlier.words} words, ${outlier.paragraphs} paragraphs, ${outlier.per1k} reactions+comments per 1k followers). Copy its build, never its content:\n<<<\n${outlier.body}\n>>>\n\nANGLES (what it's about; pick the one the passage truly supports):\n${a}\n\nJOEL'S OWN WORDS (pick 1 to 3 passages):\n${p}\n\nREADER PHRASES:\n${READER_PHRASES.map((r) => '- ' + r).join('\n')}${feedback ? `\n\nYOUR LAST DRAFT (angle ${last.angle}, passages ${last.passages ?? last.passage}) WAS REJECTED. Keep what works and fix only these:\n- ${feedback.join('\n- ')}\n\nLAST DRAFT:\n${last.post}` : ''}`;
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

// THE FIVE RULES (Joel, 7 Oct 2026: "it needs to sound like me more than anything else ... KEEP RULES SIMPLE!!!").
// The old ~25 style checks (paragraph sizes, three-part lines, phrase bans, angle rotation, research counts and the rest)
// binned nearly every draft and are gone. What's left:
//   1. Sound like Joel: at least 35% of the post's words come from his own passages (counted, not guessed).
//   2. Nothing made up: figures, research claims, and the separate fact check below.
//   3. Nothing private: no names or places from his calls.
//   4. Never: link, ask, price or places, regulated advice, drugs.
//   5. Short: about 205 words (median of the 3x outliers in the 1,000-post pull), never over 250.
// Plus Joel's copying rule (SCRIPTING.md 1b), so another creator's words never go out under his name.
const MIN_OWN = 0.35;
const WIN_WORDS = 205;
const MAX_WORDS = 250;

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

// The model may build from 1 to 3 passages (7 Oct 2026: it kept answering "7,8,9", which the old code read as a
// passage that "does not exist", binning 3 of 5 tries). Accepts a number, "7,8,9" or [7,8,9].
function pickedPassages(d, passages) {
  const ids = [...new Set(String(d.passages ?? d.passage ?? '').match(/\d+/g) || [])].map(Number).filter((i) => passages[i]).slice(0, 3);
  return ids.length ? { ids, text: ids.map((i) => passages[i].text).join('\n\n'), hashes: ids.map((i) => hash(passages[i].text)).join(','), date: passages[ids[0]].date } : null;
}

function check(d, passages, names, outlier) {
  const problems = [];
  const source = pickedPassages(d, passages);
  if (!source) return ['No passage picked. Give the numbers of the passages you used.'];
  d.source = source;
  const post = String(d.post || '').trim();
  // 1. Sound like Joel.
  const ownShare = joelShare(post, source.text);
  d.ownShare = ownShare;
  if (ownShare < MIN_OWN) problems.push(`Too little of Joel's own words: ${Math.round(ownShare * 100)}% of the post is from his passages (needs ${Math.round(MIN_OWN * 100)}%). Use his sentences, tidy only the filler.`);
  // 2. Nothing made up.
  const src = norm(source.text + ' ' + JOEL_FACTS).replace(/[\s,]/g, '');
  for (const f of post.match(/(?:£|\$|€)\s?\d[\d,.]*k?|\d[\d,.]*\s?(?:%|per ?cent)/gi) || []) {
    if (!src.includes(norm(f).replace(/[\s,]/g, ''))) problems.push(`Figure "${f.trim()}" is not in Joel's words or facts.`);
  }
  if (/\b(studies show|study shows|research shows|research says|according to|a recent study|scientists?)\b/i.test(post) && !/\b(study|research)\b/i.test(source.text)) problems.push('Makes a research claim that is not in the passage.');
  // 3. Nothing private. Capitalised names in the passages (partners, exes, friends, firms) must not reach the post.
  for (const n of names) if (new RegExp(`\\b${n.replace(/[^A-Za-z'-]/g, '')}\\b`, 'i').test(post)) problems.push(`Contains the name "${n}" from a private call.`);
  const ALLOW = /^(Joel|Money|Story|Method|Way|Wealth|MSc|Behavioural|Economics|Qualified|Financial|Planner|The|And|But|So|When|Then|Now|Yeah|Right|Okay|Jesus|God|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|January|February|March|April|May|June|July|August|September|October|November|December|Uber|Instagram|LinkedIn|Christmas)$/;
  const midSentence = (s) => new Set((s.match(/(?<=[a-z,] )[A-Z][a-z]{2,}\b/g) || []).filter((w) => !ALLOW.test(w)));
  const inCall = midSentence(source.text);
  for (const w of midSentence(post)) if (inCall.has(w)) problems.push(`Uses the name or place "${w}" from a private call.`);
  // 4. Never.
  if (/https?:\/\/|www\.|\.com\b|\.shop\b/i.test(post)) problems.push('Contains a link. LinkedIn native posts carry no link.');
  if (/\b(link in (?:my )?bio|book (?:a|your)|free (?:20[- ]minute )?call|DM me|message me|get in touch|sign up|comment below)\b/i.test(post)) problems.push('Contains an ask. LinkedIn native posts have no ask, at most one soft question.');
  if (/£\s?(1,?000|500|334)\b|\b(?:5|five) (?:people|clients|places)\b|\b(?:spots?|places?)\b[^.\n]{0,20}\b(?:left|open|remaining)\b/i.test(post)) problems.push('Mentions the price or places. Never in a LinkedIn post.');
  if (/\b(you should invest|buy shares|investment advice|put your money in|pay less tax|avoid tax)\b/i.test(post)) problems.push('Reads like regulated advice.');
  if (/\b(drugs?|cocaine|weed)\b/i.test(post)) problems.push('Mentions drugs. Never, including Joel\'s own past (Joel, 2026-09-27).');
  // 5. Short.
  const words = post.split(/\s+/).length;
  if (words > MAX_WORDS) problems.push(`Post is ${words} words; keep it under ${MAX_WORDS}, about ${WIN_WORDS}. Cut your own joining words first, never Joel's lines.`);
  const copied = copiedFromOutlier(post, outlier.body);
  if (copied) problems.push(`Copies too much of the outlier's wording (${copied}). Keep its hook and its build; every other line is Joel's.`);
  return problems;
}

// Separate pass: a fresh call that only compares claims with the source. Draft first, audit second.
// Made-up facts block the draft ("Not in Joel's words"). Its opinion on voice never blocks: it goes to Joel as a
// "Voice note" on the draft, and he decides (7 Oct 2026). The count of his own words above is the voice check.
async function audit(post, sourceText) {
  const system = `You are a strict fact checker. You get Joel's own words (call transcript passages), Joel's fixed facts, and a LinkedIn post written from them. List every statement in the post about something that happened, a person, a number, a feeling Joel had, or what someone did, that is NOT supported by the passages or the facts. The FACTS are true and count as support. Where the passages and the FACTS differ on Joel's own credentials or story numbers, the FACTS win (a loose word on a call is not a problem). General reflections and questions to the reader are fine. Also flag if the post turns Joel's own story into a client's, or a client's into Joel's, or describes or hints at who anyone else in the passages is. A named research idea that matches one of these is fine: ${RESEARCH.map((r) => r.line.split(':')[0]).join('; ')}. Leaving out a detail, or leaving someone unnamed, is never a problem. The post copies the BUILD of a real LinkedIn post (its hook pattern, its paragraph shape, its list or its questions): that framing is fine and needs no support, as long as every statement of fact, story or feeling comes from Joel. Separately, list (issue starting "Not Joel's voice:", quote the exact words) any line that reads like a generic coach or AI rather than Joel talking. Keep every issue short. Output only JSON: {"items": [{"issue": "short description", "real_problem": true or false}]}`;
  const user = `FACTS:\n${JOEL_FACTS}\n\nPASSAGES:\n${sourceText}\n\nPOST:\n${post}`;
  // One retry: on 6 and 7 Oct the checker's reply sometimes couldn't be read, which binned otherwise good drafts.
  let r;
  try { r = await claude(system, user, 3000); } catch { r = await claude(system, user, 3000); }
  return (r.items || []).filter((i) => i.real_problem === true).map((i) => (/^Not Joel's voice/i.test(i.issue) ? `Voice note: ${i.issue.replace(/^Not Joel's voice:\s*/i, '')}` : `Not in Joel's words: ${i.issue}`));
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
  // state.passage holds one hash, or several joined by commas when a post used up to 3 passages (7 Oct 2026).
  const usedHash = (s, h) => String(s.passage || '').split(',').includes(h);
  const fresh21 = (p) => !state.some((s) => usedHash(s, hash(p.text)) && Date.now() - Date.parse(s.date) < 21 * 864e5);

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
    ? all.filter((p) => String(orig.passage).split(',').includes(hash(p.text)))
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

  // Hard fails never reach Joel. If no attempt passes everything, the draft with the most of his words that has only
  // length or voice notes is sent with those notes on top: he approves every post anyway.
  const HARD = /^(Mentions drugs|Contains a link|Contains an ask|Mentions the price|Makes a research claim|Reads like regulated|Figure "|Contains the name|Uses the name or place|No passage picked|Too little of Joel's own words|Copies too much of the outlier)/;
  let feedback = orig ? joelFix : null, draft = null, best = null, flags = [];
  let last = orig ? { angle: orig.angle, passage: 0, post: orig.text, problem: orig.text, pursuit: '', payoff: '' } : null;
  for (let attempt = 1; attempt <= 5; attempt++) {
    let d;
    try { d = await claude(SYSTEM, userPrompt(passages, angles, feedback, last, job, outlier), 4500); } catch (e) { console.log(`Attempt ${attempt}: bad reply (${e.message.slice(0, 80)}). Retrying.`); continue; }
    // One post now (the outlier sets the shape); stored in problem so the draft page and rewrites work as before.
    d.post = String(d.post || [d.problem, d.pursuit, d.payoff].filter(Boolean).join('\n\n')).replace(/\s*[—–]\s*/g, ', ').trim();
    d.problem = d.post; d.pursuit = ''; d.payoff = '';
    // The angle is only a label for Joel now (7 Oct 2026), so a wrong one is corrected, never a reason to bin the draft.
    if (!pool.includes(Number(d.angle))) d.angle = pool[0];
    let problems = check(d, passages, names, outlier);
    const hard = problems.some((p) => HARD.test(p));
    if (!hard) { try { problems = problems.concat(await audit(d.post, d.source.text)); } catch (e) { problems.push('The fact check could not read its own reply. Try again.'); } }
    if (!problems.length) { draft = d; break; }
    // A draft the fact check never finished on is unchecked, so it counts as unbacked too (6 Oct 2026: one slipped through).
    const unbacked = problems.some((p) => /^(Not in Joel's words|The fact check could not read)/.test(p));
    if (!hard && !unbacked && (!best || d.ownShare > best.d.ownShare || (d.ownShare === best.d.ownShare && problems.length < best.problems.length))) best = { d, problems };
    console.log(`Attempt ${attempt} rejected: ${problems.length} problem(s). Joel's own words: ${Math.round((d.ownShare || 0) * 100)}%.`);
    // Kinds of problem only, cut before any quote or detail: the logs are public.
    console.log('  kinds: ' + problems.map((p) => p.split(/[:("“]/)[0].trim().slice(0, 50)).join(' | '));
    if (DRY) console.log('  - ' + problems.join('\n  - ') + `\n  [angle ${d.angle}, passages ${d.source?.ids?.join(",")}]\n${d.post}\n`);
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
    console.log(`\n----- PASSAGES USED (${draft.source.date}) -----\n${draft.source.text}\n\n----- LINKEDIN POST -----\n` + draft.post + `\n-------------------------`);
    return;
  }
  // Store the draft privately on Netlify, then Fred sends it to Joel with the Approve button. Never logged.
  const r = await fetch(`${SITE}/api/linkedin/draft?action=create`, {
    method: 'POST', headers: { 'content-type': 'application/json', 'x-fred-secret': FRED_SECRET },
    body: JSON.stringify({ text: draft.post, angle: Number(draft.angle), passage: draft.source.hashes, problem: draft.problem, pursuit: draft.pursuit, payoff: draft.payoff }),
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
  state.push({ date: new Date().toISOString().slice(0, 10), job, angle: Number(draft.angle), passage: draft.source.hashes, outlier: outlier.id });
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
