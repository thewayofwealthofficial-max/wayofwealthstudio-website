// POST /api/sequence/booked   (header x-fred-secret)   body { email, booked: true | false }
//
// Called by the Money Story Diagnostic's Calendly webhook. While someone has a call booked, their diagnostic
// email series pauses (sequence-runner.js checks `booked/${email}`); if they cancel, it picks up again.
// This replaces MailerLite's "call_booked = yes" checks (28 Sep 2026).

const crypto = require('crypto');
const { connectLambda, getStore } = require('@netlify/blobs');

const same = (a, b) => { const x = Buffer.from(String(a || '')), y = Buffer.from(String(b || '')); return x.length === y.length && crypto.timingSafeEqual(x, y); };
const json = (status, obj) => ({ statusCode: status, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(obj) });

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return json(405, { error: 'POST only' });
  if (!process.env.FRED_SECRET || !same(event.headers['x-fred-secret'], process.env.FRED_SECRET)) return json(401, { error: 'unauthorised' });
  let body;
  try { body = JSON.parse(event.body || '{}'); } catch { return json(400, { error: 'bad json' }); }
  const email = String(body.email || '').trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json(400, { error: 'bad email' });
  connectLambda(event);
  const store = getStore('sequences');
  if (body.booked === false) await store.delete(`booked/${email}`);
  else await store.setJSON(`booked/${email}`, { at: new Date().toISOString() });
  return json(200, { ok: true, booked: body.booked !== false });
};
