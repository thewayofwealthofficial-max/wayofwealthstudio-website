/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Copied from the coaching portal by scripts/sync-cashflow-engine.mjs.
 * Change the portal, run `npm run sync:engine`, commit the result.
 */
import type { USTaxAssumptions } from "./types";
import { DEFAULT_US_TAX_SINGLE } from "./types";

/**
 * Compute US federal income tax + FICA on a single annual gross salary.
 * Single filer, 2024 brackets by default. Standard deduction applied.
 *
 * Does NOT model: state income tax, local taxes, AMT, qualified dividends,
 * capital gains, dependents/credits, 401(k) pre-tax adjustments. Coaches in
 * the US should treat this as federal-only and adjust take-home accordingly
 * for state-tax states.
 */
export function calcUSTaxAndFICA(
  annualGross: number,
  assumptions: USTaxAssumptions = DEFAULT_US_TAX_SINGLE
): { tax: number; fica: number; total: number; takeHome: number } {
  if (annualGross <= 0) return { tax: 0, fica: 0, total: 0, takeHome: 0 };

  const taxable = Math.max(0, annualGross - assumptions.standardDeduction);

  let tax = 0;
  let prevCeiling = 0;
  for (const bracket of assumptions.brackets) {
    const ceiling = bracket.upTo ?? Infinity;
    const inBracket = Math.max(0, Math.min(taxable, ceiling) - prevCeiling);
    tax += inBracket * (bracket.ratePct / 100);
    prevCeiling = ceiling;
    if (taxable <= ceiling) break;
  }

  // FICA — Social Security + Medicare + Additional Medicare
  const ssTaxable = Math.min(annualGross, assumptions.socialSecurityWageBase);
  const ss = ssTaxable * (assumptions.socialSecurityRatePct / 100);
  const medicare = annualGross * (assumptions.medicareRatePct / 100);
  const addMedicare =
    annualGross > assumptions.additionalMedicareThreshold
      ? (annualGross - assumptions.additionalMedicareThreshold) *
        (assumptions.additionalMedicareRatePct / 100)
      : 0;
  const fica = ss + medicare + addMedicare;

  const total = tax + fica;
  return { tax, fica, total, takeHome: annualGross - total };
}
