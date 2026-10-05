// POST /api/session/booked   body: {"email": "..."}
//
// Called by /your-number when the Calendly box on the page says a booking was made (calendly.event_scheduled).
// Stops that person's booking reminders (session-reminder sequence) by marking their record done.
// Only acts on someone already enrolled, and only ever stops emails, so a stray call can't start anything.

const { connectLambda, getStore } = require('@netlify/blobs');

const json = (status, obj) => ({ statusCode: status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }, body: JSON.stringify(obj) });

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return json(405, { ok: false, error: 'POST only' });
  let body;
  try { body = JSON.parse(event.body || '{}'); } catch { return json(400, { ok: false, error: 'bad json' }); }
  const email = String(body.email || '').trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json(400, { ok: false, error: 'bad email' });

  connectLambda(event);
  // Strong reads: people often book within a minute of step 1, and the default (eventual) read can miss
  // that brand-new enrolment (seen in testing, 5 Oct).
  const store = getStore({ name: 'sequences', consistency: 'strong' });
  const key = `session-reminder/${email}`;
  const state = await store.get(key, { type: 'json' });
  if (!state) return json(200, { ok: true, note: 'not enrolled' });
  if (!state.done) await store.setJSON(key, { ...state, done: true, bookedAt: new Date().toISOString() });
  return json(200, { ok: true, stopped: true });
};
