// Cost decoration (model/engineCosts.ts) — pure logic over the /costs payload. What is
// worth pinning: the join drives which tables grow cost columns (and structural_solids
// joins as "concrete", the one section whose names differ), decoration never reorders or
// drops BOM rows, staleness surfaces rather than disappears, and the subtitle is honest
// about missing prices.

import type { EngineCosts } from "../engine/EngineClient";
import { groupBom } from "./engineBom";
import {
  buildExtraTable,
  costsSubtitle,
  decorateWithCosts,
  formatRange,
  staleEntries,
} from "./engineCosts";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const BOM = {
  framing_by_size: [
    { profile: "2x6", pieces: 412, order_length_ft: 3_296 },
    { profile: "2x10", pieces: 64, order_length_ft: 768 },
  ],
  structural_solids: [
    { category: "slab", count: 3, volume_cubic_yards: 18.2 },
  ],
  drainage: [
    { category: "gutter", product: "aluminum", length_ft: 62.0 },
  ],
};

const COSTS: EngineCosts = {
  prices_loaded: true,
  estimate: {
    sections: {
      framing: {
        rows: [{ key: "2x6", quantity: 3_296, unit: "LF",
          unit_price: { low: 0.95, high: 1.35 },
          cost: { low: 3_131.2, high: 4_449.6 }, cost_fmt: "$3,131.20 – $4,449.60" }],
        subtotal: { low: 3_131.2, high: 4_449.6 }, subtotal_fmt: "",
      },
      concrete: {
        rows: [{ key: "slab", quantity: 18.2, unit: "cy",
          unit_price: { low: 200, high: 200 },
          cost: { low: 3_640, high: 3_640 }, cost_fmt: "$3,640.00" }],
        subtotal: { low: 3_640, high: 3_640 }, subtotal_fmt: "",
      },
    },
    total: { low: 6_771.2, high: 8_089.6 },
    total_fmt: "",
    unpriced: [{ section: "framing", key: "2x10", quantity: 768, unit: "LF" }],
  },
  join: {
    framing: { bom_key: "framing_by_size", key_field: "profile",
      quantity_field: "order_length_ft", unit: "LF" },
    concrete: { bom_key: "structural_solids", key_field: "category",
      quantity_field: "volume_cubic_yards", unit: "cy" },
  },
  entries: {
    framing: {
      "2x6": { paid: true, paid_date: "2026-08-01", product: "Menards SPF #2",
        actual_cost: 3_184.5, note: null },
      "2x97": { paid: true, paid_date: null, product: null, actual_cost: 10, note: null },
    },
  },
  extra: [
    { id: "permit", name: "Building permit", cost: { low: 1_800, high: 2_400 },
      paid: false, product: null, category: "fees", note: null },
  ],
  stale: [{ section: "framing", key: "2x97" }],
  totals: {
    estimate: { low: 6_771.2, high: 8_089.6 },
    extra: { low: 1_800, high: 2_400 },
    combined: { low: 8_571.2, high: 10_489.6 },
    actual_paid: 3_184.5,
    paid_entries: 1,
  },
};

export function runEngineCostsTests() {
  // --- formatRange ------------------------------------------------------------------------

  assert(formatRange({ low: 1234, high: 1234 }) === "$1,234.00",
    "An exact range prints once");
  assert(formatRange({ low: 1200, high: 1500 }) === "$1,200.00 – $1,500.00",
    "A spread prints both ends");
  assert(formatRange(null) === null && formatRange(undefined) === null,
    "Nothing to say prints nothing, never $0.00");

  // --- decoration -------------------------------------------------------------------------

  const groups = decorateWithCosts(groupBom(BOM), COSTS);
  const sections = new Map(groups.flatMap((g) => g.sections.map((s) => [s.key, s])));

  const framing = sections.get("framing_by_size")!;
  assert(framing.costSection === "framing", "framing_by_size joins the framing prices");
  assert(framing.table.columns.includes("paid") && framing.table.columns.includes("product"),
    "A joined table grows the cost columns");
  assert(framing.table.rows.length === 2 && framing.table.rowCosts?.length === 2,
    "Decoration appends columns — it never adds or drops rows");
  const [row26, row210] = framing.table.rowCosts!;
  assert(row26.key === "2x6" && row26.entry?.paid === true
    && row26.estimate?.cost.low === 3_131.2,
    "A row with an entry and an estimate carries both");
  assert(row210.key === "2x10" && row210.entry === null && row210.estimate === null,
    "An unpriced, untracked row still gets its identity — the checkbox needs it");
  const paidIdx = framing.table.columns.indexOf("paid");
  assert(framing.table.rows[0][paidIdx] === true && framing.table.rows[1][paidIdx] === false,
    "The paid cell mirrors the entry");

  // The one join whose names differ: structural_solids prices as "concrete".
  const solids = sections.get("structural_solids")!;
  assert(solids.costSection === "concrete",
    "structural_solids joins the concrete price table");
  assert(solids.table.rowCosts?.[0].estimate?.cost.low === 3_640,
    "…and finds its estimate row by the category key");

  // A section outside the join passes through untouched.
  const drainage = sections.get("drainage")!;
  assert(!("rowCosts" in drainage.table) || drainage.table.rowCosts === undefined,
    "An unjoined section grows nothing");
  assert(!drainage.table.columns.includes("paid"),
    "…not even the paid column");

  // --- stale + extras ---------------------------------------------------------------------

  const stale = staleEntries(COSTS);
  assert(stale.length === 1 && stale[0].key === "2x97" && stale[0].entry?.paid === true,
    "A stale check-off surfaces with its recorded state — never silently dropped");

  const extras = buildExtraTable(COSTS);
  assert(extras.rows.length === 1 && extras.items[0].id === "permit",
    "Extras table carries the item identity for edit/delete wiring");
  assert(extras.rows[0][extras.columns.indexOf("cost")] === "$1,800.00 – $2,400.00",
    "An extra's cost renders as a range");

  // --- subtitle ---------------------------------------------------------------------------

  const subtitle = costsSubtitle(COSTS);
  assert(subtitle.includes("est. $8,571.20 – $10,489.60"),
    "The subtitle totals estimate + extras");
  assert(subtitle.includes("paid $3,184.50"), "…and says what has actually been paid");
  assert(subtitle.includes("1 unpriced"), "…and confesses the unpriced rows");
  const noPrices = costsSubtitle({ ...COSTS, prices_loaded: false, estimate: null,
    totals: { extra: { low: 0, high: 0 } } });
  assert(noPrices.includes("no prices.toml"),
    "No price file reads as a fact, not as a $0 estimate");

  console.log("Engine costs presentation tests passed.");
}
