import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { LINKS } from '../config/links';
import { statSync } from 'node:fs';

// Each post carries its Pinterest pin (public/cards/pin/<slug>.jpg, made by scripts/title-cards.mjs before the
// build) as an enclosure and as the first image, so Pinterest's RSS auto-publish can pin it (28 Sep 2026).
const pinSize = (id: string) => { try { return statSync(`public/cards/pin/${id}.jpg`).size; } catch { return 0; } };

export async function GET(context: APIContext) {
  const posts = (await getCollection('blog', ({ data }) => !data.draft))
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());

  return rss({
    title: 'Way of Wealth — Blog',
    description: 'Honest, research-based notes on the behavioural side of money. By Joel — MSc Behavioural Economics, Qualified Financial Planner.',
    site: context.site ?? LINKS.siteUrl,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      link: `/blog/${post.id}/`,
      categories: [post.data.category, ...post.data.tags],
      author: 'Joel — Way of Wealth',
      ...(pinSize(post.id)
        ? {
            enclosure: { url: `${LINKS.siteUrl}/cards/pin/${post.id}.jpg`, length: pinSize(post.id), type: 'image/jpeg' },
            content: `<p><img src="${LINKS.siteUrl}/cards/pin/${post.id}.jpg" alt="${post.data.title.replace(/"/g, '&quot;')}" /></p><p>${post.data.description}</p>`,
          }
        : {}),
    })),
    customData: '<language>en-gb</language>',
  });
}
