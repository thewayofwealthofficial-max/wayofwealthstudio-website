// Money Story Diagnostic: Qualified — Pre-Call Sequence (7-day). Moved from MailerLite to Resend on 28 Sep 2026 (Joel: "just do the emails").
// Source: wow-money-story-diagnostic/EMAIL-SEQUENCES-V2.md, word for word, except: Josh's quote corrected to his
// verbatim words (Worship day 3); bare Calendly links made clickable; {{report_line}} = the person's own report link.
// One email a day. Sending pauses while they have a call booked (see sequence-runner.js + sequence-booked.js).

module.exports = {
  footerReason: 'you took the Money Story Diagnostic at discover.thewayofwealth.shop',
  emails: [
    {
      id: "01-your-money-story-and-why-i-d-like-to-tal",
      afterHours: 0,
      subject: "Your Money Story, and why I'd like to talk",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYou've just seen your full Money Story breakdown. The pattern, the scores, where it started, and what it's quietly costing you. Most people never get that far. They feel something is off with money for years and never name it, and you just did.\n\n{{report_line}}\n\nHere's why I'm writing to you personally. From what you shared, you don't need another app or another budgeting tip, because you already earn. The thing in your way is the pattern running underneath your decisions, and that's exactly what I help people change. It's also the same thing that sits between most people and their first proper £100k, the pattern they keep running without ever seeing it.\n\nSo I'd like to offer you a free, private call. No pitch and no slides, just twenty minutes where we map what your pattern is costing you and what changing it would actually look like.\n\nIf that feels right, grab a time here:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nIt's just a conversation, and you'll leave it clearer either way.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "02-what-the-call-is-actually-like",
      afterHours: 24,
      subject: "What the call is actually like",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nI know \"book a call\" can make people tense, so let me take the mystery out of it.\n\nThere's no hard sell and no script. We talk, I ask a few questions, and you'll probably hear yourself say something out loud that you've never quite put into words, and that's usually where it shifts. By the end you'll know three things: your real pattern, where it came from, and whether working together makes sense. If it doesn't, I'll say so, and you'll still leave with something useful.\n\nTake Alon. When he came to me his money life was, in his words, a lot of avoidance, because money felt tied to status and slightly at odds with who he was, so he kept it at arm's length. By the end that flipped, and he started using money as a tool for the life he wants, right down to opening his own gym studio. His income didn't change first. His relationship with it did.\n\nNot grabbed a time yet?\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nJoel\n",
    },
    {
      id: "03-the-part-most-people-get-wrong",
      afterHours: 48,
      subject: "The part most people get wrong",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nMost people try to fix their money from the outside in. A new budget, a new app, a stricter month, more willpower. It works for a few weeks and then the old pattern quietly takes the wheel again, because the pattern was never about the spreadsheet.\n\nThis is the thing I want you to take from these emails even if we never speak. The behaviour you keep repeating is downstream of a belief you picked up long before you earned a penny, and once you see the belief, the behaviour stops feeling like a personal failing and starts looking like something you can actually change.\n\nThat's the whole job of the call. We find the belief, we name what it's been costing, and you walk away with a clear picture of what shifts when it does.\n\nIf you've been meaning to book and life got in the way, here's the link again:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nAnd if now isn't the moment, hit reply and tell me the one money thing you'd most want to change this year. I read every email that comes back.\n\nJoel\n",
    },
    {
      id: "04-what-this-is-quietly-costing-you",
      afterHours: 72,
      subject: "What this is quietly costing you",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nOne thing I want to name before we go further.\n\nPatterns like yours don't announce themselves. They just quietly take a little off the top, every month, for years. A bit of money that slips away, a bit of peace you don't get to feel, and a version of the next twelve months that looks a lot like the last twelve. That's the real cost. Not dramatic, just steady.\n\nYou don't have to keep paying it. The call is free, it's private, and it's the fastest way to see what changes when the pattern does:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "05-you-don-t-need-more-information",
      afterHours: 96,
      subject: "You don't need more information",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nIf knowing the right thing to do with money was enough, you'd already be where you want to be, because you're not short on information. You can find a budgeting method in thirty seconds. The gap was never knowledge.\n\nThis is what I do differently, and it's why I went and got the behavioural economics behind it after I lost a fair amount of my own money learning the hard way. I don't hand people another system to white-knuckle. We change the thing the system keeps bouncing off, which is the belief and the feeling underneath the decision. When that moves, the right behaviour stops needing willpower and starts feeling obvious.\n\nThat's twenty minutes on a call. Nothing to prepare, nothing to buy:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nJoel\n",
    },
    {
      id: "06-try-this-before-we-speak",
      afterHours: 120,
      subject: "Try this before we speak",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's something you can do today that gives you a taste of the work.\n\nTake the next money decision that makes you hesitate, however small, and before you act, ask one question: what am I actually feeling right now, and what am I hoping this decision will fix? Don't change the decision. Just name the feeling and the job you're quietly asking money to do.\n\nDo that three or four times this week and a pattern will show up. The same feeling, asking money to do the same job, over and over. That pattern is the script. Seeing it is the first move, and it's free, and you can start now.\n\nWhen you want to go from seeing it to changing it, that's exactly what the call is for:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "07-last-note-from-me-for-now",
      afterHours: 144,
      subject: "Last note from me (for now)",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nThis is the last of these, so I'll keep it simple.\n\nYou named your pattern this week. You saw where it came from and what it's been costing. The only thing left is deciding whether you want to keep carrying it or actually change it, and a twenty-minute call is the cleanest way to find out what changing it would look like for you.\n\nNo pitch, no pressure, just a proper conversation and a clear plan you can use whether we work together or not:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nAnd if the timing's wrong, that's genuinely fine. Save this email, and come back when the moment's right. I'll be here, and I read every reply.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
  ],
};
