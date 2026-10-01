#!/usr/bin/env node
// LinkedIn niche monitor (Joel, 28 Sep 2026): every Monday, find the best-performing PUBLIC LinkedIn posts from the
// last 12 months in Joel's space (never repeating one already sent), so his own posts can copy what's working.
//   1. Brave Search (past week) for public LinkedIn posts: money, wellness, and the bridge between them.
//   2. Read each post's public page LOGGED OUT, the same method as research/2026-09-25-linkedin/v2 (JSON-LD counts).
//      Never logs in, never uses Joel's account or cookies. Small and slow on purpose (max 180 reads, monthly, 2.5-4 s apart).
//   3. Rank by engagement per 1,000 followers (so small accounts that punch above their weight show up).
//   4. Claude tags each top post's pattern from its text (hook type, structure). Top 10 go to Fred.
//   5. Saves scripts/state/linkedin-monitor/latest.json (links, numbers, patterns, first line only) for the
//      LinkedIn writer to use as "what's working this week" context.
//   6. Adds the month to scripts/state/linkedin-monitor/bank.json (linkedin-bank.mjs), the running memory of shapes
//      and topics. Anything that wins across months from different people is promoted, and Joel gets a note.
//
// ENV: SERPER_API_KEY (preferred) or BRAVE_API_KEY, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. DRY_RUN=1 prints instead of sending.

import { writeFile, mkdir, readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { TOPICS, PROMOTE, emptyBank, addRun } from './linkedin-bank.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'scripts', 'state', 'linkedin-monitor');
const DRY = process.env.DRY_RUN === '1';
const { BRAVE_API_KEY, SERPER_API_KEY, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID } = process.env;
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// The three areas from the LinkedIn research: A money, B wellness, C the bridge.
// Widened 28 Sep after the first run found only 2 on-topic posts in 23: phrases this room actually uses.
// No quote marks: with Brave's past-year filter, quoted phrases return almost nothing (tested 28 Sep).
// About 39 searches a week (~170 a month), well inside Brave's free $5 (1,000 searches) a month.
const QUERIES = {
  money: ['money mindset coach', 'relationship with money', 'money story', 'money script', 'money blocks', 'money anxiety', 'emotional spending', 'money psychology', 'money and emotions', 'financial wellbeing', 'behavioural finance', 'scarcity mindset money'],
  wellness: ['breathwork facilitator money', 'yoga teacher pricing', 'yoga teacher income', 'energy healer money', 'reiki charging', 'wellness practitioner pricing', 'holistic practitioner money', 'therapist private practice fees', 'sliding scale practitioner'],
  bridge: ['undercharging', 'charging your worth', 'raise my prices coach', 'pricing my services guilt', 'free sessions burnout', 'money guilt', 'afraid to charge', 'worthy of receiving money', 'spiritual business money'],
  // Wider room (Joel, 28 Sep: "go a bit broader"): money coaches and the money side of solo businesses.
  wider: ['money coach', 'financial coach', 'freelancer pricing', 'self-employed income', 'irregular income budgeting', 'pay yourself a salary business owner', 'solopreneur money', 'small business cash flow owner', 'coaching business pricing'],
};

// Google results via Serper.dev when SERPER_API_KEY is set (Google's own search API closed to new sign-ups in 2025);
// otherwise Brave. Brave's LinkedIn coverage proved thin for this niche (28 Sep: 7 on-topic of 69).
async function search(q) {
  if (SERPER_API_KEY) {
    const r = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: `site:linkedin.com/posts ${q}`, num: 20, tbs: 'qdr:y', gl: 'gb', hl: 'en' }),
    });
    if (!r.ok) throw new Error(`Serper ${r.status}`);
    return ((await r.json()).organic || []).map((x) => x.link).filter((u) => /linkedin\.com\/posts\/.+activity-\d+/.test(u));
  }
  const url = `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(`site:linkedin.com/posts ${q}`)}&count=20&freshness=py`; // Brave indexes LinkedIn posts late: past week/month return nothing, past year works (28 Sep)
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

