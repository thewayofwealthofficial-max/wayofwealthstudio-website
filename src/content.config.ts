import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string().max(100),
    // Short <title> tag (max 60) when "title — Way of Wealth" is too long. The full title stays as the H1.
    seoTitle: z.string().max(60).optional(),
    description: z.string().max(170),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    category: z.enum([
      'Spending & shame',
      'Anxiety & avoidance',
      'ADHD & money',
      'Self-employed',
      'Budgeting that sticks',
      'Behavioural basics',
    ]),
    redditSource: z.string().url().optional(),
    redditQuestion: z.string().optional(),
    ogImage: z.string().optional(),
    draft: z.boolean().default(false),
    readingTime: z.string().optional(),
  }),
});

export const collections = { blog };
