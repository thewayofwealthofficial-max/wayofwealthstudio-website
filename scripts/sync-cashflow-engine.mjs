#!/usr/bin/env node
/**
 * Copy the cash flow engine from the coaching portal into this site.
 *
 *   npm run sync:engine
 *
 * The portal is the ONE source of truth for the maths. This site's free
 * Cash Flow Model tool used to hold its own hand-copied duplicate, which
 * silently drifted: for a while every bug fixed in the portal was still live
 * here. Rather than maintain two engines, we copy the portal's files verbatim
 * and rewrite the import paths, which is the only thing that ever differed.
 *
 * The copied files are marked as generated. Do not hand-edit them — fix the
 * portal and run this again.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const site = resolve(here, "..");
const portal = resolve(site, "..", "wow-coaching-portal");
const out = join(site, "src", "lib", "cashflow");

/** portal path → this site's filename */
const FILES = [
  ["src/types/cashflow-plan.ts", "types.ts"],
  ["src/lib/cashflow-projections.ts", "projections.ts"],
  ["src/lib/cashflow-calc.ts", "cashflow-calc.ts"],
  ["src/lib/uk-tax.ts", "uk-tax.ts"],
  ["src/lib/us-tax.ts", "us-tax.ts"],
];

const BANNER = `/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Copied from the coaching portal by scripts/sync-cashflow-engine.mjs.
 * Change the portal, run \`npm run sync:engine\`, commit the result.
 */
`;

/** The only difference between the two copies: how they name their imports. */
function rewriteImports(source) {
  return source
    .replace(/@\/types\/cashflow-plan/g, "./types")
    .replace(/@\/lib\/cashflow-projections/g, "./projections")
    .replace(/@\/lib\//g, "./");
}

if (!existsSync(portal)) {
  console.error(`Cannot find the coaching portal at ${portal}`);
  console.error("This script expects the two projects to sit side by side.");
  process.exit(1);
}

let changed = 0;
for (const [from, to] of FILES) {
  const src = join(portal, from);
  if (!existsSync(src)) {
    console.error(`Missing in the portal: ${from}`);
    process.exit(1);
  }
  const next = BANNER + rewriteImports(readFileSync(src, "utf8"));
  const dest = join(out, to);
  const prev = existsSync(dest) ? readFileSync(dest, "utf8") : null;
  if (prev === next) {
    console.log(`  unchanged  ${to}`);
    continue;
  }
  writeFileSync(dest, next, "utf8");
  console.log(`  updated    ${to}`);
  changed++;
}

console.log(
  changed === 0
    ? "\nEngine already in step with the portal."
    : `\n${changed} file${changed === 1 ? "" : "s"} updated from the portal.`
);
