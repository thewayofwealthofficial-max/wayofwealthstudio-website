// The Pay Yourself Plan (rebuilt /reset, 11 Oct 2026). One place for the sums, the email text and the PDF, so
// the three can never disagree. The page sends the six answers; nothing here is stored. Same maths as the page:
// VAT (a sixth, standard 20% rate) -> profit -> tax on profit -> buffer % of what's left -> wage.
const { jsPDF } = require('jspdf');
const FONTS = require('./fonts/pdf-fonts');

const CALENDLY = 'https://calendly.com/thewayofwealth-official/your-cash-flow-session';
const POA_URL = 'https://www.gov.uk/understand-self-assessment-bill/payments-on-account';
const BUF = 10;
const VAT_NOTE = "If your costs have VAT on them too, you can usually take that off, so your real VAT bill is often lower. Your accountant will know.";
// BUF = % of what's left after tax that goes to the buffer; the plan also shows 5% and 15% (Joel, 11 Oct).

function calc(p, bufferPct) {
  const vat = p.vat ? p.income / 6 : 0;
  const profit = p.income - vat - p.costs;
  const tax = Math.max(0, profit) * (p.taxPct / 100);
  const left = profit - tax;
  const buffer = Math.max(0, left) * (bufferPct / 100);
  const monthly = Math.max(0, left - buffer);
  return { vat, profit, tax, left, buffer, monthly, weekly: (monthly * 12) / 52 };
}

// Checks the six answers. Returns null if anything is missing or silly.
function normalise(p) {
  if (!p || typeof p !== 'object') return null;
  const num = (k, max) => (Number.isFinite(Number(p[k])) && Number(p[k]) >= 0 && Number(p[k]) <= max ? Number(p[k]) : null);
  const plan = {
    income: num('income', 1e7), costs: num('costs', 1e7), life: num('life', 1e7),
    taxPct: [20, 25, 30].includes(Number(p.taxPct)) ? Number(p.taxPct) : null,
    vat: p.vat === true, payNow: p.payNow === null ? null : num('payNow', 1e6),
  };
  if ([plan.income, plan.costs, plan.life, plan.taxPct].some((x) => x === null) || plan.income <= 0) return null;
  if (p.payNow !== null && plan.payNow === null) return null;
  return plan;
}

const m = (x) => `£${Math.round(x).toLocaleString('en-GB')}`;

// Same order as the page: life gap, over-paying, no wage, under-paying, close.
function gapLine(plan, c) {
  // 14 Oct 2026 (Joel's test: £12k in, VAT, £11k costs): when the business costs more than comes in, THAT is
  // the problem to name first, before any life gap. Profit 0 or below = nothing to split yet.
  if (c.profit < 0) return `Right now your business costs ${m(-c.profit)} a month more than comes in, before you pay yourself anything. That's ${m(-c.profit * 12)} a year.`;
  if (c.profit === 0) return "Right now your business uses up everything that comes in. There's nothing left to pay you yet.";
  if (plan.life > c.monthly) return `Your life costs ${m(plan.life - c.monthly)} a month more than your business can pay you. That's ${m((plan.life - c.monthly) * 12)} a year.`;
  if (plan.payNow !== null && plan.payNow - c.weekly > 50) return `You're taking ${m(plan.payNow - c.weekly)} a week more than your business can support. That's ${m((plan.payNow - c.weekly) * 52)} a year.`;
  if (plan.payNow === null) return "Right now you don't have a wage. This plan gives you one.";
  if (c.weekly - plan.payNow > 50) return `You could pay yourself ${m(c.weekly - plan.payNow)} a week more. That's ${m((c.weekly - plan.payNow) * 52)} a year.`;
  return "You're close. Now make it automatic.";
}

