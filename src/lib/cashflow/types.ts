/**
 * A per-year step in a line's monthly amount. `fromYear` is a 1-indexed
 * projection year (year 1 = the first year after "today"); `amount` is the
 * monthly figure that applies from that year until the next step (or the end
 * of the horizon).
 *
 * When a line has ANY steps, the projector uses the stepped schedule INSTEAD
 * of growing the flat amount by the assumption rate — the numbers you type are
 * the numbers used (Voyant-style manual "step changes"). The line's base
 * `amount` / `monthlyAmount` is the value used for years before the first step.
 * This is how "salary £40k now, £45k in year 2, drops to £35k in year 3 after
 * the baby" and "invest £500 then £1,000 then £500" are modelled per-year.
 */
export type AmountStep = {
  /** 1-indexed projection year this value takes effect. */
  fromYear: number;
  /** Monthly amount (same units as the line — gross if the line isGross). */
  amount: number;
};

/**
 * Resolve the monthly amount for a given 1-indexed projection year.
 * - No steps → returns null (caller falls back to the auto-grown flat value).
 * - Steps    → the amount of the latest step whose fromYear <= year, or `base`
 *              for years before the first step. Steps are absolute: no growth
 *              is applied on top, so what the coach types is what is used.
 */
export function resolveSteppedAmount(
  base: number,
  steps: AmountStep[] | undefined,
  year: number
): number | null {
  if (!steps || steps.length === 0) return null;
  let value = base;
  for (const s of [...steps].sort((a, b) => a.fromYear - b.fromYear)) {
    if (year >= s.fromYear) value = s.amount;
    else break;
  }
  return value;
}

/**
 * A person in the plan. A plan has 1 person (single) or 2 (a couple). Each
 * person is taxed separately — their own Personal Allowance, bands, NI and
 * pension annual allowance. Expenses stay at the household level.
 */
export type Person = {
  id: string;
  name: string;
  currentAge?: number;
};

/** Stable id for the implicit single person on legacy / single-person plans. */
export const DEFAULT_PERSON_ID = "person_you";

export type IncomeLine = {
  id: string;
  label: string;
  amount: number;
  frequency: "monthly";
  /** Whose income this is (drives per-person tax). Undefined = the first/only
   *  person. */
  personId?: string;
  // When true, amount is treated as GROSS (pre-tax). The projector computes
  // UK PAYE + NI and deducts. Default false for backward compat with the
  // Financial Snapshot worksheet which captures "Take-home pay (after tax)".
  isGross?: boolean;
  /** Optional per-year step schedule. When present, overrides auto-growth —
   *  see AmountStep. `amount` above is the value before the first step. */
  steps?: AmountStep[];
  /**
   * Optional active window (1-indexed projection years; year 0 = today). The
   * income only counts in years where startYear <= y <= endYear. This models
   * age/year-triggered streams: a salary that STOPS at retirement (endYear), or
   * a State Pension / DB pension / annuity that STARTS later (startYear).
   * - startYear undefined → active from today
   * - endYear   undefined → continues indefinitely
   */
  startYear?: number;
  endYear?: number;
};

/**
 * Funding priority, Voyant-style. When a year can't fund everything (even after
 * drawing on savings), the lowest priority is sacrificed first. 1 = Basics
 * (rent, food — fund first), 2 = Leisure, 3 = Luxury (give up first).
 */
export type ExpensePriority = 1 | 2 | 3;

export const EXPENSE_PRIORITY_LABELS: Record<ExpensePriority, string> = {
  1: "Basics",
  2: "Leisure",
  3: "Luxury",
};

export type ExpenseLine = {
  id: string;
  category: "essentials" | "lifestyle" | "discretionary" | "other";
  label: string;
  amount: number;
  /** Funding priority. Defaults from category via expensePriority(). */
  priority?: ExpensePriority;
  /** Optional per-year step schedule. When present, overrides inflation-growth
   *  — see AmountStep. `amount` above is the value before the first step. */
  steps?: AmountStep[];
};

/** Default funding priority for an expense — explicit override wins, else
 *  derived from its category. */
export function expensePriority(e: { category: ExpenseLine["category"]; priority?: ExpensePriority }): ExpensePriority {
  if (e.priority) return e.priority;
  switch (e.category) {
    case "essentials":
      return 1;
    case "discretionary":
      return 3;
    case "lifestyle":
    case "other":
    default:
      return 2;
  }
}

