#!/usr/bin/env node
// Diagnostic for funnelhack-digest.mjs.
// When the digest says "no new emails" but you know emails are arriving, run this.
//
// Shows:
//   1. Whether a "Funnel-Hack" Gmail label exists (exact spelling + ID)
//   2. How many emails per competitor sender arrived in the last 24h (bypasses label filter)
//   3. What labels those emails currently have
//
// Run via GitHub Actions workflow_dispatch, or locally with the same env vars.

import { getAccessToken, listMessages, getMessageMetadata, parseSenderName } from './gmail-client.mjs';
import { COMPETITOR_SENDERS } from './funnelhack-senders.mjs';

const GMAIL_CLIENT_ID = process.env.GMAIL_CLIENT_ID;
const GMAIL_CLIENT_SECRET = process.env.GMAIL_CLIENT_SECRET;
const GMAIL_REFRESH_TOKEN = process.env.GMAIL_REFRESH_TOKEN;

if (!GMAIL_CLIENT_ID || !GMAIL_CLIENT_SECRET || !GMAIL_REFRESH_TOKEN) {
  console.error('FATAL: missing GMAIL_* env vars.');
  process.exit(1);
}

async function gmailFetch(path, accessToken, params = {}) {
  const url = new URL(`https://gmail.googleapis.com/gmail/v1${path}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } });
  if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`);
  return res.json();
}

async function main() {
  const accessToken = await getAccessToken({
    clientId: GMAIL_CLIENT_ID,
    clientSecret: GMAIL_CLIENT_SECRET,
    refreshToken: GMAIL_REFRESH_TOKEN,
  });

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('1. GMAIL LABELS — is "Funnel-Hack" configured?');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  const labelData = await gmailFetch('/users/me/labels', accessToken);
  const userLabels = (labelData.labels || []).filter((l) => l.type === 'user');
  const funnelMatches = userLabels.filter((l) => /funnel|hack/i.test(l.name));
  if (funnelMatches.length === 0) {
    console.log('  ✗ No label matching /funnel|hack/ found.');
    console.log('  → The old label-based flow is broken. The new sender-list flow will still work.');
  } else {
    console.log('  Found label(s):');
    for (const l of funnelMatches) console.log(`    • "${l.name}" (id: ${l.id})`);
  }
  console.log(`  Total user labels: ${userLabels.length}`);

  console.log('');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('2. COMPETITOR SENDERS — who sent emails in the last 24h?');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  let totalFound = 0;
  const labelMap = new Map((labelData.labels || []).map((l) => [l.id, l.name]));

  for (const { name, email } of COMPETITOR_SENDERS) {
    const refs = await listMessages({
      accessToken,
      query: `from:${email} newer_than:1d`,
      maxResults: 10,
    });
    if (refs.length === 0) {
      console.log(`  · ${name} <${email}> — 0 emails`);
      continue;
    }
    totalFound += refs.length;
    const messages = await Promise.all(
      refs.map((r) => getMessageMetadata({ accessToken, id: r.id }))
    );
    const labelsForThisSender = new Set();
    for (const m of messages) for (const id of m.labelIds || []) labelsForThisSender.add(id);
    const labelNames = [...labelsForThisSender]
      .map((id) => labelMap.get(id) || id)
      .filter((n) => !['INBOX', 'UNREAD', 'CATEGORY_PERSONAL', 'CATEGORY_UPDATES', 'CATEGORY_PROMOTIONS', 'IMPORTANT'].includes(n))
      .join(', ') || '(no user labels)';
    console.log(`  ✓ ${name} <${email}> — ${refs.length} email${refs.length === 1 ? '' : 's'}`);
    console.log(`      labels: ${labelNames}`);
    for (const m of messages.slice(0, 2)) {
      console.log(`      · "${m.subject}"`);
    }
  }

  console.log('');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`SUMMARY: ${totalFound} emails found across ${COMPETITOR_SENDERS.length} tracked senders in the last 24h.`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  if (totalFound === 0) {
    console.log('No competitor emails at all → check Gmail account you authenticated is the one receiving them.');
    console.log('If a new competitor sender isn\'t in the list, add it to scripts/funnelhack-senders.mjs.');
  }
}

main().catch((e) => {
  console.error('Diagnostic failed:', e);
  process.exit(1);
});
