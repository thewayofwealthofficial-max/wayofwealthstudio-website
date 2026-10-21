/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Copied from the coaching portal by scripts/sync-cashflow-engine.mjs.
 * Change the portal, run `npm run sync:engine`, commit the result.
 */
import type { CashflowPlanData, EventLink, IncomeLine, Intervention } from "./types";

/**
 * Events drive the plan (10 Oct 2026, Voyant's events as shared timing anchors).
 *
 * A start or end year can be LINKED to a life event instead of typed in: "salary's last year = the year before
 * Stops working", "pension starts the year of Stops working". The linked year is always the event's year plus
 * the link's offset, so moving the event once moves everything linked to it.
 *
 * What can be linked: an income line's start / end, a pot's contribution start / end, a pot's drawdown start.
 * Anything not linked keeps its typed-in year exactly as before. A link to an event that has been deleted is
 * dropped and the year it last had is kept.
 *
 * applyEventLinks writes the linked years into the plan's ordinary year fields, so every reader (the engine,
 * the PDF, the client page, Excel) sees the same years without knowing links exist.
 */

/** Earliest a start can be (year 1 = first projected year). An end can be 0 = stopped before year 1. */
const MIN_START = 1;
const MIN_END = 0;

const linkedYear = (events: Map<string, Intervention>, link: EventLink | undefined, min: number): number | null => {
  if (!link) return null;
  const ev = events.get(link.eventId);
  if (!ev) return null;
  return Math.max(min, Math.round(ev.year + (link.offset || 0)));
};

/** The year a link gives, or null if the event is gone. For showing in the editor. */
export function resolveLink(plan: CashflowPlanData, link: EventLink, kind: "start" | "end"): number | null {
  const events = new Map((plan.interventions ?? []).map((iv) => [iv.id, iv]));
  return linkedYear(events, link, kind === "start" ? MIN_START : MIN_END);
}

/**
 * The plan with every linked year set from its event. Returns the SAME object when nothing changes, so it is
 * cheap to call on every edit and never causes a needless re-render.
 */
export function applyEventLinks(plan: CashflowPlanData): CashflowPlanData {
  const hasLinks =
    plan.income.some((l) => l.yearLinks) || plan.savings.some((s) => s.yearLinks);
  if (!hasLinks) return plan;
  const events = new Map((plan.interventions ?? []).map((iv) => [iv.id, iv]));
  let changed = false;

  const income = plan.income.map((l) => {
    const links = l.yearLinks;
    if (!links) return l;
    let next = l;
    const keep = { ...links };
    for (const k of ["start", "end"] as const) {
      const link = links[k];
      if (!link) continue;
      const y = linkedYear(events, link, k === "start" ? MIN_START : MIN_END);
      const field = k === "start" ? "startYear" : "endYear";
      if (y === null) delete keep[k]; // event deleted: keep the year, drop the link
      else if (next[field] !== y) next = { ...next, [field]: y };
    }
    if (Object.keys(keep).length !== Object.keys(links).length) {
      next = { ...next, yearLinks: Object.keys(keep).length ? keep : undefined };
    }
    if (next !== l) changed = true;
    return next;
  });

  const savings = plan.savings.map((s) => {
    const links = s.yearLinks;
    if (!links) return s;
    let next = s;
    const keep = { ...links };
    for (const k of ["start", "end"] as const) {
      const link = links[k];
      if (!link) continue;
      const y = linkedYear(events, link, k === "start" ? MIN_START : MIN_END);
      const field = k === "start" ? "startYear" : "endYear";
      if (y === null) delete keep[k];
      else if (next[field] !== y) next = { ...next, [field]: y };
    }
    if (links.drawdownStart) {
      const y = linkedYear(events, links.drawdownStart, MIN_START);
      if (y === null) delete keep.drawdownStart;
      else if (next.drawdown && next.drawdown.startYear !== y) next = { ...next, drawdown: { ...next.drawdown, startYear: y } };
    }
    if (Object.keys(keep).length !== Object.keys(links).length) {
      next = { ...next, yearLinks: Object.keys(keep).length ? keep : undefined };
    }
    if (next !== s) changed = true;
    return next;
  });

  return changed ? { ...plan, income, savings } : plan;
}