export type DebtLine = {
  id: string;
  name: string;
  balance: number;
  rate: number;
  minPayment: number;
  actualPayment: number;
};

export type AssetKind = "cash" | "stocks" | "pension" | "property";

export const ASSET_KIND_LABELS: Record<AssetKind, string> = {
  cash: "Cash savings",
  stocks: "Stocks & shares",
  pension: "Pension",
  property: "Property",
};

/**
 * Tax wrapper for a savings pot — drives how its GROWTH is taxed each year.
 * Orthogonal to AssetKind (which drives the growth rate) and to pension relief
 * (which is keyed off kind === "pension").
 * - "isa"   → tax-free (ISA / LISA / pension-sheltered): no growth tax
 * - "gia"   → General Investment Account: dividends taxed yearly above the
 *             dividend allowance (capital gains are deferred to disposal)
 * - "cash_taxed" → unwrapped cash: interest taxed above the PSA at the
 *             client's marginal rate
 * - "none"  → no tax modelling (default — preserves legacy behaviour)
 */
export type TaxWrapper = "isa" | "gia" | "cash_taxed" | "none";

export const TAX_WRAPPER_LABELS: Record<TaxWrapper, string> = {
  isa: "ISA / sheltered (tax-free)",
  gia: "GIA — taxed (dividends)",
  cash_taxed: "Cash — taxed (interest)",
  none: "No tax modelling",
};

export type SavingsAllocation = {
  id: string;
  label: string;
  monthlyAmount: number;
  target: number | null;
  current: number;
  kind?: AssetKind;
  /** Tax wrapper — how this pot's growth is taxed. Default "none" (no drag),
   *  preserving legacy behaviour. See TaxWrapper. */
  wrapper?: TaxWrapper;
  /** Which person owns this pot (drives per-person pension annual allowance and
   *  per-person dividend/savings allowances). Undefined = first/only person, or
   *  "joint" for a shared pot (taxed against the first person). */
  ownerId?: string;
  /**
   * Optional contribution window. The bucket's monthlyAmount applies only in
   * projection years where startYear <= y <= endYear (both inclusive,
   * 1-indexed where year 1 is the first projection year after "today").
   * - startYear undefined → contributions begin immediately at year 1
   * - endYear   undefined → contributions continue indefinitely
   * Existing balance still compounds across the entire horizon regardless of
   * the contribution window.
   */
  startYear?: number;
  endYear?: number;
  /**
   * Optional per-year step schedule for the monthly contribution. When present,
   * overrides the flat `monthlyAmount` (which becomes the pre-first-step value)
   * — see AmountStep. This is the per-year "give this gear steps" control:
   * e.g. invest £500 in year 1, £1,000 in year 2, £500 in year 3. The
   * startYear/endYear window still gates whether ANY contribution lands.
   */
  steps?: AmountStep[];
};

export type InterventionType =
  | "income_change"
  | "expense_change"
  | "savings_change"
  | "lump_sum_in"
  | "lump_sum_out"
  | "buy_house"
  | "downsize"
  | "remortgage"
  | "death"
  | "asset_crash";

/**
 * Region-aware annual contribution limits for tax-advantaged accounts.
 * Used by the savings UI to flag over-limit contributions. Coaches can
 * mentally override (e.g., a "Stocks" bucket might actually be a GIA, not
 * an ISA — the flag is a heuristic, not enforcement).
 */
export const ANNUAL_LIMITS: Record<Region, Record<AssetKind, number>> = {
  UK: { pension: 60000, stocks: 20000, cash: Infinity, property: Infinity }, // ISA / SIPP
  US: { pension: 23000, stocks: 7000, cash: Infinity, property: Infinity }, // 401(k) / IRA
  OTHER: { pension: Infinity, stocks: Infinity, cash: Infinity, property: Infinity },
};

/**
 * Where annual surplus is sent. Surplus cascades down an ordered list of these:
 * destination 1 fills first (up to its optional cap), overflow spills to
 * destination 2, and so on. Anything left after the last destination stays
 * UNALLOCATED ("money with no job") — it is assumed spent and does not grow
 * net worth. This mirrors Voyant's "savings order / sweep" and its behavioural
 * default that surplus is not silently saved.
 */
