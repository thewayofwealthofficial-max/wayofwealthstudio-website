/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Copied from the coaching portal by scripts/sync-cashflow-engine.mjs.
 * Change the portal, run `npm run sync:engine`, commit the result.
 */
import type {
  AssetKind,
  CashflowPlanData,
  DebtLine,
  ExpenseLine,
  Intervention,
  ProjectionAssumptions,
  SavingsAllocation,
  YearProjection,
} from "./types";
import { DEFAULT_UK_TAX, DEFAULT_UK_ALLOWANCES, DEFAULT_US_TAX_SINGLE, DEFAULT_LIQUIDATION_ORDER, expensePriority, resolveSteppedAmount, effectivePeople, resolvePersonId, taxCategoryOf } from "./types";
import type { TaxWrapper } from "./types";
import { totalDebtBalance, totalDebtPayments, totalExpenses } from "./cashflow-calc";
import { calcUKTaxAndNI, ukMarginalBand, taperedPensionAllowance, calcUKInvestmentTax } from "./uk-tax";
import { calcUSTaxAndFICA } from "./us-tax";

/**
 * Sum monthly take-home income (post-tax for gross lines, raw for net lines)
 * given the current set of income lines and the plan's region tax model.
 *
 * Couples: gross lines are grouped BY personId and each person is taxed
 * separately (own Personal Allowance, bands, NI). For a single person (all
 * lines share a personId, or none is set) this is identical to taxing the
 * pooled total. Net (already post-tax) lines are pooled regardless of person.
 * `grossByPerson` is returned so the pension annual allowance can be tapered
 * per person.
 */
function netMonthlyIncomeFromLines(
  lines: { amount: number; isGross?: boolean; personId?: string }[],
  assumptions: ProjectionAssumptions
): {
  netMonthly: number;
  grossAnnual: number;
  taxAnnual: number;
  niAnnual: number;
  grossByPerson: Record<string, number>;
} {
  let netMonthly = 0;
  let grossAnnual = 0;
  let taxAnnual = 0;
  let niAnnual = 0;
  const grossByPerson: Record<string, number> = {};
  const region = assumptions.region ?? "UK";

  // Net (post-tax) lines pool together — no tax applied.
  netMonthly += lines.filter((l) => !l.isGross).reduce((s, l) => s + (l.amount || 0), 0);

  // Gross lines grouped per person, each taxed on their own.
  const grossMonthlyByPerson: Record<string, number> = {};
  for (const l of lines) {
    if (!l.isGross) continue;
    const pid = l.personId ?? "__default";
    grossMonthlyByPerson[pid] = (grossMonthlyByPerson[pid] || 0) + (l.amount || 0);
  }

  for (const [pid, grossMonthly] of Object.entries(grossMonthlyByPerson)) {
    if (grossMonthly <= 0) continue;
    const annualGross = grossMonthly * 12;
    grossAnnual += annualGross;
    grossByPerson[pid] = annualGross;
    if (region === "UK") {
      const t = calcUKTaxAndNI(annualGross, assumptions.ukTax ?? DEFAULT_UK_TAX);
      taxAnnual += t.tax;
      niAnnual += t.ni;
      netMonthly += t.takeHome / 12;
    } else if (region === "US") {
      const t = calcUSTaxAndFICA(annualGross, assumptions.usTax ?? DEFAULT_US_TAX_SINGLE);
      taxAnnual += t.tax;
      niAnnual += t.fica; // niAnnual field reused for US FICA — UI labels appropriately
      netMonthly += t.takeHome / 12;
    } else {
      // OTHER region — no tax modelling. Treat gross amounts as if they were net.
      netMonthly += grossMonthly;
    }
  }
  return { netMonthly, grossAnnual, taxAnnual, niAnnual, grossByPerson };
}

/**
 * Project a cashflow plan year-by-year over the assumption horizon.
 *
 * Methodology:
 * - Income grows at incomeGrowthPct/yr (subject to interventions)
 * - Expenses grow at expenseInflationPct/yr (subject to interventions)
 * - Each savings allocation has a `kind` (cash / stocks / pension / property)
 *   and grows at the per-class rate
 * - Pension contributions get a tax-relief uplift (default 25% — UK basic rate);
 *   the contribution credited is monthlyAmount × (1 + taxRelief/100)
 * - Debt actual payments stay constant unless interventions change them;
 *   balances amortise with interest at each debt's rate
 * - Interventions fire at their year:
 *     income_change / expense_change / savings_change → permanent monthly delta
 *     lump_sum_in / lump_sum_out → one-time bucket adjustment
 *     buy_house → zero a rent line, add a mortgage payment, take a deposit
 *                 from cash, add a property asset that appreciates
 * - Net worth = sum of savings (across all classes) - remaining debt
 *
 * Year 0 is "today" — current state.
 */
