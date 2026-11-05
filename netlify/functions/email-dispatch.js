// Starts the list emails on time. GitHub runs scheduled jobs 2 to 5.5 hours late (audit, 27 Sep), so the
// "13:40 UK" email was landing around 18:00. Netlify's scheduler is punctual, so this runs at :55 every hour
// and, at the right UK hour, tells GitHub to run the "List Emails" workflow now.
//   Tue  07:55 UK   ·   Thu  07:55 UK   (UK time, so it follows the clock change by itself; lands ~8:00)
//   2 Nov 2026: Sun 13:40 and Fri 07:40 only (Joel: 2 emails a week).
//   5 Nov 2026: Tue and Thu ~8:00 (Joel).
// The GitHub cron stays as a backup; send-daily.mjs refuses to send twice on the same day.
//
// Netlify env: GITHUB_DISPATCH_PAT, GITHUB_REPO (same as fred-approve.js).

exports.handler = async () => {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/London', weekday: 'short', hour: '2-digit', hour12: false })
      .formatToParts(new Date()).map((p) => [p.type, p.value]),
  );
  const day = parts.weekday, hour = Number(parts.hour);
  const due = (day === 'Tue' || day === 'Thu') && hour === 7;
  if (!due) return { statusCode: 200, body: `not due (${day} ${hour}:55 UK)` };

  const { GITHUB_DISPATCH_PAT, GITHUB_REPO } = process.env;
  const r = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/dispatches`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${GITHUB_DISPATCH_PAT}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_type: 'daily-email' }),
  });
  if (!r.ok) {
    console.error(`GitHub dispatch failed ${r.status}: ${(await r.text()).slice(0, 200)}`);
    return { statusCode: 500, body: 'dispatch failed; the GitHub cron will still run later as a backup' };
  }
  return { statusCode: 200, body: `dispatched (${day} ${hour}:55 UK)` };
};