function accountsFor(plan, c) {
  const per1k = (x) => (x / plan.income) * 1000;
  return [
    { k: 'Yours', note: 'your weekly wage', v: c.monthly },
    { k: 'Tax', note: `${plan.taxPct}% of profit. Never touch it`, v: c.tax },
    { k: 'Business costs', note: 'what the business needs to run', v: plan.costs },
    { k: 'Slow-month buffer', note: `${BUF}% of what's left after tax`, v: c.buffer },
    ...(plan.vat ? [{ k: 'VAT', note: "HMRC's money, about a sixth at 20%", v: c.vat }] : []),
  ].map((a) => ({ ...a, per1k: per1k(a.v) }));
}

const VAT_THRESHOLD_YEAR = 90000; // GOV.UK, checked 5 Oct 2026
const down50 = (x) => Math.floor(x / 50) * 50;
const up50 = (x) => Math.ceil(x / 50) * 50;

// 15 Oct 2026 (Joel): when the wage doesn't cover what their life costs, the plan must say WHAT to change and
// show the target numbers. Sums on their own numbers only: the aim is a wage that covers their life costs.
// wage = (income - VAT - costs) x (1 - tax%) x (1 - buffer%), so the profit needed = life / that factor.
function targets(plan, c) {
  if (!(plan.life > 0) || c.monthly >= plan.life - 1) return null;
  const keep = (1 - plan.taxPct / 100) * (1 - BUF / 100);
  const vatShare = plan.vat ? 1 / 6 : 0;
  const needProfit = plan.life / keep;
  const gapProfit = needProfit - c.profit; // how much more profit a month is needed
  const options = [];
  const costsTo = down50(plan.income * (1 - vatShare) - needProfit);
  if (costsTo >= 0 && costsTo < plan.costs) {
    options.push({ kind: 'costs', costs: costsTo, income: plan.income,
      text: `Bring business costs down to ${m(costsTo)} a month or less (from ${m(plan.costs)}), with what comes in staying the same.` });
  }
  const incomeTo = up50((needProfit + plan.costs) / (1 - vatShare));
  const overVat = !plan.vat && incomeTo * 12 > VAT_THRESHOLD_YEAR;
  options.push({ kind: 'income', costs: plan.costs, income: incomeTo,
    text: `Bring in about ${m(incomeTo)} a month (from ${m(plan.income)}), with costs staying the same.` +
      (overVat ? ` At that level you'd pass the £90,000 VAT threshold, so VAT would apply too.` : '') });
  const mixCosts = down50(plan.costs - gapProfit / 2);
  const mixIncome = up50(plan.income + gapProfit / 2 / (1 - vatShare));
  if (mixCosts >= 0 && mixCosts < plan.costs) {
    options.push({ kind: 'mix', costs: mixCosts, income: mixIncome,
      text: `Or a mix of both: costs down to about ${m(mixCosts)} and about ${m(mixIncome)} coming in.` });
  }
  const pick = options[0]; // costs first when it can work on its own; otherwise more coming in
  const tPlan = { ...plan, income: pick.income, costs: pick.costs };
  const tc = calc(tPlan, BUF);
  return {
    options, pick, plan: tPlan, c: tc, accounts: accountsFor(tPlan, tc),
    costsAlone: options.some((o) => o.kind === 'costs'),
    intro: `To pay yourself what your life costs (${m(plan.life)} a month), one of these needs to change:`,
  };
}

function build(raw) {
  const plan = normalise(raw);
  if (!plan) return null;
  const c = calc(plan, BUF);
  const t = targets(plan, c);
  // Buffer, setup and the 5% / 15% lines follow the target plan when there is one.
  const bp = t ? t.plan : plan, bc = t ? t.c : c;
  const month = plan.life + plan.costs;
  return {
    plan, c, accounts: accountsFor(plan, c), gap: gapLine(plan, c), loss: c.profit <= 0, t,
    goal: { plan: bp, c: bc },
    buffer: {
      first: bp.life + bp.costs, full: (bp.life + bp.costs) * 6,
      firstMonths: bc.buffer > 0 ? Math.ceil((bp.life + bp.costs) / bc.buffer) : null,
      fullMonths: bc.buffer > 0 ? Math.ceil(((bp.life + bp.costs) * 6) / bc.buffer) : null,
    },
    slow: calc(bp, 5), fast: calc(bp, 15), month,
  };
}