export function projectYears(
  plan: CashflowPlanData,
  assumptions: ProjectionAssumptions
): YearProjection[] {
  // 75 years covers a 25-year-old planned through to 100. The old 30-year cap
  // silently truncated any real retirement plan.
  const horizon = Math.max(1, Math.min(75, assumptions.horizonYears || 5));
  const incomeGrowth = (assumptions.incomeGrowthPct || 0) / 100;
  const expenseInflation = (assumptions.expenseInflationPct || 0) / 100;
  const taxReliefMultiplier = 1 + (assumptions.pensionTaxReliefPct || 0) / 100;

  const classGrowth = (kind: AssetKind | undefined): number => {
    const k = kind ?? "cash";
    if (k === "stocks") return (assumptions.stocksGrowthPct || 0) / 100;
    if (k === "pension") return (assumptions.pensionGrowthPct || 0) / 100;
    if (k === "property") return (assumptions.propertyGrowthPct || 0) / 100;
    // cash falls back to legacy savingsGrowthPct if cashGrowthPct missing
    return (
      ((assumptions.cashGrowthPct ?? assumptions.savingsGrowthPct) || 0) / 100
    );
  };

  // People (1 single, 2 a couple). Legacy plans synthesise a single person.
  const people = effectivePeople(plan);
  // Survivor scenario: the year (1-indexed) each person dies, if ever. Declared
  // up here because activeIncome (used from year 0) closes over it.
  const deceasedFrom: Record<string, number> = {};

  // Mutable income lines so interventions can add new gross/net income.
  // `amount` is the working per-year value; `base`+`steps` drive the stepped
  // schedule. Lines with steps use absolute step values (no auto-growth);
  // lines without steps grow `amount` by incomeGrowth each year. personId is
  // resolved to a concrete person up front so per-person tax lines up.
  type IncomeState = { amount: number; base: number; isGross?: boolean; label: string; steps?: import("./types").AmountStep[]; startYear?: number; endYear?: number; personId: string };
  let incomeLines: IncomeState[] = plan.income.map((l) => ({
    amount: l.amount || 0,
    base: l.amount || 0,
    isGross: l.isGross,
    label: l.label,
    steps: l.steps,
    startYear: l.startYear,
    endYear: l.endYear,
    personId: resolvePersonId(l.personId, people),
  }));

  // Is an income stream active in projection year y? (year 0 = today).
  const incomeInWindow = (l: { startYear?: number; endYear?: number }, y: number): boolean =>
    (l.startYear === undefined || y >= l.startYear) &&
    (l.endYear === undefined || y <= l.endYear);

  // Gate contributed amounts by the active window without disturbing the
  // growing base — an out-of-window line still tracks its grown value so it
  // resumes at the right figure when it switches back on.
  const activeIncome = (lines: IncomeState[], y: number): IncomeState[] =>
    lines.map((l) => {
      const dead = deceasedFrom[l.personId] !== undefined && y >= deceasedFrom[l.personId];
      return { ...l, amount: incomeInWindow(l, y) && !dead ? l.amount : 0 };
    });

  const startTax = netMonthlyIncomeFromLines(activeIncome(incomeLines, 0), assumptions);
  const startingMonthlyIncome = startTax.netMonthly;
  const startingMonthlyExpenses = totalExpenses(plan);

  // Build per-bucket balance state. monthlyContrib carried separately so
  // interventions can adjust per-bucket monthly amounts later. startYear /
  // endYear gate when the contribution actually fires — outside the window
  // the balance still compounds, but no new monthly contributions land.
  // baseMonthly = the flat / pre-first-step contribution. `steps` (when set)
  // override it per year with absolute values; deltaFromInterventions carries
  // any savings_change life-event adjustments. effectiveMonthly() combines all
  // three for a given year.
  type BucketState = {
    id: string;
    label: string;
    kind: AssetKind;
    balance: number;
    baseMonthly: number;
    steps?: import("./types").AmountStep[];
    deltaFromInterventions: number;
    startYear?: number;
    endYear?: number;
    wrapper?: TaxWrapper;
    ownerId: string;
    liquidation?: "when_needed" | "never";
    crystallised?: boolean;
    drawdown?: SavingsAllocation["drawdown"];
    withdrawalLimit?: SavingsAllocation["withdrawalLimit"];
  };
  // May the projector sell this pot down on its own to cover an overspend?
  // Property is ring-fenced by default — Voyant never auto-liquidates a primary
  // residence, and you cannot sell a house a slice at a time.
  const canLiquidate = (b: { kind: AssetKind; liquidation?: "when_needed" | "never" }): boolean =>
    (b.liquidation ?? (b.kind === "property" ? "never" : "when_needed")) === "when_needed";
  // The order pots are drawn down in. Cash is already liquid so it goes first;
  // sheltered stocks before unwrapped (which trigger CGT); pension late because
  // it is taxed on the way out; property last of all. Voyant makes this order a
  // plan setting (spec §2.5) — that is gap S7, still to come.
  /**
   * The most this pot may give up ad hoc in year `y` to plug a gap — Voyant's
   * Withdrawal Limit (spec §2.7). Infinity means "take what you need"; 0 means
   * the pot is ring-fenced. Separate from a planned withdrawal, which comes out
   * whether the plan needs it or not.
   */
  const adHocAllowance = (
    b: {
      kind: AssetKind;
      liquidation?: "when_needed" | "never";
      withdrawalLimit?: { mode: "maximum" | "none" | "capped"; capPerYear?: number; allowFromYear?: number };
    },
    y: number
  ): number => {
    if (!canLiquidate(b)) return 0;
    const wl = b.withdrawalLimit;
    if (!wl) return Infinity;
    if (wl.mode === "none") return 0;
    if (wl.allowFromYear !== undefined && y < wl.allowFromYear) return 0;
    if (wl.mode === "capped") return Math.max(0, wl.capPerYear ?? 0);
    return Infinity;
  };
  // The order pots are sold down in (spec §2.5). Cash first — it is already
  // liquid and needs no selling. Then the three tax categories in whatever
  // order the plan sets, defaulting to Voyant's: taxable, tax deferred, tax
  // free. Property is always last; a home is not a cash machine.
  const liquidationOrder = assumptions.liquidationOrder ?? DEFAULT_LIQUIDATION_ORDER;
  const liquidationTier = (b: { kind: AssetKind; wrapper?: TaxWrapper }): number => {
    if (b.kind === "cash") return 0;
    if (b.kind === "property") return 99;
    const idx = liquidationOrder.indexOf(taxCategoryOf(b));
    return 1 + (idx < 0 ? liquidationOrder.length : idx);
  };
  const effectiveMonthly = (
    b: { baseMonthly: number; steps?: import("./types").AmountStep[]; deltaFromInterventions: number },
    y: number
  ): number =>
    Math.max(0, (resolveSteppedAmount(b.baseMonthly, b.steps, y) ?? b.baseMonthly) + b.deltaFromInterventions);

  // Each person gets a default cash account, exactly as Voyant does (spec §2.2):
  // created by the software, opening balance £0, a holding tin for money that
  // has arrived but has no home yet. It is stage 2 of expense fulfilment — the
  // first place drawn from once the year's income is gone. Appended AFTER the
  // plan's own pots so nothing that indexes into the list shifts.
  const defaultCashId = (personId: string) => `__cash_${personId}`;
  const defaultCashBuckets: BucketState[] = people.map((p) => ({
    id: defaultCashId(p.id),
    label: people.length > 1 ? `${p.name}'s cash` : "Ready cash",
    kind: "cash" as AssetKind,
    balance: 0,
    baseMonthly: 0,
    deltaFromInterventions: 0,
    ownerId: p.id,
  }));

  const readyCashIds = new Set(defaultCashBuckets.map((b) => b.id));

  /**
   * Can this person legally reach their pension in projection year `y`? Age may
   * be recorded on the person OR only on the Retirement card, so fall back
   * through both. With neither, use the retirement date rather than assuming
   * the pot is available — showing a shortfall is honest, silently spending a
   * 30-year-old's pension is not.
   */
  const pensionRegionAllowances =
    (assumptions.region ?? "UK") === "UK"
      ? assumptions.ukAllowances ?? DEFAULT_UK_ALLOWANCES
      : undefined;
  const canAccessPension = (ownerId: string, y: number): boolean => {
    if (!pensionRegionAllowances) return true;
    const age = people.find((p) => p.id === ownerId)?.currentAge ?? plan.retirement?.currentAge;
    if (age !== undefined) return age + y >= pensionRegionAllowances.pensionAccessAge;
    const untilRetirement = plan.retirement?.yearsUntilRetirement;
    if (untilRetirement !== undefined) return y >= untilRetirement;
    return false;
  };

  const startingBuckets: BucketState[] = [
    ...plan.savings.map((s) => ({
      id: s.id,
      label: s.label,
      kind: s.kind ?? "cash",
      balance: s.current || 0,
      baseMonthly: s.monthlyAmount || 0,
      steps: s.steps,
      deltaFromInterventions: 0,
      startYear: s.startYear,
      endYear: s.endYear,
      wrapper: s.wrapper,
      ownerId: resolvePersonId(s.ownerId, people),
      liquidation: s.liquidation,
      crystallised: s.crystallised,
      drawdown: s.drawdown,
      withdrawalLimit: s.withdrawalLimit,
    })),
    ...defaultCashBuckets,
  ];

  const startingSavingsBalance = startingBuckets.reduce((s, b) => s + b.balance, 0);
  const startingMonthlySavings = startingBuckets.reduce((s, b) => s + b.baseMonthly, 0);
  const startingMonthlyDebtPayments = totalDebtPayments(plan);

  // Year 0 — today (interventions don't fire on year 0)
  const today: YearProjection = {
    year: 0,
    yearLabel: "Today",
    annualIncome: startingMonthlyIncome * 12,
    annualGrossIncome: startTax.grossAnnual || undefined,
    annualExpenses: startingMonthlyExpenses * 12,
    annualSurplus:
      (startingMonthlyIncome -
        startingMonthlyExpenses -
        startingMonthlyDebtPayments -
        startingMonthlySavings) *
      12,
    cumulativeSavings: startingSavingsBalance,
    cashBalance: sumByKind(startingBuckets, "cash"),
    stocksBalance: sumByKind(startingBuckets, "stocks"),
    pensionBalance: sumByKind(startingBuckets, "pension"),
    propertyBalance: sumByKind(startingBuckets, "property"),
    totalDebtBalance: totalDebtBalance(plan),
    debtBalances: plan.debts.map((d) => ({ id: d.id, name: d.name, balance: d.balance })),
    annualTaxPaid: startTax.taxAnnual || undefined,
    annualNIPaid: startTax.niAnnual || undefined,
    netWorth: startingSavingsBalance - totalDebtBalance(plan),
  };

  // Mutable working state.
  // Per-line expense state so each line can carry its own step schedule.
  // `expenseInterventionDelta` accumulates expense_change / buy_house
  // adjustments (and inflates each year, matching the old scalar behaviour).
  type ExpenseState = { base: number; amount: number; steps?: import("./types").AmountStep[] };
  let expenseLines: ExpenseState[] = (plan.expenses || []).map((e) => ({
    base: e.amount || 0,
    amount: e.amount || 0,
    steps: e.steps,
  }));
  let expenseInterventionDelta = 0;
  let monthlyExpenses = startingMonthlyExpenses;
  let buckets: BucketState[] = startingBuckets.map((b) => ({ ...b }));
  let debtState: DebtLine[] = plan.debts.map((d) => ({ ...d }));
  let interventionMonthlyDelta = 0; // accumulates income_change interventions (post-tax)
  // Survivor scenario: once a person dies, the household's base expenses scale
  // down (one mouth, not two). `deceasedFrom` is declared above.
  let expenseSurvivorFactor = 1;
  // Pinned raises: monthly £ that each income_change has earmarked for a
  // specific bucket. Persists once a raise fires (the higher pay continues),
  // so this is added to, never reset. Keyed by bucket id.
  const directedMonthlyByBucket: Record<string, number> = {};
  const surplusDestinations = (plan.surplusDestinations || []).slice();
  const interventions = (plan.interventions || []).slice();

  // Returns the next-year debts AND the per-debt principal/interest split
  // for this year (used for the year-detail breakdown).
  type DebtDelta = {
    id: string;
    name: string;
    openingBalance: number;
    interestPaid: number;
    principalPaid: number;
    paymentsMade: number;
    surplusOverpaid?: number;
    closingBalance: number;
  };
  const stepDebtsOneYear = (
    debts: DebtLine[],
  ): { next: DebtLine[]; deltas: DebtDelta[] } => {
    const deltas: DebtDelta[] = [];
    const next = debts.map((d) => {
      const opening = d.balance;
      if (d.balance <= 0) {
        deltas.push({ id: d.id, name: d.name, openingBalance: opening, interestPaid: 0, principalPaid: 0, paymentsMade: 0, closingBalance: 0 });
        return d;
      }
      let bal = d.balance;
      let interestThisYear = 0;
      let principalThisYear = 0;
      let paidThisYear = 0;
      const monthlyRate = (d.rate || 0) / 100 / 12;
      for (let m = 0; m < 12; m++) {
        if (bal <= 0) break;
        const interest = bal * monthlyRate;
        // Never pay more than it takes to clear the debt outright. This is what
        // stops a full year of payments being charged in the month it clears.
        const payment = Math.min(d.actualPayment || 0, bal + interest);
        paidThisYear += payment;
        const principal = payment - interest;
        interestThisYear += interest;
        if (principal >= 0) {
          // Payment clears the month's interest — the rest comes off the balance.
          principalThisYear += principal;
          bal -= principal;
        } else {
          // Payment does NOT cover the interest. The unpaid interest is added to
          // what's owed, so the debt grows. A negative "principal paid" is how
          // that shows up in the year-detail table.
          principalThisYear += principal;
          bal -= principal;
        }
      }
      deltas.push({
        id: d.id,
        name: d.name,
        openingBalance: opening,
        interestPaid: interestThisYear,
        principalPaid: principalThisYear,
        paymentsMade: paidThisYear,
        closingBalance: bal,
      });
      return { ...d, balance: bal };
    });
    return { next, deltas };
  };

  // Snapshot of expense category split at year 0; reused each year for the
  // year-detail breakdown. Sum to 1 unless plan.expenses is empty.
  const totalInitialExpenses = (plan.expenses || []).reduce((s, e) => s + (e.amount || 0), 0);
  const sumCat = (cat: ExpenseLine["category"]) =>
    (plan.expenses || []).filter((e) => e.category === cat).reduce((s, e) => s + (e.amount || 0), 0);
  const categoryRatios = {
    essentials: totalInitialExpenses > 0 ? sumCat("essentials") / totalInitialExpenses : 0,
    lifestyle: totalInitialExpenses > 0 ? sumCat("lifestyle") / totalInitialExpenses : 0,
    discretionary: totalInitialExpenses > 0 ? sumCat("discretionary") / totalInitialExpenses : 0,
    other: totalInitialExpenses > 0 ? sumCat("other") / totalInitialExpenses : 1,
  };

  // Snapshot of the spend split by funding priority (Basics/Leisure/Luxury).
  // Used to attribute any shortfall to the tiers sacrificed first.
  const sumPriority = (pr: 1 | 2 | 3) =>
    (plan.expenses || [])
      .filter((e) => expensePriority(e) === pr)
      .reduce((s, e) => s + (e.amount || 0), 0);
  const priorityRatios = {
    basics: totalInitialExpenses > 0 ? sumPriority(1) / totalInitialExpenses : 1,
    leisure: totalInitialExpenses > 0 ? sumPriority(2) / totalInitialExpenses : 0,
    luxury: totalInitialExpenses > 0 ? sumPriority(3) / totalInitialExpenses : 0,
  };

  const projections: YearProjection[] = [today];
  const startYear = new Date().getFullYear();

  for (let y = 1; y <= horizon; y++) {
    const events: string[] = [];

    // Balances BEFORE any life event fires. Without this snapshot an event's
    // spending is invisible: the pot is already lower by the time the year
    // detail records its opening balance.
    const openingBalances = new Map(buckets.map((b) => [b.id, b.balance]));
    // What each pot paid out to / received from life events this year.
    const eventPaidOut: Record<string, number> = {};
    const eventPaidIn: Record<string, number> = {};
    // Money a life event needed and no pot could provide. Never invented —
    // it lands in this year's shortfall.
    let unfundedEventSpend = 0;

    /**
     * Take `amount` out of the plan to pay for a life event, honouring Voyant's
     * payment-source rules (spec §2.1):
     *   1. the named Payment Source, if there is one
     *   2. "Only Allowed Source" stops there — any gap is a shortfall by design
     *   3. otherwise the payer's default cash account, then every other
     *      liquidatable pot in liquidation order
     * Returns what was actually funded. The caller decides what to do with any
     * gap; the engine never quietly makes the money up.
     */
    const spendForEvent = (
      amount: number,
      opts: { sourceBucketId?: string; onlySource?: boolean; ownerId?: string } = {}
    ): { funded: number; short: number; from: Array<{ id: string; label: string; amount: number }> } => {
      const from: Array<{ id: string; label: string; amount: number }> = [];
      let need = Math.max(0, amount);
      const take = (b: BucketState) => {
        if (need <= 0 || b.balance <= 0) return;
        const got = Math.min(b.balance, need);
        b.balance -= got;
        need -= got;
        eventPaidOut[b.id] = (eventPaidOut[b.id] || 0) + got;
        from.push({ id: b.id, label: b.label, amount: got });
      };

      const named = opts.sourceBucketId
        ? buckets.find((b) => b.id === opts.sourceBucketId)
        : undefined;
      if (named) take(named);
      if (opts.onlySource) {
        return { funded: amount - need, short: need, from };
      }
      // Default cash account for the payer, then everything else that may be
      // liquidated, cheapest-to-touch first.
      const ownerCash = buckets.find(
        (b) => b.id === defaultCashId(opts.ownerId ?? people[0].id)
      );
      if (ownerCash) take(ownerCash);
      // Voyant checks each tax category across everyone before dropping to the
      // next one, but inside a category it spends the payer's own money first
      // (spec §2.1) — so a couple's plan never raids one partner's ISA while
      // the other has the same kind of pot sitting there.
      const payer = opts.ownerId ?? people[0].id;
      const rest = buckets
        .filter((b) => b !== named && b !== ownerCash && adHocAllowance(b, y) > 0)
        .sort(
          (a, b) =>
            liquidationTier(a) - liquidationTier(b) ||
            (a.ownerId === payer ? 0 : 1) - (b.ownerId === payer ? 0 : 1)
        );
      for (const b of rest) take(b);
      return { funded: amount - need, short: need, from };
    };

    /** Put money a life event produced into a pot (or the payer's ready cash). */
    const receiveFromEvent = (amount: number, bucketId?: string, ownerId?: string) => {
      if (amount <= 0) return;
      const target =
        (bucketId ? buckets.find((b) => b.id === bucketId) : undefined) ??
        buckets.find((b) => b.id === defaultCashId(ownerId ?? people[0].id));
      if (!target) return;
      target.balance += amount;
      eventPaidIn[target.id] = (eventPaidIn[target.id] || 0) + amount;
    };

    // Carry last year's event-driven income and expense adjustments forward,
    // grown. This happens BEFORE this year's events fire so a cost starting
    // now is used at the figure that was typed, not a year already inflated.
    // Income events grow too — an expense event inflating while a pay rise
    // stayed frozen quietly made every plan look worse each year.
    expenseInterventionDelta = expenseInterventionDelta * (1 + expenseInflation);
    interventionMonthlyDelta = interventionMonthlyDelta * (1 + incomeGrowth);

    // Apply interventions that fire AT THE START of this year (before growth)
    const firing = interventions.filter((iv) => iv.year === y);
    for (const iv of firing) {
      // Death is handled here (not in applyIntervention) because it touches
      // loop-level state: the deceased set, the survivor expense factor, and
      // pot ownership transfer.
      if (iv.type === "death") {
        const pid = resolvePersonId(iv.deceasedPersonId, people);
        deceasedFrom[pid] = y;
        const deceasedName = people.find((p) => p.id === pid)?.name || "Partner";
        const survivorId = people.find((p) => p.id !== pid)?.id ?? pid;
        // The deceased's pots pass to the survivor.
        buckets = buckets.map((b) => (b.ownerId === pid ? { ...b, ownerId: survivorId } : b));
        // Life cover pays out to cash (explicit amount, else sum of term-life).
        const payout =
          iv.lifeCoverPayout ??
          (plan.policies || [])
            .filter((p) => p.kind === "term_life")
            .reduce((s, p) => s + (p.sumAssured || 0), 0);
        // A protection pay-out is a lump sum inflow — it lands in the
        // survivor's ready cash (spec §2.3).
        receiveFromEvent(payout, undefined, survivorId);
        // Household expenses fall (one person, not two).
        const reductionPct = iv.expenseReductionPct ?? 33;
        expenseSurvivorFactor = Math.max(0, 1 - reductionPct / 100);
        events.push(
          `${deceasedName} dies: income stops${payout > 0 ? `, ${money(payout)} life cover paid` : ""}, household expenses −${reductionPct}%`
        );
        continue;
      }
      const applied = applyIntervention(iv, {
        getInterventionDelta: () => interventionMonthlyDelta,
        setInterventionDelta: (n) => {
          interventionMonthlyDelta = n;
        },
        // Expense interventions (expense_change, buy_house rent/mortgage) are
        // relative adjustments — apply them to the intervention delta, which is
        // added on top of the (possibly stepped) per-line expense total.
        getMonthlyExpenses: () => expenseInterventionDelta,
        setMonthlyExpenses: (n) => {
          expenseInterventionDelta = n;
        },
        buckets,
        addBucket: (b) => {
          buckets = [...buckets, b];
        },
        addDebt: (d) => {
          debtState = [...debtState, d];
        },
        addIncome: (line) => {
          // Steps hold it level — an annuity does not rise with the assumption
          // rate unless the coach says so. Base 0 keeps it silent before it
          // starts; the window gate does the same job belt-and-braces.
          incomeLines = [
            ...incomeLines,
            {
              amount: line.monthly,
              base: 0,
              isGross: line.isGross,
              label: line.label,
              steps: [{ fromYear: line.fromYear, amount: line.monthly }],
              startYear: line.fromYear,
              personId: line.personId,
            },
          ];
        },
        ownerId: resolvePersonId(iv.ownerId, people),
        canAccessPension: (ownerId) => canAccessPension(ownerId, y),
        debts: debtState,
        defaultOwnerId: people[0]?.id ?? resolvePersonId(undefined, people),
        spend: (amount, o) =>
          spendForEvent(amount, {
            // `bucketId` is the long-standing "which pot does this come out of"
            // field on a lump sum out — it still means exactly that.
            sourceBucketId: iv.paymentSourceBucketId ?? iv.bucketId,
            onlySource: iv.paymentSourceOnly,
            ownerId: o?.ownerId ?? resolvePersonId(iv.ownerId, people),
          }),
        receive: (amount, bucketId) => receiveFromEvent(amount, bucketId),
        reportUnfunded: (amount) => {
          unfundedEventSpend += amount;
        },
        inflationFactor: Math.pow(1 + expenseInflation, y),
      });
      if (applied) events.push(applied);
      // Pinned raise: earmark this income_change's monthly delta for a bucket
      // so it gets first claim on surplus before the general cascade.
      if (iv.type === "income_change" && iv.destinationBucketId && (iv.monthlyDelta || 0) > 0) {
        directedMonthlyByBucket[iv.destinationBucketId] =
          (directedMonthlyByBucket[iv.destinationBucketId] || 0) + (iv.monthlyDelta || 0);
      }
    }

    // Resolve income & expenses for the year. Lines WITH steps use their
    // absolute per-year step values (no auto-growth — what's typed is used);
    // lines WITHOUT steps grow at the assumption rate, exactly as before.
    incomeLines = incomeLines.map((l) => {
      const stepped = resolveSteppedAmount(l.base, l.steps, y);
      return { ...l, amount: stepped !== null ? stepped : l.amount * (1 + incomeGrowth) };
    });
    expenseLines = expenseLines.map((e) => {
      const stepped = resolveSteppedAmount(e.base, e.steps, y);
      return { ...e, amount: stepped !== null ? stepped : e.amount * (1 + expenseInflation) };
    });
    monthlyExpenses =
      expenseLines.reduce((s, e) => s + e.amount, 0) * expenseSurvivorFactor + expenseInterventionDelta;

    // Recompute tax on this year's gross income — only streams active this
    // year count (a salary that ended, a pension not yet started, contribute 0).
    const taxResult = netMonthlyIncomeFromLines(activeIncome(incomeLines, y), assumptions);
    const monthlyIncome = taxResult.netMonthly + interventionMonthlyDelta;

    // Step debts forward (with per-debt principal/interest deltas)
    const debtStep = stepDebtsOneYear(debtState);
    debtState = debtStep.next;
    let remainingDebt = debtState.reduce((s, d) => s + d.balance, 0);

    // ---- Stage 1: income meets living costs and debt commitments -----------
    // Voyant's rule: "Future contributions will only be made if funds remain
    // available after expenses are met", and "the actual deposit may be lower
    // than the planned contribution if the funds are unavailable". So the cash
    // left after living costs and debt is the CEILING on this year's saving —
    // a plan can no longer save money it never had.
    // Cash actually handed over on debts this year — the months each one ran,
    // not a flat 12 payments. In the year a debt clears, only the months up to
    // the payoff are charged.
    const annualDebtPaid = debtStep.deltas.reduce((s, d) => s + d.paymentsMade, 0);
    // Only buckets currently in their contribution window intend to save this
    // year; out-of-window buckets free up their share for available cash.
    const monthlySavings = buckets.reduce((s, b) => {
      const inWindow =
        (b.startYear === undefined || y >= b.startYear) &&
        (b.endYear === undefined || y <= b.endYear);
      return s + (inWindow ? effectiveMonthly(b, y) : 0);
    }, 0);

    // UK tax config — needed here because planned withdrawals below are taxed
    // on the way out, and their net proceeds count as this year's cash.
    const region = assumptions.region ?? "UK";
    const ukTaxCfg = assumptions.ukTax ?? DEFAULT_UK_TAX;
    const ukAllow = region === "UK" ? assumptions.ukAllowances ?? DEFAULT_UK_ALLOWANCES : undefined;
    const grossByPerson = taxResult.grossByPerson;
    const incomeRatePctFor = (ownerId: string): number => {
      const band = ukMarginalBand(grossByPerson[ownerId] || 0, ukTaxCfg);
      return band === "basic"
        ? ukTaxCfg.basicRatePct
        : band === "higher"
          ? ukTaxCfg.higherRatePct
          : ukTaxCfg.additionalRatePct;
    };
    const cgtRatePctFor = (ownerId: string): number => {
      if (!ukAllow) return 0;
      const band = ukMarginalBand(grossByPerson[ownerId] || 0, ukTaxCfg);
      return band === "basic" ? ukAllow.cgtBasicPct : ukAllow.cgtHigherPct;
    };
    const pensionAccessible = (b: BucketState): boolean => canAccessPension(b.ownerId, y);
    // ---- Tax on money coming OUT of a pot ----------------------------------
    // Allowances are per person per year and are consumed as the year goes on,
    // so these track what each person has used so far. Without them a retiree
    // with no earned income was charged basic rate from the first pound, even
    // though £12,570 of Personal Allowance was sitting unused.
    const paUsedByPerson: Record<string, number> = {};
    const cgtUsedByPerson: Record<string, number> = {};
    /** Personal Allowance this person has NOT used against earned income. */
    const unusedPA = (ownerId: string): number => {
      if (region !== "UK") return 0;
      const gross = grossByPerson[ownerId] || 0;
      const pa = ukTaxCfg.personalAllowance;
      const effective = gross > 100000 ? Math.max(0, pa - (gross - 100000) / 2) : pa;
      return Math.max(0, effective - gross - (paUsedByPerson[ownerId] || 0));
    };
    /** Capital gains annual exempt amount still available this year. */
    const unusedCGT = (ownerId: string): number => {
      if (region !== "UK" || !ukAllow) return 0;
      return Math.max(0, ukAllow.cgtAnnualExempt - (cgtUsedByPerson[ownerId] || 0));
    };
    /** Tax on taking `gross` out of this pot, plus the allowance it uses up. */
    const withdrawalTax = (
      b: BucketState,
      gross: number
    ): { tax: number; paUsed: number; cgtUsed: number } => {
      if (region !== "UK" || gross <= 0) return { tax: 0, paUsed: 0, cgtUsed: 0 };
      if (b.kind === "pension") {
        // An uncrystallised pot pays out 25% tax free (UFPLS). A crystallised
        // one has already had its tax-free cash, so all of it is income.
        // Either way, unused Personal Allowance covers the taxable part first.
        const taxable = gross * (b.crystallised ? 1 : 0.75);
        const covered = Math.min(taxable, unusedPA(b.ownerId));
        return {
          tax: (taxable - covered) * (incomeRatePctFor(b.ownerId) / 100),
          paUsed: covered,
          cgtUsed: 0,
        };
      }
      if (b.wrapper === "gia" && ukAllow) {
        const gain = gross * ukAllow.giaGainFraction;
        const covered = Math.min(gain, unusedCGT(b.ownerId));
        return {
          tax: (gain - covered) * (cgtRatePctFor(b.ownerId) / 100),
          paUsed: 0,
          cgtUsed: covered,
        };
      }
      return { tax: 0, paUsed: 0, cgtUsed: 0 }; // cash / ISA / property
    };
    const commitAllowance = (b: BucketState, r: { paUsed: number; cgtUsed: number }) => {
      if (r.paUsed) paUsedByPerson[b.ownerId] = (paUsedByPerson[b.ownerId] || 0) + r.paUsed;
      if (r.cgtUsed) cgtUsedByPerson[b.ownerId] = (cgtUsedByPerson[b.ownerId] || 0) + r.cgtUsed;
    };
    /**
     * How much must come OUT of this pot to leave `net` in hand. Tax here is
     * piecewise-linear — free until the allowance runs out, then taxed — so
     * this solves each piece rather than applying a flat ratio.
     */
    const grossForNet = (b: BucketState, net: number): number => {
      if (region !== "UK" || net <= 0) return net;
      if (b.kind === "pension") {
        const room = unusedPA(b.ownerId);
        const rate = incomeRatePctFor(b.ownerId) / 100;
        const taxableFraction = b.crystallised ? 1 : 0.75;
        if (rate <= 0) return net;
        if (net <= room / taxableFraction) return net; // allowance covers it
        return (net - room * rate) / (1 - taxableFraction * rate);
      }
      if (b.wrapper === "gia" && ukAllow) {
        const room = unusedCGT(b.ownerId);
        const f = ukAllow.giaGainFraction;
        const rate = cgtRatePctFor(b.ownerId) / 100;
        if (rate <= 0 || f <= 0) return net;
        if (net <= room / f) return net; // exemption covers the gain
        return (net - rate * room) / (1 - rate * f);
      }
      return net;
    };

    // ---- Planned withdrawals (Voyant's Draw Down Strategy, spec §2.7) -------
    // Taken every year whether the plan needs the money or not. This is what
    // makes "draw £2,000 a month from the SIPP from 60" modellable. The net
    // proceeds become this year's cash; the tax is charged on the way out.
    const plannedWithdrawnByBucket: Record<string, number> = {};
    let plannedWithdrawalsGross = 0;
    let plannedWithdrawalTax = 0;
    let plannedWithdrawalCash = 0;
    for (const b of buckets) {
      const dd = b.drawdown;
      if (!dd || dd.value <= 0 || b.balance <= 0) continue;
      const from = dd.startYear ?? 1;
      if (y < from) continue;
      if (dd.endYear !== undefined && y > dd.endYear) continue;
      if (b.kind === "pension" && !pensionAccessible(b)) continue;
      const wanted =
        dd.mode === "percent"
          ? b.balance * (dd.value / 100)
          : dd.indexed
            ? dd.value * Math.pow(1 + expenseInflation, y - from)
            : dd.value;
      const gross = Math.min(b.balance, Math.max(0, wanted));
      if (gross <= 0) continue;
      const tax = withdrawalTax(b, gross);
      commitAllowance(b, tax);
      const net = gross - tax.tax;
      b.balance -= gross;
      plannedWithdrawnByBucket[b.id] = (plannedWithdrawnByBucket[b.id] || 0) + gross;
      plannedWithdrawalsGross += gross;
      plannedWithdrawalCash += net;
      plannedWithdrawalTax += gross - net;
    }
    if (plannedWithdrawalsGross > 0) {
      events.push(
        `Planned withdrawals: ${money(plannedWithdrawalsGross)}${plannedWithdrawalTax > 0 ? ` (${money(plannedWithdrawalTax)} tax)` : ""}`
      );
    }

    const cashBeforeSaving =
      (monthlyIncome - monthlyExpenses) * 12 - annualDebtPaid + plannedWithdrawalCash;
    const plannedContributions = monthlySavings * 12;
    const affordableContributions = Math.max(
      0,
      Math.min(plannedContributions, cashBeforeSaving)
    );
    // How the shortfall in saving is shared out. With no savings order set,
    // every contribution scales back by the same fraction — the engine's
    // long-standing behaviour. Set an order (spec §2.4) and earlier tax
    // categories are funded in full before later ones get anything.
    const contributionScale =
      plannedContributions > 0 ? affordableContributions / plannedContributions : 0;
    const savingsOrder = assumptions.savingsOrder;
    /** The fraction of THIS pot's intended contribution that actually lands. */
    const scaleFor = (b: BucketState): number => {
      if (!savingsOrder || savingsOrder.length === 0) return contributionScale;
      if (affordableContributions >= plannedContributions) return 1;
      // Walk the categories in order, handing each its full ask until the
      // money runs out; the category the money runs out in shares what's left.
      const cat = taxCategoryOf(b);
      let budget = affordableContributions;
      for (const c of savingsOrder) {
        const wanted = buckets
          .filter((x) => taxCategoryOf(x) === c)
          .reduce((s, x) => {
            const inW =
              (x.startYear === undefined || y >= x.startYear) &&
              (x.endYear === undefined || y <= x.endYear);
            return s + (inW ? effectiveMonthly(x, y) * 12 : 0);
          }, 0);
        if (c === cat) return wanted > 0 ? Math.min(1, budget / wanted) : 0;
        budget = Math.max(0, budget - wanted);
      }
      return 0; // a category the coach left off the list is funded last
    };
    const unaffordableContribution = plannedContributions - affordableContributions;
    if (unaffordableContribution > 0) {
      events.push(
        `Only ${money(affordableContributions)} of this year's ${money(plannedContributions)} saving was affordable — the rest was never paid in`
      );
    }

    // Grow each bucket: add 12 months of contribution (with pension tax relief
    // uplift), then compound the whole balance at the per-class rate.
    // Contributions only land in years where startYear <= y <= endYear.
    // Capture per-bucket deltas for the year-detail breakdown.
    const pensionUsedByPerson: Record<string, number> = {};
    const pensionAAFor = (ownerId: string): number =>
      ukAllow ? taperedPensionAllowance(grossByPerson[ownerId] || 0, ukAllow) : Infinity;
    let pensionCapped = false;

    const bucketDeltas: NonNullable<YearProjection["bucketDeltas"]> = [];
    // Cash the client actually parted with to fund savings this year, and cash
    // a contribution limit turned away. Voyant overflows a blocked contribution
    // to the next account rather than losing it (spec §2.4); here the refused
    // cash returns to surplus, which then flows down surplusDestinations — the
    // same outcome by the same route.
    let actualContributions = 0;
    let refusedByLimit = 0;
    buckets = buckets.map((b) => {
      // Opening balance is what the pot held BEFORE this year's life events, so
      // a deposit or a lump sum shows up as a visible movement rather than a
      // balance that quietly started lower.
      const opening = openingBalances.get(b.id) ?? b.balance;
      const paidOut = eventPaidOut[b.id] || 0;
      const paidIn = eventPaidIn[b.id] || 0;
      const plannedOut = plannedWithdrawnByBucket[b.id] || 0;
      const contributionMultiplier = b.kind === "pension" ? taxReliefMultiplier : 1;
      const inWindow =
        (b.startYear === undefined || y >= b.startYear) &&
        (b.endYear === undefined || y <= b.endYear);
      const monthlyThisYear = effectiveMonthly(b, y);
      // Cash the client actually hands over, after the affordability scale-back.
      let cashContribution = (inWindow ? monthlyThisYear * 12 : 0) * scaleFor(b);
      let yearContribution = cashContribution * contributionMultiplier;
      // Pension annual allowance: cap the GROSS (incl. relief) contribution at
      // the owner's tapered allowance, tracked per person.
      if (b.kind === "pension" && yearContribution > 0) {
        const aa = pensionAAFor(b.ownerId);
        if (aa !== Infinity) {
          const used = pensionUsedByPerson[b.ownerId] || 0;
          const room = Math.max(0, aa - used);
          if (yearContribution > room) {
            yearContribution = room;
            // Hand back the cash that could not be paid in.
            const cashNeeded = yearContribution / contributionMultiplier;
            refusedByLimit += cashContribution - cashNeeded;
            cashContribution = cashNeeded;
            pensionCapped = true;
          }
          pensionUsedByPerson[b.ownerId] = used + yearContribution;
        }
      }
      actualContributions += cashContribution;
      const grown = (b.balance + yearContribution) * (1 + classGrowth(b.kind));
      bucketDeltas.push({
        id: b.id,
        label: b.label,
        kind: b.kind,
        openingBalance: opening,
        eventPaidOut: paidOut || undefined,
        eventPaidIn: paidIn || undefined,
        plannedWithdrawn: plannedOut || undefined,
        contributions: yearContribution,
        // Growth is whatever the closing balance cannot be explained by.
        growth: grown - opening + paidOut - paidIn + plannedOut - yearContribution,
        closingBalance: grown,
      });
      return { ...b, balance: grown };
    });
    if (pensionCapped) {
      events.push(
        `Pension contribution capped at the annual allowance${refusedByLimit > 0 ? ` — ${money(refusedByLimit)} stayed as available cash` : ""}`
      );
    }

    // ---- Tax on unwrapped investment income (dividends + cash interest) -----
    // Dividends on GIA pots and interest on taxed-cash pots, above each owner's
    // allowances, at THAT owner's marginal band (each person gets their own
    // dividend allowance + PSA). CGT on capital growth is deferred to disposal
    // — not charged here.
    let investmentTaxPaid = 0;
    if (ukAllow) {
      const byOwner: Record<string, { dividends: number; interest: number }> = {};
      for (const d of bucketDeltas) {
        const b = buckets.find((x) => x.id === d.id);
        if (!b) continue;
        if (b.wrapper !== "gia" && b.wrapper !== "cash_taxed") continue;
        // Income is earned on the money that was ACTUALLY invested this year.
        // A pot emptied in January by a house deposit or a drawdown didn't earn
        // a full year of dividends, and charging it as if it had could take a
        // pot below zero.
        const invested = Math.max(
          0,
          d.openingBalance - (d.eventPaidOut || 0) + (d.eventPaidIn || 0) - (d.plannedWithdrawn || 0)
        );
        const acc = byOwner[b.ownerId] || { dividends: 0, interest: 0 };
        if (b.wrapper === "gia") acc.dividends += invested * (ukAllow.giaDividendYieldPct / 100);
        else acc.interest += Math.max(0, invested * classGrowth("cash"));
        byOwner[b.ownerId] = acc;
      }
      /** Take `amount` of tax from this owner's pots. Returns what it couldn't
       *  collect — you cannot take tax out of a pot that no longer has it. */
      const deduct = (ownerId: string, group: TaxWrapper, amount: number): number => {
        if (amount <= 0) return 0;
        const members = buckets.filter((b) => b.ownerId === ownerId && b.wrapper === group && b.balance > 0);
        const base = members.reduce((s, b) => s + b.balance, 0);
        if (base <= 0) return amount;
        let uncollected = 0;
        for (const b of members) {
          const wanted = amount * (b.balance / base);
          const share = Math.min(wanted, b.balance); // never drive a pot negative
          uncollected += wanted - share;
          b.balance -= share;
          const d = bucketDeltas.find((x) => x.id === b.id);
          if (d) {
            d.growth -= share;
            d.closingBalance -= share;
          }
        }
        return uncollected;
      };
      for (const [ownerId, inc] of Object.entries(byOwner)) {
        const band = ukMarginalBand(grossByPerson[ownerId] || 0, ukTaxCfg);
        const t = calcUKInvestmentTax(inc.dividends, inc.interest, band, ukAllow, ukTaxCfg);
        // Only count what was actually taken, so the reported tax matches the
        // money that really moved.
        investmentTaxPaid += t.total;
        investmentTaxPaid -= deduct(ownerId, "gia", t.dividendTax);
        investmentTaxPaid -= deduct(ownerId, "cash_taxed", t.interestTax);
      }
      investmentTaxPaid = Math.max(0, investmentTaxPaid);
      if (investmentTaxPaid > 0) {
        events.push(`Investment tax: ${money(investmentTaxPaid)} (dividends/interest on unwrapped pots)`);
      }
    }

    const annualIncome = monthlyIncome * 12;
    const annualExpenses = monthlyExpenses * 12;
    // Saving can no longer push a year into deficit — only living costs and
    // debt can. A negative surplus now means income genuinely fell short.
    // `actualContributions` is what was really paid in: the affordable amount
    // less anything a contribution limit turned away.
    const annualSurplus = cashBeforeSaving - actualContributions;

    // ---- Give surplus a job ------------------------------------------------
    // Distribute positive surplus: pinned raises first, then the priority
    // cascade (caps + overflow). Whatever's left stays UNALLOCATED — assumed
    // spent, does not grow net worth. Mirrors Voyant's savings-order/sweep.
    let remainingSurplus = Math.max(0, annualSurplus);
    let allocatedSurplus = 0;
    const allocToBucket: Record<string, number> = {};
    const allocToDebt: Record<string, number> = {};
    const bucketById = new Map(buckets.map((b) => [b.id, b]));

    // 1. Directed (pinned) raises — first claim, ignore caps (it's intentional).
    for (const [bid, monthly] of Object.entries(directedMonthlyByBucket)) {
      if (remainingSurplus <= 0) break;
      if (!bucketById.has(bid)) continue; // bucket removed → falls to cascade
      const give = Math.min(monthly * 12, remainingSurplus);
      if (give > 0) {
        allocToBucket[bid] = (allocToBucket[bid] || 0) + give;
        remainingSurplus -= give;
      }
    }

    // 2. Cascade down the priority list. Each destination fills to its cap,
    //    overflow spills to the next. Already-directed amounts count toward a
    //    bucket's cap so a pinned raise + a capped sweep don't double-fill.
    for (const dest of surplusDestinations) {
      if (remainingSurplus <= 0) break;
      const inWindow =
        (dest.startYear === undefined || y >= dest.startYear) &&
        (dest.endYear === undefined || y <= dest.endYear);
      if (!inWindow) continue;
      if (dest.target.kind === "bucket") {
        const bid = dest.target.bucketId;
        if (!bucketById.has(bid)) continue;
        const already = allocToBucket[bid] || 0;
        const room = dest.capPerYear === undefined ? Infinity : Math.max(0, dest.capPerYear - already);
        const give = Math.min(remainingSurplus, room);
        if (give > 0) {
          allocToBucket[bid] = already + give;
          remainingSurplus -= give;
        }
      } else {
        const did = dest.target.debtId;
        const debt = debtState.find((d) => d.id === did);
        if (!debt || debt.balance <= 0) continue;
        const already = allocToDebt[did] || 0;
        const capRoom = dest.capPerYear === undefined ? Infinity : Math.max(0, dest.capPerYear - already);
        const room = Math.min(capRoom, debt.balance - already); // never overpay below £0
        const give = Math.min(remainingSurplus, room);
        if (give > 0) {
          allocToDebt[did] = already + give;
          remainingSurplus -= give;
        }
      }
    }

    // 2b. Voyant's "Transfer Excess Income / Credits to Savings" (spec §2.3).
    //     Off by default: surplus with no destination is assumed SPENT, which
    //     is the behavioural point. Switched on, whatever the cascade did not
    //     claim is banked as ready cash instead of disappearing.
    if (assumptions.transferExcessToSavings && remainingSurplus > 0) {
      const readyCash = buckets.find((b) => b.id === defaultCashId(people[0].id));
      if (readyCash) {
        allocToBucket[readyCash.id] = (allocToBucket[readyCash.id] || 0) + remainingSurplus;
        remainingSurplus = 0;
      }
    }

    // 3. Apply allocations to balances and the year-detail deltas.
    for (const [bid, amt] of Object.entries(allocToBucket)) {
      const target = bucketById.get(bid);
      if (target) target.balance += amt;
      const d = bucketDeltas.find((x) => x.id === bid);
      if (d) {
        d.surplusAdded = (d.surplusAdded || 0) + amt;
        d.closingBalance += amt;
      }
      allocatedSurplus += amt;
    }
    for (const [did, amt] of Object.entries(allocToDebt)) {
      const debt = debtState.find((x) => x.id === did);
      if (debt) debt.balance = Math.max(0, debt.balance - amt);
      const d = debtStep.deltas.find((x) => x.id === did);
      if (d) {
        d.surplusOverpaid = (d.surplusOverpaid || 0) + amt;
        d.principalPaid += amt;
        d.closingBalance = Math.max(0, d.closingBalance - amt);
      }
      allocatedSurplus += amt;
    }
    const unallocatedSurplus = Math.max(0, annualSurplus - allocatedSurplus);

    // ---- Deficit: fund an overspend by drawing pots down, TAX-AWARE --------
    // Retirement decumulation lives here: when income < outgoings, draw pots in
    // a tax-efficient order and charge the tax that really applies, so "will the
    // money last?" is honest rather than flattering.
    //   1. cash / taxed-cash → tax-free to withdraw (interest already taxed)
    //   2. ISA-sheltered     → tax-free
    //   3. GIA               → CGT on the gain portion of each withdrawal
    //   4. pension           → 25% tax-free, 75% taxed at the owner's marginal
    //                          rate; only once the owner can access it
    //   5. property          → last resort, tax-free (main residence)
    // Whatever still can't be funded is an UNMET SHORTFALL — the red bar.
    let assetsDrawn = 0;
    let shortfall = 0;
    let decumulationTaxPaid = 0;
    if (annualSurplus < 0) {
      let need = -annualSurplus; // NET cash still required

      const drawOrder = buckets
        .filter((b) => b.balance > 0 && adHocAllowance(b, y) > 0)
        .sort((a, b) => liquidationTier(a) - liquidationTier(b));

      for (const b of drawOrder) {
        if (need <= 0) break;
        if (b.balance <= 0) continue;
        if (b.kind === "pension" && !pensionAccessible(b)) continue;
        // A withdrawal limit caps how much may come out of this pot this year,
        // net of anything its planned drawdown has already taken.
        const room = Math.max(
          0,
          Math.min(b.balance, adHocAllowance(b, y) - (plannedWithdrawnByBucket[b.id] || 0))
        );
        if (room <= 0) continue;
        // Most this pot could yield if emptied to its limit, after tax.
        const maxNet = room - withdrawalTax(b, room).tax;
        if (maxNet <= 0) continue;
        const takeNet = Math.min(maxNet, need);
        // Emptying it? take the lot. Otherwise solve for the gross that nets
        // exactly what's still needed.
        const gross = takeNet >= maxNet ? room : grossForNet(b, takeNet);
        const t = withdrawalTax(b, gross);
        commitAllowance(b, t);
        const tax = t.tax;
        b.balance -= gross;
        need -= gross - tax; // what actually reached the client's pocket
        assetsDrawn += gross;
        decumulationTaxPaid += tax;
        // Record as a negative "surplus movement" so the delta still reconciles.
        const d = bucketDeltas.find((x) => x.id === b.id);
        if (d) {
          d.surplusAdded = (d.surplusAdded || 0) - gross;
          d.closingBalance -= gross;
        }
      }
      shortfall = need; // still unmet after draining everything → RED year
    }
    // ---- Year-end sweep: spare cash gets a job (spec §2.2) -----------------
    // Lump sums — an inheritance, house sale proceeds, a life cover pay-out —
    // land in ready cash. Without a sweep they sit there at cash rates forever.
    // Runs AFTER the deficit drawdown so we never invest money this year still
    // needs, and only ever moves cash that is genuinely spare.
    let sweptToWork = 0;
    if (assumptions.sweepSpareCash !== false && surplusDestinations.length > 0) {
      for (const cash of buckets) {
        if (!readyCashIds.has(cash.id) || cash.balance <= 0) continue;
        for (const dest of surplusDestinations) {
          if (cash.balance <= 0) break;
          const inWindow =
            (dest.startYear === undefined || y >= dest.startYear) &&
            (dest.endYear === undefined || y <= dest.endYear);
          if (!inWindow) continue;
          const destTarget = dest.target;

          if (destTarget.kind === "bucket") {
            const target = buckets.find((b) => b.id === destTarget.bucketId);
            if (!target || target === cash) continue;
            let room = dest.capPerYear ?? Infinity;
            // A pension can only take what is left of the annual allowance —
            // Voyant caps a sweep at the limit and overflows the rest.
            if (target.kind === "pension") {
              const aa = pensionAAFor(target.ownerId);
              if (aa !== Infinity) {
                room = Math.min(room, Math.max(0, aa - (pensionUsedByPerson[target.ownerId] || 0)));
              }
            }
            const move = Math.min(cash.balance, room);
            if (move <= 0) continue;
            cash.balance -= move;
            target.balance += move;
            if (target.kind === "pension") {
              pensionUsedByPerson[target.ownerId] =
                (pensionUsedByPerson[target.ownerId] || 0) + move;
            }
            sweptToWork += move;
            const dFrom = bucketDeltas.find((x) => x.id === cash.id);
            if (dFrom) {
              dFrom.surplusAdded = (dFrom.surplusAdded || 0) - move;
              dFrom.closingBalance -= move;
            }
            const dTo = bucketDeltas.find((x) => x.id === target.id);
            if (dTo) {
              dTo.surplusAdded = (dTo.surplusAdded || 0) + move;
              dTo.closingBalance += move;
            }
          } else {
            const debt = debtState.find((d) => d.id === destTarget.debtId);
            if (!debt || debt.balance <= 0) continue;
            const move = Math.min(cash.balance, debt.balance, dest.capPerYear ?? Infinity);
            if (move <= 0) continue;
            cash.balance -= move;
            debt.balance -= move;
            sweptToWork += move;
            const dFrom = bucketDeltas.find((x) => x.id === cash.id);
            if (dFrom) {
              dFrom.surplusAdded = (dFrom.surplusAdded || 0) - move;
              dFrom.closingBalance -= move;
            }
            const dDebt = debtStep.deltas.find((x) => x.id === debt.id);
            if (dDebt) {
              dDebt.surplusOverpaid = (dDebt.surplusOverpaid || 0) + move;
              dDebt.principalPaid += move;
              dDebt.closingBalance = Math.max(0, dDebt.closingBalance - move);
            }
          }
        }
      }
      if (sweptToWork > 0) {
        events.push(`${money(sweptToWork)} of spare cash put to work`);
      }
    }

    // A life event that no pot could pay for is a shortfall too. Attribution to
    // spend tiers below deliberately uses only the living-costs part — a house
    // deposit that could not be funded is not "cutting back on luxuries".
    const spendShortfall = shortfall;
    shortfall += unfundedEventSpend;
    if (unfundedEventSpend > 0) {
      events.push(
        `${money(unfundedEventSpend)} of this year's plans could not be paid for from any pot`
      );
    }
    if (decumulationTaxPaid > 0) {
      events.push(`Tax on drawdown: ${money(decumulationTaxPaid)} (pension income tax / GIA CGT)`);
    }

    // Attribute the shortfall to spend tiers — Luxury sacrificed first, then
    // Leisure, then Basics (Voyant's priority-funding order).
    let droppedByPriority: { basics: number; leisure: number; luxury: number } | undefined;
    if (spendShortfall > 0) {
      const lux = annualExpenses * priorityRatios.luxury;
      const lei = annualExpenses * priorityRatios.leisure;
      let s = spendShortfall;
      const dropLux = Math.min(s, lux); s -= dropLux;
      const dropLei = Math.min(s, lei); s -= dropLei;
      const dropBas = Math.max(0, s); // remainder eats into Basics
      droppedByPriority = { basics: dropBas, leisure: dropLei, luxury: dropLux };
    }

    // Recompute totals AFTER allocation + drawdown so net worth is honest.
    const cumulativeSavings = buckets.reduce((s, b) => s + b.balance, 0);
    remainingDebt = debtState.reduce((s, d) => s + d.balance, 0);

    // Approximate per-category expense breakdown by applying the original
    // category ratios to the inflation-adjusted total. Good-enough for the
    // year-detail view; not exact when interventions add untyped expense.
    const annualExp = annualExpenses;
    const expensesByCategory = {
      essentials: annualExp * categoryRatios.essentials,
      lifestyle: annualExp * categoryRatios.lifestyle,
      discretionary: annualExp * categoryRatios.discretionary,
      other: annualExp * categoryRatios.other,
    };

    projections.push({
      year: y,
      yearLabel: String(startYear + y),
      annualIncome,
      annualGrossIncome: taxResult.grossAnnual || undefined,
      annualExpenses,
      annualSurplus,
      allocatedSurplus,
      unallocatedSurplus,
      plannedContributions: plannedContributions || undefined,
      actualContributions: actualContributions || undefined,
      unaffordableContribution: unaffordableContribution || undefined,
      plannedWithdrawals: plannedWithdrawalsGross || undefined,
      plannedWithdrawalTax: plannedWithdrawalTax || undefined,
      assetsDrawn: assetsDrawn || undefined,
      shortfall: shortfall || undefined,
      droppedByPriority,
      cumulativeSavings,
      cashBalance: sumByKind(buckets, "cash"),
      stocksBalance: sumByKind(buckets, "stocks"),
      pensionBalance: sumByKind(buckets, "pension"),
      propertyBalance: sumByKind(buckets, "property"),
      totalDebtBalance: remainingDebt,
      debtBalances: debtState.map((d) => ({ id: d.id, name: d.name, balance: d.balance })),
      annualTaxPaid: taxResult.taxAnnual || undefined,
      annualNIPaid: taxResult.niAnnual || undefined,
      investmentTaxPaid: investmentTaxPaid || undefined,
      decumulationTaxPaid: decumulationTaxPaid || undefined,
      netWorth: cumulativeSavings - remainingDebt,
      events: events.length > 0 ? events : undefined,
      bucketDeltas,
      debtDeltas: debtStep.deltas,
      expensesByCategory,
    });
  }

  return projections;
}