export type SurplusDestinationTarget =
  | { kind: "bucket"; bucketId: string } // add to a savings/investment/pension pot
  | { kind: "debt"; debtId: string }; // overpay a debt (extra principal)

export type SurplusDestination = {
  id: string;
  target: SurplusDestinationTarget;
  /** Optional annual cap (£). Fill up to the cap, then overflow to the next
   *  destination. undefined = no cap (absorbs all remaining surplus). */
  capPerYear?: number;
  /** Optional active window (1-indexed projection years). Outside it, this
   *  destination is skipped and surplus flows to the next one. */
  startYear?: number;
  endYear?: number;
};

export type Intervention = {
  id: string;
  year: number;
  type: InterventionType;
  label: string;
  // For income_change / expense_change / savings_change: monthly delta
  monthlyDelta?: number;
  /**
   * For income_change / lump_sum_in: pin the money this event creates to a
   * specific savings bucket so it gets first claim on surplus before the
   * general cascade. This is how "the £500 raise in year 2 funds the pension"
   * is modelled — the raise's monthly delta is directed into bucketId every
   * year from `year` onward (capped by available surplus). undefined = the
   * money just lifts general surplus and flows down surplusDestinations. */
  destinationBucketId?: string;
  // For lump_sum_in / lump_sum_out: amount
  amount?: number;
  // For lump sums: which bucket id (or "any" for first cash)
  bucketId?: string;
  // For buy_house:
  deposit?: number;
  mortgageMonthly?: number;
  mortgageBalance?: number; // initial mortgage loan amount
  mortgageRate?: number; // annual interest rate %
  rentReplaced?: number; // amount of rent (essentials) that goes to zero
  propertyValue?: number;
  // For downsize / remortgage:
  /** The property bucket being sold/downsized, or the mortgage being changed.
   *  Falls back to the first property bucket / first mortgage-like debt. */
  propertyBucketId?: string;
  mortgageDebtId?: string;
  /** remortgage: new annual interest rate % (undefined = unchanged). */
  newRate?: number;
  /** remortgage: new monthly payment (undefined = unchanged). */
  newMonthlyPayment?: number;
  /** remortgage / downsize: equity released as new borrowing — added to the
   *  mortgage balance and paid out to cash. */
  equityRelease?: number;
  /** downsize: rent to add back to expenses if selling up and renting again. */
  newRentMonthly?: number;
  // For death (survivor scenario):
  /** Which person dies. Their income stops, their pots pass to the survivor,
   *  life cover pays out to cash, and household expenses drop. */
  deceasedPersonId?: string;
  /** % the household's expenses fall to once one person has died (one mouth,
   *  not two). Default ~33% reduction. */
  expenseReductionPct?: number;
  /** Lump sum paid out by life cover on death (to cash). If omitted, the sum
   *  of the plan's term-life policy sums-assured is used. */
  lifeCoverPayout?: number;
  // For asset_crash:
  crashPct?: number; // % drop applied to target asset class (default 30)
  targetKind?: "stocks" | "property" | "all"; // which asset class crashes
  // Scenario tag for side-by-side comparison.
  // - undefined / "both" → fires in both base and alternative projections
  // - "alt" → only fires in the alternative projection
  // (no "base only" tag — base is everything-not-marked-alt)
  altOnly?: boolean;
};

export type Region = "UK" | "US" | "OTHER";

export const REGION_LABELS: Record<Region, string> = {
  UK: "United Kingdom",
  US: "United States",
  OTHER: "Other / no tax modelling",
};

// Suggested currency + locale defaults per region. Coach can override.
export const REGION_DEFAULTS: Record<Region, { currency: string; locale: string }> = {
  UK: { currency: "GBP", locale: "en-GB" },
  US: { currency: "USD", locale: "en-US" },
  OTHER: { currency: "GBP", locale: "en-GB" },
};

export type USTaxAssumptions = {
  filingStatus: "single" | "married_jointly";
  standardDeduction: number;
  // Federal brackets — cumulative ceilings; null upTo = unlimited
  brackets: Array<{ upTo: number | null; ratePct: number }>;
  // FICA
  socialSecurityRatePct: number;
  socialSecurityWageBase: number;
  medicareRatePct: number;
  additionalMedicareRatePct: number;
  additionalMedicareThreshold: number;
};

