// Estimate arrangement (model/engineEstimate.ts) — pure ranking over the /costs payload.
// What is worth pinning: one sort key governs both the group order and the row order inside
// it, excluded sections group last whatever the sort says, a bar's geometry is derived from
// the payload rather than guessed, and a bid stage at zero survives to the page (a hidden
// zero-markup rung would misreport an owner-build number as a bid).

import type { EngineEstimate } from "../engine/EngineClient";
import {
  barWidths,
  defaultCollapsed,
  rowDescription,
  basisSlices,
  estimateSubtitle,
  flattenEstimate,
  groupRows,
  ladderStages,
  maxHigh,
  shareOfTotal,
  sumRanges,
} from "./engineEstimate";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const ESTIMATE: EngineEstimate = {
  sections: {
    concrete: {
      rows: [
        { key: "slab", quantity: 18.2, unit: "cy", unit_price: { low: 200, high: 260 },
          cost: { low: 3_640, high: 4_732 }, cost_fmt: "", basis: "installed",
          trade: "concrete", nahb_code: "1300" },
        { key: "footing", quantity: 9, unit: "cy", unit_price: { low: 300, high: 300 },
          cost: { low: 2_700, high: 2_700 }, cost_fmt: "", basis: "material",
          trade: "concrete", nahb_code: "1200" },
      ],
      subtotal: { low: 6_340, high: 7_432 }, subtotal_fmt: "", in_total: true,
    },
    allowances: {
      rows: [
        { key: "site-excavation", quantity: 1, unit: "ls",
          unit_price: { low: 24_000, high: 55_000 },
          cost: { low: 24_000, high: 55_000 }, cost_fmt: "", basis: "installed",
          trade: "earth" },
      ],
      subtotal: { low: 24_000, high: 55_000 }, subtotal_fmt: "", in_total: true,
    },
    furnishings: {
      rows: [
        { key: "sofa", quantity: 1, unit: "ea", unit_price: { low: 5_010, high: 28_750 },
          cost: { low: 5_010, high: 28_750 }, cost_fmt: "", trade: "furniture" },
      ],
      subtotal: { low: 5_010, high: 28_750 }, subtotal_fmt: "", in_total: false,
    },
  },
  total: { low: 30_340, high: 62_432 },
  total_fmt: "",
  excluded_sections: ["furnishings"],
  excluded_total: { low: 5_010, high: 28_750 },
  grand_total: { low: 35_350, high: 91_182 },
  basis_declared: true,
  bid: {
    net: {
      material: { low: 2_700, high: 2_700 },
      labour: { low: 0, high: 0 },
      merged: { low: 27_640, high: 59_732 },
    },
    stages: [
      { label: "subtotal_net", low: 30_340, high: 62_432, fmt: "" },
      { label: "waste", low: 135, high: 135, fmt: "" },
      { label: "subtotal_ordered", low: 30_475, high: 62_567, fmt: "" },
      { label: "contingency", low: 3_047.5, high: 6_256.7, fmt: "", rate: 0.1 },
      { label: "overhead", low: 0, high: 0, fmt: "", rate: 0 },
      { label: "profit", low: 0, high: 0, fmt: "", rate: 0 },
      { label: "tax", low: 250, high: 250, fmt: "", rate: 0.0853 },
      { label: "total", low: 33_772.5, high: 69_073.7, fmt: "" },
    ],
    subtotal_net: { low: 30_340, high: 62_432 },
    subtotal_ordered: { low: 30_475, high: 62_567 },
    total: { low: 33_772.5, high: 69_073.7 },
    total_fmt: "",
    untaxed_merged: { low: 27_640, high: 59_732 },
    material_tax_already_paid: { low: 0, high: 0 },
    taxable_material: { low: 2_700, high: 2_700 },
  },
  areas: { conditioned: 5_114, gross: 6_012 },
  per_sf: {
    total: { conditioned: { low: 5.93, high: 12.21 }, gross: { low: 5.05, high: 10.38 } },
    bid_total: { conditioned: { low: 6.6, high: 13.51 }, gross: { low: 5.62, high: 11.49 } },
    sections: {},
  },
  unpriced: [{ section: "framing", key: "2x10", quantity: 768, unit: "LF" }],
};

