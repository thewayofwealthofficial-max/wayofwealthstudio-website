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
      ['email', 'Gave their email (got the guide)'],
    ],
    // The book and Skool buttons were removed from /reset (book: Joel, 9 Oct 2026). The guide is the next step.
    extra: [],
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

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Steps that ping Joel the moment they happen. Everything else waits for the 20:00 round-up.
// p = { from, name, email }. from is the plain source; name/email only arrive with 'began' and 'email',
// go into the ping and are never stored (Joel, 8 Oct: "who started and opened ... and where its from").
const who = (p) => (p.name ? `<b>${esc(p.name)}</b>${p.email ? ` (${esc(p.email)})` : ''}` : p.email ? esc(p.email) : 'someone');
const PING = {
  opened: (tool, p) => `👀 <b>${TOOLS[tool].name}</b>: someone opened it. From: ${esc(p.from)}`,
  started: (tool, p) => `✍️ <b>${TOOLS[tool].name}</b>: someone started it. From: ${esc(p.from)}`,
  began: (tool, p) => `✍️ <b>${TOOLS[tool].name}</b>: ${who(p)} started it. From: ${esc(p.from)}`,
  email: (tool, p) => `🧲 <b>${TOOLS[tool].name}</b>: ${who(p)} gave their email. From: ${esc(p.from)}`,
  book: (tool, p) => `🔥 <b>${TOOLS[tool].name}</b>: ${who(p)} clicked the book-a-call button. From: ${esc(p.from)}`,
};

// A stored source label in plain words. ?src= tags show as written; known sites get their name.
const SITES = [
  [/instagram/, 'Instagram'], [/facebook|^fb\.|\.fb\.com$/, 'Facebook'], [/linkedin|^lnkd\.in$/, 'LinkedIn'],
  [/google\./, 'Google'], [/youtube|^youtu\.be$/, 'YouTube'], [/^t\.co$|twitter|^x\.com$/, 'X'],
  [/mail\.|outlook|^gmail/, 'Email'], [/wayofwealthcoaching\.com$/, 'Your website'], [/thewayofwealth\.shop$/, 'Your diagnostic site'],
];
function plainSource(label) {
  if (!label || label === 'not recorded') return 'not recorded';
  if (label === 'direct') return 'no link info (typed in, an app, or a DM)';
  if (!label.includes('.')) return `tag "${label}"`;
  const hit = SITES.find(([re]) => re.test(label));
  return hit ? hit[1] : label;
}

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

// Where one visitor came from, as a short safe label (7 Oct 2026). The ?src= tag on the link wins (e.g. ig-bio),
// else the host of the page they clicked from (e.g. l.instagram.com), else 'direct' (typed it, an app, or an
// email that hides where it came from). Only [a-z0-9.-_] survives, so it is safe in a blob key and in Telegram HTML.
function fromLabel(src, ref) {
  const tag = typeof src === 'string' ? src.toLowerCase().replace(/[^a-z0-9_-]/g, '').slice(0, 30) : '';
  if (tag) return tag;
  const host = typeof ref === 'string' ? ref.toLowerCase().replace(/^www\./, '') : '';
  if (/^[a-z0-9.-]{3,80}$/.test(host)) return host;
  return 'direct';
}

// The round-up for one UK day: per tool, how many different people reached each step, and the biggest drop.
async function rollup(store, day) {
  const { blobs } = await store.list({ prefix: `${day}/` });
  const seen = {}; // tool -> step -> Set(visitor)
  const from = {}; // tool -> visitor -> label
  for (const { key } of blobs) {
    const [, tool, vid, step, label] = key.split('/');
    if (step === 'from' && TOOLS[tool] && label) { (from[tool] ??= {})[vid] = label; continue; }
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
    // Where they came from: people opened per source, and how many of those gave their email.
    const bySource = {};
    for (const vid of seen[tool]?.opened || []) {
      const s = (bySource[plainSource(from[tool]?.[vid] || 'not recorded')] ??= { opened: 0, email: 0 });
      s.opened++;
      if (seen[tool]?.email?.has(vid)) s.email++;
    }
    const rows = Object.entries(bySource).sort((a, b) => b[1].opened - a[1].opened);
    if (rows.length) {
      out.push('Where they came from:');
      for (const [label, s] of rows) out.push(`  ${label}: ${s.opened} opened · ${s.email} email`);
    }
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

module.exports = { TOOLS, PING, isStep, ukDate, telegram, rollup, counts, fromLabel, plainSource };
