// Money Story Diagnostic: Nurture — Money Avoidance (7-day). Moved from MailerLite to Resend on 28 Sep 2026 (Joel: "just do the emails").
// Source: wow-money-story-diagnostic/EMAIL-SEQUENCES-V2.md, word for word, except: Josh's quote corrected to his
// verbatim words (Worship day 3); bare Calendly links made clickable; {{report_line}} = the person's own report link.
// One email a day. Sending pauses while they have a call booked (see sequence-runner.js + sequence-booked.js).

module.exports = {
  footerReason: 'you took the Money Story Diagnostic at discover.thewayofwealth.shop',
  emails: [
    {
      id: "01-your-money-story-avoidance-the-full-brea",
      afterHours: 0,
      subject: "Your Money Story: Avoidance, the full breakdown",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYou've just seen your breakdown, and Money Avoidance came through as your strongest pattern.\n\n{{report_line}}\n\nI know that word can sting, so before anything else: avoidance is a form of protection. Your brain learned a long time ago that looking at money felt unsafe, so it does the sensible thing and looks away, and your nervous system is only doing its job. You saw on your profile where it shows up and what it's been costing, so I won't go over it again. I'd rather give you something to do with it.\n\nYour first move this week: spend sixty seconds with your bank balance, and nothing else. Don't fix anything, don't plan anything, just look. There's nothing to repair here. You're teaching your brain that money and safety can sit in the same room, and sixty seconds is enough.\n\nOver the next few days I'll show you where this pattern came from, the one shift that actually changes it, and what it quietly costs if it keeps running. One short note each morning.\n\nJoel\nWay of Wealth\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "02-where-your-money-avoidance-actually-star",
      afterHours: 24,
      subject: "Where your Money Avoidance actually started",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYesterday I told you that Money Avoidance is protection, not laziness, and today I want to show you where it started.\n\nThink back to the earliest memory you have of money in your house. Not what happened, but how it felt. For most people with this script money wasn't discussed, or when it was there was tension, raised voices, a door closing, a parent going quiet, and money became the thing that made the room feel unsafe. Your child brain absorbed that, not as words but as a felt sense that money equals danger, and your nervous system built a wall around it.\n\nThat wall has been running ever since. It's why opening the banking app creates a physical response, a tightness in your chest or a knot in your stomach, and it's why you can think clearly about everything except your finances, and it's why you've started budgets and apps and plans and abandoned all of them within days. The pattern isn't the problem. The pattern is a symptom of something that happened before the pattern.\n\nThis is what most budgeting advice gets badly wrong, because it hands you a spreadsheet and tells you to be more disciplined, and that's like handing someone with a broken leg a treadmill.\n\nIf reading this brought up an early money memory, hit reply and tell me about it. I read every one.\n\nMore tomorrow.\n\nJoel\n",
    },
    {
      id: "03-the-client-who-used-to-look-away-too",
      afterHours: 48,
      subject: "The client who used to look away too",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nI want to tell you about Alon, because his start looked a lot like yours.\n\nWhen we began, money was, in his words, \"a lot of avoidance.\" He'd been raised to believe there's more to life than money, which is a good thing, but it meant he quietly put money to the side and never really looked, and he saw it as a status thing that clashed with who he was. He told me he was uncomfortable even talking about money, with close friends, with his own brother. None of that was a discipline problem. It was the same protective pattern you're running, doing exactly what it was built to do.\n\nWhat changed wasn't an app or a stricter budget. In one session it clicked that he already had real financial responsibility, that the fear, as he put it, \"is not really there, it's in your mind.\" Once money stopped feeling like a threat, the avoidance loosened on its own. He described it simply: now when something about finance comes up online, he actually listens, instead of scrolling past it. And the money became the tool to fund the thing he genuinely cares about, opening his own gym studio to help people with their health.\n\nI'm telling you this because the thing you scored today is not a life sentence. It's a pattern, and patterns change once you can see them clearly.\n\nHit reply and tell me where you're at with it right now. I read every one.\n\nJoel\n",
    },
    {
      id: "04-the-one-shift-that-finally-makes-looking",
      afterHours: 72,
      subject: "The one shift that finally makes looking feel safe",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nI've spent years studying why intelligent, capable people avoid their finances, and I want to give you the whole answer, not a teaser.\n\nIt's not a discipline problem, it's a design problem, because every budgeting tool you've tried was built for someone who can already sit calmly with their numbers, someone whose heart rate doesn't change when they open the banking app. That person doesn't need help, and you've been handed their tools.\n\nHere's what actually works instead, and you can start all three today.\n\nFirst, start with feelings, not figures. Before you touch a single number, name the emotion that shows up when you think about money, because you can't change what you can't see, and that naming is diagnostic, not soft.\n\nSecond, reduce the cost of looking. Make the first step so small it doesn't trip the avoidance response. One number, one account, one minute. Not a full budget, just a glance.\n\nThird, build the habit before the system. Most people try to build a complex budget on day one, which is like running a marathon before you've walked to the end of your road. The habit of engaging with money matters more than the system you use.\n\nThat's the method. No catch, no thing to buy. It's the same place I'd start if you were sitting across from me, and if you do those three for a fortnight you'll feel the difference.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "05-what-avoidance-quietly-takes",
      afterHours: 96,
      subject: "What avoidance quietly takes",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nThe hard thing about this script is that it never sends a bill.\n\nIt just takes a little off the top, quietly, every month. The gap between where your finances actually are and where you think they are widens a bit. A decision you could have made early gets made late, or not at all. A bit of peace you should get to feel goes missing. And the next twelve months end up looking a lot like the last twelve, not because anything dramatic happened, but because the looking-away kept running in the background.\n\nThat's the real cost. Not a disaster, just a slow drift, and the longer it runs the heavier the first proper look feels.\n\nYou've already started changing that this week, sixty seconds at a time. If at some point you'd like someone to help you do the bigger version of this properly, that's exactly the kind of thing I work on with people. No rush. More tomorrow.\n\nJoel\n",
    },
    {
      id: "06-a-two-minute-ritual-for-the-week-ahead",
      afterHours: 120,
      subject: "A two-minute ritual for the week ahead",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's a small thing that does a lot of work, laid out so you can start tonight.\n\nPick a fixed time each day, something you already do, like the kettle going on in the morning. At that time, open your banking app for two minutes. You're not budgeting and not fixing. You look at one number, you notice the feeling that shows up, you name it in your head, and you close the app. That's the whole ritual.\n\nIt feels too small to matter, and that's the point, because the avoidance response only fires when the step feels big. Keep it tiny and repeat it, and within a week or two your nervous system stops tagging the app as a threat. The calm you've been waiting to feel before you look is the thing that gets built by looking, in small safe doses, on purpose.\n\nThat's a free, real tool. If you'd like to go from steadying the pattern to actually changing what's underneath it, that's what a call with me is for, and I'll share how that works tomorrow.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "07-want-me-to-map-this-with-you",
      afterHours: 144,
      subject: "Want me to map this with you?",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nThis is the last note in the series, so here's the honest invitation.\n\nOver the past week you've named your pattern, seen where it came from, learned the shift that changes it, and you've got a daily ritual to steady it. That's further than most people ever get on their own. If you want to go from steadying it to genuinely changing the belief underneath, I'd like to offer you a free, private twenty-minute call.\n\nNo pitch and no slides. We map what your avoidance has been costing you and what changing it would actually look like, and you leave with a clear plan whether we work together or not.\n\nGrab a time here:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nAnd if the timing isn't right, that's completely fine, because this is your script and you get to move at your pace. Save this, come back when the window opens, and reply any time. I read every one.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
  ],
};
