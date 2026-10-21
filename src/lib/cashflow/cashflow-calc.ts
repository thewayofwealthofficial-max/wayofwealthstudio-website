/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Copied from the coaching portal by scripts/sync-cashflow-engine.mjs.
 * Change the portal, run `npm run sync:engine`, commit the result.
 */
import type { CashflowPlanData } from "./types";

export function totalIncome(plan: CashflowPlanData): number {
  return plan.income.reduce((sum, line) => sum + (line.amount || 0), 0);
}

export function totalExpenses(plan: CashflowPlanData): number {
  return plan.expenses.reduce((sum, line) => sum + (line.amount || 0), 0);
}

export function totalDebtPayments(plan: CashflowPlanData): number {
  return plan.debts.reduce((sum, d) => sum + (d.actualPayment || 0), 0);
}

export function totalSavingsAllocations(plan: CashflowPlanData): number {
  return plan.savings.reduce((sum, s) => sum + (s.monthlyAmount || 0), 0);
}

export function netSurplus(plan: CashflowPlanData): number {
  return (
    totalIncome(plan) -
    totalExpenses(plan) -
    totalDebtPayments(plan) -
    totalSavingsAllocations(plan)
  );
}

export function totalDebtBalance(plan: CashflowPlanData): number {
  return plan.debts.reduce((sum, d) => sum + (d.balance || 0), 0);
}

/**
 * Months until a debt is paid off given its actual payment & rate.
 * Returns null if the actual payment doesn't cover the interest.
 */
export function monthsToDebtFree(
  balance: number,
  monthlyRatePct: number,
  monthlyPayment: number
): number | null {
  if (balance <= 0) return 0;
  if (monthlyPayment <= 0) return null;
  const r = monthlyRatePct / 100 / 12;
  if (r === 0) return Math.ceil(balance / monthlyPayment);
  // If interest accrues faster than payment, never pays off
  const monthlyInterest = balance * r;
  if (monthlyPayment <= monthlyInterest) return null;
  // n = -log(1 - (rB/P)) / log(1+r)
  const months = -Math.log(1 - (r * balance) / monthlyPayment) / Math.log(1 + r);
  return Math.ceil(months);
}

/**
 * Months to hit a savings target at the given monthly contribution rate,
 * starting from the current balance. Ignores growth — keeps it honest for
 * short horizons. v2 will add a growth assumption.
 */
export function monthsToSavingsGoal(
  current: number,
  target: number,
  monthlyContribution: number
): number | null {
  if (current >= target) return 0;
  if (monthlyContribution <= 0) return null;
  return Math.ceil((target - current) / monthlyContribution);
}

/**
 * Locale-aware currency formatter. Use this instead of fmtGBP wherever the
 * plan's region/currency might vary. fmtGBP is kept as a back-compat alias.
 */
export function fmtMoney(
  n: number,
  currency: string = "GBP",
  locale: string = "en-GB"
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(n);
}

/**
 * The plan's saved currency, checked. The old free-text box saved every key press, so a plan can
 * hold a half-typed code ("I", "IL") that makes Intl throw and takes the whole page down (Sam, 20 Oct
 * 2026). A bad code shows as GBP with `invalid` set, so the builder can say so plainly.
 */
export function planCurrency(code: string | undefined): { code: string; invalid: string | null } {
  if (!code) return { code: "GBP", invalid: null };
  try {
    new Intl.NumberFormat("en-GB", { style: "currency", currency: code });
    return { code, invalid: null };
  } catch {
    return { code: "GBP", invalid: code };
  }
}

/**
 * Monthly mortgage payment. Repayment: the standard annuity formula, clearing the loan over the term.
 * Interest-only: just the interest. Moved here from the what-if wizard so the builder and engine share it.
 */
export function mortgageMonthlyPayment(loan: number, ratePct: number, years: number, interestOnly = false): number {
  if (loan <= 0) return 0;
  const r = ratePct / 100 / 12;
  if (interestOnly) return loan * r;
  const n = Math.max(1, Math.round(years * 12));
  if (r === 0) return loan / n;
  return (loan * r) / (1 - Math.pow(1 + r, -n));
}

export function fmtGBP(n: number): string {
  return fmtMoney(n, "GBP", "en-GB");
}
