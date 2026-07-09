// Client-side PDF report generator for the Cash Flow Model lead magnet.
// Runs entirely in the browser (jsPDF) so the user's figures never leave their
// device. Called by cash-flow-model.astro after the projection is computed.
//
// generateReport(answers, proj, snap, chart)
//   answers : the 10 raw inputs
//   proj    : output of the page's compute() (auto/job net-worth arrays, retirement + goal analytics)
//   snap    : today's monthly snapshot { tax, afterOut, affSave, gap }
//   chart   : { url: dataURL(PNG of the on-screen chart), ratio: height/width }

import { jsPDF } from 'jspdf';

const NAVY = [28, 42, 58], CREAM = [245, 240, 232], GOLD = [196, 162, 101], GOLDD = [159, 124, 52],
  SLATE = [123, 133, 147], CREAM_DIM = [200, 193, 180], GOOD = [63, 122, 85], BAD = [178, 58, 72],
  PAPER = [251, 250, 247], LINE = [221, 214, 201], INK = [28, 42, 58];

const CALENDLY = 'https://calendly.com/thewayofwealth-official/20min';

const gbp0 = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 });
const money = n => gbp0.format(Math.round(n));
function moneyK(n) {
  const a = Math.abs(n), s = n < 0 ? '-' : '';
  if (a >= 1e6) return s + '£' + (a / 1e6).toFixed(a >= 1e7 ? 1 : 2) + 'm';
  if (a >= 1000) return s + '£' + (a / 1000).toFixed(a >= 1e5 ? 0 : 1) + 'k';
  return money(n);
}

