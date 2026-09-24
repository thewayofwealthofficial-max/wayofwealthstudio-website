// Saves every competitor email (full HTML + plain text + headers) to OUT_DIR, one folder per email.
// Also writes a tally of every sender in the inbox, so competitors missing from the list can be spotted.
// Run in GitHub Actions (the Gmail token only lives there); the folder is uploaded as an artifact.

import fs from 'node:fs';
import path from 'node:path';
import { getAccessToken } from './gmail-client.mjs';
import { COMPETITOR_SENDERS } from './funnelhack-senders.mjs';

const OUT = process.env.OUT_DIR || 'competitor-emails';
const token = await getAccessToken({
  clientId: process.env.GMAIL_CLIENT_ID,
  clientSecret: process.env.GMAIL_CLIENT_SECRET,
  refreshToken: process.env.GMAIL_REFRESH_TOKEN,
});

async function gmail(p, params = {}) {
  const url = new URL(`https://gmail.googleapis.com/gmail/v1/users/me${p}`);
  for (const [k, v] of Object.entries(params)) if (v != null) url.searchParams.set(k, v);
  for (let attempt = 0; attempt < 4; attempt++) {
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) return res.json();
    if (res.status === 429 || res.status >= 500) { await new Promise((r) => setTimeout(r, 1500 * (attempt + 1))); continue; }
    throw new Error(`Gmail ${p} ${res.status} ${await res.text()}`);
  }
  throw new Error(`Gmail ${p} kept failing`);
}

async function listAll(q) {
  const ids = [];
  let pageToken;
  do {
    const d = await gmail('/messages', { q, maxResults: 500, pageToken });
    ids.push(...(d.messages || []).map((m) => m.id));
    pageToken = d.nextPageToken;
  } while (pageToken);
  return ids;
}

const decode = (s) => Buffer.from(String(s).replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8');
function parts(payload, out = { html: '', text: '' }) {
  if (!payload) return out;
  if (payload.body?.data) {
    if (payload.mimeType === 'text/html' && !out.html) out.html = decode(payload.body.data);
    if (payload.mimeType === 'text/plain' && !out.text) out.text = decode(payload.body.data);
  }
  for (const p of payload.parts || []) parts(p, out);
  return out;
}
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'x';

// 1) Competitor emails, all time.
const fromQ = COMPETITOR_SENDERS.map((c) => `from:${c.email}`).join(' OR ');
const ids = [...new Set([...(await listAll(`(${fromQ}) in:anywhere`)), ...(await listAll('label:Funnel-Hack in:anywhere'))])];
console.log(`Competitor emails found: ${ids.length}`);

const index = [];
let n = 0;
for (const id of ids) {
  try {
    const m = await gmail(`/messages/${id}`, { format: 'full' });
    const hs = m.payload?.headers || [];
    const h = (k) => hs.find((x) => x.name.toLowerCase() === k)?.value || '';
    const from = h('from');
    const email = (from.match(/<([^>]+)>/)?.[1] || from).toLowerCase().trim();
    const known = COMPETITOR_SENDERS.find((c) => c.email.toLowerCase() === email);
    const sender = known ? known.name : from.replace(/<.*>/, '').replace(/"/g, '').trim() || email;
    const date = new Date(Number(m.internalDate)).toISOString();
    const { html, text } = parts(m.payload);
    const dir = path.join(OUT, slug(sender), `${date.slice(0, 10)}_${id}`);
    fs.mkdirSync(dir, { recursive: true });
    const meta = { id, threadId: m.threadId, sender, from, email, date, subject: h('subject'), preheaderSnippet: m.snippet, listUnsubscribe: h('list-unsubscribe'), hasHtml: !!html };
    fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify(meta, null, 2));
    if (html) fs.writeFileSync(path.join(dir, 'email.html'), html);
    if (text) fs.writeFileSync(path.join(dir, 'email.txt'), text);
    index.push({ ...meta, dir: path.relative(OUT, dir).replace(/\\/g, '/') });
    if (++n % 25 === 0) console.log(`  saved ${n}/${ids.length}`);
  } catch (e) {
    console.log(`  skip ${id}: ${e.message.slice(0, 120)}`);
  }
}
index.sort((a, b) => a.sender.localeCompare(b.sender) || a.date.localeCompare(b.date));
fs.writeFileSync(path.join(OUT, 'index.json'), JSON.stringify(index, null, 2));

// 2) Sender tally for the last 180 days, to spot competitors not on the list.
const tally = {};
let pageToken, scanned = 0;
do {
  const d = await gmail('/messages', { q: 'newer_than:180d -in:sent -in:chats', maxResults: 500, pageToken });
  for (const r of d.messages || []) {
    const m = await gmail(`/messages/${r.id}`, { format: 'metadata', metadataHeaders: 'From' });
    const f = m.payload?.headers?.find((x) => x.name === 'From')?.value || '?';
    tally[f] = (tally[f] || 0) + 1;
    scanned++;
  }
  pageToken = d.nextPageToken;
} while (pageToken && scanned < 3000);
const sorted = Object.entries(tally).sort((a, b) => b[1] - a[1]).map(([from, count]) => ({ from, count }));
fs.writeFileSync(path.join(OUT, 'all-senders-180d.json'), JSON.stringify(sorted, null, 2));

const bySender = index.reduce((a, x) => ((a[x.sender] = (a[x.sender] || 0) + 1), a), {});
console.log('Saved per competitor:', JSON.stringify(bySender, null, 1));
console.log(`Inbox senders scanned: ${scanned}, distinct: ${sorted.length}`);