function sumByKind(
  buckets: Array<{ kind: AssetKind; balance: number }>,
  kind: AssetKind
): number {
  return buckets
    .filter((b) => b.kind === kind)
    .reduce((s, b) => s + b.balance, 0);
}

type InterventionContext = {
  getInterventionDelta: () => number;
  setInterventionDelta: (n: number) => void;
  getMonthlyExpenses: () => number;
  setMonthlyExpenses: (n: number) => void;
  buckets: Array<{
    id: string;
    label: string;
    kind: AssetKind;
    balance: number;
    baseMonthly: number;
    deltaFromInterventions: number;
    steps?: import("./types").AmountStep[];
    ownerId?: string;
    crystallised?: boolean;
  }>;
  /** Can this person legally reach their pension in this year? */
  canAccessPension: (ownerId: string) => boolean;
  addBucket: (b: {
    id: string;
    label: string;
    kind: AssetKind;
    balance: number;
    baseMonthly: number;
    deltaFromInterventions: number;
    ownerId: string;
    crystallised?: boolean;
  }) => void;
  /** Start a new income stream mid-plan — an annuity, say. Level by default. */
  addIncome: (line: {
    label: string;
    monthly: number;
    isGross: boolean;
    personId: string;
    fromYear: number;
  }) => void;
  /** Whose pots this event should reach for first. */
  ownerId: string;
  addDebt: (d: DebtLine) => void;
  /** Live list of current debts — mutate items in place (downsize/remortgage). */
  debts: DebtLine[];
  /** Person to own pots created by interventions (e.g. a bought property). */
  defaultOwnerId: string;
  /**
   * Take money out of the plan to pay for this event, honouring the event's
   * payment source and then the liquidation order. Returns what was actually
   * funded and what could not be. NEVER invents money.
   */
  spend: (
    amount: number,
    opts?: { ownerId?: string }
  ) => { funded: number; short: number; from: Array<{ id: string; label: string; amount: number }> };
  /** Put money this event produced into a pot, or the payer's ready cash. */
  receive: (amount: number, bucketId?: string) => void;
  /** Tell the year that this much event spending could not be funded. */
  reportUnfunded: (amount: number) => void;
  /**
   * How much prices have risen since the plan started, i.e. (1+inflation)^year.
   * An event that cancels an existing cost — buying a house ends the rent —
   * must cancel it at TODAY'S value, not the value typed years ago, or a
   * sliver of phantom rent is left behind forever.
   */
  inflationFactor: number;
};

