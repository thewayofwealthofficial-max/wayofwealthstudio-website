// Shared rules for the blog generators (generate-daily-post.mjs, news-engine/generate-news-post.mjs).
// 6 Nov 2026: posts had invented web addresses for us (wealthofway.com, wayofwealth.co.uk) and slugs cut
// mid-word. This file holds the link check, the length limits and the word-safe trims.

import { readdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const PAGES_DIR = join(ROOT, 'src', 'pages');
const BLOG_DIR = join(ROOT, 'src', 'content', 'blog');

export const SITE_HOST = 'wayofwealthcoaching.com';
export const SEO_TITLE_MAX = 60; // the <title> tag
export const DESCRIPTION_MAX = 155; // the meta description
export const TITLE_SUFFIX = ' — Way of Wealth'; // added to the <title> by src/pages/blog/[...slug].astro

// ---------- lengths ----------

// Cut to at most `max` characters, never mid-word. Drops a trailing comma, colon, dash or "and".
export function trimAtWord(text, max) {
  const s = String(text || '').trim();
  if (s.length <= max) return s;
  let cut = s.slice(0, max + 1);
  const space = cut.lastIndexOf(' ');
  cut = space > 0 ? cut.slice(0, space) : s.slice(0, max);
  return cut.replace(/[\s,;:–—-]+$/, '').replace(/\s+(?:and|or|but|the|a|to|of)$/i, '').trim();
}

// Slug from a title: lowercase words joined by hyphens, at most `max` characters, never cut mid-word.
export function slugify(text, max = 70) {
  const s = String(text || '')
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (s.length <= max) return s;
  const cut = s.slice(0, max + 1);
  const dash = cut.lastIndexOf('-');
  return (dash > 0 ? cut.slice(0, dash) : s.slice(0, max)).replace(/-+$/, '');
}

// The <title> text: seoTitle when set, else the title plus the suffix.
export function needsSeoTitle(title) {
  return `${title}${TITLE_SUFFIX}`.length > SEO_TITLE_MAX;
}

// ---------- links ----------

// Every page on wayofwealthcoaching.com, from src/pages and the blog folder.
export function sitePaths() {
  const paths = new Set(['/']);
  const walk = (dir, base) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.isDirectory()) { walk(join(dir, e.name), `${base}${e.name}/`); continue; }
      const m = e.name.match(/^(.+)\.(astro|md|mdx)$/);
      if (!m || m[1].startsWith('[') || m[1] === '404') continue;
      paths.add(m[1] === 'index' ? (base || '/') : `${base}${m[1]}/`);
    }
  };
  walk(PAGES_DIR, '/');
  if (existsSync(BLOG_DIR)) {
    for (const f of readdirSync(BLOG_DIR)) if (/\.mdx?$/.test(f)) paths.add(`/blog/${f.replace(/\.mdx?$/, '')}/`);
  }
  return paths;
}

// The main site pages (not every blog post), for the prompts.
export const MAIN_PAGES = [
  ['/', 'home page'],
  ['/#start', 'join The Thursday Money Note, the free newsletter'],
  ['/coaching/', 'The Money Story Method, the 12-week 1:1 programme'],
  ['/coaching/#apply', 'apply for coaching and book a call'],
  ['/your-number/', 'the free Cash Flow Session'],
  ['/about/', 'about Joel'],
  ['/blog/', 'the blog'],
];

export const LINK_RULE = `

LINKS (hard rule): our only website is ${SITE_HOST}. Link to our pages ONLY with these relative links, written exactly like this:
${MAIN_PAGES.map(([p, what]) => `- ${p} (${what})`).join('\n')}
- /blog/<slug>/ only for a post given to you in this message.
Never write out any other web address for Way of Wealth, Joel, the newsletter or the programme, linked or not. Never make up a domain (no wealthofway.com, wayofwealth.co.uk, thewayofwealth.com or similar). If you are not sure a page exists, don't link it.`;

// A host that looks like ours but is not wayofwealthcoaching.com (wealthofway.com, wayofwealth.co.uk, thewayofwealth.shop ...).
export function fakeOurHost(host) {
  const h = String(host || '').toLowerCase().replace(/^www\./, '');
  if (h === SITE_HOST) return false;
  return /way-?of-?wealth|wealth-?of-?way/.test(h);
}

const MD_LINK_RE = /\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)/g;
const BARE_DOMAIN_RE = /\b(?:https?:\/\/)?((?:[a-z0-9-]+\.)+[a-z]{2,6})\b/gi;

function hostOf(url) {
  try { return new URL(url).hostname.toLowerCase(); } catch { return ''; }
}
function pathOf(url) {
  const p = url.replace(/^https?:\/\/(?:www\.)?wayofwealthcoaching\.com/i, '').split(/[?#]/)[0] || '/';
  return p.endsWith('/') ? p : `${p}/`;
}

// What is wrong with the links in a post. Outside sources (news sites, research) are allowed.
export function checkSiteLinks(text, paths = sitePaths()) {
  const problems = new Set();
  for (const [, , url] of text.matchAll(MD_LINK_RE)) {
    if (url.startsWith('#') || url.startsWith('mailto:')) continue;
    if (url.startsWith('/')) {
      if (!paths.has(pathOf(url))) problems.add(`Links to ${url}, which is not a page on ${SITE_HOST}. Use only the pages in the LINKS list.`);
      continue;
    }
    const host = hostOf(url);
    if (host.replace(/^www\./, '') === SITE_HOST) {
      if (!paths.has(pathOf(url))) problems.add(`Links to ${url}, which is not a page on ${SITE_HOST}. Use only the pages in the LINKS list.`);
    } else if (fakeOurHost(host)) {
      problems.add(`Links to ${host}, which is not our website. Our only site is ${SITE_HOST}: use a relative link from the LINKS list.`);
    }
  }
  for (const [, host] of text.matchAll(BARE_DOMAIN_RE)) {
    if (fakeOurHost(host)) problems.add(`Mentions ${host}, which is not our website. Our only site is ${SITE_HOST}: use a relative link from the LINKS list.`);
  }
  return [...problems];
}

// Last guard before a post is written: drop links to fake "our" domains or missing pages (keep the words),
// and swap any bare fake domain for the real one.
export function stripBadLinks(text, paths = sitePaths()) {
  const out = text.replace(MD_LINK_RE, (all, label, url) => {
    if (url.startsWith('#') || url.startsWith('mailto:')) return all;
    const host = hostOf(url);
    const ours = url.startsWith('/') || host.replace(/^www\./, '') === SITE_HOST;
    if (ours && paths.has(pathOf(url))) return all;
    if (ours || fakeOurHost(host)) return label;
    return all;
  });
  return out.replace(BARE_DOMAIN_RE, (all, host) => (fakeOurHost(host) ? SITE_HOST : all));
}
