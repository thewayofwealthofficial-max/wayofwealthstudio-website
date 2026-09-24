// Sends every email in a sequence to one address right now, marked [TEST n/N], so Joel can read the whole thing.
// Does not enrol anyone or touch any list.
//
// Usage (from wow-website):
//   RESEND_API_KEY=... UNSUBSCRIBE_SECRET=... node scripts/sequences/send-test.mjs welcome-newsletter joeleezekiel@gmail.com [FirstName]

import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const core = require('../../netlify/functions/lib/sequence-core.js');

const [seqId, to, firstName = 'Joel'] = process.argv.slice(2);
const seq = core.SEQUENCES[seqId];
if (!seq || !to) {
  console.error(`Usage: node scripts/sequences/send-test.mjs <${Object.keys(core.SEQUENCES).join('|')}> <email> [firstName]`);
  process.exit(1);
}

const n = seq.emails.length;
for (const [i, email] of seq.emails.entries()) {
  const tagged = { ...email, subject: `[TEST ${i + 1}/${n} · after ${email.afterHours}h] ${email.subject}` };
  const id = await core.sendEmail({ to, email: tagged, firstName, footerReason: seq.footerReason, tagSeq: `test_${seqId}` });
  console.log(`sent ${i + 1}/${n}  ${email.id}  -> ${id}`);
}
