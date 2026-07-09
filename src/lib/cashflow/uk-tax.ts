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

  const taxable = Math.max(0, annualGross - effectivePA);
  const basicCap = Math.max(0, basicRateThreshold - effectivePA);
  const higherCap = Math.max(0, higherRateThreshold - effectivePA);

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

  // NI Class 1 employee — flat-band approximation
  let ni = 0;
  if (annualGross > niPrimaryThreshold) {
    const main = Math.min(annualGross, niUpperEarningsLimit) - niPrimaryThreshold;
    ni += Math.max(0, main) * (niMainRatePct / 100);
    if (annualGross > niUpperEarningsLimit) {
      ni += (annualGross - niUpperEarningsLimit) * (niUpperRatePct / 100);
    }
  }

  const total = tax + ni;
  const takeHome = annualGross - total;
  return { tax, ni, total, takeHome };
}
