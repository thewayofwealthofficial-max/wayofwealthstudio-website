// Shared cash-flow computation + chart rendering, used by both the tool page
// (on-screen) and the booking page (to rebuild the PDF's chart client-side).
// Keeps the two in exact sync and lets the booking page regenerate the whole
// report from just the stashed answers — so nothing large crosses pages.

import { projectYears, findTimeToGoal, requiredMonthlySurplusToHitGoal } from './projections';
import { DEFAULT_ASSUMPTIONS, DEFAULT_PERSON_ID } from './types';

const NOW_Y = new Date().getFullYear();

const gbp0 = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 });
export const money = n => gbp0.format(Math.round(n));
export function moneyK(n) {
  const a = Math.abs(n), s = n < 0 ? '-' : '';
  if (a >= 1e6) return s + '£' + (a / 1e6).toFixed(a >= 1e7 ? 1 : 2) + 'm';
  if (a >= 1000) return s + '£' + (a / 1000).toFixed(a >= 1e5 ? 0 : 1) + 'k';
  return money(n);
}

function buildPlan(a, horizon, investLeftover) {
  const tax = a.income * a.taxPct / 100;
  return {
    people: [{ id: DEFAULT_PERSON_ID, name: 'You', currentAge: a.ageNow }],
    income: [{ id: 'inc', label: 'Income', amount: a.income, frequency: 'monthly', isGross: false }],
    expenses: [
      { id: 'tax', category: 'essentials', label: 'Tax set-aside', amount: tax, priority: 1 },
      { id: 'biz', category: 'essentials', label: 'Cost of working', amount: a.business, priority: 1 },
      { id: 'ess', category: 'essentials', label: 'Essential bills', amount: a.essentials, priority: 1 },
      { id: 'debt', category: 'essentials', label: 'Debt repayments', amount: a.debt, priority: 1 },
      { id: 'life', category: 'discretionary', label: 'Lifestyle', amount: a.lifestyle, priority: 3 },
    ],
    debts: [],
    savings: [
      { id: 'cash', label: 'Cash savings', kind: 'cash', current: a.cash, monthlyAmount: 0, wrapper: 'cash_taxed', ownerId: DEFAULT_PERSON_ID },
      { id: 'investments', label: 'Investments', kind: 'stocks', current: a.investments, monthlyAmount: a.savings, wrapper: 'isa', ownerId: DEFAULT_PERSON_ID },
      { id: 'pension', label: 'Pension', kind: 'pension', current: a.pension, monthlyAmount: 0, wrapper: 'isa', ownerId: DEFAULT_PERSON_ID },
    ],
    interventions: [],
    surplusDestinations: investLeftover ? [{ id: 'sd', target: { kind: 'bucket', bucketId: 'investments' } }] : [],
    contextNote: '', coachPrepNotes: '',
    assumptions: { ...DEFAULT_ASSUMPTIONS, horizonYears: horizon, region: 'UK' },
  };
}

export function snapshot(a) {
  const tax = a.income * a.taxPct / 100;
  const out = tax + a.business + a.essentials + a.debt + a.lifestyle;
  const afterOut = a.income - out;
  const affSave = Math.max(0, Math.min(a.savings, afterOut));
  return { tax, out, afterOut, affSave, gap: afterOut - a.savings };
}

export function computeProjection(a) {
  const snap = snapshot(a);
  const yearsToRet = Math.max(1, Math.round(a.retireAge - a.ageNow));
  const goalYears = Math.max(1, Math.round(a.targetYear - NOW_Y));
  const horizon = Math.min(30, Math.max(10, yearsToRet, goalYears));
  const asm = { ...DEFAULT_ASSUMPTIONS, horizonYears: horizon, region: 'UK' };

  const planAuto = buildPlan(a, horizon, false);
  const planJob = buildPlan(a, horizon, true);
  const rowsAuto = projectYears(planAuto, asm);
  const rowsJob = projectYears(planJob, asm);

  const auto = rowsAuto.slice(1).map(r => r.netWorth);
  const job = rowsJob.slice(1).map(r => r.netWorth);
  let firstShortfall = null;
  for (let i = 1; i < rowsAuto.length; i++) { if ((rowsAuto[i].shortfall || 0) > 0) { firstShortfall = i; break; } }

  const retIdx = Math.min(yearsToRet, horizon) - 1;
  const goalIdx = Math.min(goalYears, horizon) - 1;
  const potNeeded = a.desiredIncome * 25;

  const ttg = findTimeToGoal(rowsAuto, a.targetAmount);
  let hitYear = null;
  if (ttg) hitYear = ttg.alreadyHit ? NOW_Y : (ttg.outOfHorizon ? null : NOW_Y + Math.round(ttg.yearsFromNow));
  let reqExtra = null, reqUnreachable = false;
  if (a.targetAmount > 0) {
    const req = requiredMonthlySurplusToHitGoal(planAuto, asm, a.targetAmount, goalYears, { bucketId: 'investments' });
    if (req) { if (req.alreadyOnTrack) reqExtra = 0; else if (req.unreachable) reqUnreachable = true; else reqExtra = req.extraMonthly; }
  }

  const proj = {
    auto, job, horizon, yearsToRet, retIdx, goalIdx, potNeeded,
    potAtRetAuto: auto[retIdx], potAtRetJob: job[retIdx],
    startNW: rowsAuto[0].netWorth, firstShortfall, hitYear, reqExtra, reqUnreachable,
    retGap: potNeeded - auto[retIdx],
  };
  return { proj, snap };
}

