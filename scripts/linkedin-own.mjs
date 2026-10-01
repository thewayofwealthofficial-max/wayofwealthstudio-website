#!/usr/bin/env node
// Joel's OWN LinkedIn results (Joel, 1 Oct 2026: Fred should learn from what works, without him).
// Every post that goes live is recorded by linkedin-publish.mjs in scripts/state/linkedin-own.json.
// Daily, this scores each post once it is 7 days old: reactions + comments per 1,000 of Joel's followers, read from
// the PUBLIC post page while logged out (same method as linkedin-monitor.mjs; never his account or cookies).
// It also tags the post's topic, and tells Joel the score. The LinkedIn writer then leans on the post types and
// topics that have beaten his own average, but only once a type has 3+ scored posts (ranking() below).
// Views are not on the public page, so they are not counted. Post text is never saved: this repo is public.
//
// ENV: FRED_SECRET, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. DRY_RUN=1 prints instead of sending.

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { TOPICS } from './linkedin-bank.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
export const OWN = join(ROOT, 'scripts', 'state', 'linkedin-own.json');
const SITE = 'https://wayofwealthcoaching.com';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
const AFTER_DAYS = 7;
const GIVE_UP_DAYS = 30;
export const MIN_POSTS = 3; // a type needs this many scored posts before it counts as better or worse

export const readOwn = () => (existsSync(OWN) ? JSON.parse(readFileSync(OWN, 'utf8')) : { posts: [] });
export const writeOwn = (own) => writeFileSync(OWN, JSON.stringify(own, null, 2) + '\n');

// Average score per angle and per topic, only for those with MIN_POSTS+ scored posts. Best first.
export function ranking(own) {
  const scored = own.posts.filter((p) => p.scored && Number.isFinite(p.scored.per1k));
  const avg = (xs) => Math.round((xs.reduce((s, x) => s + x, 0) / xs.length) * 100) / 100;
  const group = (key) => {
    const g = {};
    for (const p of scored) if (p[key] != null) (g[p[key]] ??= []).push(p.scored.per1k);
    return Object.entries(g).filter(([, xs]) => xs.length >= MIN_POSTS).map(([k, xs]) => ({ key: k, n: xs.length, avg: avg(xs) })).sort((a, b) => b.avg - a.avg);
  };
  return { overall: scored.length ? avg(scored.map((p) => p.scored.per1k)) : null, scoredCount: scored.length, angles: group('angle'), topics: group('topic') };
}

// The post's public page, logged out. Same JSON-LD the monitor reads.
async function readPublic(urn) {
  const r = await fetch(`https://www.linkedin.com/feed/update/${urn}/`, { headers: { 'User-Agent': UA, 'Accept-Language': 'en-GB,en;q=0.9' }, redirect: 'follow' });
  if (!r.ok) return null;
  const m = (await r.text()).match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  if (!m) return null;
  let ld;
  try { ld = JSON.parse(m[1]); } catch { return null; }
  const count = (stats, type) => (Array.isArray(stats) ? stats : [stats]).filter(Boolean).find((s) => String(s.interactionType || '').endsWith(type))?.userInteractionCount;
  const reactions = count(ld.interactionStatistic, 'LikeAction');
  let author = ld.author || ld.creator || {};
  if (Array.isArray(author)) author = author[0];
  const followers = count(author?.interactionStatistic, 'FollowAction');
  if (!Number.isInteger(followers) || followers <= 0) return null;
  // LinkedIn leaves a count out when it is zero, so a missing count on a readable page means 0.
  return { reactions: reactions ?? 0, comments: count(ld.interactionStatistic, 'CommentAction') ?? ld.commentCount ?? 0, followers };
}

async function claude(system, user) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-6', max_tokens: 50, system, messages: [{ role: 'user', content: user }] }),
  });
  if (!r.ok) throw new Error(`Anthropic ${r.status}`);
  return ((await r.json()).content || []).map((b) => b.text || '').join('').trim();
}

