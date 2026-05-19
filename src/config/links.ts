// Canonical site constants. Single source of truth.
// If you change a URL here it propagates to every component that imports LINKS.
export const LINKS = {
  siteUrl: 'https://thewayofwealth.shop',
  siteName: 'Way of Wealth',
  quiz: 'https://money-beliefs-quiz.netlify.app',
  etsy: 'https://www.etsy.com/shop/WayofWealthStudio',
  // Cheat sheet form (MailerLite embedded) — routes subscribers to main list + triggers Cheat Sheet Delivery automation
  cheatSheet: 'https://preview.mailerlite.io/forms/1977493/184455001091867806/share',
  // Finance Fridays newsletter form (separate MailerLite group, ID 185123527460914938)
  newsletter: 'https://preview.mailerlite.io/forms/1977493/185123534091060787/share',
  contactEmail: 'mailto:joel@thewayofwealth.shop',
  coaching: '/coaching',
  portalApplyApi: 'https://portal.thewayofwealth.shop/api/leads/submit',
  // Lead-magnet funnel pages
  budgetTracker: '/budget-tracker',
  budgetTrackerThanks: '/thanks/budget-tracker',
  // DM Sorcery post-booking confirmation (Calendly redirect target)
  booked: '/booked',
  // Lead-magnet form endpoint (Netlify function — see netlify/functions/lead-magnet-subscribe.js)
  leadMagnetApi: '/api/lead-magnet/subscribe',
  // Google Drive direct-download URL for the Budget Tracker PDF.
  // Replace <FILE_ID> with the real Drive file ID once Joel uploads.
  // Format: https://drive.google.com/uc?export=download&id=<FILE_ID>
  // Note: file MUST be shared as "Anyone with the link" → Viewer.
  budgetTrackerDownload: 'https://drive.google.com/uc?export=download&id=REPLACE_WITH_FILE_ID',
  // Legacy gmail kept intentionally for competitor funnel-hacking signups only.
  // Do NOT use for customer-facing contact or lead routing.
  funnelHackInbox: 'thewayofwealth.official@gmail.com',
} as const;