export const DEFAULT_US_TAX_SINGLE: USTaxAssumptions = {
  filingStatus: "single",
  standardDeduction: 14600,
  brackets: [
    { upTo: 11600, ratePct: 10 },
    { upTo: 47150, ratePct: 12 },
    { upTo: 100525, ratePct: 22 },
    { upTo: 191950, ratePct: 24 },
    { upTo: 243725, ratePct: 32 },
    { upTo: 609350, ratePct: 35 },
    { upTo: null, ratePct: 37 },
  ],
  socialSecurityRatePct: 6.2,
  socialSecurityWageBase: 168600,
  medicareRatePct: 1.45,
  additionalMedicareRatePct: 0.9,
  additionalMedicareThreshold: 200000,
};

export type UKTaxAssumptions = {
  personalAllowance: number; // £
  basicRateThreshold: number; // £ (income above PA where basic rate ends)
  higherRateThreshold: number; // £ (where higher rate ends, additional begins)
  basicRatePct: number; // 20
  higherRatePct: number; // 40
  additionalRatePct: number; // 45
  // National Insurance Class 1 (employee) thresholds & rates
  niPrimaryThreshold: number; // £
  niUpperEarningsLimit: number; // £
  niMainRatePct: number; // 8 (2024-25)
  niUpperRatePct: number; // 2
};

export const DEFAULT_UK_TAX: UKTaxAssumptions = {
  personalAllowance: 12570,
  basicRateThreshold: 50270,
  higherRateThreshold: 125140,
  basicRatePct: 20,
  higherRatePct: 40,
  additionalRatePct: 45,
  niPrimaryThreshold: 12570,
  niUpperEarningsLimit: 50270,
  niMainRatePct: 8,
  niUpperRatePct: 2,
};

/**
 * UK tax allowances for investment income and pension contributions, used to
 * tax unwrapped (GIA / taxed-cash) pots and to cap pension contributions.
 * 2024-25 defaults. All amounts £, all rates %.
 */
export type UKTaxAllowances = {
  dividendAllowance: number; // £500
  dividendBasicPct: number; // 8.75
  dividendHigherPct: number; // 33.75
  dividendAdditionalPct: number; // 39.35
  /** Assumed dividend yield on GIA equity balances (% of opening balance). */
  giaDividendYieldPct: number; // ~2
  psaBasic: number; // £1,000 personal savings allowance (basic-rate)
  psaHigher: number; // £500 (higher-rate); additional-rate = £0
  pensionAnnualAllowance: number; // £60,000
  pensionTaperThreshold: number; // £260,000 adjusted income
  pensionAnnualAllowanceMin: number; // £10,000 (floor after taper)
  // --- Capital gains (charged on disposal during decumulation) ---
  cgtAnnualExempt: number; // £3,000
  cgtBasicPct: number; // 18
  cgtHigherPct: number; // 24
  /** Assumed fraction of a GIA withdrawal that is taxable gain (vs returned
   *  capital) — we don't track cost basis, so this is a pragmatic proxy. */
  giaGainFraction: number; // 0.5
  /** Age a pension can first be accessed (UK: 55, rising to 57). Pots aren't
   *  drawn for income before the owner reaches this age. */
  pensionAccessAge: number; // 57
};

export const DEFAULT_UK_ALLOWANCES: UKTaxAllowances = {
  dividendAllowance: 500,
  dividendBasicPct: 8.75,
  dividendHigherPct: 33.75,
  dividendAdditionalPct: 39.35,
  giaDividendYieldPct: 2,
  psaBasic: 1000,
  psaHigher: 500,
  pensionAnnualAllowance: 60000,
  pensionTaperThreshold: 260000,
  pensionAnnualAllowanceMin: 10000,
  cgtAnnualExempt: 3000,
  cgtBasicPct: 18,
  cgtHigherPct: 24,
  giaGainFraction: 0.5,
  pensionAccessAge: 57,
};

