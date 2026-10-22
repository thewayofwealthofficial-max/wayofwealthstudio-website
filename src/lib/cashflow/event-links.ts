/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Copied from the coaching portal by scripts/sync-cashflow-engine.mjs.
 * Change the portal, run `npm run sync:engine`, commit the result.
 */
import { DEFAULT_MORTALITY_AGE, type CashflowPlanData, type EventLink, type IncomeLine, type Intervention } from "./types";

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
  const events = new Map(timelineEvents(plan).map((iv) => [iv.id, iv]));
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
  const events = new Map(timelineEvents(plan).map((iv) => [iv.id, iv]));
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
    // A final salary pension starts at their retirement unless it has its own start (Voyant help 360054426571).
    if (l.kind === "db_pension" && l.startYear === undefined && !l.yearLinks?.start) {
      const end = retFor(l.personId).lastWorkYear;
      if (end === undefined) return l;
      changed = true;
      return { ...l, startYear: end + 1 };
    }
    if ((l.kind === "employment" || l.kind === "self_employment") && l.endYear === undefined && !l.yearLinks?.end) {
      const end = retFor(l.personId).lastWorkYear;
      if (end === undefined) return l;
      changed = true;
      return { ...l, endYear: end };
    }
    return l;
  });

  const savings = plan.savings.map((s) => {
    // Any payment in, the client's or the employer's (the sweep found employer-only pots ran on past retirement).
    const paying = s.monthlyAmount > 0 || (s.employerMonthly ?? 0) > 0 || (s.employeePctOfSalary ?? 0) > 0 || (s.employerPctOfSalary ?? 0) > 0;
    if (s.kind === "pension" && paying && s.endYear === undefined && !s.yearLinks?.end) {
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
    // Deferred past State Pension age: "For every 9 weeks you defer, you'll get 1% added ... just under 5.8% for
    // every 52 weeks" (gov.uk/deferring-state-pension, new State Pension; checked 22 Oct 2026). Voyant's help
    // doesn't describe deferral, so this is GOV.UK's rule.
    const statutory = statePensionAgeFor(ret.age);
    const deferredYears = Math.max(0, ret.spa - statutory);
    const uplift = 1 + (deferredYears * 52) / 9 / 100;
    income.push({
      id: `__state_pension_${id ?? "you"}`,
      label: deferredYears > 0 ? `State pension (deferred ${deferredYears} yr)` : "State pension",
      amount: (ret.statePension / 12) * uplift,
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

/**
 * Each person's death year (projection years) from their age and "Lives to" age, 90 by default. Null when
 * anyone's age is unknown: then the plan keeps its own forecast length. Voyant: the later death is the plan's
 * end (help 4405509976475).
 */
export function mortalityYears(plan: CashflowPlanData): { byPerson: Record<string, number>; planEnd: number } | null {
  const people = plan.people?.length ? plan.people : null;
  if (!people) {
    const age = plan.retirement?.currentAge;
    if (age === undefined) return null;
    const end = Math.max(1, DEFAULT_MORTALITY_AGE - age);
    return { byPerson: {}, planEnd: end };
  }
  if (people.some((p) => p.currentAge === undefined)) return null;
  const byPerson: Record<string, number> = {};
  for (const p of people) byPerson[p.id] = Math.max(1, (p.mortalityAge ?? DEFAULT_MORTALITY_AGE) - (p.currentAge as number));
  return { byPerson, planEnd: Math.max(...Object.values(byPerson)) };
}

/** Costs tied to a child's ages get their years from the child's birth year (21 Oct 2026). Engine only. */
export function applyChildren(plan: CashflowPlanData, thisYear = new Date().getFullYear()): CashflowPlanData {
  const kids = new Map((plan.children ?? []).map((c) => [c.id, c]));
  if (!kids.size || !plan.expenses.some((e) => e.childId)) return plan;
  const expenses = plan.expenses.map((e) => {
    const kid = e.childId ? kids.get(e.childId) : undefined;
    if (!kid) return e;
    const from = e.childFromAge !== undefined ? kid.birthYear + e.childFromAge - thisYear : undefined;
    const to = e.childToAge !== undefined ? kid.birthYear + e.childToAge - thisYear : undefined;
    return {
      ...e,
      startYear: e.startYear ?? (from !== undefined && from > 0 ? from : undefined),
      endYear: e.endYear ?? (to !== undefined ? Math.max(0, to) : undefined),
    };
  });
  return { ...plan, expenses };
}

/**
 * Voyant's default timeline events (help 4405509976475): each person's Retirement and Mortality, alongside the
 * plan's own events, so a year can follow them ("pension starts the year of John retires"). Synthetic: they're
 * only for linking and never fire in the engine.
 */
export function timelineEvents(plan: CashflowPlanData): Intervention[] {
  const out: Intervention[] = [...(plan.interventions ?? [])];
  const people = plan.people?.length ? plan.people : [{ id: "you", name: "", currentAge: plan.retirement?.currentAge }];
  const mort = mortalityYears(plan);
  people.forEach((p, i) => {
    const name = p.name || (i === 0 ? "You" : "Partner");
    const retireYear =
      i === 0
        ? plan.retirement
          ? Math.round(plan.retirement.yearsUntilRetirement)
          : undefined
        : "retirementAge" in p && p.retirementAge !== undefined && p.currentAge !== undefined
          ? p.retirementAge - p.currentAge
          : undefined;
    if (retireYear !== undefined && retireYear >= 1) {
      out.push({ id: `__retire_${p.id}`, year: retireYear, type: "income_change", label: `${name} retires` });
    }
    const dies = mort?.byPerson[p.id] ?? (i === 0 && !plan.people?.length ? mort?.planEnd : undefined);
    if (dies !== undefined) out.push({ id: `__dies_${p.id}`, year: dies, type: "death", label: `${name} dies (life expectancy)` });
  });
  return out;
}
