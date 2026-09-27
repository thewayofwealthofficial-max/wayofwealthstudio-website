// Welcome sequence for people who use the Money Reset Tool (/reset). Joel approved the plan and email 1 on
// 27 Sep 2026. Shape: the lead-magnet welcome in BIG_SENDERS_SEQUENCES.md §5a (Ramit Sethi's welcome).
// Email 1 delivers what the page promises. {{breakdown}} is filled at send time from the figures the person
// chose to email themselves (the tick box on /reset), or with the no-numbers paragraph. Figures are NEVER stored.
// Emails 2-7 are drafted one at a time for Joel's approval, then added here.
//
// afterHours = hours after sign-up. Email 1 goes instantly from the sign-up form.

const CALL = 'https://calendly.com/thewayofwealth-official/20min';

module.exports = {
  footerReason: 'you used the Money Reset Tool at wayofwealthcoaching.com',
  emails: [
    {
      id: '01-your-numbers',
      afterHours: 0,
      subject: 'your numbers (and what to do with them)',
      preheader: "What's yours to keep, and where the rest goes.",
      // Used when no figures were ticked, or when the hourly runner retries a failed first send (no figures then).
      defaults: {
        breakdown: "The tool splits what comes in into four pots: tax, work bills, a slow-month buffer, and a steady weekly wage, so you know what's yours to keep. Your numbers stayed on the page, so [run it again here](https://wayofwealthcoaching.com/reset/) any time you want to see them.",
      },
      body: `
Hey {{name}},

Here's your breakdown from the Money Reset Tool, like I promised.

{{breakdown}}

Now, why four pots and not one account?

Because most of us run everything through one account. A big payment lands, the balance looks huge, and it feels like you're doing great. But a lot of that money was never yours.

Over the next week or so I'll send you a few short emails:
- the one pot to set up first, in about three minutes
- why earning more doesn't fix this on its own
- my own story (the expensive version)
- how one client took money off the pedestal

Two small asks.

**Hit reply and tell me which number surprised you.** One line is plenty. Your replies come straight to me.

**Move this email to your Primary tab**, or star it, so the next ones don't get lost in Promotions.

Joel
MSc Behavioural Economics | Qualified Financial Planner

P.S. Want this set up in your actual bank accounts? We set up these exact sub-accounts and automated transfers together. [Book a free 20-minute call](${CALL}).
`,
    },
    {
      // Approved by Joel 27 Sep. Pot wording = his "tax wall" step (diagnostic dossier.js); P.S. = live welcome email 2.
      id: '02-one-pot',
      afterHours: 20,
      subject: '3 minutes, one pot',
      preheader: 'The one pot to set up first.',
      body: `
Hey {{name}},

Yesterday I sent you your four pots. Today, just one. It takes about three minutes.

Open your banking app today and make one new pot. Name it **TAX. NOT MINE.**

Every time a client payment lands, move the tax % you picked in the tool straight in. Not sure of your real figure? Your accountant can tell you.

That's it. The name is doing the work: money you have labelled as not yours stops feeling spendable, which is the whole point.

There's a name for this, by the way. Researchers call it earmarking: money that's labelled for something gets spent less.

If your bank doesn't do pots, a second account works the same way.

Hit reply when it's done and tell me: **did you make it?** Even a one-word "done" is fine.

Tomorrow I'll show you why earning more doesn't fix this on its own.

Joel

P.S. One of my clients, Jessica, found exactly where her money was leaking when we worked together, and started closing the gaps. That's where it starts.
`,
    },
  ],
};
