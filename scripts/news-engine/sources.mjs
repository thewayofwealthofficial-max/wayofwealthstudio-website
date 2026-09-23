// Free, official-or-public feeds that show what people are reading and searching for right now.
// No API keys, no scraping of sites that block bots. Every source is optional: one failing never
// stops the run.

const UA = 'Mozilla/5.0 (compatible; WayOfWealthBot/1.0; +https://thewayofwealth.shop)';

const FEEDS = [
  { name: 'Guardian Money', url: 'https://www.theguardian.com/money/rss' },
  { name: 'Guardian Business', url: 'https://www.theguardian.com/uk/business/rss' },
  { name: 'BBC Business', url: 'https://feeds.bbci.co.uk/news/business/rss.xml' },
  { name: 'BBC Technology', url: 'https://feeds.bbci.co.uk/news/technology/rss.xml' },
  { name: 'Google News: self-employed and tax', url: 'https://news.google.com/rss/search?q=%28self-employed+OR+HMRC+OR+%22self+assessment%22+OR+freelancer%29+when%3A2d&hl=en-GB&gl=GB&ceid=GB%3Aen' },
  { name: 'Google News: money and cost of living', url: 'https://news.google.com/rss/search?q=%28%22cost+of+living%22+OR+%22interest+rates%22+OR+savings+OR+%22energy+bills%22+OR+mortgage%29+when%3A2d&hl=en-GB&gl=GB&ceid=GB%3Aen' },
  { name: 'Google Trends UK', url: 'https://trends.google.com/trending/rss?geo=GB', trends: true },
];

const decode = (s) => String(s || '')
  .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
  .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
  .replace(/&#39;|&apos;/g, "'").replace(/&nbsp;/g, ' ');
const strip = (s) => decode(s).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
const pick = (block, tag) => {
  const m = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, 'i'));
  return m ? m[1] : '';
};

async function get(url, ms = 15000) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'application/rss+xml, application/xml, text/xml, text/html, */*' }, signal: ctl.signal, redirect: 'follow' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.text();
  } finally { clearTimeout(t); }
}

function parseItems(xml, source, isTrends) {
  const items = [];
  const blocks = xml.match(/<item[\s\S]*?<\/item>/gi) || [];
  for (const b of blocks) {
    const title = strip(pick(b, 'title'));
    if (!title) continue;
    if (isTrends) {
      const traffic = strip(pick(b, 'ht:approx_traffic'));
      const news = (b.match(/<ht:news_item>[\s\S]*?<\/ht:news_item>/gi) || []).slice(0, 2).map((n) => ({
        title: strip(pick(n, 'ht:news_item_title')), url: strip(pick(n, 'ht:news_item_url')), src: strip(pick(n, 'ht:news_item_source')),
      })).filter((n) => n.title);
      items.push({ source, kind: 'trend', title, traffic, link: (news[0] && news[0].url) || '', summary: news.map((n) => `${n.src}: ${n.title}`).join(' | '), pubDate: strip(pick(b, 'pubDate')) });
    } else {
      items.push({ source, kind: 'news', title, link: strip(pick(b, 'link')) || strip(pick(b, 'guid')), summary: strip(pick(b, 'description')).slice(0, 300), pubDate: strip(pick(b, 'pubDate')) });
    }
  }
  return items;
}

export async function gatherItems({ maxAgeHours = 60 } = {}) {
  const all = [];
  const report = [];
  await Promise.all(FEEDS.map(async (f) => {
    try {
      const xml = await get(f.url);
      const items = parseItems(xml, f.name, !!f.trends);
      report.push(`${f.name}: ${items.length}`);
      all.push(...items);
    } catch (e) {
      report.push(`${f.name}: FAILED (${e.message})`);
    }
  }));
  const cutoff = Date.now() - maxAgeHours * 3600 * 1000;
  const fresh = all.filter((i) => {
    const t = Date.parse(i.pubDate);
    return Number.isNaN(t) || t >= cutoff;
  });
  const seen = new Set();
  const dedup = fresh.filter((i) => {
    const k = i.title.toLowerCase().replace(/[^a-z0-9]+/g, ' ').slice(0, 60);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
  return { items: dedup, report };
}

// Fetch an article page and return plain text (for grounding facts). Returns '' if blocked.
export async function fetchArticleText(url, maxChars = 6000) {
  if (!url) return '';
  try {
    const html = await get(url, 15000);
    const body = html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ').replace(/<nav[\s\S]*?<\/nav>/gi, ' ').replace(/<footer[\s\S]*?<\/footer>/gi, ' ');
    const paras = (body.match(/<p[\s\S]*?<\/p>/gi) || []).map(strip).filter((p) => p.length > 60);
    return paras.join('\n\n').slice(0, maxChars);
  } catch { return ''; }
}
