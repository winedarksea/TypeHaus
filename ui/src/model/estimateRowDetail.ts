// What one estimate row is actually made of — the fields the ranked table has no room for.
//
// The Estimate table answers "what moves the number". This answers the next question, the one
// an estimator asks of a single line: how is it split, what waste is in it, has tax already
// been paid on it, and which account does it book to. Every fact here was already in the
// `/costs` payload and rendered nowhere; `haus takeoff --csv` has carried all of them since
// the cost-code pass, so until this module the spreadsheet was a strictly better breakdown
// than the page.
//
// Pure and flat by design (the sibling of engineEstimate.ts): a list of labelled facts the
// component renders without deciding anything, so the decisions are testable without a DOM.

import type { EngineEstimateRow, EngineEstimateSection, EnginePriceRange } from "../engine/EngineClient";
import { formatRange } from "./engineCosts";

/** One labelled fact about a row. `note` is the muted second line, when it needs one. */
export interface DetailFact {
  key: string;
  label: string;
  text: string;
  note?: string;
  /** True for the three basis figures, which the panel prints as one proportional group. */
  basisPart?: boolean;
  /** A fact the reader should not skim past: an unusual treatment, not a routine number. */
  flag?: boolean;
}

const BASIS_LABELS: Record<string, string> = {
  material: "material only", labour: "labour only", installed: "installed",
};

function isZero(range: EnginePriceRange | undefined): boolean {
  return !range || (range.low === 0 && range.high === 0);
}

/** Money, or an em dash — a zero bucket is "none of this row", not "$0.00". */
function money(range: EnginePriceRange | undefined): string {
  return isZero(range) ? "—" : formatRange(range) ?? "—";
}

/** `1,234.5 LF`, matching the table's own quantity cell. */
function quantity(value: number, unit: string): string {
  return `${value.toLocaleString()} ${unit}`;
}

/**
 * How this row's cost splits, and why it may not split at all.
 *
 * A `merged` figure is an installed price whose material/labour split nobody declared. The
 * engine never divides one (`takeoff/cost_model.py`), and neither does this: it is reported
 * whole, flagged, so a reader who sees "—" against material understands it as undeclared
 * rather than as zero material.
 */
function basisFacts(row: EngineEstimateRow, section?: EngineEstimateSection): DetailFact[] {
  const merged = !isZero(row.merged);
  const basis = row.basis ?? "material";
  return [
    {
      key: "basis",
      label: "Basis",
      text: merged ? `${BASIS_LABELS[basis] ?? basis} · split undeclared`
        : BASIS_LABELS[basis] ?? basis,
      note: section?.basis_note ?? undefined,
      flag: merged,
    },
    { key: "material", label: "Material", text: money(row.material), basisPart: true },
    { key: "labour", label: "Labour", text: money(row.labour), basisPart: true },
    {
      key: "merged", label: "Merged", text: money(row.merged), basisPart: true,
      note: merged ? "installed price, reported whole and never divided" : undefined,
    },
  ];
}

/**
 * The waste fact — and the one genuinely surprising thing on this page.
 *
 * Four sections (framing, sheet_goods, floor_finishes, wood_surfaces) carry their waste
 * INSIDE the BOM quantity rather than as a bid-ladder stage, because a finish is bought with
 * its waste and pricing the net area would under-cost every plank room. Their rows therefore
 * show `order_quantity === quantity` and contribute nothing to the ladder's waste rung — a
 * materially different treatment from every other section, and one no number on the page
 * announced before now.
 */
function wasteFact(row: EngineEstimateRow): DetailFact {
  const pct = row.waste_pct ?? 0;
  const ordered = row.order_quantity;
  if (row.waste_in_quantity) {
    return {
      key: "waste",
      label: "Waste",
      text: pct ? `${Number((pct * 100).toFixed(2))}% — already in the quantity`
        : "already in the quantity",
      note: "this section is bought with its waste, so the bid ladder's waste rung skips it",
      flag: true,
    };
  }
  if (!pct) return { key: "waste", label: "Waste", text: "none" };
  return {
    key: "waste",
    label: "Waste",
    text: `${Number((pct * 100).toFixed(2))}%`,
    note: ordered !== undefined && ordered !== row.quantity
      ? `${quantity(row.quantity, row.unit)} net → ${quantity(ordered, row.unit)} ordered`
      : undefined,
  };
}

/** NAHB account and CSI division, the two codes an estimating package imports on. */
function codeFact(row: EngineEstimateRow): DetailFact | null {
  const parts = [
    row.nahb_code ? `NAHB ${row.nahb_code}` : null,
    row.csi_code ? `CSI ${row.csi_code}` : null,
  ].filter(Boolean);
  if (!parts.length) return null;
  return { key: "codes", label: "Cost codes", text: parts.join(" · ") };
}

/**
 * Every fact about one row, in reading order.
 *
 * `section` is the row's own block from the payload, which is where the basis note and the
 * waste treatment live — the row cannot answer for either on its own.
 */
export function rowDetailFacts(
  row: EngineEstimateRow,
  section?: EngineEstimateSection,
): DetailFact[] {
  const facts: DetailFact[] = [...basisFacts(row, section), wasteFact(row)];
  if (row.tax_included) {
    facts.push({
      key: "tax",
      label: "Sales tax",
      text: "already in the authored price",
      note: "the bid ladder's tax stage skips this row rather than charging it twice",
      flag: true,
    });
  }
  const codes = codeFact(row);
  if (codes) facts.push(codes);
  return facts;
}

/**
 * How the three basis buckets divide this row, for the panel's proportional bar.
 *
 * Shares are of the row's own midpoint, not of the estimate — the bar answers "how is THIS
 * line split", which is the only question a row-level bar can honestly answer.
 */
export function rowBasisShares(row: EngineEstimateRow): { key: string; share: number }[] {
  const mid = (range: EnginePriceRange | undefined) =>
    range ? (range.low + range.high) / 2 : 0;
  const parts = [
    { key: "material", value: mid(row.material) },
    { key: "labour", value: mid(row.labour) },
    { key: "merged", value: mid(row.merged) },
  ];
  const denominator = parts.reduce((acc, part) => acc + part.value, 0);
  if (!denominator) return [];
  return parts
    .filter((part) => part.value > 0)
    .map((part) => ({ key: part.key, share: part.value / denominator }));
}
