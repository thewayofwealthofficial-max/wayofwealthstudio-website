#!/usr/bin/env node
// LinkedIn niche monitor (Joel, 28 Sep 2026): every Monday, find the best-performing PUBLIC LinkedIn posts from the
// past week in Joel's space, so his own posts can copy what's working.
//   1. Brave Search (past week) for public LinkedIn posts: money, wellness, and the bridge between them.
//   2. Read each post's public page LOGGED OUT, the same method as research/2026-09-25-linkedin/v2 (JSON-LD counts).
//      Never logs in, never uses Joel's account or cookies. Small and slow on purpose (max 60 reads, 2.5-4 s apart).
//   3. Rank by engagement per 1,000 followers (so small accounts that punch above their weight show up).
//   4. Claude tags each top post's pattern from its text (hook type, structure). Top 10 go to Fred.
//   5. Saves scripts/state/linkedin-monitor/latest.json (links, numbers, patterns, first line only) for the
//      LinkedIn writer to use as "what's working this week" context.
//
// ENV: BRAVE_API_KEY, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. DRY_RUN=1 prints instead of sending.

import { writeFile, mkdir } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'scripts', 'state', 'linkedin-monitor');
const DRY = process.env.DRY_RUN === '1';
const { BRAVE_API_KEY, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID } = process.env;
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// The three areas from the LinkedIn research: A money, B wellness, C the bridge.
const QUERIES = {
  money: ['"money mindset"', '"relationship with money"', '"money story"', 'overspending habits', '"self-employed" money', '"financial wellbeing"'],
  wellness: ['breathwork practitioner business', 'yoga teacher income', 'healer charging', '"wellness practitioner" money', 'retreat leader pricing', 'coach undercharging'],
  bridge: ['"money blocks"', 'charging your worth coach', 'guilt charging clients', '"money and the nervous system"', 'manifesting money behaviour', 'pricing guilt wellness'],
};

async function search(q) {
  const url = `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(`site:linkedin.com/posts ${q}`)}&count=20&freshness=pw`;
  const r = await fetch(url, { headers: { 'X-Subscription-Token': BRAVE_API_KEY, Accept: 'application/json' } });
  if (!r.ok) throw new Error(`Brave ${r.status}`);
  return ((await r.json()).web?.results || []).map((x) => x.url).filter((u) => /linkedin\.com\/posts\/.+activity-\d+/.test(u));
}

const num = (s) => (s == null ? null : Number(String(s).replace(/,/g, '')));
function parse(h) {
  const m = h.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  if (!m) return null;
  let ld; try { ld = JSON.parse(m[1]); } catch { return null; }
  const stats = Object.fromEntries((ld.interactionStatistic || []).filter((s) => s && typeof s === 'object').map((s) => [String(s.interactionType || '').split('/').pop(), s.userInteractionCount]));
  const reactions = stats.LikeAction ?? num((h.match(/data-num-reactions="(\d+)"/) || [])[1]);
  const comments = stats.CommentAction ?? ld.commentCount ?? num((h.match(/data-num-comments="(\d+)"/) || [])[1]);
  let author = ld.author || ld.creator || {}; if (Array.isArray(author)) author = author[0];
  const fLd = author?.interactionStatistic?.userInteractionCount ?? null;
  const fCard = num((h.match(/public-post-author-card__followers[^>]*>\s*([\d,]+) followers/) || [])[1]);
  const followers = fLd != null && fCard != null ? (fLd === fCard ? fLd : null) : (fLd ?? fCard);
  const body = String(ld.articleBody || '');
  return { author: author?.name || '', followers, reactions, comments, date: ld.datePublished || '', body };
}

async function claude(system, user) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-6', max_tokens: 2500, system, messages: [{ role: 'user', content: user }] }),
  });
  if (!r.ok) throw new Error(`Anthropic ${r.status}`);
  const t = ((await r.json()).content || []).map((b) => b.text || '').join('');
  return JSON.parse(t.slice(t.indexOf('{'), t.lastIndexOf('}') + 1));
}

