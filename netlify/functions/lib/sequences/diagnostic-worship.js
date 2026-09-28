// Money Story Diagnostic: Nurture — Money Worship (7-day). Moved from MailerLite to Resend on 28 Sep 2026 (Joel: "just do the emails").
// Source: wow-money-story-diagnostic/EMAIL-SEQUENCES-V2.md, word for word, except: Josh's quote corrected to his
// verbatim words (Worship day 3); bare Calendly links made clickable; {{report_line}} = the person's own report link.
// One email a day. Sending pauses while they have a call booked (see sequence-runner.js + sequence-booked.js).

module.exports = {
  footerReason: 'you took the Money Story Diagnostic at discover.thewayofwealth.shop',
  emails: [
    {
      id: "01-your-money-story-worship-the-full-breakd",
      afterHours: 0,
      subject: "Your Money Story: Worship, the full breakdown",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYou've just seen your breakdown, and Money Worship came through as your strongest pattern.\n\n{{report_line}}\n\nBefore you react to that word, let me reframe it. Money Worship is the quiet habit of reaching for money, or for spending, to feel better. The stress valve. The belief that a bit more would finally settle things, and the relief that never quite lasts. You saw on your profile how it shows up for you and what it's been costing, so I won't go over it again. I'd rather give you a first move.\n\nYour first move this week: before your next non-essential purchase, pause for ninety seconds and name the feeling that's underneath it. Don't stop the purchase. Just see what money is actually being asked to do in that moment.\n\nNinety seconds. That's the start.\n\nOver the next few days I'll show you where this loop began, the shift that quiets it, and why earning more has never made it go away. One short note each morning.\n\nJoel\nWay of Wealth\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "02-why-earning-more-never-fixes-the-feeling",
      afterHours: 24,
      subject: "Why earning more never fixes the feeling",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYesterday I said Money Worship isn't about being materialistic, it's about using money to feel better. Today I want to show you where the loop started.\n\nThink about the adults around you growing up, and how they related to spending. For most people with this script one of two things was true. Either money was scarce and you watched the stress and the sacrifice and swore you'd never feel that way, so spending became freedom, proof you'd made it past the struggle. Or money flowed freely, and the adults spent when they were happy and spent when they were stressed, so money became movement and stillness felt wrong. Either way your brain built one equation: spending equals relief.\n\nAnd it works, for about twenty minutes. Then the guilt arrives, or the balance drops, or the number doesn't match the life you thought you were building, so you earn more and spend more and the finish line moves again. That's the loop. Earn, spend for relief, feel empty, earn more.\n\nIt isn't a willpower problem, it's a chemical one, because spending gives you a hit of dopamine and dopamine always fades, and the size of your paycheck doesn't change the chemistry.\n\nIf a moment came to mind just now where you spent to feel better, hit reply and tell me. I read every one.\n\nMore tomorrow.\n\nJoel\n",
    },
    {
      id: "03-the-client-who-took-money-off-the-pedest",
      afterHours: 48,
      subject: "The client who took money off the pedestal",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nI want to tell you about Josh.\n\nWhen we started, money sat on a pedestal in his mind. It was constantly there, the thing he thought about most, the thing he believed he had to sort before he could feel okay, and a lot of debt from medical and family costs had left him, in his words, feeling stuck. He was ashamed to even talk about it.\n\nWe didn't fix that with a budgeting app. We worked on the meaning he'd attached to money until it stopped running him. The way he put it near the end stuck with me: \"You've removed money from the pedestal for me. You've put me back on the pedestal. Now it's just a tool. I am in control of it. It is not in control of me.\"\n\nNothing magic happened to his bank balance overnight. What changed was the grip. Money went from the thing he chased for relief to a tool he uses on purpose, and the weight he'd been carrying lifted.\n\nThat shift is available to you too, and it starts exactly where you are.\n\nHit reply and tell me where you're at with it. I read every one.\n\nJoel\n",
    },
    {
      id: "04-the-spending-trigger-most-people-never-s",
      afterHours: 72,
      subject: "The spending trigger most people never see",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's the whole answer, not a teaser.\n\nThe problem was never the spending. It's what happens in the half hour before the spending. There's always a trigger, stress at work, a hard conversation, boredom that feels like emptiness, a quiet \"I deserve this,\" and spending is just the fastest route your brain knows to relief.\n\nSo here's what actually works, and you can start all three today.\n\nFirst, track triggers, not transactions. Most budgets record what you spent, which is a post-mortem. What changes the pattern is noticing what happened in the thirty minutes before. Stress, boredom, a comparison. That's the data that matters.\n\nSecond, create a ninety-second gap. Not a ban, a pause. When the impulse hits, set a timer, name what you're feeling, and let it run. The impulse will still be there at the end, but now you're choosing instead of reacting.\n\nThird, separate reward from spending. Your brain needs reward, that part isn't up for negotiation, but spending is only one way to get it. Movement, making something, time with people who matter, they all hit the same circuits. You're not removing reward, you're widening it.\n\nThat's the method. No catch and nothing to buy. It's the same place I'd start if you were sitting across from me.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "05-the-finish-line-that-keeps-moving",
      afterHours: 96,
      subject: "The finish line that keeps moving",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nThe cruel thing about this script is that it feels like progress.\n\nYou earn a bit more, you buy the thing, you get the lift, and for a moment it feels like you're getting somewhere. Then the lift fades and the bar quietly resets, a little higher than before, so the income goes up and the contentment stays flat, and the gap between the two can widen for years without you noticing. That's the real cost. Not the spending itself, but the relief you keep paying for and never get to keep.\n\nYou've already started changing that this week, ninety seconds at a time. If at some point you'd like help breaking the loop properly, getting underneath the belief that's been driving it, that's exactly the kind of thing I work on with people. No rush. More tomorrow.\n\nJoel\n",
    },
    {
      id: "06-a-ninety-second-habit-for-the-week-ahead",
      afterHours: 120,
      subject: "A ninety-second habit for the week ahead",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's a small practice that does a lot of work, laid out so you can start today.\n\nFor the next week, before any non-essential spend, run a quick check. Pause and ask three things. What am I feeling right now. What am I hoping this will fix. And will it still feel worth it tomorrow. You don't have to cancel the purchase. You just have to see it clearly first.\n\nDo this a handful of times and a pattern shows up fast. The same feeling, asking money to do the same job, over and over. That pattern is the script, and naming it in the moment is what starts to loosen its grip, because the loop only runs on autopilot. The second you make it conscious, you get a choice back.\n\nThat's a free, real tool. When you want to go from seeing the loop to actually changing what drives it, that's what a call with me is for, and I'll share how that works tomorrow.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "07-want-me-to-help-you-break-the-loop",
      afterHours: 144,
      subject: "Want me to help you break the loop?",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nThis is the last note in the series, so here's the honest invitation.\n\nThis week you've named your pattern, seen where the loop began, learned the shift that quiets it, and you've got a habit to catch it in the moment. That's further than most people ever get. If you want to go from managing the loop to changing the belief underneath it, I'd like to offer you a free, private twenty-minute call.\n\nNo pitch and no slides. We map what the loop has been costing you and what life looks like once money stops being the thing you reach for, and you leave with a clear plan whether we work together or not.\n\nGrab a time here:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nAnd if the timing isn't right, that's genuinely fine. Save this, come back when the moment's right, and reply any time. I read every one.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
  ],
};