function applyIntervention(iv: Intervention, ctx: InterventionContext): string | null {
  switch (iv.type) {
    case "income_change": {
      const delta = iv.monthlyDelta || 0;
      ctx.setInterventionDelta(ctx.getInterventionDelta() + delta);
      return `${iv.label || "Income change"}: ${delta >= 0 ? "+" : ""}${money(delta)}/mo (post-tax)`;
    }
    case "expense_change": {
      const delta = iv.monthlyDelta || 0;
      ctx.setMonthlyExpenses(ctx.getMonthlyExpenses() + delta);
      return `${iv.label || "Expense change"}: ${delta >= 0 ? "+" : ""}${money(delta)}/mo`;
    }
    case "savings_change": {
      const delta = iv.monthlyDelta || 0;
      const target = ctx.buckets.find((b) => b.id === iv.bucketId) ?? ctx.buckets[0];
      if (target) target.deltaFromInterventions += delta;
      return `${iv.label || "Savings change"}: ${delta >= 0 ? "+" : ""}${money(delta)}/mo`;
    }
    case "lump_sum_in": {
      const amount = iv.amount || 0;
      // A lump sum landing with no home goes to ready cash — Voyant's rule for
      // lump sum inflows (spec §2.3).
      ctx.receive(amount, iv.bucketId);
      return `${iv.label || "Lump sum in"}: +${money(amount)}`;
    }
    case "lump_sum_out": {
      const amount = iv.amount || 0;
      const paid = ctx.spend(amount, {});
      if (paid.short > 0) ctx.reportUnfunded(paid.short);
      const sources = paid.from.map((f) => `${f.label} ${money(f.amount)}`).join(", ");
      return `${iv.label || "Lump sum out"}: -${money(paid.funded)}${sources ? ` from ${sources}` : ""}${
        paid.short > 0 ? ` — ${money(paid.short)} could not be funded` : ""
      }`;
    }
    case "buy_house": {
      const deposit = iv.deposit || 0;
      const mortgageMonthly = iv.mortgageMonthly || 0;
      const mortgageBalance = iv.mortgageBalance || 0;
      const mortgageRate = iv.mortgageRate || 0;
      const rentReplaced = iv.rentReplaced || 0;
      const propertyValue = iv.propertyValue || deposit;

      // Pay the deposit from the named payment source, then ready cash, then
      // the liquidation order. If the money isn't there, it is NOT invented —
      // the gap becomes a shortfall and the year turns red.
      const paid = ctx.spend(deposit, {});
      if (paid.short > 0) ctx.reportUnfunded(paid.short);
      const depositSources = paid.from.map((f) => `${f.label} ${money(f.amount)}`).join(", ");

      // Stop the rent. It has been inflating since the plan started, so cancel
      // it at what it costs NOW — cancelling the original figure would leave a
      // slice of rent running forever after the house is bought.
      ctx.setMonthlyExpenses(ctx.getMonthlyExpenses() - rentReplaced * ctx.inflationFactor);

      // Add the mortgage as a debt that amortises year-by-year
      if (mortgageBalance > 0) {
        ctx.addDebt({
          id: `mortgage_${iv.id}`,
          name: iv.label ? `${iv.label} mortgage` : "Mortgage",
          balance: mortgageBalance,
          rate: mortgageRate,
          minPayment: mortgageMonthly,
          actualPayment: mortgageMonthly,
        });
      } else if (mortgageMonthly > 0) {
        // Backward compat: no mortgage balance set — treat as flat expense add
        ctx.setMonthlyExpenses(ctx.getMonthlyExpenses() + mortgageMonthly);
      }

      // Add property bucket (no monthly contribution; appreciates at property rate)
      ctx.addBucket({
        id: `prop_${iv.id}`,
        label: iv.label || "Home",
        kind: "property",
        balance: propertyValue,
        baseMonthly: 0,
        deltaFromInterventions: 0,
        ownerId: ctx.defaultOwnerId,
      });

      return `${iv.label || "Buy house"}: deposit ${money(paid.funded)}${depositSources ? ` from ${depositSources}` : ""}${
        paid.short > 0 ? ` — ${money(paid.short)} of the deposit could not be funded` : ""
      }, mortgage ${money(mortgageMonthly)}/mo${mortgageBalance > 0 ? ` (${money(mortgageBalance)} @ ${mortgageRate}%)` : ""}`;
    }
    case "downsize": {
      // Sell (or trade down) a property: clear its mortgage from the sale,
      // release the net equity to cash, optionally buy a cheaper place, and
      // add rent back if selling up to rent.
      const prop =
        ctx.buckets.find((b) => b.id === iv.propertyBucketId && b.kind === "property") ??
        ctx.buckets.find((b) => b.kind === "property");
      if (!prop) return `${iv.label || "Downsize"}: no property to sell`;
      const saleValue = prop.balance;
      const mortgage =
        ctx.debts.find((d) => d.id === iv.mortgageDebtId && d.balance > 0) ??
        ctx.debts.find((d) => /mortgage/i.test(d.name) && d.balance > 0);
      const mortgagePayoff = mortgage ? mortgage.balance : 0;
      const newVal = iv.propertyValue ?? 0;
      const released = Math.max(0, saleValue - mortgagePayoff - newVal);

      prop.balance = newVal; // 0 = sold up; >0 = traded down to a cheaper home
      if (mortgage) {
        mortgage.balance = 0; // cleared from sale proceeds (payment auto-stops)
      }
      ctx.receive(released);
      if (newVal <= 0 && (iv.newRentMonthly || 0) > 0) {
        ctx.setMonthlyExpenses(ctx.getMonthlyExpenses() + (iv.newRentMonthly || 0));
      }
      return `${iv.label || "Downsize"}: sold ${money(saleValue)}${mortgagePayoff > 0 ? `, cleared ${money(mortgagePayoff)} mortgage` : ""}, released ${money(released)}${newVal > 0 ? ` into a ${money(newVal)} home` : " (now renting)"}`;
    }
    case "remortgage": {
      const mortgage =
        ctx.debts.find((d) => d.id === iv.mortgageDebtId && d.balance > 0) ??
        ctx.debts.find((d) => /mortgage/i.test(d.name) && d.balance > 0);
      if (!mortgage) return `${iv.label || "Remortgage"}: no mortgage to change`;
      if (iv.newRate !== undefined) mortgage.rate = iv.newRate;
      if (iv.newMonthlyPayment !== undefined) {
        mortgage.actualPayment = iv.newMonthlyPayment;
        mortgage.minPayment = Math.min(mortgage.minPayment, iv.newMonthlyPayment);
      }
      const release = iv.equityRelease || 0;
      if (release > 0) {
        mortgage.balance += release;
        ctx.receive(release);
      }
      const parts = [
        iv.newRate !== undefined ? `rate → ${iv.newRate}%` : null,
        iv.newMonthlyPayment !== undefined ? `${money(iv.newMonthlyPayment)}/mo` : null,
        release > 0 ? `released ${money(release)}` : null,
      ].filter(Boolean);
      return `${iv.label || "Remortgage"}: ${parts.length ? parts.join(", ") : "no change"}`;
    }
    case "crystallise_pension": {
      // Take the tax-free cash and move the rest into drawdown. Voyant models
      // these as two different account types (spec §2.11): what's left behind
      // is fully taxable on the way out, because the 25% has been had.
      const pot =
        ctx.buckets.find((b) => b.id === iv.pensionBucketId && b.kind === "pension") ??
        ctx.buckets.find((b) => b.kind === "pension" && !b.crystallised && b.balance > 0);
      if (!pot || pot.balance <= 0) return `${iv.label || "Crystallise"}: no pension to crystallise`;
      if (!ctx.canAccessPension(pot.ownerId ?? ctx.defaultOwnerId)) {
        return `${iv.label || "Crystallise"}: too early — the pension can't be reached yet`;
      }
      const amount = Math.min(pot.balance, iv.crystalliseAmount ?? pot.balance);
      if (amount <= 0) return `${iv.label || "Crystallise"}: nothing to crystallise`;
      const taxFreeCash = amount * 0.25;
      const intoDrawdown = amount - taxFreeCash;
      pot.balance -= amount;
      ctx.receive(taxFreeCash); // PCLS is a lump sum — it lands as ready cash
      ctx.addBucket({
        id: `drawdown_${iv.id}`,
        label: `${pot.label} (drawdown)`,
        kind: "pension",
        balance: intoDrawdown,
        baseMonthly: 0,
        deltaFromInterventions: 0,
        ownerId: pot.ownerId ?? ctx.defaultOwnerId,
        crystallised: true,
      });
      return `${iv.label || "Crystallise pension"}: ${money(taxFreeCash)} tax-free cash taken, ${money(intoDrawdown)} moved to drawdown`;
    }
    case "buy_annuity": {
      // Swap a pension pot for a guaranteed income. The purchase itself is not
      // taxed; the income it pays is taxed as income, year after year.
      const pot =
        ctx.buckets.find((b) => b.id === iv.pensionBucketId && b.kind === "pension") ??
        ctx.buckets.find((b) => b.kind === "pension" && b.balance > 0);
      if (!pot || pot.balance <= 0) return `${iv.label || "Annuity"}: no pension to convert`;
      if (!ctx.canAccessPension(pot.ownerId ?? ctx.defaultOwnerId)) {
        return `${iv.label || "Annuity"}: too early — the pension can't be reached yet`;
      }
      const spend = Math.min(pot.balance, iv.annuityAmount ?? pot.balance);
      const ratePct = iv.annuityRatePct ?? 0;
      if (spend <= 0 || ratePct <= 0) {
        return `${iv.label || "Annuity"}: set an amount and an annuity rate`;
      }
      pot.balance -= spend;
      const annualIncome = spend * (ratePct / 100);
      ctx.addIncome({
        label: iv.label || "Annuity",
        monthly: annualIncome / 12,
        isGross: true, // annuity income is taxed as income
        personId: pot.ownerId ?? ctx.defaultOwnerId,
        fromYear: iv.year,
      });
      return `${iv.label || "Buy annuity"}: ${money(spend)} buys ${money(annualIncome)}/yr for life at ${ratePct}%`;
    }
    case "asset_crash": {
      const crashPct = iv.crashPct ?? 30;
      const target = iv.targetKind ?? "stocks";
      const factor = 1 - crashPct / 100;
      ctx.buckets.forEach((b) => {
        if (target === "all" || b.kind === target) {
          b.balance = Math.max(0, b.balance * factor);
        }
      });
      const targetLabel = target === "all" ? "All assets" : target === "stocks" ? "Stocks" : "Property";
      return `${iv.label || "Market crash"}: ${targetLabel} −${crashPct}%`;
    }
    default:
      return null;
  }
}

