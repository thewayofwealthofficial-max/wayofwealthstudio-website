// Netlify runs this automatically after every successful deploy (a function named "deploy-succeeded").
// It tells Bing (and the other IndexNow engines, which share pings) about blog posts from the last 3 days,
// so new posts are found quickly. It runs AFTER publishing, so the pages already exist when Bing arrives.
// The key file public/<key>.txt proves the pings come from this site; it is public by design.
// Added 28 Sep 2026. Never throws: indexing must never affect a deploy.

const SITE = 'https://wayofwealthcoaching.com';
const KEY = '18bce0f9c1c417174e3f3827bf0a7bdd';

exports.handler = async (event) => {
  try {
    const deploy = (JSON.parse(event.body || '{}').payload) || {};
    if (deploy.context && deploy.context !== 'production') return { statusCode: 200, body: 'not production' };

    const rss = await (await fetch(`${SITE}/rss.xml`)).text();
    const since = Date.now() - 3 * 864e5;
    const urls = [];
    for (const item of rss.split('<item>').slice(1)) {
      const link = (item.match(/<link>([^<]+)<\/link>/) || [])[1];
      const date = Date.parse((item.match(/<pubDate>([^<]+)<\/pubDate>/) || [])[1] || '');
      if (link && link.startsWith(SITE) && date >= since) urls.push(link);
    }
    if (!urls.length) return { statusCode: 200, body: 'no new posts' };

    const res = await fetch('https://api.indexnow.org/indexnow', {
      method: 'POST',
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ host: 'wayofwealthcoaching.com', key: KEY, keyLocation: `${SITE}/${KEY}.txt`, urlList: urls }),
    });
    console.log(`[indexnow] ${res.status} for ${urls.length} url(s)`);
    return { statusCode: 200, body: `indexnow ${res.status}` };
  } catch (err) {
    console.error('[indexnow] failed:', err.message);
    return { statusCode: 200, body: 'failed quietly' };
  }
};
