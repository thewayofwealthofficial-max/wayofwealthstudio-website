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
