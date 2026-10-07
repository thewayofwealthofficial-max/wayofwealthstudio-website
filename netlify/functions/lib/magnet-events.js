// Lead magnet tracking: which steps people reach in each free tool, and where they stop.
// Replaces the quiz-events GitHub job (quiz retired 30 Sep 2026). Joel, 1 Oct: "monitor anyone who clicks
// onto any lead magnets ... the progression, drop off".
//
// One blob per (UK day, tool, visitor, step) in the 'magnet-events' store. Writing a separate key for each
// step means two steps arriving at once can never overwrite each other (Blobs reads lag, see linkedin-post.mjs).

const TOOLS = {
  reset: {
    name: 'Money Reset Tool',
    steps: [
      ['opened', 'Opened the page'],
      ['started', 'Touched the numbers'],
      ['reveal', 'Pressed "Reset My Numbers"'],
      ['email', 'Gave their email (unlocked)'],
      ['book', 'Clicked "Book a Free Consultation"'],
    ],
    extra: [['skool', 'Clicked "Join the Skool Community"']],
  },
  masterclass: {
    name: 'Free Masterclass',
    steps: [
      ['opened', 'Opened the page'],
      ['email', 'Gave their email (got the video)'],
      ['play', 'Pressed play'],
      ['book', 'Clicked "Book your free call"'],
    ],
    extra: [],
  },
  diagnostic: {
    name: 'Money Story Diagnostic',
    steps: [
      ['opened', 'Opened the page'],
      ['began', 'Typed their name and began'],
      ['answered_1', 'Answered 1'],
      ['answered_2', 'Answered 2'],
      ['answered_3', 'Answered 3'],
      ['answered_4', 'Answered 4'],
      ['answered_5', 'Answered 5'],
      ['gate', 'Reached the email box'],
      ['email', 'Gave their email (got the report)'],
      ['book', 'Clicked "Book your free 20 minute call"'],
    ],
    extra: [],
  },
};

// Steps that ping Joel the moment they happen. Everything else waits for the 20:00 round-up.
const PING = {
  email: (tool) => `🧲 <b>${TOOLS[tool].name}</b>: someone just gave their email.`,
  book: (tool) => `🔥 <b>${TOOLS[tool].name}</b>: someone just clicked the book-a-call button.`,
};

const isStep = (tool, step) => !!TOOLS[tool] && [...TOOLS[tool].steps, ...TOOLS[tool].extra].some(([k]) => k === step);

function ukDate(d = new Date()) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/London', year: 'numeric', month: '2-digit', day: '2-digit' }).format(d);
}

async function telegram(html) {
  const { TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID } = process.env;
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) throw new Error('TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing on Netlify');
  const r = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text: html, parse_mode: 'HTML', disable_web_page_preview: true }),
  });
  if (!r.ok) throw new Error(`Telegram ${r.status}: ${(await r.text()).slice(0, 200)}`);
}

// The round-up for one UK day: per tool, how many different people reached each step, and the biggest drop.
async function rollup(store, day) {
  const { blobs } = await store.list({ prefix: `${day}/` });
  const seen = {}; // tool -> step -> Set(visitor)
  for (const { key } of blobs) {
    const [, tool, vid, step] = key.split('/');
    if (!isStep(tool, step)) continue;
    ((seen[tool] ??= {})[step] ??= new Set()).add(vid);
  }
  const out = [`📊 <b>Free tools today</b> (${day})`];
  for (const [tool, t] of Object.entries(TOOLS)) {
    const n = (k) => seen[tool]?.[k]?.size || 0;
    out.push('', `<b>${t.name}</b>`);
    if (!n('opened') && !Object.keys(seen[tool] || {}).length) { out.push('Nobody opened it today.'); continue; }
    for (const [k, label] of [...t.steps, ...t.extra]) out.push(`${n(k)} · ${label}`);
    // Biggest drop between two steps in a row (main path only, not the extra buttons).
    let worst = null;
    for (let i = 1; i < t.steps.length; i++) {
      const lost = n(t.steps[i - 1][0]) - n(t.steps[i][0]);
      if (lost > 0 && (!worst || lost > worst.lost)) worst = { lost, after: t.steps[i - 1][1] };
    }
    if (worst) out.push(`⬇️ Most people left after: <i>${worst.after}</i> (${worst.lost} stopped there)`);
  }
  return out.join('\n');
}

// Plain numbers for one UK day: { tool: { step: people } }. The morning brief reads yesterday's (7 Oct 2026).
async function counts(store, day) {
  const { blobs } = await store.list({ prefix: `${day}/` });
  const seen = {};
  for (const { key } of blobs) {
    const [, tool, vid, step] = key.split('/');
    if (isStep(tool, step)) ((seen[tool] ??= {})[step] ??= new Set()).add(vid);
  }
  return Object.fromEntries(Object.keys(TOOLS).map((t) => [t, Object.fromEntries(Object.entries(seen[t] || {}).map(([s, v]) => [s, v.size]))]));
}

module.exports = { TOOLS, PING, isStep, ukDate, telegram, rollup, counts };