// ---------- the email text (short: the PDF carries the detail) ----------
function planText(raw) {
  const d = build(raw);
  if (!d) return null;
  const { plan, c } = d;
  return [
    `**Your safe weekly wage: ${m(c.weekly)}** (${m(c.monthly)} a month)`,
    '',
    d.gap,
    '',
    ...(d.t
      ? [
          '**What needs to change**',
          '',
          d.t.intro,
          ...d.t.options.map((o, i) => `${i + 1}. ${o.text}`),
          '',
          `**Your target plan** (option 1: ${m(d.t.pick.income)} coming in, ${m(d.t.pick.costs)} business costs)`,
          `- **Your weekly wage:** ${m(d.t.c.weekly)} (${m(d.t.c.monthly)} a month)`,
          ...d.t.accounts.filter((a) => a.k !== 'Yours').map((a) => `- **${a.k}:** ${m(a.v)} a month (${m(a.per1k)} of every £1,000)`),
        ]
      : [
          `**Your ${plan.vat ? '' : 'four '}accounts, from every £1,000 that comes in**`,
          ...d.accounts.map((a) => `- **${a.k}:** ${m(a.per1k)} (${m(a.v)} a month)`),
        ]),
    ...(plan.vat ? ['', VAT_NOTE] : []),
    '',
    d.t
      ? 'Your full plan is attached as a PDF: what to change, your target accounts, your buffer target, your 30-minute setup and your slow-month rule.'
      : 'Your full plan is attached as a PDF: your accounts, your buffer target, your 30-minute setup and your slow-month rule.',
  ].join('\n');
}

// ---------- the PDF ----------
const C = {
  bg: [11, 17, 25], panel: [19, 29, 41], line: [38, 50, 63], text: [245, 240, 232], mute: [154, 167, 180],
  gold: [196, 162, 101], white: [255, 255, 255], warn: [242, 169, 158], warnLine: [214, 90, 74], onGold: [20, 32, 44],
};
const W = 595.28, H = 841.89, X = 48, CW = W - X * 2;

function setupFonts(doc) {
  const add = (file, name, style) => { doc.addFileToVFS(`${file}.ttf`, FONTS[file]); doc.addFont(`${file}.ttf`, name, style); };
  add('Inter-Regular', 'Inter', 'normal'); add('Inter-SemiBold', 'Inter', 'semibold'); add('Inter-Bold', 'Inter', 'bold');
  add('Fraunces-SemiBold', 'Fraunces', 'normal'); add('Fraunces-SemiBoldItalic', 'Fraunces', 'italic');
}
function page(doc, n) {
  doc.setFillColor(...C.bg); doc.rect(0, 0, W, H, 'F');
  doc.setFont('Inter', 'semibold'); doc.setFontSize(8.5); doc.setTextColor(...C.gold);
  doc.text('WAY OF WEALTH', X, 40, { charSpace: 1.6 });
  doc.setFont('Inter', 'normal'); doc.setTextColor(...C.mute);
  doc.text(`Pay Yourself Plan · page ${n} of 4`, W - X, 40, { align: 'right' });
  doc.setDrawColor(...C.line); doc.setLineWidth(0.6); doc.line(X, 52, W - X, 52);
  doc.setFontSize(8); doc.text('wayofwealthcoaching.com · Joel Ezekiel · MSc Behavioural Economics | Qualified Financial Planner', W / 2, H - 28, { align: 'center' });
}
function kicker(doc, s, y) { doc.setFont('Inter', 'semibold'); doc.setFontSize(9); doc.setTextColor(...C.gold); doc.text(s.toUpperCase(), X, y, { charSpace: 1.4 }); }
function h2(doc, s, y) { doc.setFont('Fraunces', 'normal'); doc.setFontSize(22); doc.setTextColor(...C.text); doc.text(s, X, y); }
function para(doc, s, y, opts = {}) {
  doc.setFont('Inter', opts.weight || 'normal'); doc.setFontSize(opts.size || 11); doc.setTextColor(...(opts.color || C.mute));
  const lines = doc.splitTextToSize(s, opts.width || CW);
  doc.text(lines, opts.x || X, y, { lineHeightFactor: 1.5 });
  return y + lines.length * (opts.size || 11) * 1.5;
}
function panel(doc, y, h, border) {
  doc.setFillColor(...C.panel); doc.setDrawColor(...(border || C.line)); doc.setLineWidth(0.8);
  doc.roundedRect(X, y, CW, h, 10, 10, 'FD');
}

