#!/usr/bin/env node
// Copies the MailerLite list into the Resend audience (see sync-list.mjs for the rules).
//   node scripts/daily-email/run-sync.mjs --dry     show what would change, change nothing
//   node scripts/daily-email/run-sync.mjs           do it
// Env: RESEND_API_KEY, MAILERLITE_API_KEY. Optional: RESEND_AUDIENCE_NAME (default "General").

import { findOrCreateAudience } from './resend.mjs';
import { syncList } from './sync-list.mjs';

const dry = process.argv.includes('--dry');
const resendKey = process.env.RESEND_API_KEY;
const mlKey = process.env.MAILERLITE_API_KEY;
if (!resendKey || !mlKey) {
  console.error('FATAL: RESEND_API_KEY and MAILERLITE_API_KEY are both required.');
  process.exit(1);
}

const audienceId = await findOrCreateAudience(resendKey, process.env.RESEND_AUDIENCE_NAME || 'General');
console.log(`${dry ? 'DRY RUN' : 'LIVE'} sync into Resend audience ${audienceId}`);
const result = await syncList({ mlKey, resendKey, audienceId, dry });
console.log(JSON.stringify(result, null, 2));
