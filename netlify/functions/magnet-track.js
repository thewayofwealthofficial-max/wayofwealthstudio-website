// Receives one step from a free tool (sendBeacon from /reset and from discover.thewayofwealth.shop).
//   POST /api/magnet/track   body: {"t":"reset","s":"opened","v":"<visitor id>"}   (text/plain, so no CORS preflight)
//                            'opened' may also carry "src" (the ?src= tag on the link) and "r" (the referrer's host).
//   GET  /api/magnet/track?report=1  with x-fred-secret: sends today's round-up now (for testing).
// Pings Joel on Telegram straight away for the steps in PING; the rest wait for magnet-report.js at 20:00 UK.
//
// Netlify env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FRED_SECRET.

const crypto = require('crypto');
const { connectLambda, getStore } = require('@netlify/blobs');
const { PING, isStep, ukDate, telegram, rollup, counts, fromLabel } = require('./lib/magnet-events');

const ORIGINS = new Set(['https://wayofwealthcoaching.com', 'https://www.wayofwealthcoaching.com', 'https://discover.thewayofwealth.shop']);

const same = (a, b) => typeof a === 'string' && typeof b === 'string' && a.length === b.length && crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));

exports.handler = async (event) => {
  const origin = event.headers.origin || '';
  const headers = { 'Cache-Control': 'no-store', ...(ORIGINS.has(origin) ? { 'Access-Control-Allow-Origin': origin, Vary: 'Origin' } : {}) };
  connectLambda(event);
  const store = getStore('magnet-events');

  if (event.httpMethod === 'GET' && event.queryStringParameters?.report) {
    if (!same(event.headers['x-fred-secret'], process.env.FRED_SECRET)) return { statusCode: 401, headers, body: 'unauthorised' };
    await telegram(await rollup(store, ukDate()));
    return { statusCode: 200, headers, body: 'sent' };
  }
  // GET /api/magnet/track?counts=YYYY-MM-DD with x-fred-secret: that day's numbers as JSON (for the morning brief).
  if (event.httpMethod === 'GET' && event.queryStringParameters?.counts) {
    if (!same(event.headers['x-fred-secret'], process.env.FRED_SECRET)) return { statusCode: 401, headers, body: 'unauthorised' };
    const day = event.queryStringParameters.counts;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return { statusCode: 400, headers, body: 'bad date' };
    return { statusCode: 200, headers: { ...headers, 'Content-Type': 'application/json' }, body: JSON.stringify(await counts(store, day)) };
  }
  if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: '' };

  let b;
  try {
    const raw = event.isBase64Encoded ? Buffer.from(event.body || '', 'base64').toString('utf8') : event.body || '';
    if (raw.length > 300) return { statusCode: 413, headers, body: '' };
    b = JSON.parse(raw);
  } catch {
    return { statusCode: 400, headers, body: '' };
  }
  const { t, s, v } = b || {};
  if (!isStep(t, s) || typeof v !== 'string' || !/^[a-z0-9]{8,32}$/.test(v)) return { statusCode: 400, headers, body: '' };

  // Where they came from (7 Oct 2026): sent with 'opened' only. The ?src= tag on the link wins, else the site
  // they clicked from, else 'direct'. Stored as its own key so the round-up can read it from the list alone.
  if (s === 'opened') {
    await store.setJSON(`${ukDate()}/${t}/${v}/from/${fromLabel(b.src, b.r)}`, { at: Date.now() });
  }

  const key = `${ukDate()}/${t}/${v}/${s}`;
  const already = PING[s] ? await store.get(key) : null; // only ping once per person per step per day
  await store.setJSON(key, { at: Date.now() });
  if (PING[s] && already === null) {
    try { await telegram(PING[s](t)); } catch (e) { console.error('magnet ping:', e.message); }
  }
  return { statusCode: 204, headers, body: '' };
};
