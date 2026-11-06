// The creator watchlist (Joel, 6 Nov 2026): 10 real people who post on LinkedIn about personal finance, money habits,
// money psychology or behavioural finance. Every Monday linkedin-monitor.mjs looks for their recent public posts,
// reads the counts logged out, and ranks each post against THAT creator's own usual (median), so a post that did 4x
// its author's normal shows up even when the author is small.
//
// Picked 6 Nov 2026 from public lists of LinkedIn finance creators (exeedin.com finance niche, authoredup.com top
// finance influencers) and web searches. Mix of big US names and UK / mid-size voices. LinkedIn blocked follower
// reads from the research machine, so sizes below are rough. The monitor matches posts by the profile slug in the
// post URL and by the author name on the page, so a wrong slug only means fewer finds, never wrong ones.
// To swap someone out, edit this list. Nothing else needs to change.

export const CREATORS = [
  { name: 'Ramit Sethi', url: 'https://www.linkedin.com/in/ramitsethi', uk: false, size: 'big', why: 'Money psychology of spending: guilt-free spending, "rich life", couples and money. Story-led posts.' },
  { name: 'Vivian Tu', url: 'https://www.linkedin.com/in/viviantu-yourrichbff', uk: false, size: 'big', why: 'Your Rich BFF: plain-talk personal finance for people new to money, very high engagement.' },
  { name: 'Tori Dunlap', url: 'https://www.linkedin.com/in/toridunlap', uk: false, size: 'big', why: 'Her First $100K: money habits, saving, money shame. Confession and story hooks.' },
  { name: 'Brian Feroldi', url: 'https://www.linkedin.com/in/brianferoldi', uk: false, size: 'big', why: 'LinkedIn-native money explainers and habit lists; one of the most engaged finance accounts on the platform.' },
  { name: 'Andrew Lokenauth', url: 'https://www.linkedin.com/in/lokenauth', uk: false, size: 'big', why: 'LinkedIn-native personal finance and wealth-building posts with big reach; good for hooks and layout.' },
  { name: 'Nischa Shah', url: 'https://uk.linkedin.com/in/nischa', uk: true, size: 'big', why: 'UK, ex-investment banker turned money educator: simple money habits, saving order, spending rules.' },
  { name: 'Iona Bain', url: 'https://uk.linkedin.com/in/iona-bain', uk: true, size: 'mid', why: 'UK, Young Money Blog: money for younger earners, money and mental health, UK framing.' },
  { name: 'Vicky Reynal', url: 'https://www.linkedin.com/in/vickyreynal', uk: true, size: 'mid', why: 'UK financial psychotherapist (Money on Your Mind): money psychology, closest to Joel\'s angle.' },
  { name: 'Clint Murphy', url: 'https://www.linkedin.com/in/clint-robert-murphy', uk: false, size: 'mid', why: 'Money mindset, habits and personal growth; mid-size account that regularly beats its own average.' },
  { name: 'Max Pashman', url: 'https://www.linkedin.com/in/maxpashman', uk: false, size: 'mid', why: 'CFP who writes plain personal-planning posts for earners; a planner\'s voice close to Joel\'s.' },
];

// "ramitsethi" from https://www.linkedin.com/in/ramitsethi. Post URLs start linkedin.com/posts/<slug>_...
export const slugOf = (url) => (String(url).match(/linkedin\.com\/in\/([^/?#]+)/) || [])[1]?.toLowerCase() || '';

const norm = (s) => String(s || '').toLowerCase().normalize('NFKD').replace(/[^a-z ]+/g, ' ').replace(/\s+/g, ' ').trim();

/** The watchlist creator a post belongs to, by the slug in its URL or the author name on its page. */
export function creatorOf(url, author = '') {
  const m = String(url).match(/linkedin\.com\/posts\/([^/_?#]+)_/i);
  const slug = m ? m[1].toLowerCase() : '';
  return CREATORS.find((c) => (slug && slug === slugOf(c.url)) || (author && norm(author).includes(norm(c.name)))) || null;
}
