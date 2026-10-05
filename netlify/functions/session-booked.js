// POST /api/session/booked   body: {"email": "..."}
//
// Called by /your-number when the Calendly box on the page says a booking was made (calendly.event_scheduled).
// Leaves a note (Blobs "sequences", key session-booked/<email>). The hourly runner checks it before every
// booking reminder and ends that person's reminders. Write-only on purpose: people often book within a minute
// of step 1, and a read here could miss their brand-new enrolment (Blobs reads are eventually consistent).
// It only ever stops emails, so a stray call can't start anything.

const { connectLambda, getStore } = require('@netlify/blobs');

const json = (status, obj) => ({ statusCode: status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }, body: JSON.stringify(obj) });

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return json(405, { ok: false, error: 'POST only' });
  let body;
  try { body = JSON.parse(event.body || '{}'); } catch { return json(400, { ok: false, error: 'bad json' }); }
  const email = String(body.email || '').trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json(400, { ok: false, error: 'bad email' });

  connectLambda(event);
  await getStore('sequences').setJSON(`session-booked/${email}`, { at: new Date().toISOString() });
  return json(200, { ok: true });
};