export type ProjectionAssumptions = {
  horizonYears: number;
  incomeGrowthPct: number;
  expenseInflationPct: number;
  // Per-asset-class growth rates (annual mean)
  cashGrowthPct: number;
  stocksGrowthPct: number;
  pensionGrowthPct: number;
  propertyGrowthPct: number;
  // Per-asset-class annual return std-dev (volatility). Used by Monte Carlo
  // and Historic stress-tests; deterministic projection uses the mean.
  // Defaults reflect long-run historical volatility:
  //   cash ~1%, stocks ~18%, pension (mixed default) ~12%, property ~8%
  cashStdDevPct?: number;
  stocksStdDevPct?: number;
  pensionStdDevPct?: number;
  propertyStdDevPct?: number;
  // Pension/retirement-account contribution tax-relief uplift (%).
  // UK: default 25 (basic rate at-source relief). US: typically 0 since pre-tax
  // 401(k) reduces taxable income directly via the gross-income flow.
  pensionTaxReliefPct: number;
  // Region drives which tax model applies and the suggested currency/locale.
  region?: Region;
  // ISO-4217 currency code (e.g., GBP, USD, EUR). Defaults follow region.
  currency?: string;
  // BCP-47 locale for number/date formatting (e.g., en-GB, en-US).
  locale?: string;
  // UK income tax + NI configuration (2024-25 defaults)
  ukTax?: UKTaxAssumptions;
  // UK investment + pension allowances (dividend/CGT/PSA/pension AA). When
  // present, unwrapped pots (wrapper "gia"/"cash_taxed") are taxed each year
  // and pension contributions are capped at the annual allowance.
  ukAllowances?: UKTaxAllowances;
  // US federal income tax + FICA configuration (2024 defaults, single filer)
  usTax?: USTaxAssumptions;
  // Legacy field; kept for back-compat with existing rows
  savingsGrowthPct?: number;
};

export const DEFAULT_ASSUMPTIONS: ProjectionAssumptions = {
  horizonYears: 5,
  incomeGrowthPct: 2,
  expenseInflationPct: 2.5,
  cashGrowthPct: 4,
  stocksGrowthPct: 7,
  pensionGrowthPct: 5,
  propertyGrowthPct: 3,
  // Long-run annual return volatility — drawn from historical UK/US data.
  cashStdDevPct: 1,
  stocksStdDevPct: 18,
  pensionStdDevPct: 12,
  propertyStdDevPct: 8,
  pensionTaxReliefPct: 25,
  region: "UK",
  currency: "GBP",
  locale: "en-GB",
  ukTax: DEFAULT_UK_TAX,
  ukAllowances: DEFAULT_UK_ALLOWANCES,
  usTax: DEFAULT_US_TAX_SINGLE,
  savingsGrowthPct: 4,
};

export type YearProjection = {
  year: number;
  yearLabel: string;
  annualIncome: number; // post-tax (take-home) annual income for cashflow
  annualGrossIncome?: number; // gross annual income (sum of isGross income lines × 12), if any
  annualExpenses: number;
  annualSurplus: number; // gross leftover: income − expenses − debt − scheduled savings
  /** Portion of annualSurplus that was given a job this year (routed into a
   *  pot or onto a debt via surplusDestinations / pinned events). Grows net
   *  worth. Only present once surplus allocation is in use. */
  allocatedSurplus?: number;
  /** Portion of annualSurplus with no destination — assumed spent, does NOT
   *  grow net worth. unallocatedSurplus = max(0, annualSurplus − allocated). */
  unallocatedSurplus?: number;
  /** Total intended bucket contributions for the year (in-window, pre
   *  tax-relief). What the plan TRIED to put away this year. */
  plannedContributions?: number;
  /** Portion of plannedContributions that drove the year into deficit — i.e.
   *  if contributions had been this much lower, the year would have broken
   *  even. This is the "you tried to save more than this year could afford"
   *  signal that powers the per-year affordability note. */
  unaffordableContribution?: number;
  /** In a deficit year, how much was pulled from liquid savings to cover the
   *  overspend (drains net worth). */
  assetsDrawn?: number;
  /** Overspend that could NOT be covered even after draining liquid assets.
   *  This is the "red bar" — a genuine shortfall the plan can't fund. */
  shortfall?: number;
  /** When there's a shortfall, which spending tiers it falls on — sacrificed
   *  lowest-first (Luxury, then Leisure, then Basics). Sums to `shortfall`. */
  droppedByPriority?: { basics: number; leisure: number; luxury: number };
  cumulativeSavings: number; // total of all asset classes combined
  // Optional per-class breakdowns (populated by projector when asset classes used)
  cashBalance?: number;
  stocksBalance?: number;
  pensionBalance?: number;
  propertyBalance?: number;
  totalDebtBalance: number;
  // Per-debt year-end balances (mortgage included once buy_house has fired)
  debtBalances?: Array<{ id: string; name: string; balance: number }>;
  // Tax & NI paid this year (only non-zero if any income line is gross)
  annualTaxPaid?: number;
  annualNIPaid?: number;
  /** Tax on unwrapped investment growth this year — dividends on GIA pots +
   *  interest on taxed-cash pots above their allowances. Drains net worth. */
  investmentTaxPaid?: number;
  /** Tax paid when drawing pots down to fund a shortfall (retirement income):
   *  income tax on the taxable 75% of pension withdrawals + CGT on GIA gains.
   *  This is what makes "will the money last?" honest. */
  decumulationTaxPaid?: number;
  netWorth: number;
  // Notes about what happened this year (interventions fired)
  events?: string[];

  /**
   * Year-detail breakdown — populated for the modal "click a year, see the
   * full cash flow statement" view. Sums aren't strictly necessary in the
   * top-level fields above, but per-bucket / per-debt deltas are needed for
   * the drill-in.
   */
  bucketDeltas?: Array<{
    id: string;
    label: string;
    kind: AssetKind;
    openingBalance: number;
    contributions: number; // net annual scheduled contribution that landed (post tax-relief)
    surplusAdded?: number; // extra surplus routed here this year (directed + cascade)
    growth: number; // closing - opening - contributions - surplusAdded
    closingBalance: number;
  }>;
  debtDeltas?: Array<{
    id: string;
    name: string;
    openingBalance: number;
    interestPaid: number;
    principalPaid: number;
    surplusOverpaid?: number; // extra principal paid from surplus this year
    closingBalance: number;
  }>;
  expensesByCategory?: {
    essentials: number;
    lifestyle: number;
    discretionary: number;
    other: number;
  };
};