/**
 * UK State Pension age from someone's age today, by the GOV.UK timetable (checked 21 Oct 2026): born before
 * 6 April 1960 → 66; 6 March 1961 to 5 April 1977 → 67; from 6 April 1978 → 68 (rising 2044-46, under review).
 * We only know the age, not the birthday, so the birth year is approximate and the months in between round up.
 */
export function statePensionAgeFor(currentAge: number, thisYear = new Date().getFullYear()): number {
  const born = thisYear - currentAge;
  return born < 1960 ? 66 : born < 1978 ? 67 : 68;
}

/**
 * What retiring does to the plan, the way Voyant treats a retirement (21 Oct 2026, after Sam's session):
 * - salary and self-employed income stop the year they retire, unless the line has its own end year;
 * - pension payments in stop with them ("contributions ... stop when that income stops", Voyant [CF] p.9);
 * - the state pension on the retirement card is paid as taxable income from state pension age, unless the
 *   plan already has a state pension income line. Before this, the card's figure never reached the chart.
 * Runs inside the engine only, like applyEventLinks, so the coach's saved plan is never rewritten. A plan with
 * no retirement settings is untouched.
 */
export function applyRetirement(plan: CashflowPlanData): CashflowPlanData {
  const r = plan.retirement;
  const people = plan.people ?? [];
  const firstId = people[0]?.id;
  // Each person's last working year (projection years), state pension age and amount. The first person (or a
  // single-person plan) uses the retirement card; a partner uses their own fields on the People card.
  type Ret = { lastWorkYear?: number; age?: number; spa?: number; statePension: number };
  const retFor = (personId: string | undefined): Ret => {
    const person = people.find((p) => p.id === personId);
    if (!person || person.id === firstId) {
      const age = people[0]?.currentAge ?? r?.currentAge;
      return {
        lastWorkYear: r ? Math.max(0, Math.round(r.yearsUntilRetirement) - 1) : undefined,
        age,
        spa: age === undefined ? undefined : r?.statePensionAge ?? statePensionAgeFor(age),
        statePension: r?.statePensionAnnual ?? 0,
      };
    }
    const age = person.currentAge;
    return {
      lastWorkYear:
        person.retirementAge !== undefined && age !== undefined ? Math.max(0, person.retirementAge - age - 1) : undefined,
      age,
      spa: age === undefined ? undefined : statePensionAgeFor(age),
      statePension: person.statePensionAnnual ?? 0,
    };
  };

  let changed = false;
  const income = plan.income.map((l) => {
    if ((l.kind === "employment" || l.kind === "self_employment") && l.endYear === undefined && !l.yearLinks?.end) {
      const end = retFor(l.personId).lastWorkYear;
      if (end === undefined) return l;
      changed = true;
      return { ...l, endYear: end };
    }
    return l;
  });

  const savings = plan.savings.map((s) => {
    if (s.kind === "pension" && s.monthlyAmount > 0 && s.endYear === undefined && !s.yearLinks?.end) {
      const end = retFor(s.ownerId).lastWorkYear;
      if (end === undefined) return s;
      changed = true;
      return { ...s, endYear: end };
    }
    return s;
  });

  // State pension per person, unless they already have a state pension income line.
  const ids = people.length ? people.map((p) => p.id) : [undefined];
  for (const id of ids) {
    const ret = retFor(id);
    if (ret.statePension <= 0 || ret.age === undefined || ret.spa === undefined) continue;
    const mine = (l: IncomeLine) => (l.personId ?? firstId) === (id ?? firstId);
    const has = plan.income.some(
      (l) => mine(l) && (l.kind === "state_pension" || /state pension|social security/i.test(l.label))
    );
    if (has) continue;
    income.push({
      id: `__state_pension_${id ?? "you"}`,
      label: "State pension",
      amount: ret.statePension / 12,
      frequency: "monthly",
      kind: "state_pension",
      isGross: true, // taxable income
      personId: id,
      startYear: ret.spa > ret.age ? ret.spa - ret.age : undefined,
    });
    changed = true;
  }

  return changed ? { ...plan, income, savings } : plan;
}