// Same fixed topic list as the market monitor, so Joel's topics and the market's can be compared.
async function topicOf(id) {
  const f = await fetch(`${SITE}/api/linkedin/draft?action=fetch&id=${id}`, { headers: { 'x-fred-secret': process.env.FRED_SECRET } });
  if (!f.ok) throw new Error(`Draft fetch ${f.status}`);
  const { text } = await f.json();
  const t = (await claude(`Name the ONE topic this LinkedIn post is mainly about. Reply with exactly one of: ${TOPICS.join(' | ')}`, String(text || '').slice(0, 3000))).toLowerCase();
  return TOPICS.find((x) => t.includes(x)) || null;
}

// Angle names live in linkedin-post.mjs, which runs when imported, so read them from its source.
function angleName(n) {
  const src = readFileSync(join(ROOT, 'scripts', 'linkedin-post.mjs'), 'utf8');
  const m = src.match(new RegExp(`\\n\\s*${n}: \\{ name: '((?:[^'\\\\]|\\\\.)*)'`));
  return m ? m[1].replace(/\\'/g, "'") : `angle ${n}`;
}

async function telegram(html) {
  if (process.env.DRY_RUN === '1') { console.log(html); return; }
  const r = await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chat_id: process.env.TELEGRAM_CHAT_ID, text: html, parse_mode: 'HTML', disable_web_page_preview: true }),
  });
  if (!r.ok) throw new Error(`Telegram ${r.status}`);
}

async function main() {
  const own = readOwn();
  const due = own.posts.filter((p) => !p.scored && Date.now() - Date.parse(p.postedAt) >= AFTER_DAYS * 864e5);
  console.log(`${own.posts.length} posts recorded; ${due.length} due for scoring.`);
  for (const p of due) {
    const counts = await readPublic(p.urn).catch(() => null);
    if (!counts) {
      if (Date.now() - Date.parse(p.postedAt) > GIVE_UP_DAYS * 864e5) { p.scored = { at: new Date().toISOString(), unreadable: true }; console.log(`${p.urn}: unreadable for ${GIVE_UP_DAYS} days, giving up.`); }
      else console.log(`${p.urn}: page not readable today; will try again tomorrow.`);
      continue;
    }
    const per1k = Math.round(((counts.reactions + counts.comments) / counts.followers) * 1000 * 100) / 100;
    p.scored = { at: new Date().toISOString(), ...counts, per1k };
    await tagTopic(p);
    writeOwn(own); // save as we go, so a later failure never loses a score
    const r = ranking(own);
    const day = new Date(p.postedAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    await telegram(
      `📈 <b>Your LinkedIn post from ${day}</b>, 7 days on\n`
      + `${counts.reactions} reactions, ${counts.comments} comments = <b>${per1k} per 1k followers</b>\n`
      + `Type: ${angleName(p.angle)}${p.topic ? ` · Topic: ${p.topic}` : ''}\n`
      + (r.scoredCount > 1 ? `Your average so far: ${r.overall} per 1k (${r.scoredCount} posts)\n` : 'First scored post, so no average yet.\n')
      + `https://www.linkedin.com/feed/update/${p.urn}/`,
    );
  }
  // A topic that failed to tag on an earlier day gets another go.
  for (const p of own.posts.filter((x) => x.scored && !x.scored.unreadable && !('topic' in x))) await tagTopic(p);
  writeOwn(own);
}

// Leaves `topic` unset on failure so tomorrow's run tries again; null means "tagged, but no topic matched".
async function tagTopic(p) {
  if ('topic' in p) return;
  try { p.topic = await topicOf(p.id); } catch (e) { console.log(`topic for ${p.id}: ${e.message}; will retry tomorrow.`); }
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  main().catch((e) => { console.error('FATAL:', e.message); process.exit(1); });
}
