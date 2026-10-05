// Booking reminders for people who gave their name and email in the /your-number booking box (step 1)
// but didn't book (5 Oct 2026). Booking on the page stops them (session-booked.js).
//
// HELD BACK until Joel approves the wording: enabled: false. People still enrol from day one.
//
// Shape: Ramit Sethi's cart-close emails (BIG_SENDERS_SEQUENCES.md §1 A and F): a recap of what they started
// and what happens next, then doubts answered as questions, then a last call with a P.S. (Ramit's is a
// "six months from now" choice; this one is a plain "no for now is fine", so no invented line).
// Words: Joel's approved lines only (Calendly description, /coaching FAQ, live cockpit pitch, money-reset emails).
// Timing (1h, 24h, 72h) is the usual abandoned-booking spacing, not from a source. Joel to confirm.
//
// afterHours = hours after they gave their email. The hourly runner sends 08:00-20:59 UK only.

const BOOK = 'https://wayofwealthcoaching.com/your-number/#book';

module.exports = {
  enabled: false,
  footerReason: 'you started booking a Cash Flow Session at wayofwealthcoaching.com',
  emails: [
    {
      id: '01-pick-a-time',
      afterHours: 1,
      subject: 'your Cash Flow Session',
      preheader: "You didn't pick a time. Here's the link.",
      body: `
Hey {{name}},

You started booking your Cash Flow Session, but it looks like you didn't pick a time.

**[Pick a time here](${BOOK})**.

75 minutes, live on screen. I build your cash flow model with you. We put your real numbers in, model different options, and see what each one actually looks like. Doing this, everything kind of falls into place.

You leave knowing your number: how much you actually need to earn, and what that means for your prices and your week.

Joel
MSc Behavioural Economics | Qualified Financial Planner

P.S. Any questions, hit reply. Your replies come straight to me.
`,
    },
    {
      id: '02-questions',
      afterHours: 24,
      subject: 'is this financial advice?',
      preheader: 'No. And two more answers before you book.',
      body: `
Hey {{name}},

**Is this financial advice?**
No. I'm a planner, not an adviser. I'm qualified but not FCA authorised. This session does not recommend any product, pension, investment, insurance or debt arrangement. Every figure is an illustration, not a forecast.

**I already have an accountant.**
Good. An accountant looks backwards to keep you legal. They don't tell you how much of today's invoice you can actually move to your own account. That's the gap we work on.

**I'm not in the UK.**
Yes, you can still book. Bring your own tax figures from your accountant. I don't give tax advice. The price is £179.99, and your bank converts it to your currency.

My promise: if you don't leave knowing your number, I'll refund you.

**[Pick a time for your session](${BOOK})**

Joel
MSc Behavioural Economics | Qualified Financial Planner
`,
    },
    {
      id: '03-last-one',
      afterHours: 72,
      subject: '5 places a week',
      preheader: 'Most of the people I work with earn decent money.',
      body: `
Hey {{name}},

Last one from me about this.

Most of the people I work with earn decent money but still end up counting down to payday. More revenue doesn't fix a leak. It scales it.

In the session you find out your number: how much you actually need to earn, and what that means for your prices and your week.

5 places a week. **[Pick a time here](${BOOK})**.

Joel
MSc Behavioural Economics | Qualified Financial Planner

P.S. And if now's not the time, that's completely fine.
`,
    },
  ],
};