export function runEngineEstimateTests(): void {
  // --- flatten ----------------------------------------------------------------------------

  const rows = flattenEstimate(ESTIMATE);
  assert(rows.length === 4, "Every priced row across every section, in one array");
  const slab = rows.find((row) => row.key === "slab")!;
  assert(slab.section === "concrete" && slab.inTotal, "A row remembers the block it came from");
  assert(slab.mid === 4_186 && slab.spread === 1_092, "…and what it is worth, and how unsure");
  assert(Math.abs(slab.spreadPct - 1_092 / 4_186) < 1e-9, "spreadPct is spread over the mid");
  const footing = rows.find((row) => row.key === "footing")!;
  assert(footing.spread === 0 && footing.spreadPct === 0,
    "An exactly-priced row has no spread — and no division by a mid of zero");
  assert(rows.find((row) => row.key === "sofa")!.inTotal === false,
    "A furnishings row knows it is beside the total, not in it");
  assert(flattenEstimate(null).length === 0, "No estimate flattens to nothing, never throws");

  assert(sumRanges(rows.map((r) => r.cost)).high === 91_182,
    "Ranges sum low-with-low and high-with-high — never a midpoint of midpoints");

  assert(rowDescription({ ...slab, description: "slab on grade" }) === "slab on grade",
    "A description that says something new is kept");
  assert(rowDescription({ ...slab, description: "slab" }) === null,
    "…one that only repeats the key is not — every allowance is described by its own key");
  assert(rowDescription({ ...slab, key: "slab:CATLIN_DECK_9", description: "CATLIN_DECK_9" })
    === null, "…nor is the qualifier a qualified key already prints");
  assert(rowDescription({ ...slab, description: null }) === null, "…and a null one is null");

  // --- sorting, both levels by one key ----------------------------------------------------

  const byCost = groupRows(rows, "trade", "cost", ESTIMATE.total);
  assert(byCost.map((g) => g.label).join(",") === "earth,concrete,furniture",
    "Cost order: the biggest trade first, and the excluded one last regardless");
  assert(byCost[1].rows.map((r) => r.key).join(",") === "slab,footing",
    "…and the biggest row first inside it");

  const bySpread = groupRows(rows, "trade", "spread", ESTIMATE.total);
  assert(bySpread[0].label === "earth", "Spread order: the least certain trade first");
  assert(bySpread[bySpread.length - 1].label === "furniture",
    "Furnishings still group last — they are not what the total is made of");
  assert(bySpread[1].rows[0].key === "slab", "…widest row first inside the group");

  const byName = groupRows(rows, "trade", "key", ESTIMATE.total);
  assert(byName.map((g) => g.label).join(",") === "earth,concrete,furniture",
    "Name order puts trades in construction sequence, not alphabetically");
  assert(byName[1].rows.map((r) => r.key).join(",") === "footing,slab",
    "…and rows alphabetically inside");

  const bySection = groupRows(rows, "section", "cost", ESTIMATE.total);
  assert(bySection.map((g) => g.label).join(",") === "allowances,concrete,furnishings",
    "Grouping by section names the prices.toml block a row lives in");

  const flat = groupRows(rows, "none", "cost", ESTIMATE.total);
  assert(flat.length === 2 && flat[0].rows.length === 3,
    "'none' is one flat ranked list — plus the excluded rows, which never rank among the "
    + "things the construction total is made of");
  assert(flat[0].rows[0].key === "site-excavation", "…ranked by the same measure");
  // --- what starts collapsed ---------------------------------------------------------------

  assert(defaultCollapsed(byCost, "trade").size === byCost.length,
    "Grouped by trade, every group starts closed — the page opens on the headlines, not on "
    + "470 rows");
  assert([...defaultCollapsed(bySection, "section")].sort().join(",")
    === bySection.map((g) => g.id).sort().join(","),
    "…and by section the same, ids and all");
  assert(defaultCollapsed(flat, "none").size === 0,
    "'none' is never collapsed: its one group IS the table, and closing it leaves a blank "
    + "page rather than a summary");
  assert(defaultCollapsed(byCost, "trade", true).size === 0,
    "An active filter expands everything — a page of closed headlines cannot tell a filter "
    + "that matched from one that did not");

  assert(flat[1].label === "Beside the total" && flat[1].rows[0].key === "sofa",
    "…and the trailing block says what it is");

  // --- what the headers print -------------------------------------------------------------

  const concrete = byCost.find((g) => g.label === "concrete")!;
  assert(concrete.subtotal.low === 6_340 && concrete.subtotal.high === 7_432,
    "A group subtotal is the sum of its rows' ranges");
  assert(Math.abs(concrete.share - 6_886 / 46_386) < 1e-9,
    "…and its share is against the construction total, midpoint over midpoint");
  const furniture = byCost.find((g) => g.label === "furniture")!;
  assert(furniture.inTotal === false, "The excluded group says it is excluded");
  assert(groupRows(rows, "trade", "cost", null)[0].share === 0,
    "No total to divide by is a share of zero, never a NaN on screen");

  // A trade shared by an in-total section and an excluded one buckets twice, not once: the
  // catlin house prices sofas in [furnishings] and cabinets in [placeables], both trade
  // "furniture", and one bucket would print a subtotal the construction total does not
  // contain and then divide it by that total.
  const mixed = groupRows(
    [...rows, { ...rows.find((r) => r.key === "sofa")!, key: "cabinet", section: "placeables",
      inTotal: true }],
    "trade", "cost", ESTIMATE.total);
  const furnitureGroups = mixed.filter((g) => g.label === "furniture");
  assert(furnitureGroups.length === 2, "One trade, two buckets: in the total and beside it");
  assert(furnitureGroups.some((g) => g.inTotal) && furnitureGroups.some((g) => !g.inTotal),
    "…and each says which it is");
  assert(mixed[mixed.length - 1].inTotal === false, "The excluded bucket is still last");
  assert(furnitureGroups.find((g) => !g.inTotal)!.share === 0,
    "An excluded bucket has no share of a total it is not part of");

  const untraded = groupRows(
    [{ ...slab, trade: undefined }], "trade", "cost", ESTIMATE.total);
  assert(untraded[0].label === "unfiled" && untraded[0].rows.length === 1,
    "A row with no trade code is filed, never dropped — dropping it understates the trade");

  // --- the marks ---------------------------------------------------------------------------

  assert(maxHigh(rows) === 55_000, "The bars share the widest high end as their denominator");
  const bar = barWidths(slab, 55_000);
  assert(Math.abs(bar.left - (3_640 / 55_000) * 100) < 1e-9,
    "The bar starts at the low end: magnitude is position");
  assert(Math.abs(bar.width - (1_092 / 55_000) * 100) < 1e-9,
    "…and its width is the uncertainty");
  assert(barWidths(footing, 55_000).width === 0.6,
    "An exact row keeps a hairline — a zero-width bar reads as missing, not as certain");
  assert(barWidths(slab, 0).width === 0, "No denominator draws no bar rather than dividing by 0");
  assert(Math.abs(shareOfTotal(slab, ESTIMATE.total) - 4_186 / 46_386) < 1e-9,
    "A row's share is its midpoint over the construction total's");
  assert(shareOfTotal(slab, null) === 0, "…and 0 when there is no total");

  // --- basis and ladder --------------------------------------------------------------------

  const slices = basisSlices(ESTIMATE);
  assert(slices.map((s) => s.key).join(",") === "material,labour,merged",
    "Basis reads material, labour, merged — in that order");
  assert(slices[2].merged && slices[2].label.includes("split unknown"),
    "Merged is labelled for what it is: installed, with no split anyone can second-guess");
  assert(Math.abs(slices.reduce((a, s) => a + s.share, 0) - 1) < 1e-9,
    "The three shares are one bar");
  assert(basisSlices(null).length === 0, "No bid block renders no basis bar");

  const ladder = ladderStages(ESTIMATE);
  assert(ladder.length === 8, "All eight rungs, in payload order");
  const overhead = ladder.find((s) => s.key === "overhead")!;
  assert(overhead.off && overhead.rate === "0%",
    "A zero markup stage stays on the page, marked off — hiding it would report an "
    + "owner-build number as a bid");
  assert(ladder.find((s) => s.key === "contingency")!.rate === "10%",
    "A rate prints as a percentage, not as 0.1");
  assert(ladder.find((s) => s.key === "tax")!.rate === "8.53%", "…to the authored precision");
  assert(ladder.find((s) => s.key === "total")!.emphasis, "The total is a rung you can add to");
  assert(ladder.find((s) => s.key === "waste")!.emphasis === false, "…a stage is not");

  // --- subtitle ----------------------------------------------------------------------------

  const subtitle = estimateSubtitle(ESTIMATE, "catlin");
  assert(subtitle.startsWith("catlin · $33,772.50 – $69,073.70"),
    "The subtitle leads with the bid total — what the estimate actually says");
  assert(subtitle.includes("$6–$11/gsf"), "…per gross square foot");
  assert(subtitle.includes("1 unpriced"), "…and confesses what it could not price");
  assert(estimateSubtitle(null).includes("no prices.toml"),
    "No price file reads as a fact, not as a $0 estimate");

  console.log("Engine estimate presentation tests passed.");
}
