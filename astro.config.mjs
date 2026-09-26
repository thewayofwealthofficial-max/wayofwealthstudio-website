import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

export default defineConfig({
  // Must match LINKS.siteUrl in src/config/links.ts — this is the only duplication (astro.config is loaded before TS).
  site: 'https://thewayofwealth.shop',
  trailingSlash: 'always', // Netlify serves folder pages at /x/ and 301s /x -> /x/, so canonicals + sitemap must end in / (26 Sep: 73 of 87 pages weren't indexed)
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/draft/'),
    }),
    mdx(),
  ],
  build: {
    format: 'directory',
  },
});
