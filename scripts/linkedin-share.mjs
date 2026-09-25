#!/usr/bin/env node
// Shares ONE blog post to Joel's LinkedIn profile. Runs 3 times a week (Joel: "best of 3").
//   1. Candidates = posts from the last 7 days not yet shared (state: scripts/state/linkedin-shared.json).
//   2. Claude picks the one that best fits the reader (wellness practitioners and coaches who struggle to
//      charge and keep money). No engagement data exists yet, so "best" = best fit, not most read.
//   3. The LinkedIn text is taken from the post itself (its title + "What you need to know" bullets, or its
//      description for older posts) + the link. No new words are written.
//   4. Posts via LinkedIn's official Posts API ("Share on LinkedIn", w_member_social).
//
// ENV: LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, ANTHROPIC_API_KEY. DRY_RUN=1 prints instead of posting.
// FORCE_SLUG=<slug> shares that post (used for the first test).

import { readFile, writeFile, readdir, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const BLOG_DIR = join(ROOT, 'src', 'content', 'blog');
const STATE = join(ROOT, 'scripts', 'state', 'linkedin-shared.json');
const SITE = 'https://thewayofwealth.shop';
const DRY = process.env.DRY_RUN === '1';
const { LINKEDIN_ACCESS_TOKEN: TOKEN, LINKEDIN_PERSON_URN: AUTHOR, ANTHROPIC_API_KEY: KEY, FORCE_SLUG } = process.env;
if (!DRY && (!TOKEN || !AUTHOR)) { console.error('FATAL: LINKEDIN_ACCESS_TOKEN / LINKEDIN_PERSON_URN not set'); process.exit(1); }

const field = (fm, k) => (fm.match(new RegExp(`^${k}:\\s*(.*)$`, 'm')) || [])[1]?.trim().replace(/^"(.*)"$/, '$1').replace(/\\"/g, '"');

async function loadPosts() {
  const out = [];
  for (const f of (await readdir(BLOG_DIR)).filter((x) => x.endsWith('.md'))) {
    const txt = await readFile(join(BLOG_DIR, f), 'utf8');
    const [, fm = '', body = ''] = txt.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/) || [];
    if (/^draft:\s*true/m.test(fm)) continue;
    const bullets = (body.match(/\*\*What you need to know\*\*\s*\n((?:\s*[-*] .+\n?){2,5})/i) || [])[1];
    out.push({
      slug: f.replace(/\.md$/, ''), title: field(fm, 'title'), description: field(fm, 'description'),
      date: field(fm, 'pubDate'), bullets: bullets ? bullets.trim().split('\n').map((l) => l.replace(/^\s*[-*]\s+/, '').trim()) : null,
    });
  }
  return out;
}

async function pickBest(cands) {
  if (cands.length === 1 || !KEY) return cands[0];
  const list = cands.map((c, i) => `${i}. ${c.title} :: ${c.description}`).join('\n');
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST', headers: { 'x-api-key': KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: process.env.CLAUDE_MODEL ?? 'claude-sonnet-4-6', max_tokens: 50,
      system: 'Pick the ONE blog post that wellness and spiritual practitioners, coaches and self-employed people who feel guilty charging, give work away, or earn but cannot keep money would most want to click on LinkedIn. Reply with the number only.',
      messages: [{ role: 'user', content: list }] }),
  });
  const n = Number(((await r.json()).content?.[0]?.text || '').match(/\d+/)?.[0]);
  return cands[Number.isInteger(n) && cands[n] ? n : 0];
}

function buildText(p) {
  const url = `${SITE}/blog/${p.slug}/`;
  const middle = p.bullets ? p.bullets.map((b) => `• ${b}`).join('\n') : p.description;
  return `${p.title}\n\n${middle}\n\nFull post: ${url}`;
}

async function main() {
  const shared = existsSync(STATE) ? JSON.parse(await readFile(STATE, 'utf8')) : [];
  const posts = await loadPosts();
  let pick;
  if (FORCE_SLUG) {
    pick = posts.find((p) => p.slug === FORCE_SLUG);
    if (!pick) throw new Error('FORCE_SLUG not found: ' + FORCE_SLUG);
  } else {
    const weekAgo = new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10);
    const cands = posts.filter((p) => p.date >= weekAgo && !shared.some((s) => s.slug === p.slug)).sort((a, b) => b.date.localeCompare(a.date));
    if (!cands.length) { console.log('No unshared posts from the last 7 days. Nothing to share.'); return; }
    pick = await pickBest(cands);
  }
  const text = buildText(pick);
  const url = `${SITE}/blog/${pick.slug}/`;
  console.log(`Picked: ${pick.title}\n----- LinkedIn text -----\n${text}\n-------------------------`);
  if (DRY) { console.log('DRY RUN: not posted.'); return; }

  const r = await fetch('https://api.linkedin.com/rest/posts', {
    method: 'POST',
    headers: { authorization: `Bearer ${TOKEN}`, 'content-type': 'application/json', 'LinkedIn-Version': process.env.LINKEDIN_VERSION ?? '202509', 'X-Restli-Protocol-Version': '2.0.0' },
    body: JSON.stringify({
      author: AUTHOR, commentary: text, visibility: 'PUBLIC',
      distribution: { feedDistribution: 'MAIN_FEED', targetEntities: [], thirdPartyDistributionChannels: [] },
      content: { article: { source: url, title: pick.title, description: (pick.description || '').slice(0, 200) } },
      lifecycleState: 'PUBLISHED', isReshareDisabledByAuthor: false,
    }),
  });
  if (r.status !== 201) throw new Error(`LinkedIn API ${r.status}: ${(await r.text()).slice(0, 400)}`);
  const id = r.headers.get('x-restli-id') || '';
  console.log('Posted to LinkedIn: ' + id);
  shared.push({ slug: pick.slug, date: new Date().toISOString().slice(0, 10), id });
  await mkdir(dirname(STATE), { recursive: true });
  await writeFile(STATE, JSON.stringify(shared, null, 2) + '\n');
  if (process.env.GITHUB_OUTPUT) {
    const { appendFile } = await import('node:fs/promises');
    await appendFile(process.env.GITHUB_OUTPUT, `title=${pick.title}\nurl=${url}\n`);
  }
}

main().catch((e) => { console.error('FATAL:', e.message); process.exit(1); });
