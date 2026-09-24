// Unsubscribe link for sequence emails.
// GET shows a confirm button (so link scanners that open every URL can't unsubscribe people).
// POST does it, which is also what Gmail's one-click "Unsubscribe" sends.
// Marks the person unsubscribed on the main list and in every sequence, and stops their sequence.

const { timingSafeEqual } = require('node:crypto');
const { connectLambda, getStore } = require('@netlify/blobs');
const core = require('./lib/sequence-core');

function page(title, body) {
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
    body: `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${title}</title></head>
<body style="margin:0;background:#F5F0E8;font-family:Georgia,serif;color:#1C2A3A;">
<div style="max-width:480px;margin:15vh auto;padding:0 20px;text-align:center;">
<h1 style="font-weight:400;font-size:28px;">${title}</h1>${body}
</div></body></html>`,
  };
}

function valid(email, token) {
  if (!email || !token) return false;
  const want = Buffer.from(core.unsubToken(email));
  const got = Buffer.from(String(token));
  return want.length === got.length && timingSafeEqual(want, got);
}

exports.handler = async (event) => {
  const params = new URLSearchParams(event.rawQuery || '');
  const email = (params.get('e') || '').trim().toLowerCase();
  const token = params.get('t') || '';
  if (!valid(email, token)) return page('That link didn’t work', '<p>Please reply to any email and I’ll take you off by hand.</p>');

  if (event.httpMethod === 'GET') {
    return page('Unsubscribe?', `<p>This stops all emails from Way of Wealth to <strong>${email.replace(/</g, '&lt;')}</strong>.</p>
<form method="POST"><button type="submit" style="margin-top:12px;padding:12px 24px;font-size:16px;background:#1C2A3A;color:#F5F0E8;border:0;border-radius:6px;cursor:pointer;">Yes, unsubscribe me</button></form>`);
  }
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'Method not allowed' };

  connectLambda(event);
  const store = getStore('sequences');
  const problems = [];

  // Main list: mark unsubscribed, or add as unsubscribed so no form ever re-adds them.
  const g = await core.getContact(core.GENERAL_AUDIENCE, email);
  const main = g
    ? await core.rs(`/audiences/${core.GENERAL_AUDIENCE}/contacts/${encodeURIComponent(email)}`, { method: 'PATCH', body: { unsubscribed: true } })
    : await core.rs(`/audiences/${core.GENERAL_AUDIENCE}/contacts`, { method: 'POST', body: { email, unsubscribed: true } });
  if (!main.ok) problems.push(`main ${main.status}`);

  for (const seqId of Object.keys(core.SEQUENCES)) {
    const aud = await core.sequenceAudienceId(seqId);
    if (await core.getContact(aud, email)) {
      const r = await core.rs(`/audiences/${aud}/contacts/${encodeURIComponent(email)}`, { method: 'PATCH', body: { unsubscribed: true } });
      if (!r.ok) problems.push(`${seqId} ${r.status}`);
    }
    const key = `${seqId}/${email}`;
    const state = await store.get(key, { type: 'json' });
    if (state) await store.setJSON(key, { ...state, done: true, unsubscribedAt: new Date().toISOString() });
  }

  if (problems.length) {
    console.error('[unsubscribe] partial failure', email, problems.join(', '));
    return page('Something went wrong', '<p>Please reply to any email and I’ll take you off by hand. Sorry about that.</p>');
  }
  return page('You’re unsubscribed', '<p>You won’t get any more emails from me. Thanks for reading while you did.</p><p>Joel</p>');
};
