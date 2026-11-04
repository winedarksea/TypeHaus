// The Estimate page's arrangement — pure, no DOM, no fetch (the sibling of engineBom.ts and
// engineCosts.ts). Every number here is the engine's: `cli/prices.estimate_costs` prices the
// BOM against the house's prices.toml and `takeoff/cost_model` runs the bid ladder, both
// served whole on `GET /costs`. Nothing in this file prices anything — it flattens, ranks,
// groups, and derives the two or three proportions a bar needs.
//
// Why it exists: the payload is eighteen fields per row across ~440 rows in a dozen sections,
// and the only question a reader actually asks of it is "what moves the number, and how sure
// are we?". That is a ranking problem, and a ranking is exactly the kind of decision that
// belongs in a tested module rather than inside a component.

import type {
  EngineBidStage,
  EngineEstimate,
  EngineEstimateRow,
  EnginePerSf,
  EnginePriceRange,
} from "../engine/EngineClient";
import { formatRange } from "./engineCosts";

/** One priced row, lifted out of its section and told what it is worth relative to itself. */
export interface EstimateRow extends EngineEstimateRow {
  /** The prices.toml block this row was authored in — the block to open to change it. */
  section: string;
  /** False for a section reported beside the construction total (furnishings). */
  inTotal: boolean;
  /** Midpoint of the cost range: the single number a ranking has to use. */
  mid: number;
  /** high − low, in dollars. How much of this row is still unknown. */
  spread: number;
  /** `spread / mid`, or 0 for a row priced exactly. Comparable across magnitudes. */
  spreadPct: number;
}

const ZERO: EnginePriceRange = { low: 0, high: 0 };

function midOf(range: EnginePriceRange): number {
  return (range.low + range.high) / 2;
}

/** Every priced row in the estimate as one array, each carrying its section and spread. */
export function flattenEstimate(estimate: EngineEstimate | null | undefined): EstimateRow[] {
  if (!estimate) return [];
  const rows: EstimateRow[] = [];
  for (const [section, body] of Object.entries(estimate.sections)) {
    const inTotal = body.in_total !== false;
    for (const row of body.rows) {
      const mid = midOf(row.cost);
      const spread = row.cost.high - row.cost.low;
      rows.push({ ...row, section, inTotal, mid, spread, spreadPct: mid ? spread / mid : 0 });
    }
  }
  return rows;
}

/** Sum a set of ranges. Low with low and high with high — never a midpoint of midpoints. */
export function sumRanges(ranges: readonly EnginePriceRange[]): EnginePriceRange {
  return ranges.reduce(
    (acc, r) => ({ low: acc.low + r.low, high: acc.high + r.high }),
    { ...ZERO },
  );
}

// Sorting and grouping live in estimateGroups.ts.

// --- the numbers a mark needs -------------------------------------------------------------

/** This row's share of the construction total, as a fraction. 0 when there is no total. */
export function shareOfTotal(
  row: { mid: number },
  total: EnginePriceRange | null | undefined,
): number {
  const denominator = total ? midOf(total) : 0;
  return denominator ? row.mid / denominator : 0;
}

/**
 * Where the range bar starts and how wide it is, in percent of the widest row's high end.
 *
 * Magnitude is the bar's position, uncertainty is its width — one mark that answers both of
 * the sorts this page offers. A row priced exactly still gets a hairline of width, because a
 * zero-width bar reads as missing data rather than as certainty.
 */
export function barWidths(
  row: { cost: EnginePriceRange },
  maxHigh: number,
): { left: number; width: number } {
  if (!maxHigh) return { left: 0, width: 0 };
  const left = Math.max(0, Math.min(100, (row.cost.low / maxHigh) * 100));
  const width = Math.max(0.6, Math.min(100 - left, ((row.cost.high - row.cost.low) / maxHigh) * 100));
  return { left, width };
}

/**
 * The row's description, or null when it only repeats what the key already says.
 *
 * `_describe` in cli/prices.py falls back to the key itself for a row with no BOM record
 * behind it (every allowance), and a QUALIFIED key already carries its qualifier
 * ("slab:CATLIN_DECK_9_INT" beside a description of "CATLIN_DECK_9_INT"). Printed under the
 * key, both read as a stutter rather than as a second fact.
 */
export function rowDescription(row: EngineEstimateRow): string | null {
  const description = row.description?.trim();
  if (!description) return null;
  if (description === row.key) return null;
  if (row.key.endsWith(`:${description}`)) return null;
  return description;
}

/**
 * What the Item column prints: the specified product, else the description without the
 * `" (key)"` that `cli/prices._describe` appends, else the key itself.
 */
export function displayName(row: EngineEstimateRow): string {
  if (row.product?.trim()) return row.product.trim();
  const description = rowDescription(row);
  if (!description) return row.key;
  const suffix = ` (${row.key})`;
  return description.endsWith(suffix) ? description.slice(0, -suffix.length) : description;
}

