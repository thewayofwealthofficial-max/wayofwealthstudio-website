// Domain move (Joel, 2026-09-26): send every thewayofwealth.shop request to the same path on
// wayofwealthcoaching.com with a 301. Edge functions run before Netlify's redirect rules, so this
// holds even for requests the netlify.toml rules somehow miss (Google's live test got a 200 on 27 Sep).
export default async (request) => {
  const url = new URL(request.url);
  if (url.hostname === 'thewayofwealth.shop' || url.hostname === 'www.thewayofwealth.shop') {
    return new Response(null, {
      status: 301,
      headers: { location: `https://wayofwealthcoaching.com${url.pathname}${url.search}`, 'cache-control': 'public, max-age=3600' },
    });
  }
  return; // every other host: carry on as normal
};

export const config = { path: '/*' };
