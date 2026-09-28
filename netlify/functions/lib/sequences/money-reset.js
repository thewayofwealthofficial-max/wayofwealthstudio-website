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
    {
      // Approved by Joel 27 Sep: welcome email 3 word for word, except the £6,000 line (his wording), "what your
      // work costs to run" (was "software and room hire") and "your four pots" (was "the tool from yesterday").
      id: '03-more-money',
      afterHours: 44,
      subject: "more money won't fix it",
      preheader: 'Earning more makes this bigger, not smaller.',
      body: `
Hey {{name}},

This one might sting a little.

A lot of people think the answer is more money. "When I'm earning more, I'll sort it out." I get it. I thought that too.

But more money doesn't fix a leak. It makes it bigger.

Think about a bucket with a hole in the bottom. Pouring water in faster doesn't fill it. It just means more water goes out the hole.

Here's what that looks like in real life. Let's say you have a good month and you take home around £6,000. It lands in the same account as everything else, and your brain reads it as £6,000 you've got. But some of it is tax. Some of it is what your work costs to run. What's actually yours to spend could be a lot less than it looks.

In behavioural economics this is called mental accounting. Richard Thaler did a lot of the work on it. Basically, our brains sort money into little boxes in our heads. If the box isn't there, the money all looks the same, and it all gets spent the same way.

So the fix isn't earning more, and it isn't trying harder. It's giving your money walls, so it splits itself before you have to decide anything. That's what your four pots do, and it's what I help people set up properly.

Does that make sense?

Hit reply and tell me: **when a big payment lands, what's the first thing you do with it?** No judgement. I'm just curious.

Joel

P.S. Tomorrow, the story of how I learned all this the hard way. It involves £150,000 and about three months.
`,
    },
  ],
};