// Claude's own web search (the Anthropic key Joel already has). Tested 28 Sep: 12 searches found 101 LinkedIn posts,
// where Brave's index gave 1-2 on-topic in 64. Each call runs up to 12 searches for one area's terms; only URLs
// from the actual search results are used, never URLs the model writes itself.
async function searchWithClaude(terms) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({
      model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-6', max_tokens: 2000,
      tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: Math.min(12, terms.length) }],
      messages: [{ role: 'user', content: `Run one web search per term below, each of the form: site:linkedin.com/posts <term>. Do not judge the results. Then reply "done".\n\n${terms.map((t) => '- ' + t).join('\n')}` }],
    }),
  });
  if (!r.ok) throw new Error(`Anthropic search ${r.status}`);
  const j = await r.json();
  return (j.content || []).filter((b) => b.type === 'web_search_tool_result').flatMap((b) => (Array.isArray(b.content) ? b.content : []).map((x) => x.url || ''))
    .filter((u) => /linkedin\.com\/posts\/.+activity-\d+/.test(u));
}

async function main() {
  const via = SERPER_API_KEY ? 'Google (Serper)' : ANTHROPIC_API_KEY ? 'Claude web search' : BRAVE_API_KEY ? 'Brave' : null;
  if (!via) { console.log('No search available; skipping.'); return; }
  console.log(`Searching with ${via}.`);
  const found = new Map();
  const add = (u, area) => { const url = u.split('?')[0].replace(/https?:\/\/[a-z]{2,3}\.linkedin/, 'https://www.linkedin'); if (!found.has(url)) found.set(url, area); };
  for (const [area, qs] of Object.entries(QUERIES)) {
    if (via === 'Claude web search') {
      try { for (const u of await searchWithClaude(qs)) add(u, area); } catch (e) { console.log(`search failed (${area}): ${e.message}`); }
      continue;
    }
    for (const q of qs) {
      try { for (const u of await search(q)) add(u, area); } catch (e) { console.log(`search failed (${area}): ${e.message}`); }
      await sleep(1100); // Brave free plan: 1 request a second
    }
  }
  console.log(`${found.size} candidate posts found.`);

  // Posts from the last 2 years that haven't been reported before, so each week only shows new winners.
  let seen = [];
  try { seen = JSON.parse(await readFile(join(OUT, 'seen.json'), 'utf8')); } catch { /* first run */ }
  const since = Date.now() - 730 * 864e5; // 2 years: web search favours older posts (28 Sep: 71 of 90 were over a year old)
  const posts = [];
  const why = { blocked: 0, unreadable: 0, tooOld: 0, under5Reactions: 0, noFollowers: 0, kept: 0 };
  for (const [url, area] of [...found].filter(([u]) => !seen.includes(u)).slice(0, 180)) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': UA, 'Accept-Language': 'en-GB,en;q=0.9' }, redirect: 'follow' });
      const p = r.ok ? parse(await r.text()) : null;
      if (!r.ok) why.blocked++;
      else if (!p) why.unreadable++;
      else if (p.date && Date.parse(p.date) < since) why.tooOld++;
      else if (!Number.isInteger(p.reactions) || p.reactions < 5) why.under5Reactions++;
      else if (!Number.isInteger(p.followers) || p.followers <= 0) why.noFollowers++;
      else { why.kept++; posts.push({ url, area, ...p, per1k: Math.round(((p.reactions + (p.comments || 0)) / p.followers) * 1000 * 100) / 100 }); }
    } catch { why.blocked++; /* one unreadable page never stops the run */ }
    await sleep(2500 + Math.random() * 1500);
  }
  console.log('Why posts dropped out:', JSON.stringify(why));
  // Relevance first (first report, 28 Sep: half the top 10 were off-topic, e.g. awards, recruiting, LinkedIn tips).
  // Claude reads every readable post, keeps only ones genuinely in Joel's space, and tags their pattern.
  // Screened in batches of 20: one call for 64 posts ran out of room and broke (28 Sep).
  const SCREEN = `You screen and tag LinkedIn posts, judging only from the text. relevant = true if the post is genuinely about one of: money mindset, money beliefs or money psychology; money behaviour or emotions (spending, saving, avoiding money, money stress, financial wellbeing); charging, pricing or receiving money for your own work; or the money side of running a solo or small business, coaching or wellness practice (pricing, cash flow, irregular income, paying yourself). Awards, job hunting, recruiting, LinkedIn growth tips, corporate company news or offsites, medical or wound care, investing product promos and tech are NOT relevant. For every post also give: hook (confession | question | story | myth | hot take | list | news | other), structure (story with lesson | story no lesson | explainer | list | call-out | promo | other), topic (exactly one of: ${TOPICS.join(' | ')}), and why (one plain sentence on what makes the first lines work). Output only JSON {"items":[{"i":0,"relevant":true,"hook":"","structure":"","topic":"","why":""}]}`;
  for (let start = 0; start < posts.length; start += 20) {
    const batch = posts.slice(start, start + 20);
    const tags = await claude(SCREEN, JSON.stringify(batch.map((p, i) => ({ i, text: p.body.slice(0, 1000) }))))
      .catch((e) => { console.log(`Screening batch failed: ${e.message}`); return { items: [] }; });
    batch.forEach((p, i) => Object.assign(p, (tags.items || []).find((t) => t.i === i) || {}));
  }
  if (process.env.DEBUG_SCREEN) posts.forEach((p) => console.log(`[${p.relevant ? 'KEEP' : 'drop'}] ${p.area} | ${(p.body.split('\n').find((l) => l.trim()) || '').slice(0, 90)}`));
  const relevant = posts.filter((p) => p.relevant === true).sort((a, b) => b.per1k - a.per1k);
  const top = relevant.slice(0, 10);
  console.log(`${posts.length} readable new posts from the last 2 years; ${relevant.length} on-topic; top ${top.length} kept.`);
  if (!top.length) { await telegram('📊 LinkedIn niche monitor: no on-topic posts found this month. Nothing to report.'); return; }

  const firstLine = (b) => (b.split('\n').find((l) => l.trim()) || '').trim().slice(0, 120);
  const lines = top.map((p, i) => `${i + 1}. ${p.author} (${p.followers.toLocaleString('en-GB')} followers) · ${p.area}\n   ${p.per1k} per 1k · ${p.reactions} reactions, ${p.comments ?? 0} comments\n   "${firstLine(p.body)}"\n   ${p.topic ? p.topic + ' · ' : ''}${p.hook || '?'} · ${p.structure || '?'}${p.why ? `: ${p.why}` : ''}\n   ${p.url}`);
  await telegram(`📊 LinkedIn: what's working in your space (this month) (${relevant.length} on-topic of ${posts.length} read)\n\n${lines.join('\n\n')}`);

  // Saved for the LinkedIn writer. Links, numbers, patterns and the first line only; never the whole post.
  await mkdir(OUT, { recursive: true });
  await writeFile(join(OUT, 'seen.json'), JSON.stringify([...seen, ...top.map((p) => p.url)].slice(-2000)) + '\n');
  await writeFile(join(OUT, 'latest.json'), JSON.stringify({
    date: new Date().toISOString().slice(0, 10),
    posts: top.map(({ url, area, author, followers, reactions, comments, per1k, hook, structure, topic, why, body }) => ({ url, area, author, followers, reactions, comments, per1k, hook, structure, topic: TOPICS.includes(topic) ? topic : null, why, firstLine: firstLine(body) })),
  }, null, 2) + '\n');

  // The running memory. Every on-topic winner this month counts, not just the top 10.
  let bank = emptyBank();
  try { bank = JSON.parse(await readFile(join(OUT, 'bank.json'), 'utf8')); } catch { /* first run */ }
  const fresh = addRun(bank, new Date().toISOString().slice(0, 7), relevant.map((p) => ({ ...p, topic: TOPICS.includes(p.topic) ? p.topic : null, firstLine: firstLine(p.body) })));
  await writeFile(join(OUT, 'bank.json'), JSON.stringify(bank, null, 2) + '\n');
  const learned = [...fresh.patterns.map((k) => `shape: ${k}`), ...fresh.topics.map((k) => `topic: ${k}`)];
  if (learned.length) {
    await telegram(`📈 Fred learned something (won in ${PROMOTE.months}+ months, from ${PROMOTE.authors}+ different people):\n${learned.map((l) => '• ' + l).join('\n')}\n\nYour LinkedIn drafts will now lean on this. To stop one, tell Claude to block it.`);
  }
}

main().catch(async (e) => { console.error('FATAL:', e.message); process.exit(1); });