function money(n: number): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(n);
}

/* ========================================================================
 * v2 — Goal trajectory analytics
 * ====================================================================== */

export interface TimeToGoal {
  /** Whole-year offset from today when target is first met. */
  yearsFromNow: number;
  /** Absolute calendar year when target is first met. */
  absoluteYear: number;
  /** Total months from today (year * 12 + interpolated remainder). */
  monthsFromNow: number;
  /** Quarter label (e.g. "Q3 2031") computed from monthsFromNow. */
  quarterLabel: string;
  /** True if the goal is already met at year 0. */
  alreadyHit: boolean;
  /** True if the goal is not hit within the projection horizon. */
  outOfHorizon: boolean;
  /** Net worth at the end of the projection horizon (informational). */
  horizonNetWorth: number;
}

/**
 * Walk the projection year-by-year and find when net worth first crosses
 * the target. Linear-interpolates between adjacent years to give a fractional
 * year, then converts to a quarter label for human readability.
 */
export function findTimeToGoal(
  projections: YearProjection[],
  targetAmount: number
): TimeToGoal | null {
  if (!projections.length || !(targetAmount > 0)) return null;

  const startYear = new Date().getFullYear();
  const horizonNetWorth = projections[projections.length - 1].netWorth;

  // Already met at year 0 — celebrate; no time-to-goal beyond "today."
  if (projections[0].netWorth >= targetAmount) {
    return {
      yearsFromNow: 0,
      absoluteYear: startYear,
      monthsFromNow: 0,
      quarterLabel: `Q${Math.floor(new Date().getMonth() / 3) + 1} ${startYear}`,
      alreadyHit: true,
      outOfHorizon: false,
      horizonNetWorth,
    };
  }

  for (let i = 1; i < projections.length; i++) {
    const prev = projections[i - 1];
    const curr = projections[i];
    if (curr.netWorth >= targetAmount) {
      // Linear interpolate between prev and curr to find fractional year.
      const span = curr.netWorth - prev.netWorth;
      const fraction = span > 0 ? (targetAmount - prev.netWorth) / span : 0;
      const yearsFromNow = (i - 1) + Math.max(0, Math.min(1, fraction));
      const monthsFromNow = Math.round(yearsFromNow * 12);
      const absoluteYear = startYear + Math.floor(yearsFromNow);
      const monthInYear = monthsFromNow % 12;
      const quarter = Math.floor(monthInYear / 3) + 1;
      return {
        yearsFromNow,
        absoluteYear,
        monthsFromNow,
        quarterLabel: `Q${quarter} ${absoluteYear}`,
        alreadyHit: false,
        outOfHorizon: false,
        horizonNetWorth,
      };
    }
  }

  return {
    yearsFromNow: Infinity,
    absoluteYear: Infinity,
    monthsFromNow: Infinity,
    quarterLabel: "Beyond horizon",
    alreadyHit: false,
    outOfHorizon: true,
    horizonNetWorth,
  };
}

