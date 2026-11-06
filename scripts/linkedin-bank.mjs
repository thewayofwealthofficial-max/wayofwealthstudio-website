// The LinkedIn "what's working" memory (Joel, 1 Oct 2026: it should keep learning, shapes AND topics).
// linkedin-monitor.mjs adds each month's top on-topic posts here instead of forgetting them. A shape or topic is
// PROMOTED (the writer leans on it) only once it has won in 2+ different months from 3+ different people, so one
// lucky post never changes Fred's writing. Joel can block anything: add its key to "blocked" in bank.json.

// Fixed list so topics can be counted across months. Matches the monitor's relevance screen.
export const TOPICS = [
  // 2 Nov 2026: broad personal finance (Joel). Pricing, paying yourself and tax removed; their old counts stay in bank.json, unused.
  'money mindset and beliefs',
  'money emotions and stress',
  'spending and saving habits',
  'looking rich vs becoming rich',
  'where the money sits: accounts and pots',
  'the order to do money in',
  'irregular income and cash flow',
  'other money',
];

export const PROMOTE = { months: 2, authors: 3 };

// The SHAPE of a post, as numbers plus its first line: what the writer copies (6 Nov 2026). Never the rest of the text.
export function shapeOf(body) {
  const text = String(body || '').replace(/\r/g, '').trim();
  const paras = text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  const words = text ? text.split(/\s+/).length : 0;
  return {
    firstLine: (lines[0] || '').slice(0, 160),
    words,
    paragraphs: paras.length,
    lines: lines.length,
    oneLineParas: paras.length ? Math.round((paras.filter((p) => !p.includes('\n') && p.split(/\s+/).length <= 20).length / paras.length) * 100) / 100 : 0,
    wordsPerLine: lines.length ? Math.round(words / lines.length) : 0,
    endsOnQuestion: /\?\s*$/.test(lines[lines.length - 1] || ''),
  };
}

export const emptyBank = () => ({ patterns: {}, topics: {}, promoted: { patterns: [], topics: [] }, blocked: [] });

// Adds one monthly run. posts: [{url, author, per1k, hook, structure, topic, why, firstLine}]. month: 'YYYY-MM'.
// Returns the keys promoted by this run, so the monitor can tell Joel.
export function addRun(bank, month, posts) {
  const note = (table, key, p) => {
    if (!key) return;
    const e = (table[key] ??= { wins: [] });
    if (e.wins.some((w) => w.url === p.url)) return; // the same post never counts twice
    e.wins.push({ month, author: p.author, per1k: p.per1k, url: p.url, firstLine: p.firstLine, why: p.why });
  };
  for (const p of posts) {
    if (p.hook && p.structure && p.hook !== 'other' && p.structure !== 'other') note(bank.patterns, `${p.hook} · ${p.structure}`, p);
    if (p.topic && p.topic !== 'other money') note(bank.topics, p.topic, p);
  }
  const fresh = { patterns: [], topics: [] };
  for (const kind of ['patterns', 'topics']) {
    for (const [key, e] of Object.entries(bank[kind])) {
      const months = new Set(e.wins.map((w) => w.month)).size;
      const authors = new Set(e.wins.map((w) => w.author)).size;
      e.months = months;
      e.authors = authors;
      if (months >= PROMOTE.months && authors >= PROMOTE.authors && !bank.promoted[kind].includes(key) && !bank.blocked.includes(key)) {
        bank.promoted[kind].push(key);
        fresh[kind].push(key);
      }
    }
    bank.promoted[kind] = bank.promoted[kind].filter((k) => !bank.blocked.includes(k));
  }
  return fresh;
}
