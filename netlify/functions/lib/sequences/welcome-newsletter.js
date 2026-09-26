// Welcome sequence for new Finance Fridays sign-ups.
// Shape copied from Ramit Sethi's 7-email welcome (18-23 Apr 2026), letter style like Denise
// Duffield-Thomas and Mind Money Balance (bold text links, no buttons). Content is Joel's own:
// the £150k story from his dictated voice memo, the gym story from his memo, Josh's quote from his
// testimonial video. See wow-intelligence-hub/.../harvest/_analysis/BIG_SENDERS_SEQUENCES.md.
//
// afterHours = hours after sign-up. Email 1 goes instantly from the sign-up form.

const CALL = 'https://calendly.com/thewayofwealth-official/20min';
const RESET = 'https://wayofwealthcoaching.com/reset';

module.exports = {
  footerReason: 'you signed up for Finance Fridays at wayofwealthcoaching.com',
  emails: [
    {
      id: '01-welcome',
      afterHours: 0,
      subject: "you're in (and one quick question)",
      preheader: 'What lands in your inbox, and when.',
      body: `
Hey {{name}},

Welcome to Finance Fridays. I'm really glad you're here.

Quick hello first. I'm Joel. I've got an MSc in Behavioural Economics and I'm a Qualified Financial Planner. But honestly, I didn't get into this because I was good with money. I got into it because I wasn't. More on that later this week.

Now, here's what lands in your inbox:

- **Every Friday:** Finance Fridays. One real story, one money lesson, one small thing to try.
- **Now and then in between:** shorter emails on why your brain does what it does with money, and what actually helps.

No spreadsheets. No "just stop buying coffee". I'm not going to tell you to budget harder, because you've probably tried that already, right?

Two small asks.

**Hit reply and tell me one thing.** What's the money thing bugging you most right now? One line is plenty. Your replies come straight to me.

**Move this email to your Primary tab**, or star it, so the next ones don't get lost in Promotions.

Tomorrow I'll send you a free tool that shows what's actually yours to keep. It takes about three minutes.

Joel
MSc Behavioural Economics | Qualified Financial Planner

P.S. If you already know you want help with this one to one, you can [book a free 20-minute call here](${CALL}).
`,
    },
    {
      id: '02-quick-win',
      afterHours: 20,
      subject: "3 minutes, and you'll see it",
      preheader: 'Where your money actually goes each month.',
      body: `
Hey {{name}},

Like I said yesterday, here's the tool.

It's called the [Money Reset Tool](${RESET}). You put in roughly what comes into your business each month, what your work costs to run, and what you want to set aside for tax. Then it splits your money into pots: tax, work bills, a slow-month buffer, and what's actually yours to keep, as a steady weekly wage.

It takes about three minutes. Your numbers never leave the page, and I can't see them.

Now, why does this matter?

Because most of us run everything through one account. Client payments, tax, rent, food, subscriptions, all of it. A big payment lands, the balance looks huge, and it feels like you're doing great. But a lot of that money was never yours.

It's like sharing a fridge with housemates when nothing's labelled. You just eat whatever's at the front, right? The tool puts the labels on.

[Try the Money Reset Tool here](${RESET})

Then hit reply and tell me: **what surprised you?** I'd love to know which number it was for you.

Tomorrow I'll show you why earning more doesn't fix this on its own.

Joel

P.S. One of my clients, Jessica, found exactly where her money was leaking when we worked together, and started closing the gaps. That's where it starts.
`,
    },
    {
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

Here's what that looks like in real life. A £6,000 payment lands in the same account as everything else. Your brain reads it as £6,000 you've got. But some of it is tax. Some of it is software and room hire. What's actually yours to spend could be a lot less than it looks.

In behavioural economics this is called mental accounting. Richard Thaler did a lot of the work on it. Basically, our brains sort money into little boxes in our heads. If the box isn't there, the money all looks the same, and it all gets spent the same way.

So the fix isn't earning more, and it isn't trying harder. It's giving your money walls, so it splits itself before you have to decide anything. That's what the tool from yesterday shows you, and it's what I help people set up properly.

Does that make sense?

Hit reply and tell me: **when a big payment lands, what's the first thing you do with it?** No judgement. I'm just curious.

Joel

P.S. Tomorrow, the story of how I learned all this the hard way. It involves £150,000 and about three months.
`,
    },
    {
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
      id: '05-meet-josh',
      afterHours: 92,
      subject: 'Meet Josh',
      preheader: 'In his own words.',
      body: `
Hey {{name}},

I want you to meet Josh.

Josh is a yacht chef, and he worked with me one to one. Here's how he put it, in his own words:

*"You've taken money off the pedestal. Now it's just a tool. I'm in control of it, not it in control of me."*

I love that line, because that's like the whole thing, right?

For a lot of us, money sits up on a pedestal. It's scary, or it's sacred, or it's something other people are good at. So we avoid it, or we chase it, and either way it's the one running the show.

Taking it off the pedestal doesn't mean caring less about money. You just get to be the one in charge of it.

[Watch Josh say it himself here](https://wayofwealthcoaching.com/testimonials/josh-pedestal.mp4).

If you want to work on this with me, one to one, [book a free 20-minute call](${CALL}). I take on five people a month.

Joel
`,
    },
    {
      id: '06-recap-offer',
      afterHours: 140,
      subject: "what you've done this week",
      preheader: 'And what most people do next.',
      body: `
Hey {{name}},

Quick look back. In under a week, you've:

- seen what's actually yours to keep, if you tried the [Money Reset Tool](${RESET})
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

I take on five people a month. If you'd like to see if it's a fit, [book a free 20-minute call](${CALL}). We just talk about where you are and whether I can help.

Joel
`,
    },
    {
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

If you want to do this properly, with me, [book a free 20-minute call](${CALL}). I take on five people a month.

And if now's not the time, that's completely fine. From here you'll get Finance Fridays every Friday, and a few shorter emails in between. I'm really glad you're here.

Joel

P.S. Reply any time. Your replies come straight to me.
`,
    },
  ],
};
