/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Copied from the coaching portal by scripts/sync-cashflow-engine.mjs.
 * Change the portal, run `npm run sync:engine`, commit the result.
 */
import type { UKTaxAssumptions, UKTaxAllowances } from "./types";
import { DEFAULT_UK_TAX } from "./types";

export type UKBand = "basic" | "higher" | "additional";

/** Which marginal income-tax band an annual gross income falls in. */
export function ukMarginalBand(
  annualGross: number,
  tax: UKTaxAssumptions = DEFAULT_UK_TAX
): UKBand {
  if (annualGross <= tax.basicRateThreshold) return "basic";
  if (annualGross <= tax.higherRateThreshold) return "higher";
  return "additional";
}

/**
 * Annual pension allowance after the high-earner taper: reduced by £1 for every
 * £2 of adjusted income over the taper threshold, floored at the minimum.
 */
export function taperedPensionAllowance(
  annualGross: number,
  a: UKTaxAllowances
): number {
  if (annualGross <= a.pensionTaperThreshold) return a.pensionAnnualAllowance;
  const reduction = (annualGross - a.pensionTaperThreshold) / 2;
  return Math.max(a.pensionAnnualAllowanceMin, a.pensionAnnualAllowance - reduction);
}

/**
 * Tax on a year's unwrapped investment income for one person:
 * - dividends (from GIA equity) above the dividend allowance, at the dividend
 *   rate for the band;
 * - cash interest above the Personal Savings Allowance, at the marginal income
 *   rate for the band.
 * Capital gains are NOT taxed here — CGT is deferred to disposal.
 */
export function calcUKInvestmentTax(
  dividends: number,
  interest: number,
  band: UKBand,
  a: UKTaxAllowances,
  tax: UKTaxAssumptions = DEFAULT_UK_TAX
): { dividendTax: number; interestTax: number; total: number } {
  const divRatePct =
    band === "basic" ? a.dividendBasicPct : band === "higher" ? a.dividendHigherPct : a.dividendAdditionalPct;
  const incomeRatePct =
    band === "basic" ? tax.basicRatePct : band === "higher" ? tax.higherRatePct : tax.additionalRatePct;
  const psa = band === "basic" ? a.psaBasic : band === "higher" ? a.psaHigher : 0;

  const dividendTax = Math.max(0, dividends - a.dividendAllowance) * (divRatePct / 100);
  const interestTax = Math.max(0, interest - psa) * (incomeRatePct / 100);
  return { dividendTax, interestTax, total: dividendTax + interestTax };
}

/**
 * Compute UK income tax + Class 1 employee NI on a single annual gross salary.
 * Uses 2024-25 defaults; assumptions are configurable per plan.
 *
 * Includes the personal-allowance taper above £100k (PA reduces by £1 for
 * every £2 of income over £100k, eliminated at £125,140).
 *
 * Does NOT model: dividend tax, capital gains tax, savings income allowance,
 * Scottish bands, salary sacrifice, employer NI. Those would come with v3.5+.
 */
export function calcUKTaxAndNI(
  annualGross: number,
  assumptions: UKTaxAssumptions = DEFAULT_UK_TAX
): { tax: number; ni: number; total: number; takeHome: number } {
  if (annualGross <= 0) return { tax: 0, ni: 0, total: 0, takeHome: 0 };

  const {
    personalAllowance: pa0,
    basicRateThreshold,
    higherRateThreshold,
    basicRatePct,
    higherRatePct,
    additionalRatePct,
    niPrimaryThreshold,
    niUpperEarningsLimit,
    niMainRatePct,
    niUpperRatePct,
  } = assumptions;

  // PA tapered above £100k
  let effectivePA = pa0;
  if (annualGross > 100000) {
    effectivePA = Math.max(0, pa0 - (annualGross - 100000) / 2);
  }

  // The bands are fixed slices of TAXABLE income (gov.uk/income-tax-rates): basic is the first £37,700
  // (50,270 − 12,570), and 45% starts above £125,140. They do not move when the allowance tapers. The old
  // code widened the basic band as the allowance shrank, undercharging £1,000 at £110k (21 Oct 2026).
  const taxable = Math.max(0, annualGross - effectivePA);
  const basicCap = Math.max(0, basicRateThreshold - pa0);
  const higherCap = Math.max(0, higherRateThreshold);

  let tax = 0;
  if (taxable <= basicCap) {
    tax = taxable * (basicRatePct / 100);
  } else if (taxable <= higherCap) {
    tax =
      basicCap * (basicRatePct / 100) +
      (taxable - basicCap) * (higherRatePct / 100);
  } else {
    tax =
      basicCap * (basicRatePct / 100) +
      (higherCap - basicCap) * (higherRatePct / 100) +
      (taxable - higherCap) * (additionalRatePct / 100);
  }

  const ni = calcUKNI(annualGross, niMainRatePct, niUpperRatePct, niPrimaryThreshold, niUpperEarningsLimit);

  const total = tax + ni;
  const takeHome = annualGross - total;
  return { tax, ni, total, takeHome };
}

/**
 * National Insurance on earnings only, at the given main and upper rates: employee Class 1 (8%, 2%) or
 * self-employed Class 4 (6%, 2%), between the primary threshold and the upper earnings limit.
 */
export function calcUKNI(
  earnings: number,
  mainPct: number,
  upperPct: number,
  threshold: number,
  upperLimit: number
): number {
  if (earnings <= threshold) return 0;
  const main = Math.max(0, Math.min(earnings, upperLimit) - threshold) * (mainPct / 100);
  const upper = earnings > upperLimit ? (earnings - upperLimit) * (upperPct / 100) : 0;
  return main + upper;
}

/** Self-employed Class 4 NI rates, verified on GOV.UK 2026-10-05 (gov.uk/self-employed-national-insurance-rates). */
export const UK_CLASS4_MAIN_PCT = 6;
export const UK_CLASS4_UPPER_PCT = 2;
