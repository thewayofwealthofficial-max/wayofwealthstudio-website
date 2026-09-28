// Money Story Diagnostic: Nurture — Money Status (7-day). Moved from MailerLite to Resend on 28 Sep 2026 (Joel: "just do the emails").
// Source: wow-money-story-diagnostic/EMAIL-SEQUENCES-V2.md, word for word, except: Josh's quote corrected to his
// verbatim words (Worship day 3); bare Calendly links made clickable; {{report_line}} = the person's own report link.
// One email a day. Sending pauses while they have a call booked (see sequence-runner.js + sequence-booked.js).

module.exports = {
  footerReason: 'you took the Money Story Diagnostic at discover.thewayofwealth.shop',
  emails: [
    {
      id: "01-your-money-story-status-the-full-breakdo",
      afterHours: 0,
      subject: "Your Money Story: Status, the full breakdown",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYou've just seen your breakdown, and Money Status came through as your strongest pattern.\n\n{{report_line}}\n\nLet me be careful with that word, because status sounds like vanity and it isn't. What it really means is that your money decisions get shaped by how they look, to other people and quietly to yourself, and your environment installed that long before you had a say in it. You saw on your profile how it plays out for you and what it's been costing, so I won't repeat it. Here's a move instead.\n\nYour first move this week: make one small money decision based entirely on what you actually want from it, stripped of what it would signal to anyone else. Then notice how it feels. Strange, freeing, uncomfortable. Whatever shows up, that feeling is information.\n\nOver the next few days I'll show you where this pattern formed, the one shift that breaks it, and why it tends to get louder with income, not quieter. One short note each morning.\n\nJoel\nWay of Wealth\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "02-why-earning-more-makes-the-gap-worse",
      afterHours: 24,
      subject: "Why earning more makes the gap worse",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nYesterday I said Money Status isn't vanity, it's a script written by your environment. Here's what I mean.\n\nThink about growing up and the role money played in how people were seen. For most people with this script one of two things was true. Either your family had less than the people around you and you felt it, in the clothes and the car and the holidays, so you learned early that money was a social marker and decided, without quite choosing to, that you'd never be on the wrong side of that line. Or your family had money and it came with expectations, the right school, the right area, the right appearance, so money became reputation and keeping it up became automatic. Either way your brain built a rule: what I have equals who I am.\n\nAnd here's the part nobody warns you about. This script speeds up with income. When you earn more the signals don't get cheaper, they get more expensive, the comparison group shifts upward, and the gap between the image you project and the reality underneath can widen quietly for years. It's why some of the highest earners feel the most financially insecure. It isn't the money. It's the script.\n\nIf a specific memory came up reading this, of feeling on the wrong side of that line, hit reply and tell me. I read every one.\n\nMore tomorrow.\n\nJoel\n",
    },
    {
      id: "03-the-client-whose-worth-was-tied-to-the-n",
      afterHours: 48,
      subject: "The client whose worth was tied to the number",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nI want to tell you about Naomi.\n\nWhen we started, her sense of self-worth was quietly fused to her net worth. The number went up and she felt okay, the number dipped and so did she, and her spending often went toward feeling connected and feeling seen rather than toward anything she actually needed. Underneath it sat a belief she'd carried for years, that she'd never really be the kind of person who has money, so why try.\n\nNone of that was vanity. It was a script she'd absorbed growing up, running exactly as designed.\n\nWhat changed was separating the two things that had been welded together: what she has, and who she is. Once her worth wasn't riding on the number, the pressure to keep spending to prove something started to drain out of her decisions, and money got quieter. Not because she earned more overnight, but because she stopped asking it to tell her she was enough.\n\nThat separation is available to you too, and it starts with the small decision I gave you on day one.\n\nHit reply and tell me where you're at with it. I read every one.\n\nJoel\n",
    },
    {
      id: "04-the-one-shift-that-stops-you-buying-to-b",
      afterHours: 72,
      subject: "The one shift that stops you buying to be seen",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's the whole answer.\n\nThe script breaks when you start anchoring money decisions to your own values instead of to external signals. That sounds abstract, so let me make it concrete, and you can start all three today.\n\nFirst, name the signal behind the purchase. Before anything significant, ask one question: am I buying this for what it gives me, or for what it says about me. No judgment either way, just clarity, because most people with this script have never actually separated the two.\n\nSecond, build a values anchor. Write down three things you genuinely value, not what you're meant to value, what actually matters to you when nobody's watching. Use them as a filter. When a purchase fits, it feels settled. When it's signal-driven, there's a specific restlessness afterwards, and once you can feel the difference you can't unfeel it.\n\nThird, track your comparison triggers. Certain feeds, certain people, certain places switch the script on. You can't avoid them all, but you can learn the sequence, comparison, then discomfort, then spending to close the gap, and naming it loosens it.\n\nThat's the method. No catch and nothing to buy. It's the same place I'd start with you one to one.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "05-the-gap-between-the-image-and-the-accoun",
      afterHours: 96,
      subject: "The gap between the image and the account",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nOver the past few days, have you noticed the gap?\n\nThe gap between the financial life you show people and the one you actually live. Between the image and the balance. Between what your spending says about you and what you'd choose if nobody was watching. That gap is the Status script in action, and most people spend years trying to close it from the wrong side, by earning more and buying more and signalling harder, and it never closes from that direction.\n\nIt closes when you decide what money means to you, on your own terms, independent of what it tells anyone else. That's a quiet, private shift, nobody sees it happen, but you feel it, and unlike a purchase the relief actually settles.\n\nYou've started this week by making one decision that was just yours. If at some point you'd like help doing the bigger version of this properly, that's exactly the kind of thing I work on with people. No rush. More tomorrow.\n\nJoel\n",
    },
    {
      id: "06-a-values-filter-for-the-week-ahead",
      afterHours: 120,
      subject: "A values filter for the week ahead",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nHere's a small tool that does a lot of work, laid out so you can start today.\n\nWrite down three things you genuinely value. Not goals, and not what sounds good, just the things that actually matter to you when no one's looking. Health, freedom, family, learning, whatever is true for you. Keep the list on your phone.\n\nThen for the next week, run every non-trivial spend through it. Before you buy, ask which of these three this is serving. If it lands on one of them, buy it and enjoy it with a clear conscience. If it's serving none of them, you've probably caught a signal-driven purchase in the act, and you get to decide with your eyes open. You're not banning anything. You're just spending from your own values instead of from comparison.\n\nThat's a free, real tool. When you want to go from filtering purchases to changing the belief that ties your worth to the number, that's what a call with me is for, and I'll share how that works tomorrow.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
    {
      id: "07-want-your-money-to-feel-like-yours-again",
      afterHours: 144,
      subject: "Want your money to feel like yours again?",
      defaults: { report_line: '' },
      body: "\nHi {{name}},\n\nThis is the last note in the series, so here's the honest invitation.\n\nThis week you've named your pattern, seen where it formed, learned the shift that breaks it, and you've got a values filter to catch it in real time. That's further than most people get on their own. If you want to go from managing the signals to changing the belief underneath, that what you have equals who you are, I'd like to offer you a free, private twenty-minute call.\n\nNo pitch and no slides. We map what the script has been costing you and what your money looks like once it's yours again, and you leave with a clear plan whether we work together or not.\n\nGrab a time here:\n[https://calendly.com/thewayofwealth-official/20min](https://calendly.com/thewayofwealth-official/20min)\nAnd if the timing isn't right, that's completely fine. Save this, come back when it is, and reply any time. I read every one.\n\nJoel\nMSc Behavioural Economics | Qualified Financial Planner\n",
    },
  ],
};
