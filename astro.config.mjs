import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';
import { readdirSync, readFileSync } from 'node:fs';

// lastmod for the sitemap: each post's updatedDate (or pubDate), read straight from the
// frontmatter because astro:content isn't available in this file. /blog/ gets the newest date.
const postDates = {};
for (const f of readdirSync('./src/content/blog')) {
  if (!/\.mdx?$/.test(f)) continue;
  const fm = (readFileSync(`./src/content/blog/${f}`, 'utf8').match(/^---\n([\s\S]*?)\n---/) || [])[1] || '';
  if (/^draft:\s*true/m.test(fm)) continue;
  const raw = (fm.match(/^updatedDate:\s*["']?([^"'\n]+)/m) || fm.match(/^pubDate:\s*["']?([^"'\n]+)/m) || [])[1];
  const d = raw ? new Date(raw.trim()) : null;
  if (d && !isNaN(d)) postDates[f.replace(/\.mdx?$/, '')] = d;
}
const newestPost = Object.values(postDates).sort((a, b) => b - a)[0];

export default defineConfig({
  // Must match LINKS.siteUrl in src/config/links.ts — this is the only duplication (astro.config is loaded before TS).
  site: 'https://wayofwealthcoaching.com',
  trailingSlash: 'always', // Netlify serves folder pages at /x/ and 301s /x -> /x/, so canonicals + sitemap must end in / (26 Sep: 73 of 87 pages weren't indexed)
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/draft/'),
      serialize(item) {
        const path = new URL(item.url).pathname;
        const m = path.match(/^\/blog\/([^/]+)\/$/);
        if (m && postDates[m[1]]) item.lastmod = postDates[m[1]].toISOString();
        else if (path === '/blog/' && newestPost) item.lastmod = newestPost.toISOString();
        return item;
      },
    }),
    mdx(),
  ],
  build: {
    format: 'directory',
  },
});
