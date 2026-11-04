// Estimate grouping (model/estimateGroups.ts). What is worth pinning: one sort key governs
// every level of the tree, excluded sections group last whatever the sort says, "Whole
// building" sits after the levels, and the page opens on trades with their categories shut.

import { flattenEstimate } from "./engineEstimate";
import { ESTIMATE_FIXTURE as ESTIMATE } from "./engineEstimate.test";
import {
  allGroupIds,
  cumulativeShares,
  defaultCollapsed,
  groupTree,
} from "./estimateGroups";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const labels = (groups: { label: string }[]) => groups.map((g) => g.label).join(",");

export function runEstimateGroupTests(): void {
  const rows = flattenEstimate(ESTIMATE);
  const slab = rows.find((row) => row.key === "slab")!;

  // --- one sort, every level ---------------------------------------------------------------

  const byCost = groupTree(rows, "trade", "cost", ESTIMATE.total);
  assert(labels(byCost) === "Earthwork,Concrete,Furniture & appliances",
    "Cost order: the biggest trade first, and the excluded one last regardless");
  assert(byCost[1].rows.map((r) => r.key).join(",") === "slab,footing",
    "…and the biggest row first inside it");
  assert(byCost[1].children?.[0].id === "trade/concrete/concrete"
    && byCost[1].children[0].label === "Concrete",
    "A trade's categories are its children, path-keyed; an uncategorised row keeps its section");
  assert(byCost[1].children[0].children === null, "…and a category is a leaf");

  const bySpread = groupTree(rows, "trade", "spread", ESTIMATE.total);
  assert(bySpread[0].label === "Earthwork" && bySpread[2].inTotal === false,
    "Spread order: least certain first, furnishings still last");

  const byName = groupTree(rows, "trade", "key", ESTIMATE.total);
  assert(labels(byName) === "Earthwork,Concrete,Furniture & appliances",
    "Name order puts trades in construction sequence");
  assert(byName[1].rows.map((r) => r.key).join(",") === "footing,slab", "…rows alphabetically");

  const byPackage = groupTree(rows, "group", "key", ESTIMATE.total);
  assert(labels(byPackage) === "Site,Concrete & masonry,Furniture",
    "Package names the viewer's toggle groups, in their order");
  assert(byPackage[0].children?.[0].label === "Earthwork", "…with its trades under it");

  const bySection = groupTree(rows, "section", "cost", ESTIMATE.total);
  assert(labels(bySection) === "allowances,concrete,furnishings" && bySection[0].children === null,
    "Section is one level: the prices.toml block a row lives in");

  const flat = groupTree(rows, "none", "cost", ESTIMATE.total);
  assert(flat.length === 2 && flat[0].rows.length === 3 && flat[1].label === "Beside the total",
    "Ranked is one list, plus the excluded rows in their own trailing block");

  const levelled = rows.map((row) => ({ ...row, level: row.key === "slab" ? "basement"
    : row.key === "footing" ? "main" : "building" }));
  const byLevel = groupTree(levelled, "level", "cost", ESTIMATE.total,
    [{ key: "basement", label: "Basement" }, { key: "main", label: "Main" }]);
  assert(byLevel[0].label === "Basement" && byLevel[2].label === "Whole building"
    && byLevel[3].inTotal === false,
    "Whole building sorts after every level, though it is the biggest; excluded still last");

  // --- what starts collapsed ---------------------------------------------------------------

  const leaves = byCost.flatMap((g) => (g.children ?? []).map((c) => c.id));
  assert([...defaultCollapsed(byCost, "trade")].sort().join() === leaves.sort().join(),
    "Trades open, categories shut: the page opens on the headlines and their split");
  assert(defaultCollapsed(bySection, "section").size === bySection.length,
    "A one-level grouping starts shut");
  assert(defaultCollapsed(flat, "none").size === 0, "Ranked never collapses");
  assert(defaultCollapsed(byCost, "trade", true).size === 0, "An active filter expands all");
  assert(allGroupIds(byCost).length === byCost.length + leaves.length, "Every id, both levels");

  // --- what the headers print -------------------------------------------------------------

  const concrete = byCost[1];
  assert(concrete.subtotal.low === 6_340 && concrete.subtotal.high === 7_432,
    "A group subtotal is the sum of its rows' ranges");
  assert(Math.abs(concrete.share - 6_886 / 46_386) < 1e-9, "…its share against the total");
  assert(byCost[0].allowance === 39_500 && concrete.allowance === 0,
    "Allowance dollars are read out per group");
  assert(groupTree(rows, "trade", "cost", null)[0].share === 0, "No total is a share of zero");

  // One trade in the total and beside it buckets twice: a sofa and a cabinet share a trade,
  // not a total.
  const mixed = groupTree(
    [...rows, { ...rows.find((r) => r.key === "sofa")!, key: "cabinet", section: "placeables",
      inTotal: true }], "trade", "cost", ESTIMATE.total);
  const furniture = mixed.filter((g) => g.label === "Furniture & appliances");
  assert(furniture.length === 2 && furniture.find((g) => !g.inTotal)!.share === 0,
    "One trade, two buckets, and the excluded one has no share");

  const untraded = groupTree([{ ...slab, trade: undefined }], "trade", "cost", ESTIMATE.total);
  assert(untraded[0].label === "unfiled", "A row with no trade is filed, never dropped");

  const shares = cumulativeShares(flat[0].rows, ESTIMATE.total);
  assert(Math.abs(shares[shares.length - 1] - 1) < 1e-9 && shares[0] < shares[1],
    "The ranked running share climbs to the whole construction total");

  console.log("Estimate grouping tests passed.");
}
