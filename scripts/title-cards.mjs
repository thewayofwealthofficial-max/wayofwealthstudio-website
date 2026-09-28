#!/usr/bin/env node
// Title cards for every blog post, in the site's own look (BRAND.md §4: navy / cream / gold, one gold accent;
// Playfair Display headings, Lora and Inter as on the website). Two sizes per post:
//   public/cards/og/<slug>.png   1200 x 630   the link preview on LinkedIn, Facebook, WhatsApp, X
//   public/cards/pin/<slug>.png  1000 x 1500  the Pinterest pin (2:3 is what Pinterest shows best)
// Runs before every build (npm "prebuild"). Existing cards are kept, so only new posts cost time.
//
// Usage: node scripts/title-cards.mjs                 all posts
//        node scripts/title-cards.mjs --only <slug> --out <dir> --force   one post, e.g. a sample

import { readFile, readdir, writeFile, mkdir, access } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import satori from 'satori';
import sharp from 'sharp';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const BLOG = join(ROOT, 'src', 'content', 'blog');
const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const ONLY = opt('--only');
const OUT = opt('--out') || join(ROOT, 'public', 'cards');
const FORCE = args.includes('--force');
// Pins (--pins) use the layout from the Pinterest research; Joel said go on 28 Sep.
const PINS = args.includes('--pins');

const C = { navy: '#1C2A3A', cream: '#F5F0E8', gold: '#C4A265', brown: '#5C4E3C', brownLight: '#7A6B57', border: '#D4C9B8' };
const font = (pkg, file) => readFile(join(ROOT, 'node_modules', '@fontsource', pkg, 'files', file));
const FONTS = [
  { name: 'Playfair', data: await font('playfair-display', 'playfair-display-latin-700-normal.woff'), weight: 700, style: 'normal' },
  { name: 'Playfair', data: await font('playfair-display', 'playfair-display-latin-400-normal.woff'), weight: 400, style: 'normal' },
  { name: 'Lora', data: await font('lora', 'lora-latin-400-italic.woff'), weight: 400, style: 'italic' },
  { name: 'Inter', data: await font('inter', 'inter-latin-500-normal.woff'), weight: 500, style: 'normal' },
];

