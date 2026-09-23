// Keeps the Resend audience in step with MailerLite, so the daily email only ever goes to people
// who are active and opted in. Rules:
//   - MailerLite ACTIVE and not in Resend            -> add to Resend (subscribed)
//   - MailerLite UNSUBSCRIBED / BOUNCED / JUNK       -> make sure Resend has them as UNSUBSCRIBED
//   - MailerLite UNCONFIRMED                          -> never added (no consent yet)
//   - Unsubscribed in Resend (they clicked the link)  -> never re-subscribed, and MailerLite is told
// So nobody who has opted out can ever be emailed again by either system.

import { listContacts, addContact, setUnsubscribed } from './resend.mjs';

const ML = 'https://connect.mailerlite.com/api';

async function fetchMailerLite(mlKey) {
  const out = [];
  let cursor = null;
  for (let page = 0; page < 100; page++) {
    const url = `${ML}/subscribers?limit=100${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`;
    const r = await fetch(url, { headers: { Authorization: `Bearer ${mlKey}`, Accept: 'application/json' } });
    if (!r.ok) throw new Error(`MailerLite subscribers failed: ${r.status} ${(await r.text()).slice(0, 200)}`);
    const j = await r.json();
    for (const s of j.data || []) {
      out.push({ email: String(s.email || '').trim().toLowerCase(), status: s.status, name: (s.fields && s.fields.name) || '' });
    }
    cursor = j.meta && j.meta.next_cursor;
    if (!cursor) break;
  }
  return out.filter((s) => s.email);
}

async function mailerLiteUnsubscribe(mlKey, email) {
  const r = await fetch(`${ML}/subscribers`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${mlKey}`, Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, status: 'unsubscribed' }),
  });
  if (!r.ok) throw new Error(`MailerLite unsubscribe failed for one contact: ${r.status}`);
}

export async function syncList({ mlKey, resendKey, audienceId, dry = false }) {
  const [ml, existing] = await Promise.all([fetchMailerLite(mlKey), listContacts(resendKey, audienceId)]);
  const inResend = new Map(existing.map((c) => [String(c.email).toLowerCase(), c]));
  const mlByEmail = new Map(ml.map((s) => [s.email, s]));
  const summary = { added: 0, markedUnsub: 0, unsubAddedAsUnsub: 0, mlUnsubscribed: 0, skippedUnconfirmed: 0, errors: 0 };

  for (const s of ml) {
    const have = inResend.get(s.email);
    const firstName = String(s.name || '').trim().split(/\s+/)[0] || undefined;
    try {
      if (s.status === 'active') {
        if (!have) {
          if (!dry) await addContact(resendKey, audienceId, { email: s.email, firstName });
          summary.added++;
        }
      } else if (['unsubscribed', 'bounced', 'junk'].includes(s.status)) {
        if (!have) {
          if (!dry) await addContact(resendKey, audienceId, { email: s.email, firstName, unsubscribed: true });
          summary.unsubAddedAsUnsub++;
        } else if (!have.unsubscribed) {
          if (!dry) await setUnsubscribed(resendKey, audienceId, have.id, true);
          summary.markedUnsub++;
        }
      } else {
        summary.skippedUnconfirmed++;
      }
    } catch (e) {
      summary.errors++;
      console.error('sync error (continuing):', e.message);
    }
  }

  // Anyone who opted out through Resend must also be opted out in MailerLite.
  for (const c of existing) {
    const email = String(c.email).toLowerCase();
    const m = mlByEmail.get(email);
    if (c.unsubscribed && m && m.status === 'active') {
      try {
        if (!dry) await mailerLiteUnsubscribe(mlKey, email);
        summary.mlUnsubscribed++;
      } catch (e) {
        summary.errors++;
        console.error('MailerLite unsubscribe error (continuing):', e.message);
      }
    }
  }

  const activeNow = ml.filter((s) => s.status === 'active' && !(inResend.get(s.email) || {}).unsubscribed).length;
  return { ...summary, mailerLiteTotal: ml.length, sendableAfterSync: activeNow };
}
