// Competitor sender list for the funnel-hack digest.
// Source of truth: wow-intelligence-hub/data/funnel-hacks/email-intelligence/competitor-email-tracker.md
//
// Add a new competitor here when you sign up to their list.
// The digest queries Gmail for `from:` any of these emails (last 24h).

export const COMPETITOR_SENDERS = [
  // Original cohort (signed up 2026-04-04/05)
  { name: 'Mind Money Balance',         email: 'lindsay@mindmoneybalance.com' },
  { name: 'Beyond Your Budget',         email: 'breakyourbudget@substack.com' },
  { name: 'Clever Girl Finance',        email: 'info@clevergirlfinance.com' },
  { name: 'Denise Duffield-Thomas',     email: 'denisedt@c.kajabimail.net' },
  { name: 'Baddies & Budgets',          email: 'admin@baddiesandbudgets.com' },
  { name: 'The Finance Therapist',      email: 'Hello@thefinancetherapist.com' },
  { name: 'The Budget Mom',             email: 'notifications@tx.teachable.com' },

  // Added 2026-04-18 cohort
  { name: 'Ramit Sethi (IWT)',          email: 'ramit.sethi@iwillteachyoutoberich.com' },
  { name: 'Lewis Howes',                email: 'lewis@schoolofgreatness.com' },
  { name: 'Keina (Wealth Over Now)',    email: 'keina@wealthovernow.com' },
  { name: 'Bari Tessler',               email: 'support@baritessler.com' },
  { name: 'Sahil Bloom',                email: 'sahil@sahilbloom.com' },
  { name: 'Talia Loderick (Club TLC)',  email: 'hello@talialoderick.co.uk' },
];

// Build a Gmail search query that matches any email from the competitor list in the last N days.
// Also honors any email manually labeled Funnel-Hack, so the old behaviour still works as a supplement.
export function buildFunnelhackQuery({ days = 1 } = {}) {
  const fromClauses = COMPETITOR_SENDERS.map((c) => `from:${c.email}`).join(' OR ');
  // Parentheses group the OR list; then we OR that with the legacy label; final newer_than gates the whole thing.
  return `((${fromClauses}) OR label:Funnel-Hack) newer_than:${days}d`;
}
