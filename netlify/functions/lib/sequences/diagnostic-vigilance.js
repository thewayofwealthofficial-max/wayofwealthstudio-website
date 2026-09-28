// Money Story Diagnostic: Nurture — Money Vigilance (7-day). Moved from MailerLite to Resend on 28 Sep 2026 (Joel: "just do the emails").
// Source: wow-money-story-diagnostic/EMAIL-SEQUENCES-V2.md, word for word, except: Josh's quote corrected to his
// verbatim words (Worship day 3); bare Calendly links made clickable; {{report_line}} = the person's own report link.
// One email a day. Sending pauses while they have a call booked (see sequence-runner.js + sequence-booked.js).

module.exports = {
  footerReason: 'you took the Money Story Diagnostic at discover.thewayofwealth.shop',
  emails: [
    {
      id: "01-your-money-story-vigilance-the-full-brea",
      afterHours: 0,
      subject: "Your Money Story: Vigilance, the full breakdown",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYou've just seen your breakdown, and Money Vigilance came through as your strongest pattern.\n\n{{report_line}}\n\nThis one surprises people, because from the outside it looks like the responsible one. You save, you track, you plan. Inside, it's exhausting, because you're always braced for a financial threat that hasn't arrived, and no amount of saving ever switches that feeling off, because it was never really about the money. You saw on your profile how it shows up for you and what it's costing you in peace, so I won't repeat it. Here's a first step.\n\nYour first move this week: write down three facts. What you earn, what you owe, what you own. Then read them back as data, not as a verdict. Most people with this pattern carry a feared version of their finances that's far worse than the real one, and putting the real numbers on paper is how you start to tell the two apart.\n\nOver the next few days I'll show you where this started, what actually shifts it, and why being good with money quietly became the anxiety itself. One short note each morning.\n\nJoel\nWay of Wealth\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "02-where-the-financial-anxiety-actually-sta",
      afterHours: 24,
      subject: "Where the financial anxiety actually started",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYesterday I said Vigilance is the script that hides behind good behaviour. Today I want to show you what's underneath it.\n\nThink about money in your childhood, not the amount but the atmosphere. For most people with this script money was tight, not always dramatically, sometimes just a background hum of worry, bills discussed in low voices, unexpected costs causing visible stress, the fridge full but the margin thin. And you absorbed it, not the facts but the feeling, and your child brain made a quiet decision: I will never be caught off guard.\n\nSo you started watching, counting, planning for every scenario, building a buffer, then a bigger one. And it helped, for a while. But here's the problem with Vigilance. The goalpost doesn't exist. There's no number in your savings that makes the anxiety stop, because the anxiety isn't about the money, it's about a sense of danger installed long before you had your own income. You're solving a childhood equation with adult money, and it doesn't balance, because it was never really about maths.\n\nIf that childhood atmosphere is familiar, hit reply and tell me one thing you remember. I read every one.\n\nMore tomorrow.\n\nJoel\n",
    },
    {
      id: "03-the-client-with-money-in-the-bank-and-no",
      afterHours: 48,
      subject: "The client with money in the bank and no peace",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nI want to tell you about Hozir.\n\nOn paper he was doing everything right. He'd saved around twenty-six thousand pounds, he was careful, he was disciplined, and by any normal measure he was winning. But he couldn't bring himself to do anything with it. He wanted to invest, he knew sitting in cash was costing him, and still the fear of loss kept him frozen, because for him money wasn't a resource, it was a threat to be guarded.\n\nThat's the part outsiders never see. The saving looked like strength, and underneath it he had no peace.\n\nWhat we worked on wasn't another spreadsheet, he had plenty of those. We worked on separating the real risk from the feared one, and on letting \"enough\" finally mean something, so that being careful could have an endpoint instead of running forever. The numbers barely moved at first. What moved was the bracing.\n\nIf you've done everything right and still don't feel safe, that isn't a flaw in you. It's the script, and the script can change.\n\nHit reply and tell me where you're at with it. I read every one.\n\nJoel\n",
    },
    {
      id: "04-you-re-allowed-to-feel-safe",
      afterHours: 72,
      subject: "You're allowed to feel safe",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's the whole answer.\n\nThe anxiety doesn't resolve with more information, because you already have the information. You track, you budget, you probably know your position to the penny, and it still doesn't help. What it resolves with is a new relationship between money and safety, and you can start all three of these today.\n\nFirst, separate your real position from your feared one. On one side write what's actually true about your finances right now, just the facts. On the other write what your anxiety tells you is true. The gap between those two is the script, made visible.\n\nSecond, practise small, guilt-free spending. This sounds backwards, but Vigilance tightens when you never challenge it. Set aside a small amount each week, even five pounds, that you spend on yourself with no justification and no mental accounting. You're teaching your nervous system that money moving outward is not a threat.\n\nThird, define enough. Vigilance never sets a finish line, so create one. What does financial safety actually look like, as a real number. Write it down, and when you reach it, you're allowed to exhale.\n\nThat's the method. No catch and nothing to buy. It's the same place I'd start with you one to one.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "05-doing-everything-right-and-still-not-sle",
      afterHours: 96,
      subject: "Doing everything right and still not sleeping",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's the quiet cost of this script.\n\nYou can do everything right for years, save hard, plan well, avoid every obvious mistake, and still lie awake bracing for something that never comes. The world praises your discipline while you privately carry a low, constant hum of dread, and because you present so well, nobody sees it. That's the cruelty of Vigilance. It looks like a virtue from the outside, and from the inside it quietly takes your peace, year after year, no matter what the numbers say.\n\nYou've started changing that this week by putting the real facts on paper. If at some point you'd like help doing the bigger version, learning to feel as safe as you actually are, that's exactly the kind of thing I work on with people. No rush. More tomorrow.\n\nJoel\n",
    },
    {
      id: "06-the-two-column-exercise-for-the-week-ahe",
      afterHours: 120,
      subject: "The two-column exercise for the week ahead",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's a small exercise that does a lot of work, laid out so you can do it tonight.\n\nTake a page and draw a line down the middle. On the left, write the real version of your finances, just the facts, what you earn, what you owe, what you own, what's coming in. On the right, write the feared version, the worst-case story your anxiety runs when it spikes. Then read both, side by side.\n\nFor almost everyone with this script, the two columns don't match, and the right-hand one is far darker than the facts justify. That gap is not reality. It's the script. And the simple act of seeing them apart, on paper, starts to give your nervous system a more accurate picture to react to. Keep the page. Next time the dread rises, read the left column again, out loud.\n\nThat's a free, real tool. When you want to go from managing the anxiety to changing the fear that drives it, that's what a call with me is for, and I'll share how that works tomorrow.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "07-want-me-to-help-you-exhale",
      afterHours: 144,
      subject: "Want me to help you exhale?",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nThis is the last note in the series, so here's the honest invitation.\n\nThis week you've named your pattern, seen where it started, learned what actually shifts it, and you've got an exercise to tell the real picture from the feared one. That's further than most people get on their own. If you want to go from managing the anxiety to changing the fear underneath it, and finally letting \"enough\" mean something, I'd like to offer you a free, private twenty-minute call.\n\nNo pitch and no slides. We map what the watching has been costing you in peace, and what it looks like to feel as safe as you actually are, and you leave with a clear plan whether we work together or not.\n\nGrab a time here:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nAnd if the timing isn't right, that's completely fine. Save this, come back when it is, and reply any time. I read every one.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
  ],
};