export type RetirementSettings = {
  yearsUntilRetirement: number; // years from today
  desiredAnnualIncome: number; // in plan's currency
  statePensionAnnual: number; // UK State Pension / US Social Security (annual)
  /** Client's current age. When set, charts label the x-axis by age (Voyant
   *  style) and place the Pre-Retirement / Retirement phase band. Optional —
   *  charts fall back to calendar years when absent. */
  currentAge?: number;
};

export const REGION_RETIREMENT_DEFAULTS: Record<Region, RetirementSettings> = {
  UK: { yearsUntilRetirement: 30, desiredAnnualIncome: 30000, statePensionAnnual: 11500 },
  US: { yearsUntilRetirement: 30, desiredAnnualIncome: 60000, statePensionAnnual: 22000 },
  OTHER: { yearsUntilRetirement: 30, desiredAnnualIncome: 30000, statePensionAnnual: 0 },
};

export type GoalMarker = {
  targetAmount: number; // net-worth target
  targetYear: number; // years from today (1..horizon)
  label?: string;
};

/**
 * A discrete planning goal beyond the headline net-worth target. Each goal
 * has a type that drives the language used in the UI and the AI narrative,
 * but the math is the same: target amount + target year, optionally funded
 * by a specific savings bucket.
 *
 * Goals are additive to the existing goalMarker (which stays as the primary
 * chart-level target). Multi-goal lets the coach track 3-6 typical
 * objectives — retirement, education, deposit, gifting, lifestyle — without
 * losing the headline.
 */
export type GoalType =
  | "retirement"
  | "education"
  | "deposit"      // house deposit, business startup capital
  | "debt_free"    // be debt-free by year X
  | "emergency"    // emergency fund target
  | "gifting"      // gift to family / charity at year X
  | "lifestyle"    // kitchen remodel, travel sabbatical, big-ticket
  | "other";

export type Goal = {
  id: string;
  name: string;
  type: GoalType;
  targetAmount: number;
  /** Years from today (1..horizonYears). */
  targetYearOffset: number;
  /** Optional savings bucket that funds this goal. */
  fundingBucketId?: string;
  /** Higher = more important. Used to break ties when allocating surplus. */
  priority?: number;
  /** Free-text note (why it matters / behavioural hook from W9). */
  note?: string;
};

export const GOAL_TYPE_LABELS: Record<GoalType, string> = {
  retirement: "Retirement",
  education: "Education",
  deposit: "Deposit / capital",
  debt_free: "Debt-free",
  emergency: "Emergency fund",
  gifting: "Gifting",
  lifestyle: "Lifestyle",
  other: "Other",
};