/**
 * Try to extract a calendar target year from free-text goal title.
 * Looks for any 4-digit year between (currentYear - 1) and (currentYear + 50).
 * Returns null if nothing usable is found.
 */
export function extractTargetYearFromGoalText(text: string | null | undefined): number | null {
  if (!text) return null;
  const currentYear = new Date().getFullYear();
  const matches = text.match(/\b(20\d{2})\b/g);
  if (!matches) return null;
  const candidates = matches
    .map((m) => parseInt(m, 10))
    .filter((y) => y >= currentYear - 1 && y <= currentYear + 50);
  if (!candidates.length) return null;
  // Prefer the latest year mentioned (handles cases like "from 2026 to 2029").
  return Math.max(...candidates);
}

/**
 * Solve (via binary search) the additional monthly surplus that must be
 * directed at savings every month for net worth at the target year to meet
 * the target amount. Returns null if no plausible solution exists.
 *
 * `extraMonthlyToBucketId` (optional) names which savings bucket the extra
 * monthly contribution lands in. Defaults to the first bucket — if no
 * buckets exist, a synthetic cash bucket is added internally.
 */
export interface RequiredSurplusResult {
  /** Extra monthly contribution required (added to whatever the plan already saves). */
  extraMonthly: number;
  /** Total monthly contribution needed = current monthly savings + extraMonthly. */
  totalMonthly: number;
  /** True if the goal is already met at the target year with no extra surplus. */
  alreadyOnTrack: boolean;
  /** True if even very large surplus values cannot close the gap (model limits hit). */
  unreachable: boolean;
}