function cssVar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
function hexA(v, a) {
  if (v[0] === '#') { let h = v.slice(1); if (h.length === 3) h = h.split('').map(c => c + c).join(''); return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`; }
  return v;
}

// Draw the two-line net-worth chart onto `canvas`. Returns a PNG data URL.
// opts.width forces a size when the canvas isn't laid out (offscreen use).
export function renderChart(canvas, proj, answers, opts) {
  const ctx = canvas.getContext('2d'), dpr = window.devicePixelRatio || 1;
  const cssW = (opts && opts.width) || canvas.clientWidth || 760;
  const cssH = Math.max(270, Math.min(370, cssW * 0.46));
  canvas.width = cssW * dpr; canvas.height = cssH * dpr; canvas.style.height = cssH + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, cssW, cssH);
  const padL = 56, padR = 18, padT = 22, padB = 34, W = cssW - padL - padR, H = cssH - padT - padB, n = proj.horizon;
  const vals = proj.auto.concat(proj.job).concat([0, proj.potNeeded]);
  let maxV = Math.max(...vals), minV = Math.min(...vals);
  if (maxV === minV) maxV = minV + 1;
  maxV += (maxV - minV) * 0.10; if (minV < 0) minV -= (maxV - minV) * 0.04;
  const navy = cssVar('--color-navy') || '#1C2A3A', slate = cssVar('--color-slate') || '#4F5C6B', gold = cssVar('--color-gold') || '#C4A265';
  const line = 'rgba(28,42,58,0.12)', paper = cssVar('--color-bg-white') || '#FAFAF7';
  const X = i => padL + (n <= 1 ? 0 : (i / (n - 1)) * W);
  const Y = v => padT + (1 - (v - minV) / (maxV - minV)) * H;
  ctx.font = '11px Inter, sans-serif'; ctx.textBaseline = 'middle';
  for (let g = 0; g <= 4; g++) { const val = minV + (maxV - minV) * (g / 4), yy = Y(val); ctx.strokeStyle = line; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(padL + W, yy); ctx.stroke(); ctx.fillStyle = slate; ctx.textAlign = 'right'; ctx.fillText(moneyK(val), padL - 10, yy); }
  const stepX = n > 16 ? 5 : (n > 8 ? 2 : 1);
  ctx.textAlign = 'center'; ctx.fillStyle = slate;
  for (let i = 0; i < n; i++) { if (i % stepX === 0 || i === n - 1) ctx.fillText("’" + String(NOW_Y + i + 1).slice(2), X(i), padT + H + 18); }
  if (proj.potNeeded > 0 && proj.potNeeded <= maxV) {
    ctx.strokeStyle = gold; ctx.lineWidth = 1.5; ctx.setLineDash([5, 4]); ctx.beginPath(); ctx.moveTo(padL, Y(proj.potNeeded)); ctx.lineTo(padL + W, Y(proj.potNeeded)); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = gold; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom'; ctx.font = '600 11px Inter, sans-serif'; ctx.fillText('retire on ' + money(answers.desiredIncome) + '/yr', padL + 4, Y(proj.potNeeded) - 4);
  }
  const rX = X(Math.min(proj.retIdx, n - 1)); ctx.strokeStyle = slate; ctx.globalAlpha = .45; ctx.setLineDash([2, 3]); ctx.beginPath(); ctx.moveTo(rX, padT); ctx.lineTo(rX, padT + H); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1;
  const plot = (series, color, width, fill) => {
    if (fill) { const gr = ctx.createLinearGradient(0, padT, 0, padT + H); gr.addColorStop(0, hexA(color, .20)); gr.addColorStop(1, hexA(color, 0)); ctx.beginPath(); ctx.moveTo(X(0), Y(series[0])); for (let i = 0; i < n; i++) ctx.lineTo(X(i), Y(series[i])); ctx.lineTo(X(n - 1), Y(minV)); ctx.lineTo(X(0), Y(minV)); ctx.closePath(); ctx.fillStyle = gr; ctx.fill(); }
    ctx.beginPath(); for (let j = 0; j < n; j++) { const px = X(j), py = Y(series[j]); j === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py); } ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
    ctx.beginPath(); ctx.arc(X(n - 1), Y(series[n - 1]), width + 1.5, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill(); ctx.strokeStyle = paper; ctx.lineWidth = 2; ctx.stroke();
  };
  plot(proj.auto, slate, 2, false);
  plot(proj.job, gold, 3, true);
  ctx.font = '600 13px Inter, sans-serif'; ctx.textAlign = 'right'; ctx.textBaseline = 'bottom'; ctx.fillStyle = navy; ctx.fillText(moneyK(proj.job[n - 1]), padL + W - 4, Y(proj.job[n - 1]) - 9);
  return canvas.toDataURL('image/png');
}
