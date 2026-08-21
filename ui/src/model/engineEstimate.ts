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

// --- sorting ------------------------------------------------------------------------------

export type SortKey = "cost" | "spread" | "quantity" | "key";

/**
 * One sort, as data: a label, the measure it reads off a row, and the measure it reads off a
 * *group*. One key governs both levels — sorting by cost with trade grouping puts the biggest
 * trade first and its biggest row first inside it, and sorting by spread puts the trade
 * nobody is sure about first. Two independent controls would have let the two disagree.
 *
 * `groupValue` for "quantity" is the row count, not a sum: quantities across a group are in
 * mixed units (cubic yards beside each), and adding them would produce a number that means
 * nothing. Counting rows is the honest reading of "most rows by quantity" at group level.
 */
export interface SortSpec {
  key: SortKey;
  label: string;
  /** How rows compare; already oriented (biggest-first for the numeric measures). */
  rowValue: (row: EstimateRow) => number | string;
  groupValue: (group: EstimateGroup) => number | string;
  /** True for the measures that read best largest-first. */
  descending: boolean;
}

export const SORTS: Record<SortKey, SortSpec> = {
  cost: {
    // The measure is the midpoint of low/high — the closest thing the payload carries to a
    // "most likely" figure, since prices.toml authors a range rather than a third point
    // estimate. Labelled "Expected" rather than "Cost" so the sort's own name says what
    // number it orders by, matching the column that now prints that number.
    key: "cost", label: "Expected", descending: true,
    rowValue: (row) => row.mid,
    groupValue: (group) => group.mid,
  },
  spread: {
    key: "spread", label: "Uncertainty", descending: true,
    // Absolute dollars, not spreadPct: a 2× range on a $400 row is not the thing to look at
    // first when a $60k row is ±$30k. The percentage is a column, not the ranking.
    rowValue: (row) => row.spread,
    groupValue: (group) => group.spread,
  },
  quantity: {
    key: "quantity", label: "Quantity", descending: true,
    rowValue: (row) => row.quantity,
    groupValue: (group) => group.rows.length,
  },
  key: {
    key: "key", label: "Name", descending: false,
    rowValue: (row) => row.key,
    // The grouping's own order — construction sequence for trades, alphabetical for
    // sections — rather than the group label, so "Name" reads as the file does.
    groupValue: (group) => group.order,
  },
};

export const SORT_KEYS: SortKey[] = ["cost", "spread", "quantity", "key"];

function compare(a: number | string, b: number | string, descending: boolean): number {
  if (typeof a === "string" || typeof b === "string") {
    return String(a).localeCompare(String(b)) * (descending ? -1 : 1);
  }
  return descending ? b - a : a - b;
}

// --- grouping -----------------------------------------------------------------------------

export type GroupKey = "trade" | "section" | "none";

/**
 * The construction trades in build order (`emit/trades.py::CONSTRUCTION_SEQUENCE`, the same
 * 13-value vocabulary the 3D viewer's visibility toggles use). Copied rather than derived
 * because the browser has no import of the engine's Python; `tests/test_solid_trade_parity.py`
 * is what keeps the two spellings from drifting.
 */
export const TRADE_SEQUENCE: string[] = [
  "earth", "concrete", "drainage", "framing", "floors", "roof", "walls", "openings",
  "plumbing", "electrical", "mechanical", "stairs", "furniture",
];

/** A set of rows that share a trade or a section, with what the header has to print. */
export interface EstimateGroup {
  id: string;
  label: string;
  /** Position in the grouping's own vocabulary — the "Name" sort's group measure. */
  order: number;
  rows: EstimateRow[];
  subtotal: EnginePriceRange;
  mid: number;
  spread: number;
  /** Fraction of the construction total, 0 when there is no total to divide by. */
  share: number;
  /** False when every row here comes from a section reported beside the total. */
  inTotal: boolean;
}

function groupLabelOf(row: EstimateRow, group: GroupKey): string {
  if (group === "section") return row.section;
  // Even ungrouped, the excluded rows keep their own trailing block and say so: a reader
  // scanning a "flat ranked list" from the top must not meet a sofa among the things the
  // construction total is made of.
  if (group === "none") return row.inTotal ? "All rows" : "Beside the total";
  // A row whose section has no cost-code default is filed rather than dropped: an unlabelled
  // row that vanished from a trade view would understate that trade silently.
  return row.trade || "unfiled";
}

/**
 * The bucket a row falls in. Excluded rows bucket SEPARATELY even when they share a label
 * with rows that are in the total — `furnishings` and `placeables` are both trade
 * `furniture`, and one bucket for the two would print a subtotal containing money the
 * construction total does not, then divide it by that total to get a share. A sofa and a
 * kitchen cabinet are the same trade and not the same number.
 */
function bucketKeyOf(row: EstimateRow, group: GroupKey): string {
  const label = groupLabelOf(row, group);
  return row.inTotal ? label : `\u0000excluded:${label}`;
}

const GROUP_LABELS: Record<GroupKey, string> = {
  trade: "Trade", section: "Section", none: "Ranked",
};

export const GROUP_KEYS: GroupKey[] = ["trade", "section", "none"];

/** The grouping vocabulary as data, for the segmented control. */
export const GROUPS = GROUP_KEYS.map((key) => ({ key, label: GROUP_LABELS[key] }));

/**
 * Rank `rows` into groups, both levels by the same sort.
 *
 * Excluded sections (furnishings) group last whatever the sort says: they are not in the
 * construction total, and a reader scanning from the top must not meet a sofa among the
 * things the total is made of.
 */
export function groupRows(
  rows: readonly EstimateRow[],
  group: GroupKey,
  sort: SortKey,
  total?: EnginePriceRange | null,
): EstimateGroup[] {
  const spec = SORTS[sort];
  const order = group === "trade" ? TRADE_SEQUENCE : null;
  const buckets = new Map<string, EstimateRow[]>();
  for (const row of rows) {
    const id = bucketKeyOf(row, group);
    const bucket = buckets.get(id);
    if (bucket) bucket.push(row);
    else buckets.set(id, [row]);
  }
  const totalMid = total ? midOf(total) : 0;
  const labels = [...new Set(rows.map((row) => groupLabelOf(row, group)))].sort();
  const groups: EstimateGroup[] = [...buckets.entries()].map(([id, bucketRows]) => {
    const subtotal = sumRanges(bucketRows.map((row) => row.cost));
    const label = groupLabelOf(bucketRows[0], group);
    const rank = order ? order.indexOf(label) : labels.indexOf(label);
    return {
      id,
      label,
      // An id outside the vocabulary ("unfiled") sorts after every known one rather than
      // to the front, which is where indexOf's -1 would have put it.
      order: rank < 0 ? Number.MAX_SAFE_INTEGER : rank,
      rows: [...bucketRows].sort((a, b) =>
        compare(spec.rowValue(a), spec.rowValue(b), spec.descending)
        || a.key.localeCompare(b.key)),
      subtotal,
      mid: midOf(subtotal),
      spread: subtotal.high - subtotal.low,
      // Only meaningful for a bucket the total contains; an excluded bucket prints "beside
      // the total" instead of a share of a number it is not part of.
      share: totalMid && bucketRows[0].inTotal ? midOf(subtotal) / totalMid : 0,
      inTotal: bucketRows[0].inTotal,
    };
  });
  return groups.sort((a, b) =>
    Number(a.inTotal === false) - Number(b.inTotal === false)
    || compare(spec.groupValue(a), spec.groupValue(b), spec.descending)
    || a.label.localeCompare(b.label));
}

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