export function generateReport(a, proj, snap, chart) {
  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const M = 46;
  const CW = W - M * 2;
  const NOW_Y = new Date().getFullYear();
  const retAge = Math.round(a.retireAge);

  const fill = c => doc.setFillColor(c[0], c[1], c[2]);
  const ink = c => doc.setTextColor(c[0], c[1], c[2]);
  const stroke = c => doc.setDrawColor(c[0], c[1], c[2]);
  const wrap = (t, w) => doc.splitTextToSize(t, w);

  function paper() { fill(PAPER); doc.rect(0, 0, W, H, 'F'); }
  function footer(page) {
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8); ink(SLATE);
    doc.text('Way of Wealth · Educational estimate, not financial advice', M, H - 30);
    doc.text(page + ' of 4', W - M, H - 30, { align: 'right' });
  }
  function sectionHead(kick, title, sub, y) {
    doc.setFont('helvetica', 'bold'); doc.setFontSize(9); ink(GOLDD); doc.text(kick.toUpperCase(), M, y);
    doc.setFont('times', 'bold'); doc.setFontSize(26); ink(NAVY); doc.text(title, M, y + 30);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(11); ink(SLATE);
    const lines = wrap(sub, CW * 0.9); doc.text(lines, M, y + 52);
    return y + 52 + lines.length * 14;
  }
  function callout(x, y, w, kind, title, body) {
    const bg = kind === 'warn' ? [251, 244, 245] : kind === 'win' ? [244, 249, 245] : [250, 246, 238];
    const bd = kind === 'warn' ? BAD : kind === 'win' ? GOOD : GOLD;
    doc.setFont('helvetica', 'normal'); doc.setFontSize(11);
    const bodyLines = wrap(body, w - 32);
    const h = 30 + bodyLines.length * 13 + 8;
    fill(bg); stroke(bd); doc.setLineWidth(0.8); doc.roundedRect(x, y, w, h, 8, 8, 'FD');
    doc.setFont('helvetica', 'bold'); doc.setFontSize(11); ink(NAVY); doc.text(title, x + 16, y + 22);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(10.5); ink(SLATE); doc.text(bodyLines, x + 16, y + 38);
    return y + h;
  }

  const spare = Math.max(0, snap.gap);
  const leakOver = proj.job[proj.horizon - 1] - proj.auto[proj.horizon - 1];

  /* ===================== PAGE 1 — COVER ===================== */
  paper();
  fill(NAVY); doc.circle(M + 9, 60, 9, 'F');
  doc.setFont('times', 'bold'); doc.setFontSize(11); ink(CREAM); doc.text('W', M + 9, 64, { align: 'center' });
  doc.setFont('helvetica', 'bold'); doc.setFontSize(9); ink(NAVY); doc.text('WAY OF WEALTH', M + 26, 63);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); ink(SLATE);
  doc.text('Prepared for you', W - M, 58, { align: 'right' });
  stroke(LINE); doc.setLineWidth(0.7); doc.line(M, 78, W - M, 78);

  doc.setFont('helvetica', 'bold'); doc.setFontSize(9); ink(GOLDD); doc.text('YOUR CASH FLOW MODEL', M, 126);
  doc.setFont('times', 'bold'); doc.setFontSize(42); ink(NAVY);
  doc.text('Where your', M, 172); doc.text('money takes you.', M, 214);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(12); ink(SLATE);
  doc.text(wrap('A clear read on where every pound goes each month — and where that leaves you by the age you want work to become optional.', CW * 0.7), M, 246);

  const py = 300, ph = 214;
  fill(NAVY); doc.roundedRect(M, py, CW, ph, 12, 12, 'F');
  doc.setFont('helvetica', 'bold'); doc.setFontSize(9); ink(GOLD); doc.text('THE HEADLINE', M + 26, py + 34);
  doc.setFont('times', 'normal'); doc.setFontSize(19); ink(CREAM);
  const headline = proj.retGap > proj.potNeeded * 0.05
    ? `On your current path you reach ${moneyK(proj.potAtRetAuto)} by ${retAge} — the life you described needs ${moneyK(proj.potNeeded)}.`
    : `You’re on track to reach ${retAge} with about ${moneyK(proj.potAtRetAuto)} behind you.`;
  doc.text(wrap(headline, CW - 52), M + 26, py + 62);

  const stats = [
    ['Spare each month', snap.gap < -1 ? money(-snap.gap) : money(spare)],
    ['Saved so far', moneyK(proj.startNW)],
    [`At ${retAge}, with a job`, moneyK(proj.potAtRetJob)],
  ];
  const sw = (CW - 52) / 3;
  stats.forEach((s, i) => {
    const sx = M + 26 + i * sw, sy = py + ph - 58;
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); ink(CREAM_DIM); doc.text(s[0], sx, sy);
    doc.setFont('times', 'bold'); doc.setFontSize(20); ink(i === 2 ? GOLD : CREAM); doc.text(s[1], sx, sy + 24);
  });

  stroke(LINE); doc.line(M, py + ph + 34, W - M, py + ph + 34);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(9); ink(SLATE);
  doc.text(wrap('Private by design. These figures were worked out on your own device — we never saw them and they were never stored. The only thing you shared was your email. This report is an educational estimate, not financial advice.', CW), M, py + ph + 52);
  footer(1);

  /* ===================== PAGE 2 — THE MONTH ===================== */
  doc.addPage(); paper();
  let y = sectionHead('The month', 'Where your money goes', 'Every pound that comes in, and the job it’s doing — this is the picture before anything’s left over, and it’s where the leaks hide.', 100);
  y += 20;

  const rows = [
    { name: 'Tax pot', val: snap.tax, c: NAVY },
    { name: 'Cost of working', val: a.business, c: [110, 124, 140] },
    { name: 'Essential bills', val: a.essentials, c: [138, 151, 166] },
    { name: 'Debt', val: a.debt, c: BAD },
    { name: 'Lifestyle', val: a.lifestyle, c: [201, 164, 106] },
    { name: 'Saving', val: snap.affSave, c: GOLD },
  ];
  if (snap.gap >= 50) rows.push({ name: 'Slips away', val: snap.gap, c: GOOD });
  const maxV = a.income || 1;

  // stacked bar
  let sx0 = M;
  const barY = y, barH = 26;
  rows.forEach(r => { const w = (r.val / maxV) * CW; fill(r.c); doc.rect(sx0, barY, w, barH, 'F'); sx0 += w; });
  stroke(LINE); doc.setLineWidth(0.8); doc.rect(M, barY, CW, barH, 'S');
  y = barY + barH + 26;

  // rows
  const labelW = 150, valW = 70, trackX = M + labelW, trackW = CW - labelW - valW - 16;
  rows.forEach(r => {
    fill(r.c); doc.circle(M + 4, y - 3, 3.2, 'F');
    doc.setFont('helvetica', 'normal'); doc.setFontSize(10.5); ink(NAVY); doc.text(r.name, M + 14, y);
    fill([232, 236, 240]); doc.roundedRect(trackX, y - 9, trackW, 11, 3, 3, 'F');
    fill(r.c); doc.roundedRect(trackX, y - 9, Math.max(2, (r.val / maxV) * trackW), 11, 3, 3, 'F');
    doc.setFont('helvetica', 'bold'); doc.setFontSize(10.5); ink(NAVY); doc.text(money(r.val), W - M, y, { align: 'right' });
    y += 22;
  });
  y += 10;

  y = callout(M, y, CW, 'gold', `Your tax pot: ${money(snap.tax)} a month, ${money(snap.tax * 12)} a year`,
    'Carved off the second money lands, this is the pot that keeps a tax bill from becoming a crisis — the single most important habit for anyone self-employed.') + 12;
  if (snap.gap >= 50) {
    callout(M, y, CW, 'win', `${money(snap.gap)} a month has no job`,
      'It’s not lost to bills — it just drifts, so it gets spent. That’s the number this whole report is really about.');
  } else if (snap.gap < -1) {
    callout(M, y, CW, 'warn', `You’re spending ${money(-snap.gap)} more than comes in`,
      'That gap gets filled by savings, debt, or a good month covering a bad one. Left alone, it compounds.');
  }
  footer(2);

  /* ===================== PAGE 3 — THE ROAD ===================== */
  doc.addPage(); paper();
  y = sectionHead('The road ahead', `From now to age ${retAge}`, 'Same income, same habits. Grey is autopilot — spare cash spent. Gold is what happens when every spare pound is given a job. The dashed line is the pot that funds the retirement you described.', 100);
  y += 14;

  if (chart && chart.url) {
    const imgH = CW * (chart.ratio || 0.46);
    doc.addImage(chart.url, 'PNG', M, y, CW, imgH);
    y += imgH + 24;
  }

  // three tiles
  const tiles = [
    ['At ' + retAge + ' · autopilot', moneyK(proj.potAtRetAuto), 'spare cash spent', proj.retGap > proj.potNeeded * 0.05 ? BAD : NAVY],
    ['The target', moneyK(proj.potNeeded), money(a.desiredIncome) + '/yr on the 4% rule', NAVY],
    ['At ' + retAge + ' · with a job', moneyK(proj.potAtRetJob), 'every spare £ invested', GOLDD],
  ];
  const tw = (CW - 24) / 3, th = 78;
  tiles.forEach((t, i) => {
    const tx = M + i * (tw + 12);
    fill([255, 255, 255]); stroke(LINE); doc.setLineWidth(0.8); doc.roundedRect(tx, y, tw, th, 8, 8, 'FD');
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); ink(SLATE); doc.text(wrap(t[0], tw - 20), tx + 12, y + 20);
    doc.setFont('times', 'bold'); doc.setFontSize(22); ink(t[3]); doc.text(t[1], tx + 12, y + 50);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8); ink(SLATE); doc.text(wrap(t[2], tw - 20), tx + 12, y + 66);
  });
  footer(3);

  /* ===================== PAGE 4 — GOALS & MOVES ===================== */
  doc.addPage(); paper();
  y = sectionHead('Your goal & first moves', 'What to do about it', 'Small, behavioural, and specific to your numbers. Not advice — habits.', 100);
  y += 16;

  // goal callout
  if (a.targetAmount > 0) {
    if (proj.reqExtra === 0 && proj.hitYear && proj.hitYear <= a.targetYear) {
      y = callout(M, y, CW, 'win', `Your ${money(a.targetAmount)} goal: on track`,
        `On your current path you cross it around ${proj.hitYear} — ${proj.hitYear < a.targetYear ? (a.targetYear - proj.hitYear) + ' year(s) early.' : 'right on time.'}`) + 14;
    } else if (proj.reqUnreachable) {
      y = callout(M, y, CW, 'warn', `Your ${money(a.targetAmount)} goal by ${a.targetYear} is a stretch`,
        'Even investing hard, this path doesn’t quite get there in time. Worth a proper look at the income or the timeline.') + 14;
    } else if (proj.reqExtra != null) {
      y = callout(M, y, CW, 'warn', `Your ${money(a.targetAmount)} goal needs about ${money(proj.reqExtra)}/month more`,
        `${proj.hitYear ? 'On today’s habits you’d hit it around ' + proj.hitYear + '. ' : ''}Finding ${money(proj.reqExtra)} a month gets you there by ${a.targetYear}.`) + 14;
    }
  }

  doc.setFont('times', 'bold'); doc.setFontSize(16); ink(NAVY); doc.text('Three moves that change the picture', M, y + 6); y += 22;
  const moves = [
    ['1', 'Split it the second it lands', `The day money arrives, move your ${Math.round(a.taxPct)}% tax into a separate pot. You can’t spend what you can’t see — and the bill never surprises you again.`],
    ['2', `Give your spare ${money(spare)} a job before the month starts`, `Name where it goes on day one — savings, investments, debt. Money with a job doesn’t drift. That single habit is worth about ${moneyK(leakOver)} more by ${NOW_Y + proj.horizon}.`],
    ['3', 'Build one month of buffer before you invest more', 'A single slow month is what turns spare cash into debt. Cover one month of essentials in easy-access cash first — then everything above it can go to work.'],
  ];
  moves.forEach(m => {
    doc.setFont('helvetica', 'normal'); doc.setFontSize(11); const bl = wrap(m[2], CW - 60);
    const h = 24 + bl.length * 13 + 8;
    fill([255, 255, 255]); stroke(LINE); doc.setLineWidth(0.8); doc.roundedRect(M, y, CW, h, 8, 8, 'FD');
    doc.setFont('times', 'bold'); doc.setFontSize(20); ink(GOLDD); doc.text(m[0], M + 16, y + 26);
    doc.setFont('helvetica', 'bold'); doc.setFontSize(11.5); ink(NAVY); doc.text(m[1], M + 44, y + 20);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(10.5); ink(SLATE); doc.text(bl, M + 44, y + 36);
    y += h + 10;
  });

  // CTA panel
  y += 4;
  const ch = 120;
  fill(NAVY); doc.roundedRect(M, y, CW, ch, 12, 12, 'F');
  doc.setFont('times', 'bold'); doc.setFontSize(17); ink(CREAM); doc.text('The leak isn’t a maths problem. It’s a habit problem.', M + 22, y + 34, { maxWidth: CW - 44 });
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10.5); ink(CREAM_DIM);
  doc.text(wrap('If this report showed you a gap, the quickest way to close it is a proper look at your numbers together — no pressure, just straight talk.', CW - 200), M + 22, y + 58);
  // gold button (clickable → Calendly)
  const bx = M + 22, by = y + ch - 44, bw = 168, bh = 30;
  fill(GOLD); doc.roundedRect(bx, by, bw, bh, 6, 6, 'F');
  doc.setFont('helvetica', 'bold'); doc.setFontSize(11); ink(NAVY); doc.text('Book your free call  →', bx + bw / 2, by + 20, { align: 'center' });
  doc.link(bx, by, bw, bh, { url: CALENDLY });

  // credential + disclaimer
  y += ch + 24;
  stroke(LINE); doc.line(M, y, W - M, y); y += 18;
  doc.setFont('helvetica', 'bold'); doc.setFontSize(10); ink(NAVY);
  doc.text('Joel Ezekiel', M, y);
  doc.setFont('helvetica', 'normal'); ink(SLATE);
  doc.text(' · MSc Behavioural Economics | Qualified Financial Planner', M + doc.getTextWidth('Joel Ezekiel'), y);
  doc.setFontSize(8); y += 16;
  doc.text(wrap('This report is an educational estimate, not regulated financial advice. Projections assume income rises ~2%/yr, costs ~2.5%/yr, cash grows 4%, investments 7% and pensions 5%, with your monthly saving invested. The retirement target assumes a ~4% annual drawdown — a rule of thumb, not a guarantee. Your real path will vary.', CW), M, y);
  footer(4);

  doc.save('way-of-wealth-cash-flow-model.pdf');
}