/** The widest high end across the rows on screen — the range bars' shared denominator. */
export function maxHigh(rows: readonly EstimateRow[]): number {
  return rows.reduce((acc, row) => Math.max(acc, row.cost.high), 0);
}

// --- the summary blocks --------------------------------------------------------------------

/** "$163 – $343 / gsf", or null when the payload carries no denominator of that name. */
export function formatPerSf(per: EnginePerSf | undefined, name: string,
                            suffix: string): string | null {
  const value = per?.[name];
  if (!value) return null;
  const dollars = (v: number) => `$${Math.round(v).toLocaleString()}`;
  const range = Math.abs(value.high - value.low) < 0.005
    ? dollars(value.low) : `${dollars(value.low)}–${dollars(value.high)}`;
  return `${range}/${suffix}`;
}

/** ReaderShell's subtitle: what the total is, per square foot, and what it leaves out. */
export function estimateSubtitle(
  estimate: EngineEstimate | null | undefined,
  houseName?: string | null,
): string {
  if (!estimate) return "no prices.toml — nothing to estimate";
  const parts: string[] = [];
  if (houseName) parts.push(houseName);
  const bid = estimate.bid;
  parts.push(formatRange(bid ? bid.total : estimate.total) ?? "—");
  const perSf = formatPerSf(estimate.per_sf?.bid_total ?? estimate.per_sf?.total,
                            "gross", "gsf");
  if (perSf) parts.push(perSf);
  const unpriced = estimate.unpriced.length;
  if (unpriced) parts.push(`${unpriced} unpriced`);
  return parts.join(" · ");
}

/** The three basis buckets of the construction total, with what each is worth as a share. */
export interface BasisSlice {
  key: string;
  label: string;
  value: EnginePriceRange;
  share: number;
  /** True for `merged`: installed prices with no declared split, which are never divided. */
  merged: boolean;
}

const BASIS_LABELS: Record<string, string> = {
  material: "Material", labour: "Labour", merged: "Installed, split unknown",
};

/** material / labour / merged from `bid.net`, proportioned for one stacked bar. */
export function basisSlices(estimate: EngineEstimate | null | undefined): BasisSlice[] {
  const net = estimate?.bid?.net;
  if (!net) return [];
  // Only the three bucket names, by name: `bid.net` also carries a parallel `fmt` map of
  // the same three as strings, and iterating the object would put it on the bar.
  const slices = ["material", "labour", "merged"]
    .map((key) => ({ key, value: net[key] as EnginePriceRange | undefined }))
    .filter((slice): slice is { key: string; value: EnginePriceRange } =>
      !!slice.value && typeof slice.value.low === "number")
    .map(({ key, value }) => ({
      key,
      label: BASIS_LABELS[key] ?? key,
      value,
      share: 0,
      merged: key === "merged",
    }));
  const denominator = slices.reduce((acc, slice) => acc + midOf(slice.value), 0);
  return slices.map((slice) => ({
    ...slice,
    share: denominator ? midOf(slice.value) / denominator : 0,
  }));
}

const STAGE_LABELS: Record<string, string> = {
  subtotal_net: "Net subtotal",
  waste: "Waste",
  subtotal_ordered: "Ordered subtotal",
  contingency: "Contingency",
  overhead: "Overhead",
  profit: "Profit",
  tax: "Sales tax",
  total: "Bid total",
};

/** One rung of the ladder, ready to render. */
export interface LadderStage {
  key: string;
  label: string;
  value: EnginePriceRange;
  fmt: string;
  /** "10%" where the stage is a rate on something, else null. */
  rate: string | null;
  /** A deliberate zero — rendered muted with an "off" chip, never hidden. */
  off: boolean;
  /** The two subtotals and the total: the rungs you can add the others up to. */
  emphasis: boolean;
}

/**
 * The bid ladder, every stage, in order.
 *
 * A stage at zero stays on the page. `overhead` and `profit` being zero is the single most
 * important thing this estimate does *not* include — a builder's markup on a construction
 * total this size is six figures — and a page that hid an empty rung would be quietly
 * reporting an owner-build number as if it were a bid.
 */
export function ladderStages(estimate: EngineEstimate | null | undefined): LadderStage[] {
  const stages: EngineBidStage[] = estimate?.bid?.stages ?? [];
  return stages.map((stage) => ({
    key: stage.label,
    label: STAGE_LABELS[stage.label] ?? stage.label,
    value: { low: stage.low, high: stage.high },
    fmt: stage.fmt,
    rate: stage.rate === undefined ? null
      : `${Number((stage.rate * 100).toFixed(2))}%`,
    off: stage.high === 0 && stage.low === 0,
    emphasis: stage.label === "total" || stage.label.startsWith("subtotal"),
  }));
}