export function requiredMonthlySurplusToHitGoal(
  plan: CashflowPlanData,
  assumptions: ProjectionAssumptions,
  targetAmount: number,
  targetYearOffset: number,
  options: { bucketId?: string; bucketKind?: AssetKind } = {}
): RequiredSurplusResult | null {
  if (!(targetAmount > 0) || !(targetYearOffset > 0)) return null;

  const horizonNeeded = Math.max(targetYearOffset, assumptions.horizonYears);
  const sandboxAssumptions: ProjectionAssumptions = {
    ...assumptions,
    horizonYears: horizonNeeded,
  };

  const evalAt = (extra: number): number => {
    const sandbox: CashflowPlanData = {
      ...plan,
      savings: plan.savings.length
        ? plan.savings.map((s, i) => {
            const isTarget = options.bucketId
              ? s.id === options.bucketId
              : i === 0;
            return isTarget
              ? { ...s, monthlyAmount: (s.monthlyAmount || 0) + extra }
              : s;
          })
        : [
            {
              id: "v2_synthetic_target",
              label: "Goal-funded savings",
              kind: options.bucketKind ?? "cash",
              current: 0,
              monthlyAmount: extra,
            } as SavingsAllocation,
          ],
    };
    const projs = projectYears(sandbox, sandboxAssumptions);
    const idx = Math.max(0, Math.min(targetYearOffset, projs.length - 1));
    return projs[idx].netWorth;
  };

  const baseline = evalAt(0);
  if (baseline >= targetAmount) {
    return { extraMonthly: 0, totalMonthly: currentMonthlySavings(plan), alreadyOnTrack: true, unreachable: false };
  }

  // Binary search: extra monthly contribution between 0 and a large ceiling.
  let lo = 0;
  let hi = 100_000; // £100k/mo extra — enough to cover essentially any goal
  // Verify hi actually clears the bar; if not the goal is unreachable in-model.
  if (evalAt(hi) < targetAmount) {
    return { extraMonthly: Infinity, totalMonthly: Infinity, alreadyOnTrack: false, unreachable: true };
  }

  for (let iter = 0; iter < 40; iter++) {
    const mid = (lo + hi) / 2;
    const nw = evalAt(mid);
    if (nw >= targetAmount) hi = mid;
    else lo = mid;
    if (hi - lo < 1) break;
  }

  const extraMonthly = Math.ceil(hi);
  return {
    extraMonthly,
    totalMonthly: currentMonthlySavings(plan) + extraMonthly,
    alreadyOnTrack: false,
    unreachable: false,
  };
}

function currentMonthlySavings(plan: CashflowPlanData): number {
  return (plan.savings || []).reduce((s, b) => s + (b.monthlyAmount || 0), 0);
}