async function telegram(text) {
  if (DRY) { console.log(text); return; }
  for (let i = 0; i < text.length; i += 3900) {
    const r = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text: text.slice(i, i + 3900), disable_web_page_preview: true }),
    });
    if (!r.ok) throw new Error(`Telegram ${r.status}`);
  }
}

async function main() {
  if (!BRAVE_API_KEY) { console.log('BRAVE_API_KEY not set yet; skipping this week.'); return; }
  const found = new Map();
  for (const [area, qs] of Object.entries(QUERIES)) {
    for (const q of qs) {
      try { for (const u of await search(q)) { const url = u.split('?')[0].replace(/https?:\/\/[a-z]{2,3}\.linkedin/, 'https://www.linkedin'); if (!found.has(url)) found.set(url, area); } }
      catch (e) { console.log(`search failed (${area}): ${e.message}`); }
      await sleep(1100); // free plan: 1 request a second
    }
  }
  console.log(`${found.size} candidate posts found.`);

  const since = Date.now() - 14 * 864e5;
  const posts = [];
  for (const [url, area] of [...found].slice(0, 60)) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': UA, 'Accept-Language': 'en-GB,en;q=0.9' }, redirect: 'follow' });
      const p = r.ok ? parse(await r.text()) : null;
      if (p && Number.isInteger(p.reactions) && p.reactions >= 5 && Number.isInteger(p.followers) && p.followers > 0 && (!p.date || Date.parse(p.date) >= since)) {
        posts.push({ url, area, ...p, per1k: Math.round(((p.reactions + (p.comments || 0)) / p.followers) * 1000 * 100) / 100 });
      }
    } catch { /* one unreadable page never stops the run */ }
    await sleep(2500 + Math.random() * 1500);
  }
  posts.sort((a, b) => b.per1k - a.per1k);
  const top = posts.slice(0, 10);
  console.log(`${posts.length} readable posts from the last 14 days; top ${top.length} kept.`);
  if (!top.length) { await telegram('📊 LinkedIn niche monitor: no readable posts from the past week this time. Nothing to report.'); return; }

  const tags = await claude(
    'You tag LinkedIn posts by their pattern, judging only from the text. For each post give: hook (confession | question | story | myth | hot take | list | news | other), structure (story with lesson | story no lesson | explainer | list | call-out | promo | other), and why (one plain sentence on what makes the first lines work). Output only JSON {"items":[{"i":0,"hook":"","structure":"","why":""}]}',
    JSON.stringify(top.map((p, i) => ({ i, text: p.body.slice(0, 1500) }))),
  ).catch(() => ({ items: [] }));
  top.forEach((p, i) => Object.assign(p, (tags.items || []).find((t) => t.i === i) || {}));

  const firstLine = (b) => (b.split('\n').find((l) => l.trim()) || '').trim().slice(0, 120);
  const lines = top.map((p, i) => `${i + 1}. ${p.author} (${p.followers.toLocaleString('en-GB')} followers) · ${p.area}\n   ${p.per1k} per 1k · ${p.reactions} reactions, ${p.comments ?? 0} comments\n   "${firstLine(p.body)}"\n   ${p.hook || '?'} · ${p.structure || '?'}${p.why ? `: ${p.why}` : ''}\n   ${p.url}`);
  await telegram(`📊 LinkedIn: what's working this week (${posts.length} public posts read)\n\n${lines.join('\n\n')}`);

  // Saved for the LinkedIn writer. Links, numbers, patterns and the first line only; never the whole post.
  await mkdir(OUT, { recursive: true });
  await writeFile(join(OUT, 'latest.json'), JSON.stringify({
    date: new Date().toISOString().slice(0, 10),
    posts: top.map(({ url, area, author, followers, reactions, comments, per1k, hook, structure, why, body }) => ({ url, area, author, followers, reactions, comments, per1k, hook, structure, why, firstLine: firstLine(body) })),
  }, null, 2) + '\n');
}

main().catch(async (e) => { console.error('FATAL:', e.message); process.exit(1); });
