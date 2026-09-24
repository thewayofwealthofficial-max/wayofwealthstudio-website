// Hourly: sends each enrolled person the next email in their sequence when it is due.
// Schedule is set in netlify.toml. Sends only between 08:00 and 20:59 UK time.
// At most one email per person per run, and never closer together than the sequence allows.

const { connectLambda, getStore } = require('@netlify/blobs');
const core = require('./lib/sequence-core');
const { notifyCaptureFailed } = require('./lib/slack');

const HOUR = 3600e3;
const BUDGET_MS = 24e3; // scheduled functions get 30s

exports.handler = async (event) => {
  const started = Date.now();
  connectLambda(event);
  const store = getStore('sequences');
  const hour = core.ukHour();
  const report = { sent: 0, graduated: 0, skipped: 0, errors: [] };

  if (hour < 8 || hour > 20) return { statusCode: 200, body: JSON.stringify({ ...report, note: 'outside sending hours' }) };

  for (const [seqId, seq] of Object.entries(core.SEQUENCES)) {
    let contacts;
    try {
      contacts = await core.listContacts(await core.sequenceAudienceId(seqId));
    } catch (e) {
      report.errors.push(`${seqId}: ${e.message}`);
      continue;
    }
    for (const c of contacts) {
      if (Date.now() - started > BUDGET_MS) break;
      if (c.unsubscribed) continue;
      const key = `${seqId}/${c.email.toLowerCase()}`;
      const state = (await store.get(key, { type: 'json' })) || { sent: [] };
      if (state.done) continue;

      const next = seq.emails.find((e) => !state.sent.includes(e.id));
      try {
        if (!next) {
          // Finished: join the main list (never re-subscribing anyone who opted out there).
          const g = await core.getContact(core.GENERAL_AUDIENCE, c.email);
          if (!g) {
            await core.rs(`/audiences/${core.GENERAL_AUDIENCE}/contacts`, {
              method: 'POST',
              body: { email: c.email, first_name: c.first_name || undefined, unsubscribed: false },
            });
          }
          await store.setJSON(key, { ...state, done: true, graduatedAt: new Date().toISOString() });
          report.graduated++;
          continue;
        }

        const enrolledAt = core.parseResendDate(c.created_at);
        if (Date.now() < enrolledAt + next.afterHours * HOUR) { report.skipped++; continue; }

        // Spacing guard, so a missed run never bunches emails into the same day.
        const prev = seq.emails[seq.emails.indexOf(next) - 1];
        const plannedGap = prev ? next.afterHours - prev.afterHours : 0;
        const minGap = plannedGap >= 12 ? 18 : 3;
        if (state.lastSentAt && Date.now() - Date.parse(state.lastSentAt) < minGap * HOUR) { report.skipped++; continue; }

        await core.sendEmail({ to: c.email, email: next, firstName: c.first_name, footerReason: seq.footerReason, tagSeq: `${seqId}_${next.id}` });
        state.sent.push(next.id);
        state.lastSentAt = new Date().toISOString();
        await store.setJSON(key, state);
        report.sent++;
      } catch (e) {
        report.errors.push(`${c.email}: ${e.message.slice(0, 160)}`);
      }
    }
  }

  if (report.errors.length) {
    await notifyCaptureFailed({ email: '(sequence runner)', magnet: 'sequences', reason: `${report.errors.length} error(s)`, detail: report.errors.slice(0, 5).join(' | ') });
  }
  console.log('[sequence-runner]', JSON.stringify(report));
  return { statusCode: 200, body: JSON.stringify(report) };
};
