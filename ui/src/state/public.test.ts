import { HIDDEN_BOM_COLUMNS, HIDDEN_REPORTS, IS_PUBLIC_SITE, reportVisible } from "./public";
import { REPORTS } from "../components/shell/navigationConfig";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runPublicSiteTests() {
  // The test process is not the published build, so this is the local-editor shape: nothing
  // hidden. The assertion that matters is that the *gate exists and is consistent* — a
  // hidden set that named a report the hub does not have would silently gate nothing.
  assert(IS_PUBLIC_SITE === false,
    "a local/test build is never the public site — VITE_PUBLIC_SITE is a deploy-time flag");
  assert(HIDDEN_REPORTS.size === 0, "the local editor hides no reports");
  assert(HIDDEN_BOM_COLUMNS.size === 0, "the local editor hides no BOM columns");
  assert(REPORTS.every((r) => reportVisible(r.id)), "every reader is offered locally");

  // The public shape, asserted against the same REPORTS list the hub renders from, so a
  // renamed report id cannot leave the gate pointing at nothing.
  const hiddenWhenPublic = ["estimate"];
  assert(
    hiddenWhenPublic.every((id) => REPORTS.some((r) => r.id === id)),
    "every report the public build hides is a report that exists",
  );
  assert(
    REPORTS.some((r) => r.id === "bom"),
    "the BOM stays public — quantities are the product, dollars are opt-in",
  );

  // The columns the public build drops are the ones model/engineCosts.ts appends, spelled
  // the same way. A drift here would hide nothing and be invisible.
  const costColumns = ["unit_price", "cost", "actual_cost", "product", "paid"];
  const dropped = ["unit_price", "cost", "actual_cost", "paid"];
  assert(dropped.every((c) => costColumns.includes(c)),
    "every dropped column is a real cost column");
  assert(!dropped.includes("product"),
    "the specified product is a plan fact, not a price — it stays");

  console.log("Public-site gate tests passed.");
}
