// Netlify function: GET /api/fred/approve?id=<signed_id>&slug=<short_id>
//
// Verifies the HMAC-signed approve token, looks up the proposal in
// .github/state/fred-proposals.json (fetched from GitHub raw), and if
// valid + not expired (<24h) triggers a repository_dispatch event that
// runs .github/workflows/fred-apply.yml.
//
// The dispatch carries the full proposal in client_payload.proposal.
//
// Pure Netlify Function (exports.handler) so the Astro site stays SSG.
//
// Routing: the Netlify redirect in netlify.toml maps
//   /api/fred/approve  →  /.netlify/functions/fred-approve
//
// Required Netlify env vars (set in Site settings → Environment variables):
//   FRED_SECRET          — same HMAC secret as the GitHub secret
//   GITHUB_DISPATCH_PAT  — PAT with `repo` scope (for dispatch call)
//   GITHUB_REPO          — "owner/name" of the wayofwealthstudio-website repo
//
// Token format:
//   signed_id = `${hmac16}.${created_at_ms}`
//   where hmac16 = HMAC-SHA256(FRED_SECRET, `${slug}:${created_at_ms}`).slice(0,16)

const crypto = require('crypto');

const TTL_MS = 24 * 60 * 60 * 1000; // 24h

const {
  FRED_SECRET,
  GITHUB_DISPATCH_PAT,
  GITHUB_REPO,
} = process.env;

function html(status, body) {
  return {
    statusCode: status,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
    body: `<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fred</title><style>body{font-family:-apple-system,Segoe UI,sans-serif;max-width:28rem;margin:4rem auto;padding:0 1rem;color:#222;line-height:1.5}h1{font-size:1.25rem;margin-bottom:.5rem}p{margin:.5rem 0}</style>${body}`,
  };
}

function invalidPage(reason) {
  return html(400, `<h1>⛔ Token invalid or expired</h1><p>Ask Fred to regenerate.</p><p style="color:#888;font-size:.85rem">${escapeHtml(reason)}</p>`);
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function verifySignedId(signedId, slug) {
  if (!signedId || typeof signedId !== 'string') return { ok: false, reason: 'no id' };
  const [mac, createdStr] = signedId.split('.');
  if (!mac || !createdStr) return { ok: false, reason: 'bad format' };
  const createdAt = Number(createdStr);
  if (!Number.isFinite(createdAt)) return { ok: false, reason: 'bad timestamp' };
  if (Date.now() - createdAt > TTL_MS) return { ok: false, reason: 'expired' };

  const expected = crypto
    .createHmac('sha256', FRED_SECRET)
    .update(`${slug}:${createdAt}`)
    .digest('hex')
    .slice(0, 16);

  // Timing-safe compare.
  const a = Buffer.from(mac);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return { ok: false, reason: 'sig mismatch' };
  if (!crypto.timingSafeEqual(a, b)) return { ok: false, reason: 'sig mismatch' };
  return { ok: true, createdAt };
}

async function fetchStateFile() {
  // Pull the current state file straight from the default branch raw URL.
  // Auth via PAT so the call works on private repos too.
  const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/.github/state/fred-proposals.json`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${GITHUB_DISPATCH_PAT}`,
      Accept: 'application/vnd.github.raw',
      'X-GitHub-Api-Version': '2022-11-28',
    },
  });
  if (!res.ok) throw new Error(`state fetch ${res.status}`);
  return res.json();
}

async function dispatchApply(proposal) {
  const url = `https://api.github.com/repos/${GITHUB_REPO}/dispatches`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${GITHUB_DISPATCH_PAT}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_type: 'fred-apply',
      client_payload: { proposal },
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`dispatch ${res.status}: ${text.slice(0, 200)}`);
  }
}

exports.handler = async (event) => {
  if (!FRED_SECRET || !GITHUB_DISPATCH_PAT || !GITHUB_REPO) {
    return html(500, `<h1>Fred misconfigured</h1><p>Missing Netlify env var. Joel needs to set FRED_SECRET, GITHUB_DISPATCH_PAT, GITHUB_REPO.</p>`);
  }

  const params = event.queryStringParameters || {};
  const signedId = params.id;
  const slug = params.slug;

  if (!signedId || !slug) {
    return invalidPage('id or slug missing');
  }

  const verified = verifySignedId(signedId, slug);
  if (!verified.ok) {
    return invalidPage(verified.reason);
  }

  let state;
  try {
    state = await fetchStateFile();
  } catch (err) {
    return html(502, `<h1>Couldn't reach GitHub</h1><p>${escapeHtml(err.message)}</p>`);
  }

  const proposal = (state.proposals || []).find((p) => p.id === slug && p.signed_id === signedId);
  if (!proposal) {
    return invalidPage('proposal not found (already applied, or a newer batch replaced it)');
  }

  const age = Date.now() - (proposal.created_at ?? verified.createdAt);
  if (age > TTL_MS) {
    return invalidPage('expired');
  }

  try {
    await dispatchApply(proposal);
  } catch (err) {
    return html(502, `<h1>Dispatch failed</h1><p>${escapeHtml(err.message)}</p>`);
  }

  return html(200, `<h1>✅ Approved</h1><p>Fred is applying the change. You'll get a Telegram confirmation when it's live.</p><p style="color:#888;font-size:.85rem">Proposal: <code>${escapeHtml(slug)}</code></p>`);
};
