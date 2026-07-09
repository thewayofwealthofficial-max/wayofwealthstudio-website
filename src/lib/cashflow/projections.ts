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
import { DEFAULT_UK_TAX, DEFAULT_UK_ALLOWANCES, DEFAULT_US_TAX_SINGLE, expensePriority, resolveSteppedAmount, effectivePeople, resolvePersonId } from "./types";
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
  const horizon = Math.max(1, Math.min(30, assumptions.horizonYears || 5));
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
  };
  const effectiveMonthly = (
    b: { baseMonthly: number; steps?: import("./types").AmountStep[]; deltaFromInterventions: number },
    y: number
  ): number =>
    Math.max(0, (resolveSteppedAmount(b.baseMonthly, b.steps, y) ?? b.baseMonthly) + b.deltaFromInterventions);

  const startingBuckets: BucketState[] = plan.savings.map((s) => ({
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
  }));

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
  const stepDebtsOneYear = (
    debts: DebtLine[],
  ): { next: DebtLine[]; deltas: Array<{ id: string; name: string; openingBalance: number; interestPaid: number; principalPaid: number; surplusOverpaid?: number; closingBalance: number }> } => {
    const deltas: Array<{ id: string; name: string; openingBalance: number; interestPaid: number; principalPaid: number; surplusOverpaid?: number; closingBalance: number }> = [];
    const next = debts.map((d) => {
      const opening = d.balance;
      if (d.balance <= 0) {
        deltas.push({ id: d.id, name: d.name, openingBalance: opening, interestPaid: 0, principalPaid: 0, closingBalance: 0 });
        return d;
      }
      let bal = d.balance;
      let interestThisYear = 0;
      let principalThisYear = 0;
      const monthlyRate = (d.rate || 0) / 100 / 12;
      for (let m = 0; m < 12; m++) {
        if (bal <= 0) break;
        const interest = bal * monthlyRate;
        const principal = Math.max(0, (d.actualPayment || 0) - interest);
        interestThisYear += interest;
        principalThisYear += Math.min(principal, bal);
        bal = Math.max(0, bal - principal);
      }
      deltas.push({
        id: d.id,
        name: d.name,
        openingBalance: opening,
        interestPaid: interestThisYear,
        principalPaid: principalThisYear,
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
        if (payout > 0) {
          const cash = buckets.find((b) => b.kind === "cash");
          if (cash) cash.balance += payout;
          else
            buckets = [
              ...buckets,
              {
                id: `lifecover_${iv.id}`,
                label: "Life cover payout",
                kind: "cash",
                balance: payout,
                baseMonthly: 0,
                deltaFromInterventions: 0,
                ownerId: survivorId,
              },
            ];
        }
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
        debts: debtState,
        defaultOwnerId: people[0]?.id ?? resolvePersonId(undefined, people),
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
    expenseInterventionDelta = expenseInterventionDelta * (1 + expenseInflation);
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

    // Grow each bucket: add 12 months of contribution (with pension tax relief
    // uplift), then compound the whole balance at the per-class rate.
    // Contributions only land in years where startYear <= y <= endYear.
    // Capture per-bucket deltas for the year-detail breakdown.
    // UK tax config for investment-income tax + pension annual allowance.
    const region = assumptions.region ?? "UK";
    const ukTaxCfg = assumptions.ukTax ?? DEFAULT_UK_TAX;
    const ukAllow = region === "UK" ? assumptions.ukAllowances ?? DEFAULT_UK_ALLOWANCES : undefined;
    // Per-person gross drives each person's pension allowance taper + their
    // marginal band for investment tax.
    const grossByPerson = taxResult.grossByPerson;
    const pensionUsedByPerson: Record<string, number> = {};
    const pensionAAFor = (ownerId: string): number =>
      ukAllow ? taperedPensionAllowance(grossByPerson[ownerId] || 0, ukAllow) : Infinity;
    let pensionCapped = false;

    const bucketDeltas: NonNullable<YearProjection["bucketDeltas"]> = [];
    buckets = buckets.map((b) => {
      const opening = b.balance;
      const contributionMultiplier = b.kind === "pension" ? taxReliefMultiplier : 1;
      const inWindow =
        (b.startYear === undefined || y >= b.startYear) &&
        (b.endYear === undefined || y <= b.endYear);
      const monthlyThisYear = effectiveMonthly(b, y);
      let yearContribution = inWindow ? monthlyThisYear * 12 * contributionMultiplier : 0;
      // Pension annual allowance: cap the GROSS (incl. relief) contribution at
      // the owner's tapered allowance, tracked per person.
      if (b.kind === "pension" && yearContribution > 0) {
        const aa = pensionAAFor(b.ownerId);
        if (aa !== Infinity) {
          const used = pensionUsedByPerson[b.ownerId] || 0;
          const room = Math.max(0, aa - used);
          if (yearContribution > room) {
            yearContribution = room;
            pensionCapped = true;
          }
          pensionUsedByPerson[b.ownerId] = used + yearContribution;
        }
      }
      const grown = (b.balance + yearContribution) * (1 + classGrowth(b.kind));
      bucketDeltas.push({
        id: b.id,
        label: b.label,
        kind: b.kind,
        openingBalance: opening,
        contributions: yearContribution,
        growth: grown - opening - yearContribution,
        closingBalance: grown,
      });
      return { ...b, balance: grown };
    });
    if (pensionCapped) {
      events.push(`Pension contribution capped at the annual allowance`);
    }

    // ---- Tax on unwrapped investment income (dividends + cash interest) -----
    // Dividends on GIA pots and interest on taxed-cash pots, above each owner's
    // allowances, at THAT owner's marginal band (each person gets their own
    // dividend allowance + PSA). Charged on opening balances (surplus added
    // later this year isn't taxed until next year). CGT on capital growth is
    // deferred to disposal — not charged here.
    let investmentTaxPaid = 0;
    if (ukAllow) {
      const byOwner: Record<string, { dividends: number; interest: number }> = {};
      for (const d of bucketDeltas) {
        const b = buckets.find((x) => x.id === d.id);
        if (!b) continue;
        if (b.wrapper !== "gia" && b.wrapper !== "cash_taxed") continue;
        const acc = byOwner[b.ownerId] || { dividends: 0, interest: 0 };
        if (b.wrapper === "gia") acc.dividends += d.openingBalance * (ukAllow.giaDividendYieldPct / 100);
        else acc.interest += d.openingBalance * classGrowth("cash");
        byOwner[b.ownerId] = acc;
      }
      const deduct = (ownerId: string, group: TaxWrapper, amount: number) => {
        if (amount <= 0) return;
        const members = buckets.filter((b) => b.ownerId === ownerId && b.wrapper === group && b.balance > 0);
        const base = members.reduce((s, b) => s + b.balance, 0);
        if (base <= 0) return;
        for (const b of members) {
          const share = amount * (b.balance / base);
          b.balance -= share;
          const d = bucketDeltas.find((x) => x.id === b.id);
          if (d) {
            d.growth -= share;
            d.closingBalance -= share;
          }
        }
      };
      for (const [ownerId, inc] of Object.entries(byOwner)) {
        const band = ukMarginalBand(grossByPerson[ownerId] || 0, ukTaxCfg);
        const t = calcUKInvestmentTax(inc.dividends, inc.interest, band, ukAllow, ukTaxCfg);
        investmentTaxPaid += t.total;
        deduct(ownerId, "gia", t.dividendTax);
        deduct(ownerId, "cash_taxed", t.interestTax);
      }
      if (investmentTaxPaid > 0) {
        events.push(`Investment tax: ${money(investmentTaxPaid)} (dividends/interest on unwrapped pots)`);
      }
    }

    // Only buckets currently in their contribution window count against
    // surplus; out-of-window buckets free up their share for "available cash".
    const monthlySavings = buckets.reduce((s, b) => {
      const inWindow =
        (b.startYear === undefined || y >= b.startYear) &&
        (b.endYear === undefined || y <= b.endYear);
      return s + (inWindow ? effectiveMonthly(b, y) : 0);
    }, 0);
    const monthlyDebt = debtState.reduce((s, d) => s + (d.balance > 0 ? d.actualPayment : 0), 0);

    const annualIncome = monthlyIncome * 12;
    const annualExpenses = monthlyExpenses * 12;
    const annualSurplus =
      (monthlyIncome - monthlyExpenses - monthlyDebt - monthlySavings) * 12;

    // Affordability of this year's planned saving. If contributions pushed the
    // year into deficit, flag how much was "too much to save this year" — the
    // signal that tells the coach to step the contribution down (the Voyant
    // red-bar feeling, but pinned to the saving rather than the whole plan).
    const plannedContributions = monthlySavings * 12;
    const unaffordableContribution =
      annualSurplus < 0 ? Math.min(plannedContributions, -annualSurplus) : 0;
    if (unaffordableContribution > 0) {
      events.push(
        `${money(unaffordableContribution)} of this year's ${money(plannedContributions)} saving wasn't affordable — income didn't cover it`
      );
    }

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
      const pensionAccessible = (b: BucketState): boolean => {
        if (!ukAllow) return true;
        const age = people.find((p) => p.id === b.ownerId)?.currentAge;
        return age === undefined || age + y >= ukAllow.pensionAccessAge;
      };
      // Net cash that £1 of withdrawal from this pot yields (after its tax).
      const netPerGross = (b: BucketState): number => {
        if (region !== "UK") return 1;
        if (b.kind === "pension") {
          const r = incomeRatePctFor(b.ownerId) / 100;
          return 0.25 + 0.75 * (1 - r); // 25% tax-free, rest taxed as income
        }
        if (b.wrapper === "gia" && ukAllow) {
          return 1 - (cgtRatePctFor(b.ownerId) / 100) * ukAllow.giaGainFraction;
        }
        return 1; // cash / taxed-cash / ISA / property — tax-free to withdraw
      };
      const tier = (b: BucketState): number => {
        if (b.kind === "cash") return 1;
        if (b.kind === "pension") return 4;
        if (b.kind === "property") return 5;
        return b.wrapper === "gia" ? 3 : 2; // ISA-sheltered stocks before GIA
      };
      const drawOrder = buckets.filter((b) => b.balance > 0).sort((a, b) => tier(a) - tier(b));

      for (const b of drawOrder) {
        if (need <= 0) break;
        if (b.balance <= 0) continue;
        if (b.kind === "pension" && !pensionAccessible(b)) continue;
        const npg = netPerGross(b);
        if (npg <= 0) continue;
        const takeNet = Math.min(b.balance * npg, need);
        const gross = takeNet / npg; // balance actually removed from the pot
        const tax = gross - takeNet; // tax incurred funding this slice
        b.balance -= gross;
        need -= takeNet;
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
    if (decumulationTaxPaid > 0) {
      events.push(`Tax on drawdown: ${money(decumulationTaxPaid)} (pension income tax / GIA CGT)`);
    }

    // Attribute the shortfall to spend tiers — Luxury sacrificed first, then
    // Leisure, then Basics (Voyant's priority-funding order).
    let droppedByPriority: { basics: number; leisure: number; luxury: number } | undefined;
    if (shortfall > 0) {
      const lux = annualExpenses * priorityRatios.luxury;
      const lei = annualExpenses * priorityRatios.leisure;
      let s = shortfall;
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
      unaffordableContribution: unaffordableContribution || undefined,
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
  }>;
  addBucket: (b: {
    id: string;
    label: string;
    kind: AssetKind;
    balance: number;
    baseMonthly: number;
    deltaFromInterventions: number;
    ownerId: string;
  }) => void;
  addDebt: (d: DebtLine) => void;
  /** Live list of current debts — mutate items in place (downsize/remortgage). */
  debts: DebtLine[];
  /** Person to own pots created by interventions (e.g. a bought property). */
  defaultOwnerId: string;
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
      const target = ctx.buckets.find((b) => b.id === iv.bucketId) ?? ctx.buckets[0];
      if (target) target.balance += amount;
      return `${iv.label || "Lump sum in"}: +${money(amount)}`;
    }
    case "lump_sum_out": {
      const amount = iv.amount || 0;
      const target = ctx.buckets.find((b) => b.id === iv.bucketId) ?? ctx.buckets[0];
      if (target) target.balance = Math.max(0, target.balance - amount);
      return `${iv.label || "Lump sum out"}: -${money(amount)}`;
    }
    case "buy_house": {
      const deposit = iv.deposit || 0;
      const mortgageMonthly = iv.mortgageMonthly || 0;
      const mortgageBalance = iv.mortgageBalance || 0;
      const mortgageRate = iv.mortgageRate || 0;
      const rentReplaced = iv.rentReplaced || 0;
      const propertyValue = iv.propertyValue || deposit;

      // Take deposit from first cash bucket
      const cashBucket = ctx.buckets.find((b) => b.kind === "cash");
      if (cashBucket) cashBucket.balance = Math.max(0, cashBucket.balance - deposit);

      // Reduce rent from expenses (mortgage goes to debt instead, not expenses)
      ctx.setMonthlyExpenses(ctx.getMonthlyExpenses() - rentReplaced);

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

      return `${iv.label || "Buy house"}: deposit ${money(deposit)}, mortgage ${money(mortgageMonthly)}/mo${mortgageBalance > 0 ? ` (${money(mortgageBalance)} @ ${mortgageRate}%)` : ""}`;
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
      const cash = ctx.buckets.find((b) => b.kind === "cash");
      if (cash) cash.balance += released;
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
        const cash = ctx.buckets.find((b) => b.kind === "cash");
        if (cash) cash.balance += release;
      }
      const parts = [
        iv.newRate !== undefined ? `rate → ${iv.newRate}%` : null,
        iv.newMonthlyPayment !== undefined ? `${money(iv.newMonthlyPayment)}/mo` : null,
        release > 0 ? `released ${money(release)}` : null,
      ].filter(Boolean);
      return `${iv.label || "Remortgage"}: ${parts.length ? parts.join(", ") : "no change"}`;
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