function buildPdf(raw, firstName) {
  const d = build(raw);
  if (!d) return null;
  const { plan, c } = d;
  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  setupFonts(doc);
  const who = (firstName || '').trim().split(/\s+/)[0];
  const date = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });

  // ---- page 1: the number ----
  page(doc, 1);
  doc.setFont('Fraunces', 'normal'); doc.setFontSize(30); doc.setTextColor(...C.text);
  doc.text(who ? `${who}'s Pay Yourself Plan` : 'Your Pay Yourself Plan', X, 110);
  doc.setFont('Inter', 'normal'); doc.setFontSize(10.5); doc.setTextColor(...C.mute); doc.text(date, X, 132);

  panel(doc, 160, 190, C.gold);
  doc.setFont('Inter', 'semibold'); doc.setFontSize(9.5); doc.setTextColor(...C.gold);
  doc.text('YOUR SAFE WEEKLY WAGE', W / 2, 200, { align: 'center', charSpace: 1.4 });
  doc.setFont('Fraunces', 'normal'); doc.setFontSize(72); doc.setTextColor(...C.white);
  doc.text(m(c.weekly), W / 2, 280, { align: 'center' });
  doc.setFont('Inter', 'normal'); doc.setFontSize(12); doc.setTextColor(...C.mute);
  doc.text(d.loss ? 'Nothing to pay yet: the business costs more than comes in' : `${m(c.monthly)} a month, paid to you like a wage`, W / 2, 314, { align: 'center' });

  // gap box
  doc.setFillColor(36, 22, 25); doc.setDrawColor(...C.warnLine); doc.setLineWidth(0.8);
  // Font set BEFORE measuring, so long lines wrap inside the box (14 Oct 2026 fix).
  doc.setFont('Inter', 'bold'); doc.setFontSize(14);
  const gapLines = doc.splitTextToSize(d.gap, CW - 40);
  const gh = 30 + gapLines.length * 21;
  doc.roundedRect(X, 372, CW, gh, 10, 10, 'FD');
  doc.setTextColor(...C.warn); doc.text(gapLines, W / 2, 398, { align: 'center', lineHeightFactor: 1.5 });

  let y = 372 + gh + 44;
  kicker(doc, 'Your numbers', y); y += 22;
  const rows = [
    ['Coming in, on average', `${m(plan.income)} a month`],
    ...(plan.vat ? [['VAT registered', 'Yes']] : []),
    ['Business costs', `${m(plan.costs)} a month`],
    ['Your life costs', `${m(plan.life)} a month`],
    ['What you pay yourself now', plan.payNow === null ? 'No set amount' : `${m(plan.payNow)} a week`],
    ['Tax set aside', `${plan.taxPct}% of profit`],
  ];
  rows.forEach(([k, v]) => {
    doc.setDrawColor(...C.line); doc.line(X, y + 10, W - X, y + 10);
    doc.setFont('Inter', 'normal'); doc.setFontSize(11); doc.setTextColor(...C.mute); doc.text(k, X, y);
    doc.setFont('Inter', 'semibold'); doc.setTextColor(...C.text); doc.text(v, W - X, y, { align: 'right' });
    y += 30;
  });
  para(doc, 'Built from the numbers you picked. A rough guide, not a forecast.', y + 8, { size: 9.5 });

  // ---- page 2: what to change (if anything) + the accounts ----
  doc.addPage(); page(doc, 2);
  const shown = d.t ? d.t : { accounts: d.accounts, plan, c };
  if (d.t) {
    kicker(doc, 'What needs to change', 100);
    h2(doc, 'Your target plan', 128);
    // the options panel
    doc.setFont('Inter', 'normal'); doc.setFontSize(10.5);
    const optLines = d.t.options.map((o, i) => doc.splitTextToSize(`${i + 1}.  ${o.text}`, CW - 40));
    const ph = 46 + optLines.reduce((n, l) => n + l.length * 15.75 + 6, 0);
    panel(doc, 148, ph, C.gold);
    para(doc, d.t.intro, 172, { x: X + 20, width: CW - 40, color: C.text, size: 10.5, weight: 'semibold' });
    let oy = 196;
    optLines.forEach((l) => { doc.setFont('Inter', 'normal'); doc.setFontSize(10.5); doc.setTextColor(...C.text); doc.text(l, X + 20, oy, { lineHeightFactor: 1.5 }); oy += l.length * 15.75 + 6; });
    y = 148 + ph + 22;
    y = para(doc, `Your target plan uses option 1: ${m(d.t.pick.income)} coming in and ${m(d.t.pick.costs)} business costs. Here's where every payment would go.`, y, { size: 10 }) + 6;
  } else {
    kicker(doc, 'Where every payment goes', 100);
    h2(doc, `Your ${plan.vat ? '' : 'four '}accounts`, 128);
    y = para(doc, 'Every time money comes in, split it like this. The bars show what each account gets from every £1,000.', 154) + 14;
  }
  shown.accounts.forEach((a, i) => {
    panel(doc, y, 62);
    doc.setFont('Fraunces', 'normal'); doc.setFontSize(14); doc.setTextColor(...C.text); doc.text(a.k, X + 18, y + 25);
    doc.setFont('Inter', 'normal'); doc.setFontSize(9); doc.setTextColor(...C.mute);
    doc.text(i === 0 ? `your weekly wage: ${m(shown.c.weekly)}` : a.note, X + 18, y + 40);
    doc.setFont('Inter', 'bold'); doc.setFontSize(14); doc.setTextColor(...C.white); doc.text(`${m(a.v)}/mo`, W - X - 18, y + 25, { align: 'right' });
    const bx = X + 18, bw = CW - 36, by = y + 47;
    doc.setFillColor(...C.line); doc.roundedRect(bx, by, bw, 6, 3, 3, 'F');
    doc.setFillColor(...(i === 0 ? C.gold : [232, 213, 176])); doc.roundedRect(bx, by, Math.max(4, bw * Math.min(1, a.per1k / 1000)), 6, 3, 3, 'F');
    doc.setFont('Inter', 'semibold'); doc.setFontSize(9); doc.setTextColor(...C.gold);
    doc.text(`${m(a.per1k)} of every £1,000`, W - X - 18, y + 40, { align: 'right' });
    y += 70;
  });
  if (plan.vat) para(doc, VAT_NOTE, y + 4, { size: 9 });

  // ---- page 3: the buffer + the setup ----
  doc.addPage(); page(doc, 3);
  y = 100;
  kicker(doc, 'Your safety net', y); y += 26;
  h2(doc, 'Your buffer target', y); y += 22;
  const tx1 = X + 10, tx2 = W - X - 10, ty = y + 34;
  doc.setDrawColor(...C.line); doc.setLineWidth(2); doc.line(tx1, ty, tx2, ty);
  const pts = [
    { x: tx1, top: 'Today', bot: m(0) },
    { x: tx1 + (tx2 - tx1) * 0.35, top: `1 month: ${m(d.buffer.first)}`, bot: d.buffer.firstMonths ? `about ${d.buffer.firstMonths} months` : 'not yet possible' },
    // Joel 11 Oct: no 'about 59 months' here, it reads as defeat. The 6-month goal is named, not timed.
    { x: tx2, top: `6 months: ${m(d.buffer.full)}`, bot: 'the long-term goal' },
  ];
  pts.forEach((pt, i) => {
    doc.setFillColor(...(i === 0 ? C.mute : C.gold)); doc.circle(pt.x, ty, 6, 'F');
    const al = i === 0 ? 'left' : i === 2 ? 'right' : 'center';
    doc.setFont('Inter', 'semibold'); doc.setFontSize(10); doc.setTextColor(...C.text); doc.text(pt.top, pt.x, ty - 16, { align: al });
    doc.setFont('Inter', 'normal'); doc.setFontSize(9.5); doc.setTextColor(...C.mute); doc.text(pt.bot, pt.x, ty + 24, { align: al });
  });
  y = ty + 56;
  y = para(doc, d.goal.c.buffer > 0
    ? `${d.t ? 'On your target plan, at' : 'At'} ${m(d.goal.c.buffer)} a month, one month of life and business costs takes about ${d.buffer.firstMonths} months. Want it faster or slower? At 5% your weekly wage would be ${m(d.slow.weekly)}. At 15%, ${m(d.fast.weekly)}. If your income swings a lot, go faster.`
    : "Right now there's nothing left over to build a buffer. That's the first thing to change.", y) + 30;

  kicker(doc, 'This week', y); y += 26;
  h2(doc, 'Your 30-minute setup', y); y += 30;
  const steps = [
    `Open ${plan.vat ? 'three' : 'two'} extra pots with your bank. Name them "Tax: untouchable"${plan.vat ? ', "VAT"' : ''} and "Slow-month buffer".`,
    'Every time a payment comes in, split it using your "from every £1,000" numbers.',
    d.t ? `Once the change above is in place, pay yourself ${m(d.goal.c.weekly)} on the same day every week, by standing order. Until then, move the tax${plan.vat ? ' and VAT' : ''} first.` : `Pay yourself ${m(c.weekly)} on the same day every week, by standing order.`,
    'Never touch Tax.',
  ];
  steps.forEach((st) => {
    doc.setDrawColor(...C.gold); doc.setLineWidth(1.2); doc.roundedRect(X, y - 11, 14, 14, 3, 3, 'S');
    y = para(doc, st, y, { x: X + 26, width: CW - 26, color: C.text, size: 11.5 }) + 10;
  });
  para(doc, 'Run a limited company? Ask your accountant how to pay this to yourself.', y + 2, { size: 10 });

  // ---- page 4: slow months, tax, the session ----
  doc.addPage(); page(doc, 4);
  y = 100;
  kicker(doc, 'When a slow month comes', y); y += 22;
  y = para(doc, 'Your wage comes from the buffer, never from Tax. Then in the next good month, top the buffer up first.', y, { color: C.text, size: 11.5 }) + 22;

  kicker(doc, 'A tax note', y); y += 22;
  y = para(doc, "Check your real tax figure with your accountant. If it's your first year paying tax this way, your January bill can include half of next year's tax too, paid early.", y);
  doc.setFont('Inter', 'semibold'); doc.setFontSize(10.5); doc.setTextColor(...C.gold);
  doc.textWithLink('How payments on account work (GOV.UK)', X, y + 4, { url: POA_URL });
  y += 40;

  panel(doc, y, 150, C.gold);
  doc.setFont('Fraunces', 'normal'); doc.setFontSize(18); doc.setTextColor(...C.text); doc.text('Want your exact number?', X + 20, y + 34);
  para(doc, 'These numbers are a rough guide. On a Cash Flow Session I build your cash flow model with you, live on screen, from rough numbers you give me. No bank statements, no bank details. 75 minutes. You leave knowing your exact number.', y + 58, { x: X + 20, width: CW - 40, size: 10.5 });
  doc.setFillColor(...C.gold); doc.roundedRect(X + 20, y + 102, 250, 32, 8, 8, 'F');
  doc.setFont('Inter', 'bold'); doc.setFontSize(11); doc.setTextColor(...C.onGold);
  doc.text('Book a Cash Flow Session (£99.97)', X + 145, y + 122, { align: 'center' });
  doc.link(X + 20, y + 102, 250, 32, { url: CALENDLY });
  y += 178;

  para(doc, 'This plan is educational, not financial advice. It does maths on the numbers you gave. Check your tax with your accountant.', y, { size: 9 });

  return Buffer.from(doc.output('arraybuffer'));
}

module.exports = { build, planText, buildPdf, calc, normalise, targets };
