// Row detail (model/estimateRowDetail.ts) — the per-row facts the ranked table has no room
// for. What is worth pinning: a merged row reports its split as undeclared rather than as
// zero material, waste-in-quantity announces itself as a different treatment (it contributes
// nothing to the ladder's waste rung, which is invisible everywhere else), a tax-inclusive
// row says the tax stage skipped it, and the basis bar divides the ROW, never the estimate.

import type { EngineEstimateRow, EngineEstimateSection } from "../engine/EngineClient";
import { rowBasisShares, rowDetailFacts } from "./estimateRowDetail";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function factOf(facts: ReturnType<typeof rowDetailFacts>, key: string) {
  const fact = facts.find((f) => f.key === key);
  assert(fact, `expected a "${key}" fact`);
  return fact;
}

const SPLIT_ROW: EngineEstimateRow = {
  key: "2x6", quantity: 427, unit: "LF", unit_price: { low: 0.95, high: 1.35 },
  cost: { low: 405.65, high: 576.45 }, cost_fmt: "", basis: "material",
  material: { low: 405.65, high: 576.45 }, labour: { low: 0, high: 0 },
  merged: { low: 0, high: 0 }, waste_pct: 0.05, order_quantity: 427,
  waste_in_quantity: true, nahb_code: "1300", csi_code: "06 10 00", trade: "framing",
};

const MERGED_ROW: EngineEstimateRow = {
  key: "slab", quantity: 18.2, unit: "cy", unit_price: { low: 400, high: 700 },
  cost: { low: 7_280, high: 12_740 }, cost_fmt: "", basis: "installed",
  material: { low: 0, high: 0 }, labour: { low: 0, high: 0 },
  merged: { low: 7_280, high: 12_740 }, waste_pct: 0.04, order_quantity: 18.93,
  waste_in_quantity: false, tax_included: false, nahb_code: "1200", trade: "concrete",
};

const CONCRETE: EngineEstimateSection = {
  rows: [], subtotal: { low: 0, high: 0 }, subtotal_fmt: "", basis: "installed",
  basis_note: "$/cy PLACED and MERGED — never divided into a guessed split",
};

export function runEstimateRowDetailTests(): void {
  // --- the merged row: undeclared, not zero -------------------------------------------------

  const merged = rowDetailFacts(MERGED_ROW, CONCRETE);
  assert(factOf(merged, "basis").text === "installed · split undeclared",
    "A merged row says its split is undeclared, not that it has one");
  assert(factOf(merged, "basis").flag === true,
    "…and flags it, because an undeclared split is not a routine number");
  assert(factOf(merged, "basis").note === CONCRETE.basis_note,
    "The section's own basis note rides along — the row cannot answer for it");
  assert(factOf(merged, "material").text === "—",
    "Material reads as an em dash: none of this row is DECLARED material, not $0.00 of it");
  assert(factOf(merged, "merged").text.startsWith("$7,280.00"),
    "…and the whole cost is reported in the merged bucket");
  assert(factOf(merged, "merged").note?.includes("never divided"),
    "…saying why it is not split");

  // --- waste, and the treatment that differs -----------------------------------------------

  const mergedWaste = factOf(merged, "waste");
  assert(mergedWaste.text === "4%", "An ordinary waste rate prints as a percentage");
  assert(mergedWaste.note === "18.2 cy net → 18.93 cy ordered",
    "…with the net→ordered quantities it produces");
  assert(!mergedWaste.flag, "…and is not flagged: it is the normal treatment");

  const inQuantity = factOf(rowDetailFacts(SPLIT_ROW), "waste");
  assert(inQuantity.text === "5% — already in the quantity",
    "A waste-in-quantity row says so on its face");
  assert(inQuantity.flag === true && inQuantity.note?.includes("bid ladder"),
    "…and is flagged, because the ladder's waste rung skips it — invisible everywhere else");

  // --- tax ---------------------------------------------------------------------------------

  assert(!merged.some((f) => f.key === "tax"),
    "A row taxed normally says nothing: the ladder already reports the tax stage");
  const taxed = rowDetailFacts({ ...MERGED_ROW, tax_included: true });
  assert(factOf(taxed, "tax").flag === true,
    "A row whose authored price already carries tax is flagged — the stage skipped it");

  // --- codes -------------------------------------------------------------------------------

  assert(factOf(merged, "codes").text === "NAHB 1200",
    "A row with only a NAHB account prints only that");
  assert(factOf(rowDetailFacts(SPLIT_ROW), "codes").text === "NAHB 1300 · CSI 06 10 00",
    "…and both codes when both apply — the two an estimating package imports on");
  assert(!rowDetailFacts({ ...MERGED_ROW, nahb_code: undefined }).some((f) => f.key === "codes"),
    "No codes, no row: an empty 'Cost codes —' line is noise");

  // --- the basis bar divides the ROW -------------------------------------------------------

  const shares = rowBasisShares(MERGED_ROW);
  assert(shares.length === 1 && shares[0].key === "merged" && shares[0].share === 1,
    "A wholly merged row is one full-width merged bar, not a third of one");
  const split = rowBasisShares({
    ...MERGED_ROW,
    material: { low: 300, high: 300 }, labour: { low: 100, high: 100 },
    merged: { low: 0, high: 0 },
  });
  assert(split.length === 2 && Math.abs(split[0].share - 0.75) < 1e-9,
    "A declared split divides by the row's own midpoint, never by the estimate's");
  assert(rowBasisShares({ ...MERGED_ROW, merged: { low: 0, high: 0 } }).length === 0,
    "A row with no basis figures at all yields no bar rather than a divide-by-zero");

  console.log("Estimate row detail tests passed.");
}