/**
 * Protection policy — term life, critical illness, income protection.
 * Used by the Life-Needs Insight panel to compute death/illness shortfalls.
 * Premiums can optionally bump monthly expenses; the calculation itself is
 * what-if (no projector impact unless tied to an intervention).
 */
export type PolicyKind = "term_life" | "critical_illness" | "income_protection";

export type Policy = {
  id: string;
  label: string;
  kind: PolicyKind;
  /** Headline benefit amount (death sum, CI lump, monthly IP benefit). */
  sumAssured: number;
  /** Monthly premium paid by the client. */
  monthlyPremium: number;
  /** Term in years (e.g., 25-year level term). Null = whole-of-life. */
  termYears?: number | null;
  /** Held in trust → benefit excluded from estate for IHT calc. */
  inTrust?: boolean;
};

export const POLICY_KIND_LABELS: Record<PolicyKind, string> = {
  term_life: "Term life",
  critical_illness: "Critical illness",
  income_protection: "Income protection",
};

export type CashflowPlanData = {
  /** People in the plan — 1 (single) or 2 (a couple). Each is taxed
   *  separately. Absent/empty on legacy plans → treated as a single person. */
  people?: Person[];
  income: IncomeLine[];
  expenses: ExpenseLine[];
  debts: DebtLine[];
  savings: SavingsAllocation[];
  interventions?: Intervention[];
  /** Ordered priority list for routing each year's surplus. Empty/undefined =
   *  surplus stays unallocated (assumed spent). See SurplusDestination. */
  surplusDestinations?: SurplusDestination[];
  retirement?: RetirementSettings;
  goalMarker?: GoalMarker;
  /** Additional planning goals beyond the headline goalMarker. */
  goals?: Goal[];
  /** Protection policies (life / CI / IP). Used by Life-Needs Insight. */
  policies?: Policy[];
  /** Number of dependents and their years-of-financial-dependency. Used by
   *  Life-Needs to size the death shortfall. Coach editable. */
  protectionContext?: {
    dependents?: number;
    yearsOfDependency?: number;
    /** Annual essentials cost the surviving family would still face. */
    annualEssentialsForFamily?: number;
  };
  contextNote: string;
  coachPrepNotes: string;
  assumptions?: ProjectionAssumptions;
};

/**
 * A named, saved version of a CashflowPlanData. Each client can have multiple
 * scenarios (Base plan / AI suggestion / What-if XYZ) and switch between them.
 * Stored as a JSONB array on cashflow_plans.scenarios; the active one is
 * tracked by cashflow_plans.active_scenario_id.
 */
export type CashflowScenario = {
  id: string;
  name: string;
  data: CashflowPlanData;
  createdAt: string; // ISO timestamp
  updatedAt: string;
};

export type CashflowPlanRow = {
  id: string;
  client_id: string;
  data: CashflowPlanData;
  shared_with_client: boolean;
  shared_at: string | null;
  created_at: string;
  updated_at: string;
};

/**
 * The plan's people, with a synthesised single person for legacy/empty plans
 * so callers can always assume at least one. Never mutates the plan.
 */
export function effectivePeople(plan: { people?: Person[] }): Person[] {
  if (plan.people && plan.people.length > 0) return plan.people;
  return [{ id: DEFAULT_PERSON_ID, name: "You" }];
}

/** Resolve an income/owner id to a concrete person id. Undefined or an unknown
 *  id (and "joint") map to the first person — who the tax is computed against. */
export function resolvePersonId(
  id: string | undefined,
  people: Person[]
): string {
  const first = people[0]?.id ?? DEFAULT_PERSON_ID;
  if (!id || id === "joint") return first;
  return people.some((p) => p.id === id) ? id : first;
}

export const EMPTY_PLAN: CashflowPlanData = {
  income: [],
  expenses: [],
  debts: [],
  savings: [],
  interventions: [],
  contextNote: "",
  coachPrepNotes: "",
};

export const DOMINANT_SCRIPTS = [
  "Money Avoidance",
  "Money Worship",
  "Money Status",
  "Money Vigilance",
] as const;

export type DominantScript = (typeof DOMINANT_SCRIPTS)[number];
