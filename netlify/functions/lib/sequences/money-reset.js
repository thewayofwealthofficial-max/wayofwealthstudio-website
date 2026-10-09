// Welcome sequence for people who use the Money Reset Tool (/reset). Joel approved the plan and email 1 on
// 27 Sep 2026. Shape: the lead-magnet welcome in BIG_SENDERS_SEQUENCES.md §5a (Ramit Sethi's welcome).
// Email 1 delivers what the page promises. {{breakdown}} is filled at send time from the figures the person
// chose to email themselves (the tick box on /reset), or with the no-numbers paragraph. Figures are NEVER stored.
// Emails 2-7 were approved one at a time by Joel on 27 Sep (mostly his live welcome emails, adapted).
//
// afterHours = hours after sign-up. Email 1 goes instantly from the sign-up form.

const CALL = 'https://calendly.com/thewayofwealth-official/20min';
// 9 Oct 2026 (Joel): one ask everywhere = the Cash Flow Session. Ask lines below now point here.
const SESSION = 'https://wayofwealthcoaching.com/your-number/';

module.exports = {
  footerReason: 'you used the Money Reset Tool at wayofwealthcoaching.com',
  emails: [
    {
      id: '01-your-numbers',
      afterHours: 0,
      // 9 Oct 2026: the tool no longer needs an email, so this email now delivers the guide (Joel: yes).
      subject: 'your guide (and what to do with your numbers)',
      preheader: 'The 5 phases, and what to do with your numbers.',
      // Used when no figures were ticked, or when the hourly runner retries a failed first send (no figures then).
      defaults: {
        breakdown: "The tool splits what comes in into four pots: tax, work bills, a slow-month buffer, and a steady weekly wage, so you know what's yours to keep. Your numbers stayed on the page, so [run it again here](https://wayofwealthcoaching.com/reset/) any time you want to see them.",
      },
      body: `
Hey {{name}},

Here's the guide I promised: **[The Money Story Method](https://wayofwealthcoaching.com/guides/the-money-story-method.pdf)**. It's the 5 phases my clients used to put these pots into their real bank accounts, and keep them there.

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

P.S. Want to know what these pots need to hold for your business? In a Cash Flow Session I build your cash flow model with you, live on screen, so you leave knowing how much you actually need to earn. **[Find out your number here](${SESSION})**.
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
    {
      // Approved by Joel 27 Sep: welcome email 4 word for word (his dictated £150k story).
      id: '04-my-story',
      afterHours: 68,
      subject: 'two messages',
      preheader: 'The morning I found out.',
      body: `
Hey {{name}},

I remember it like it was yesterday, honestly.

I was teaching myself to trade. No degree. I was buying on leverage and adding more almost every week. Add more. Add more.

Then around February 2021, my account started to blow up. It was growing by ten grand every other day. It went from three grand, to ten k, all the way to one fifty k by around May. I was like, oh my god, I'm going to the moon. I thought I was a genius.

Then it crashed. I told myself it's fine, it's fine, it's just a little bump. It went down to a hundred k. Maybe eighty. Three months of panic.

And then, as fast as I'd made the one fifty k, I lost it even faster.

I remember waking up the next morning and meditating for twenty minutes to calm my mind down. Then I looked at my phone. Two messages.

The first one said: your account has been liquidated.

The second was from the girl I was seeing, saying she couldn't do this anymore.

I didn't just get punched in the face once. I got punched in the face twice. I was numb. I literally couldn't speak.

That day I said to myself, I will do whatever it takes to make sure this never happens again. So I went and got my master's in behavioural economics, and then I became a financial planner. I wanted to understand what had actually happened to me.

Because one fifty k in three months is life-changing money. And I didn't realise it then. Looking back, I realise all the psychological biases that stopped me from pushing the sell button.

That's the stuff I help people with now, the stuff underneath the numbers.

More of my story soon.

Joel

P.S. I'm so grateful for that morning now, because it changed my life. But wow, did I drop the ball on life-changing money.
`,
    },
    {
      // Approved by Joel 27 Sep: welcome email 5, with Josh's real words (22 May graduation call, verbatim) and
      // "head chef on a yacht" (Joel, 27 Sep).
      id: '05-meet-josh',
      afterHours: 92,
      subject: 'Meet Josh',
      preheader: 'In his own words.',
      body: `
Hey {{name}},

I want you to meet Josh.

Josh is a head chef on a yacht, and he worked with me one to one. Here's how he put it, in his own words:

*"You've removed money from the pedestal for me. You've put me back on the pedestal. Now it's just a tool. I am in control of it. It is not in control of me."*

I love that line, because that's like the whole thing, right?

For a lot of us, money sits up on a pedestal. It's scary, or it's sacred, or it's something other people are good at. So we avoid it, or we chase it, and either way it's the one running the show.

Taking it off the pedestal doesn't mean caring less about money. You just get to be the one in charge of it.

[Watch Josh say it himself here](https://wayofwealthcoaching.com/testimonials/josh-pedestal.mp4).

If you want to work on this with me, start with a Cash Flow Session: 75 minutes, live on screen, and you leave knowing your number. **[Find out your number here](${SESSION})**. 5 places a week.

Joel
`,
    },
    {
      // Approved by Joel 27 Sep: welcome email 6 word for word, recap list adapted to this series.
      id: '06-recap-offer',
      afterHours: 140,
      subject: "what you've done this week",
      preheader: 'And what most people do next.',
      body: `
Hey {{name}},

Quick look back. In under a week, you've:

- seen what's actually yours to keep, with your four pots
- set up your TAX. NOT MINE. pot (or at least thought about it)
- learned why earning more doesn't fix a leak on its own
- heard how I lost £150k, and what it taught me
- met Josh, who took money off the pedestal

Now, most people stop here. They read the emails, they nod, they think "yeah, that's me", and then nothing changes. Not because they're lazy. Because knowing isn't the same as doing. I know that one personally.

So here's what working together actually looks like. It's called the Money Story Method. Twelve weeks, one to one, just you and me.

- **Weeks 1 to 3:** we find your money script, the one running the show. You put 90 days of statements through a leak sheet, and we compare what you think you spend with what you really spend. By week 3 the money moves: we set up your pots and the standing orders that fill them.
- **Weeks 4 and 5:** we go deep on where your money story comes from and what money means to you. You get your Money Story Profile, then your Behavioural Pattern Report, which is your patterns with proof from your own spending.
- **Weeks 6 to 8:** we pick the belief holding you back the most and rewrite it. Then we set up guardrails for the moments you usually slip.
- **Weeks 9 to 12:** goal planning, mapping out your cash flow with the new system in place, where you go from here, and graduation.

It's not a course or a PDF. It's the work on why it hasn't stuck before, plus the system, set up with you.

If you'd like to start, book a Cash Flow Session. 75 minutes, live on screen, and you leave knowing how much you actually need to earn. **[Find out your number here](${SESSION})**. 5 places a week.

Joel
`,
    },
    {
      // Approved by Joel 27 Sep: welcome email 7 word for word (he confirmed he hears this objection a lot).
      id: '07-not-ready',
      afterHours: 188,
      subject: '"what if I\'m not ready?"',
      preheader: 'The thing I hear a lot.',
      body: `
Hey {{name}},

Something I hear a lot is, "My income's too up and down for a system."

I get it. When one month is great and the next is quiet, a system feels like it'll just break.

But honestly, it feels up and down because of how you take money out. When there's no buffer, every quiet month feels like an emergency. Get a buffer in place and a big month pays for a small one.

I learned something like this in the gym, of all places. On the days I didn't want to go, the best thing to do was just open the front door. As soon as I took that first step outside, my whole attitude changed. It taught me that the hardest step is leaving the door.

So you don't need to wait for a calm month to start.

If you want to do this properly, with me, **[find out your number here](${SESSION})**. 75 minutes, live on screen. 5 places a week.

And if now's not the time, that's completely fine. From here you'll get Finance Fridays every Friday, and a few shorter emails in between. I'm really glad you're here.

Joel

P.S. Reply any time. Your replies come straight to me.
`,
    },
  ],
};