const h = (type, style, ...children) => ({ type, props: { style: { display: 'flex', ...style }, children: children.flat().filter((c) => c !== null && c !== undefined) } });
const field = (fm, k) => (fm.match(new RegExp(`^${k}:\\s*(.*)$`, 'm')) || [])[1]?.trim().replace(/^["'](.*)["']$/, '$1').replace(/\\"/g, '"');
const size = (t, big, mid, small) => (t.length <= 50 ? big : t.length <= 85 ? mid : small);
const CRED = 'Joel Ezekiel · MSc Behavioural Economics | Qualified Financial Planner';

function og(title) {
  return h('div', { width: 1200, height: 630, background: C.cream, padding: '64px 72px', flexDirection: 'column', justifyContent: 'space-between' },
    h('div', { fontFamily: 'Playfair', fontSize: 22, letterSpacing: 5, color: C.navy }, 'WAY OF WEALTH'),
    h('div', { flexDirection: 'column' },
      h('div', { fontFamily: 'Playfair', fontWeight: 700, fontSize: size(title, 64, 54, 44), lineHeight: 1.15, color: C.navy }, title),
      h('div', { width: 90, height: 4, background: C.gold, marginTop: 34 })),
    h('div', { justifyContent: 'space-between', fontFamily: 'Inter', fontSize: 19, color: C.brown },
      h('div', {}, CRED), h('div', { color: C.brownLight }, 'wayofwealthcoaching.com')));
}

// Pin layout copied from the most-saved blog pins in this niche (research/2026-09-28-pinterest-pins/FINDINGS.md):
// 2:3, light background, a big bold 5-10 word headline in the top half, a soft photo with no face below,
// the web address small at the very bottom, 2-3 bits of text, no "save this" and no button.
const PHOTOS = ['0EFDQKW84D', 'JHJH4PS68L', 'YR1I6HCCOP', '8Y0EDX4VP9', 'DPKNIIN5X3']; // CC0, see pin-photos/LICENSE.txt
const photoCache = {};
async function photoFor(slug) {
  let n = 0; for (const ch of slug) n = (n * 31 + ch.charCodeAt(0)) >>> 0;
  const id = PHOTOS[n % PHOTOS.length];
  if (!photoCache[id]) {
    const buf = await sharp(join(ROOT, 'scripts', 'pin-photos', `${id}.jpg`)).resize(1000, 690, { fit: 'cover' }).jpeg({ quality: 86 }).toBuffer();
    photoCache[id] = `data:image/jpeg;base64,${buf.toString('base64')}`;
  }
  return photoCache[id];
}

// 5-10 words is what most top pins use; Joel (28 Sep) chose to keep readers' full questions up to 14 words. A post can set `pinTitle:` in its front matter; otherwise the title is used
// if it's short enough, or its first clause (the words before the first comma or question mark).
function pinHeadline(fm, title) {
  const set = field(fm, 'pinTitle');
  if (set) return set;
  const words = (s) => s.trim().split(/\s+/).length;
  if (words(title) <= 14 && !/[—–]/.test(title)) return title; // Joel, 28 Sep: keep the reader's full question up to 14 words
  const first = (title.match(/^[^,?:;]+[?]?/) || [title])[0].trim();
  return words(first) >= 4 && words(first) <= 14 ? first : title;
}

function pin(headline, photo) {
  return h('div', { width: 1000, height: 1500, background: C.cream, flexDirection: 'column' },
    h('div', { height: 740, padding: '90px 80px 0', flexDirection: 'column', justifyContent: 'center' },
      h('div', { fontFamily: 'Playfair', fontSize: 26, letterSpacing: 6, color: C.navy, marginBottom: 44 }, 'WAY OF WEALTH'),
      h('div', { fontFamily: 'Playfair', fontWeight: 700, fontSize: size(headline, 92, 78, 64), lineHeight: 1.1, color: C.navy }, headline),
      h('div', { width: 120, height: 5, background: C.gold, marginTop: 44 })),
    { type: 'img', props: { src: photo, width: 1000, height: 690, style: { width: 1000, height: 690, objectFit: 'cover' } } },
    h('div', { height: 70, alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter', fontSize: 26, color: C.brown }, 'wayofwealthcoaching.com'));
}

async function render(tree, width, height, file) {
  const svg = await satori(tree, { width, height, fonts: FONTS });
  const img = sharp(Buffer.from(svg));
  // Pins carry a photo, so JPEG (about a fifth of the PNG size); text-only cards stay PNG.
  await writeFile(file, await (file.endsWith('.jpg') ? img.jpeg({ quality: 88, mozjpeg: true }) : img.png({ compressionLevel: 9 })).toBuffer());
}
const exists = (p) => access(p).then(() => true, () => false);

await mkdir(join(OUT, 'og'), { recursive: true });
// The share picture for every page that isn't a blog post (the homepage's own headline).
if (!ONLY && (FORCE || !(await exists(join(OUT, 'og-default.png'))))) await render(og("Behavioural money coaching for people who've tried everything else"), 1200, 630, join(OUT, 'og-default.png'));
await mkdir(join(OUT, 'pin'), { recursive: true });
let made = 0;
for (const f of (await readdir(BLOG)).filter((x) => x.endsWith('.md'))) {
  const slug = f.replace(/\.md$/, '');
  if (ONLY && slug !== ONLY) continue;
  const fm = ((await readFile(join(BLOG, f), 'utf8')).match(/^---\r?\n([\s\S]*?)\r?\n---/) || [])[1] || '';
  if (/^draft:\s*true/m.test(fm)) continue;
  const title = field(fm, 'title') || slug;
  const description = field(fm, 'description') || '';
  const ogFile = join(OUT, 'og', `${slug}.png`), pinFile = join(OUT, 'pin', `${slug}.jpg`);
  if (FORCE || !(await exists(ogFile))) { await render(og(title), 1200, 630, ogFile); made++; }
  if (PINS && (FORCE || !(await exists(pinFile)))) { await render(pin(pinHeadline(fm, title), await photoFor(slug)), 1000, 1500, pinFile); made++; }
}
console.log(`title cards: ${made} made`);
