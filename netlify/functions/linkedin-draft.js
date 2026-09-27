// Netlify function: /api/linkedin/draft
//
// Holds Joel's native LinkedIn drafts privately until he approves them (Joel, 2026-09-27: Fred sends each
// post for a one-tap Approve for the first 2 weeks). This repo and its Action logs are PUBLIC, so drafts
// live in Netlify Blobs, never in the repo or a log.
//
//   POST ?action=create            (x-fred-secret)  body {text, angle} -> {id, sig}. Called by scripts/linkedin-post.mjs.
//   GET  ?id=&sig=                                  Confirm page with an "Approve and post" button. A GET never
//                                                   posts, so Telegram's link previews can't approve by accident.
//   POST ?id=&sig= (form)                           Approve: dispatches linkedin-post-approved to GitHub with the id only.
//   GET  ?action=fetch&id=         (x-fred-secret)  -> {text}. Called by scripts/linkedin-publish.mjs.
//   POST ?action=done&id=          (x-fred-secret)  Marks the draft posted.
//
// Netlify env: FRED_SECRET, GITHUB_DISPATCH_PAT, GITHUB_REPO (same as fred-approve.js).

const crypto = require('crypto');
const { connectLambda, getStore } = require('@netlify/blobs');

const TTL_MS = 48 * 60 * 60 * 1000;
const { FRED_SECRET, GITHUB_DISPATCH_PAT, GITHUB_REPO } = process.env;

const sign = (id) => crypto.createHmac('sha256', FRED_SECRET).update(`linkedin:${id}`).digest('hex').slice(0, 24);
const same = (a, b) => { const x = Buffer.from(String(a || '')), y = Buffer.from(String(b || '')); return x.length === y.length && crypto.timingSafeEqual(x, y); };
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const json = (status, obj) => ({ statusCode: status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }, body: JSON.stringify(obj) });
const html = (status, body) => ({
  statusCode: status,
  headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' },
  body: `<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Fred</title><style>body{font-family:-apple-system,Segoe UI,sans-serif;max-width:32rem;margin:2rem auto;padding:0 1rem;color:#222;line-height:1.5}h1{font-size:1.25rem}pre{white-space:pre-wrap;font:inherit;background:#f6f4ef;padding:1rem;border-radius:8px}button{font-size:1.05rem;padding:.8rem 1.4rem;border:0;border-radius:8px;background:#1f3d2b;color:#fff;width:100%}</style>${body}`,
});

exports.handler = async (event) => {
  if (!FRED_SECRET || !GITHUB_DISPATCH_PAT || !GITHUB_REPO) return html(500, '<h1>Fred misconfigured</h1><p>Missing FRED_SECRET, GITHUB_DISPATCH_PAT or GITHUB_REPO on Netlify.</p>');
  connectLambda(event);
  const store = getStore('linkedin-drafts');
  const q = event.queryStringParameters || {};
  const robot = same(event.headers['x-fred-secret'], FRED_SECRET);

  // --- Robot calls (secret required) ---
  if (q.action) {
    if (!robot) return json(401, { error: 'unauthorised' });
    if (q.action === 'create' && event.httpMethod === 'POST') {
      const { text, angle, passage, problem, pursuit, payoff } = JSON.parse(event.body || '{}');
      if (!text || text.length > 3000) return json(400, { error: 'text missing or over 3000 characters' });
      const id = crypto.randomBytes(8).toString('hex');
      await store.setJSON(id, { text, angle, passage, problem, pursuit, payoff, createdAt: Date.now(), status: 'pending' });
      return json(200, { id, sig: sign(id) });
    }
    const d = q.id && (await store.get(q.id, { type: 'json' }));
    if (!d) return json(404, { error: 'not found' });
    if (q.action === 'fetch') return json(200, d);
    if (q.action === 'done' && event.httpMethod === 'POST') {
      await store.setJSON(q.id, { ...d, status: 'posted', postedAt: Date.now() });
      return json(200, { ok: true });
    }
    return json(400, { error: 'unknown action' });
  }

  // --- Joel's link ---
  if (!q.id || !same(q.sig, sign(q.id))) return html(400, '<h1>⛔ Link invalid</h1><p>Ask Fred for a new draft.</p>');
  const d = await store.get(q.id, { type: 'json' });
  if (!d) return html(404, '<h1>⛔ Draft not found</h1>');
  if (d.status === 'posted') return html(200, '<h1>✅ Already posted</h1><p>This one is on LinkedIn.</p>');
  if (d.status === 'approved') return html(200, '<h1>⏳ Already approved</h1><p>It is posting now. Fred will confirm.</p>');
  if (d.status === 'revising') return html(200, '<h1>✏️ Being rewritten</h1><p>Fred will send the new version. Use the link on that one.</p>');
  if (Date.now() - d.createdAt > TTL_MS) return html(410, '<h1>⌛ Expired</h1><p>Drafts last 48 hours. Nothing was posted.</p>');

  const dispatch = async (event_type) => {
    const r = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/dispatches`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${GITHUB_DISPATCH_PAT}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type, client_payload: { id: q.id } }),
    });
    return r.ok ? null : (await r.text()).slice(0, 200);
  };

  if (event.httpMethod === 'POST') {
    const form = new URLSearchParams(event.isBase64Encoded ? Buffer.from(event.body || '', 'base64').toString('utf8') : event.body || '');
    if (form.get('do') === 'revise') {
      const fix = String(form.get('fix') || '').trim();
      if (fix.length < 3) return html(400, '<h1>Write what needs fixing</h1><p>Go back and type it in the box.</p>');
      await store.setJSON(q.id, { ...d, status: 'revising', feedback: fix.slice(0, 2000), revisedAt: Date.now() });
      const err = await dispatch('linkedin-post-revise');
      if (err) { await store.setJSON(q.id, d); return html(502, `<h1>❌ Couldn't reach GitHub</h1><p>${esc(err)}</p><p>Nothing changed. Try again.</p>`); }
      return html(200, '<h1>✏️ Got it</h1><p>Rewriting with your fixes now. Fred will send the new version in a few minutes.</p>');
    }
    const err = await dispatch('linkedin-post-approved');
    if (err) return html(502, `<h1>❌ Couldn't reach GitHub</h1><p>${esc(err)}</p><p>Nothing was posted. Try again.</p>`);
    await store.setJSON(q.id, { ...d, status: 'approved', approvedAt: Date.now() });
    return html(200, '<h1>✅ Approved</h1><p>Posting to your LinkedIn now. Fred will confirm in a minute or two.</p>');
  }

  const action = `/api/linkedin/draft?id=${esc(q.id)}&sig=${esc(q.sig)}`;
  return html(200, `<h1>LinkedIn post, ready to go</h1><pre>${esc(d.text)}</pre>`
    + `<form method="POST" action="${action}"><input type="hidden" name="do" value="approve"><button type="submit">Approve and post</button></form>`
    + `<h1 style="margin-top:2rem">Or: what needs fixing?</h1><form method="POST" action="${action}"><input type="hidden" name="do" value="revise"><textarea name="fix" rows="5" style="width:100%;box-sizing:border-box;font:inherit;padding:.6rem;border-radius:8px;border:1px solid #ccc" placeholder="e.g. Cut the last line. Open on the moment I lost it. That bit about my clients isn't true."></textarea><button type="submit" style="margin-top:.6rem;background:#8a6d3b">Rewrite it</button></form>`
    + `<p style="color:#888;font-size:.85rem">Don't want it? Just ignore it. It expires in 48 hours and nothing is posted.</p>`);
};
