// Minimal Gmail API client. Exchanges refresh token for access token, then lists + fetches messages.
// Used by funnelhack-digest.mjs.

export async function getAccessToken({ clientId, clientSecret, refreshToken }) {
  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: 'refresh_token',
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Token refresh failed: ${res.status} ${text}`);
  }
  const { access_token } = await res.json();
  if (!access_token) throw new Error('No access_token in refresh response');
  return access_token;
}

async function gmailFetch(path, accessToken, params = {}) {
  const url = new URL(`https://gmail.googleapis.com/gmail/v1${path}`);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, item);
    else url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Gmail API ${path} failed: ${res.status} ${text}`);
  }
  return res.json();
}

// List messages matching a Gmail search query (e.g. `label:funnel-hack newer_than:1d`).
export async function listMessages({ accessToken, query, maxResults = 50 }) {
  const data = await gmailFetch('/users/me/messages', accessToken, {
    q: query,
    maxResults,
  });
  return data.messages ?? [];
}

// Fetch a message with From / Subject / Date headers + snippet.
export async function getMessageMetadata({ accessToken, id }) {
  const data = await gmailFetch(`/users/me/messages/${id}`, accessToken, {
    format: 'metadata',
    metadataHeaders: ['From', 'Subject', 'Date'],
  });
  const headers = data.payload?.headers ?? [];
  const h = (name) => headers.find((x) => x.name.toLowerCase() === name.toLowerCase())?.value ?? '';
  return {
    id: data.id,
    from: h('From'),
    subject: h('Subject'),
    date: h('Date'),
    snippet: data.snippet ?? '',
    labelIds: data.labelIds ?? [],
  };
}

// Convenience: list + fetch metadata for all matches.
export async function fetchDigest({ clientId, clientSecret, refreshToken, query }) {
  const accessToken = await getAccessToken({ clientId, clientSecret, refreshToken });
  const refs = await listMessages({ accessToken, query });
  const messages = await Promise.all(
    refs.map((r) => getMessageMetadata({ accessToken, id: r.id }))
  );
  // Sort newest first by Date header (falls back to original order on parse failure)
  messages.sort((a, b) => {
    const da = Date.parse(a.date) || 0;
    const db = Date.parse(b.date) || 0;
    return db - da;
  });
  return messages;
}

// Parse "Name <email@example.com>" into its display name (or return the raw email if no name).
export function parseSenderName(fromHeader) {
  if (!fromHeader) return '(unknown)';
  const match = fromHeader.match(/^(.*?)\s*<.*>$/);
  if (match && match[1]) return match[1].replace(/^"|"$/g, '').trim();
  return fromHeader.trim();
}

// --- Full-body fetch (used by the daily-email pipeline to read competitor copy) ---

function b64urlDecode(data) {
  try {
    return Buffer.from(String(data).replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8');
  } catch {
    return '';
  }
}

function stripHtml(html) {
  return html
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&[a-z]+;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

// Walk a Gmail payload tree, preferring text/plain, falling back to stripped text/html.
function extractText(payload) {
  if (!payload) return '';
  if (payload.mimeType === 'text/plain' && payload.body?.data) return b64urlDecode(payload.body.data);
  if (payload.mimeType === 'text/html' && payload.body?.data) return stripHtml(b64urlDecode(payload.body.data));
  let plain = '';
  let html = '';
  for (const p of payload.parts || []) {
    const t = extractText(p);
    if (!t) continue;
    if (p.mimeType === 'text/plain' && !plain) plain = t;
    else if (p.mimeType === 'text/html' && !html) html = t;
    else if (!plain && !html) plain = t;
  }
  return plain || html || '';
}

// Fetch one message with its decoded text body (capped at maxChars).
export async function getMessageFull({ accessToken, id, maxChars = 4000 }) {
  const data = await gmailFetch(`/users/me/messages/${id}`, accessToken, { format: 'full' });
  const headers = data.payload?.headers ?? [];
  const h = (name) => headers.find((x) => x.name.toLowerCase() === name.toLowerCase())?.value ?? '';
  let body = extractText(data.payload);
  if (body.length > maxChars) body = body.slice(0, maxChars) + '…';
  return { id: data.id, from: h('From'), subject: h('Subject'), date: h('Date'), snippet: data.snippet ?? '', body };
}

// List + fetch full bodies for a query (capped). Individual fetch failures are skipped.
export async function fetchCompetitorEmails({ clientId, clientSecret, refreshToken, query, maxBodies = 25 }) {
  const accessToken = await getAccessToken({ clientId, clientSecret, refreshToken });
  const refs = await listMessages({ accessToken, query });
  const messages = [];
  for (const r of refs.slice(0, maxBodies)) {
    try {
      messages.push(await getMessageFull({ accessToken, id: r.id }));
    } catch {
      /* skip individual message failures */
    }
  }
  messages.sort((a, b) => (Date.parse(b.date) || 0) - (Date.parse(a.date) || 0));
  return messages;
}
