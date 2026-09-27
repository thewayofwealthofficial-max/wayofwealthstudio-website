#!/usr/bin/env node
// Posts ONE approved native LinkedIn draft. Runs only after Joel taps "Approve and post" on the page Fred links to
// (netlify/functions/linkedin-draft.js dispatches linkedin-post-approved with the draft id, nothing else).
// The text is fetched from Netlify with FRED_SECRET and never printed: this repo and its Action logs are PUBLIC.
//
// ENV: DRAFT_ID, FRED_SECRET, LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN.

const SITE = 'https://wayofwealthcoaching.com';
const { DRAFT_ID: ID, FRED_SECRET, LINKEDIN_ACCESS_TOKEN: TOKEN, LINKEDIN_PERSON_URN: AUTHOR } = process.env;
if (!/^[0-9a-f]{16}$/.test(ID || '')) { console.error('FATAL: bad DRAFT_ID'); process.exit(1); }
if (!FRED_SECRET || !TOKEN || !AUTHOR) { console.error('FATAL: FRED_SECRET / LINKEDIN_ACCESS_TOKEN / LINKEDIN_PERSON_URN not set'); process.exit(1); }

async function main() {
  const f = await fetch(`${SITE}/api/linkedin/draft?action=fetch&id=${ID}`, { headers: { 'x-fred-secret': FRED_SECRET } });
  if (!f.ok) throw new Error(`Draft fetch ${f.status}`);
  const { text, status } = await f.json();
  if (status === 'posted') { console.log('Already posted. Nothing to do.'); return; }

  // Same version fallback as linkedin-share.mjs: LinkedIn retires API versions after about a year.
  const body = JSON.stringify({
    author: AUTHOR, commentary: text, visibility: 'PUBLIC',
    distribution: { feedDistribution: 'MAIN_FEED', targetEntities: [], thirdPartyDistributionChannels: [] },
    lifecycleState: 'PUBLISHED', isReshareDisabledByAuthor: false,
  });
  let r, version;
  for (let back = 1; back <= 12; back++) {
    const d = new Date(); d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() - back);
    version = `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
    r = await fetch('https://api.linkedin.com/rest/posts', {
      method: 'POST',
      headers: { authorization: `Bearer ${TOKEN}`, 'content-type': 'application/json', 'LinkedIn-Version': version, 'X-Restli-Protocol-Version': '2.0.0' },
      body,
    });
    if (r.status !== 426) break;
  }
  if (r.status !== 201) throw new Error(`LinkedIn API ${r.status} (version ${version}): ${(await r.text()).slice(0, 300)}`);
  const urn = r.headers.get('x-restli-id') || '';
  console.log(`Posted to LinkedIn (version ${version}): ${urn}`);

  const done = await fetch(`${SITE}/api/linkedin/draft?action=done&id=${ID}`, { method: 'POST', headers: { 'x-fred-secret': FRED_SECRET } });
  if (!done.ok) console.log(`Warning: posted, but could not mark the draft done (${done.status}).`);
  if (process.env.GITHUB_OUTPUT) {
    const { appendFile } = await import('node:fs/promises');
    await appendFile(process.env.GITHUB_OUTPUT, `url=https://www.linkedin.com/feed/update/${urn}/\n`);
  }
}

main().catch((e) => { console.error('FATAL:', e.message); process.exit(1); });
