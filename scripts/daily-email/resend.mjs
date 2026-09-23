// Minimal Resend client for the daily email. Used for the email list ONLY.
// Resend allows about 2 requests a second, so every call is spaced out and retried on 429.

const BASE = 'https://api.resend.com';
const GAP_MS = 650;
let last = 0;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function rs(apiKey, path, { method = 'GET', body } = {}) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const wait = last + GAP_MS - Date.now();
    if (wait > 0) await sleep(wait);
    last = Date.now();
    const res = await fetch(BASE + path, {
      method,
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 429) {
      await sleep(1500 * (attempt + 1));
      continue;
    }
    const text = await res.text();
    let json = null;
    try { json = text ? JSON.parse(text) : null; } catch { /* leave null */ }
    if (!res.ok) throw new Error(`Resend ${method} ${path} failed: ${res.status} ${text.slice(0, 300)}`);
    return json;
  }
  throw new Error(`Resend ${method} ${path} still rate limited after retries`);
}

export async function findOrCreateAudience(apiKey, name) {
  const list = await rs(apiKey, '/audiences');
  const hit = (list.data || []).find((a) => a.name.toLowerCase() === name.toLowerCase());
  if (hit) return hit.id;
  const made = await rs(apiKey, '/audiences', { method: 'POST', body: { name } });
  return made.id;
}

export async function listContacts(apiKey, audienceId) {
  const out = [];
  let after = null;
  for (let page = 0; page < 50; page++) {
    const q = `?limit=100${after ? `&after=${after}` : ''}`;
    const j = await rs(apiKey, `/audiences/${audienceId}/contacts${q}`);
    const rows = j.data || [];
    out.push(...rows);
    if (!j.has_more || !rows.length) break;
    after = rows[rows.length - 1].id;
  }
  return out;
}

export function addContact(apiKey, audienceId, { email, firstName, unsubscribed = false }) {
  return rs(apiKey, `/audiences/${audienceId}/contacts`, {
    method: 'POST',
    body: { email, first_name: firstName || undefined, unsubscribed },
  });
}

export function setUnsubscribed(apiKey, audienceId, idOrEmail, unsubscribed = true) {
  return rs(apiKey, `/audiences/${audienceId}/contacts/${encodeURIComponent(idOrEmail)}`, {
    method: 'PATCH',
    body: { unsubscribed },
  });
}

export async function listBroadcasts(apiKey) {
  const j = await rs(apiKey, '/broadcasts');
  return j.data || [];
}

export async function createBroadcast(apiKey, { audienceId, from, replyTo, subject, previewText, html, text, name }) {
  const j = await rs(apiKey, '/broadcasts', {
    method: 'POST',
    body: { audience_id: audienceId, from, reply_to: replyTo, subject, preview_text: previewText || undefined, html, text, name },
  });
  return j.id;
}

export function sendBroadcast(apiKey, id) {
  return rs(apiKey, `/broadcasts/${id}/send`, { method: 'POST', body: {} });
}
