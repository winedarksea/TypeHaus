// The Estimate page's sorting and grouping — pure, no DOM. Split out of engineEstimate.ts
// when grouping grew a second level (trade → category). One sort key governs every level:
// sorting by cost puts the biggest trade first, its biggest category first, and its biggest
// row first.

import type { EnginePriceRange } from "../engine/EngineClient";
import vocabulary from "../generated/vocabulary.json";
import { ALL_TRADES } from "../state/vocabulary";
import { TRADE_GROUP_OF, TRADE_GROUPS, TRADE_LABEL } from "./tradeVisibility";
import { displayName, sumRanges, type EstimateRow } from "./engineEstimate";

// --- sorting ------------------------------------------------------------------------------

export type SortKey = "cost" | "spread" | "quantity" | "key";

/**
 * One sort, as data: a label, the measure it reads off a row, and the measure it reads off a
 * group. `groupValue` for "quantity" is the row count: quantities across a group are in
 * mixed units, and their sum would mean nothing.
 */
export interface SortSpec {
  key: SortKey;
  label: string;
  rowValue: (row: EstimateRow) => number | string;
  groupValue: (group: EstimateGroup) => number | string;
  /** True for the measures that read best largest-first. */
  descending: boolean;
}

export const SORTS: Record<SortKey, SortSpec> = {
  // The midpoint of low/high: prices.toml authors a range, not a point estimate.
  cost: {
    key: "cost", label: "Expected", descending: true,
    rowValue: (row) => row.mid,
    groupValue: (group) => group.mid,
  },
  // Absolute dollars, not spreadPct: ±$30k on a $60k row matters before 2× on a $400 one.
  spread: {
    key: "spread", label: "Uncertainty", descending: true,
    rowValue: (row) => row.spread,
    groupValue: (group) => group.spread,
  },
  quantity: {
    key: "quantity", label: "Quantity", descending: true,
    rowValue: (row) => row.quantity,
    groupValue: (group) => group.rows.length,
  },
  // Rows by the name shown; groups by the grouping's own order (construction sequence).
  key: {
    key: "key", label: "Name", descending: false,
    rowValue: (row) => displayName(row).toLowerCase(),
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

export type GroupKey = "trade" | "group" | "level" | "section" | "none";
type Axis = "trade" | "category" | "group" | "level" | "section" | "none";

/** Outer axis → inner axis. Section and Ranked are one level. */
const INNER: Record<GroupKey, Axis | null> = {
  trade: "category", group: "trade", level: "trade", section: null, none: null,
};

const GROUP_LABELS: Record<GroupKey, string> = {
  trade: "Trade", group: "Package", level: "Level", section: "Section", none: "Ranked",
};

export const GROUP_KEYS: GroupKey[] = ["trade", "group", "level", "section", "none"];
export const GROUPS = GROUP_KEYS.map((key) => ({ key, label: GROUP_LABELS[key] }));

export const BUILDING_LEVEL = "building";

const CATEGORIES = vocabulary.costCategories as { id: string; label: string }[];
const CATEGORY_ORDER = CATEGORIES.map((c) => c.id);
const CATEGORY_LABEL = new Map(CATEGORIES.map((c) => [c.id, c.label]));
const PACKAGE_ORDER = TRADE_GROUPS.map((group) => group.label);

/** What a trade prints; an unfiled row keeps its raw token. */
export function tradeLabel(trade: string | null | undefined): string {
  if (!trade) return "unfiled";
  return (TRADE_LABEL as Record<string, string>)[trade] ?? trade;
}

/** A category token's label; a section name or house override prints de-underscored. */
export function categoryLabel(token: string | null | undefined): string {
  if (!token) return "Uncategorised";
  const label = CATEGORY_LABEL.get(token) ?? token.replace(/_/g, " ");
  return label.charAt(0).toUpperCase() + label.slice(1);
}

/** Level keys in model order with their labels, for the Level grouping. */
export interface LevelInfo { key: string; label: string }

/** The grouping's raw id for a row, before any label. */
function axisValue(row: EstimateRow, axis: Axis): string {
  switch (axis) {
    case "section": return row.section;
    case "category": return row.category || row.section;
    case "level": return row.level || BUILDING_LEVEL;
    case "group": {
      const id = row.trade ? (TRADE_GROUP_OF as Record<string, string>)[row.trade] : undefined;
      return TRADE_GROUPS.find((g) => g.id === id)?.label ?? "unfiled";
    }
    // Even ungrouped, excluded rows keep their own trailing block.
    case "none": return row.inTotal ? "All rows" : "Beside the total";
    default: return row.trade || "unfiled";
  }
}

function axisLabel(value: string, axis: Axis, levels: readonly LevelInfo[]): string {
  if (axis === "trade") return tradeLabel(value === "unfiled" ? null : value);
  if (axis === "category") return categoryLabel(value);
  if (axis === "level") {
    if (value === BUILDING_LEVEL) return "Whole building";
    return levels.find((l) => l.key === value)?.label ?? value;
  }
  return value;
}

function axisOrder(value: string, axis: Axis, levels: readonly LevelInfo[]): number {
  const order = axis === "trade" ? ALL_TRADES as readonly string[]
    : axis === "category" ? CATEGORY_ORDER
      : axis === "group" ? PACKAGE_ORDER
        : axis === "level" ? levels.map((l) => l.key) : null;
  const rank = order ? order.indexOf(value) : -1;
  return rank < 0 ? Number.MAX_SAFE_INTEGER : rank;
}

/** A set of rows sharing one value of one axis, and what its header prints. */
export interface EstimateGroup {
  /** Path id (`trade/electrical`, `trade/electrical/lighting`) — the collapse key. */
  id: string;
  label: string;
  /** Position in the axis's own vocabulary — the "Name" sort's group measure. */
  order: number;
  depth: number;
  /** Every row under this group, sorted, children's included. */
  rows: EstimateRow[];
  /** Sub-groups, or null for a leaf whose rows are shown directly. */
  children: EstimateGroup[] | null;
  subtotal: EnginePriceRange;
  mid: number;
  spread: number;
  /** Fraction of the construction total; 0 with no total, or beside it. */
  share: number;
  /** Midpoint dollars of the placeholder (`[allowances]`) rows inside — a readout only. */
  allowance: number;
  inTotal: boolean;
}

function bucket(rows: readonly EstimateRow[], axis: Axis): Map<string, EstimateRow[]> {
  const out = new Map<string, EstimateRow[]>();
  for (const row of rows) {
    // Excluded rows bucket SEPARATELY: a sofa and a cabinet share a trade, not a total.
    const id = row.inTotal ? axisValue(row, axis) : `excluded:${axisValue(row, axis)}`;
    const list = out.get(id);
    if (list) list.push(row);
    else out.set(id, [row]);
  }
  return out;
}

function build(
  rows: readonly EstimateRow[], axes: readonly Axis[], parent: string, depth: number,
  spec: SortSpec, totalMid: number, levels: readonly LevelInfo[],
): EstimateGroup[] {
  const [axis, ...rest] = axes;
  const groups = [...bucket(rows, axis).entries()].map(([id, members]): EstimateGroup => {
    const value = axisValue(members[0], axis);
    const subtotal = sumRanges(members.map((row) => row.cost));
    const mid = (subtotal.low + subtotal.high) / 2;
    const path = `${parent}/${id}`;
    const inTotal = members[0].inTotal;
    return {
      id: path,
      label: axisLabel(value, axis, levels),
      order: axisOrder(value, axis, levels),
      depth,
      rows: [...members].sort((a, b) =>
        compare(spec.rowValue(a), spec.rowValue(b), spec.descending) || a.key.localeCompare(b.key)),
      children: rest.length ? build(members, rest, path, depth + 1, spec, totalMid, levels) : null,
      subtotal,
      mid,
      spread: subtotal.high - subtotal.low,
      share: totalMid && inTotal ? mid / totalMid : 0,
      allowance: members.filter((row) => row.section === "allowances")
        .reduce((acc, row) => acc + row.mid, 0),
      inTotal,
    };
  });
  // Excluded last whatever the sort; "Whole building" last among the levels in the total.
  const tail = (g: EstimateGroup) =>
    (g.inTotal ? 0 : 2) + (axis === "level" && g.id.endsWith(`/${BUILDING_LEVEL}`) ? 1 : 0);
  return groups.sort((a, b) => tail(a) - tail(b)
    || compare(spec.groupValue(a), spec.groupValue(b), spec.descending)
    || a.label.localeCompare(b.label));
}

/** Rank `rows` into the grouping's tree, every level by the same sort. */
export function groupTree(
  rows: readonly EstimateRow[],
  outer: GroupKey,
  sort: SortKey,
  total?: EnginePriceRange | null,
  levels: readonly LevelInfo[] = [],
): EstimateGroup[] {
  const inner = INNER[outer];
  const axes: Axis[] = inner ? [outer, inner] : [outer];
  const totalMid = total ? (total.low + total.high) / 2 : 0;
  return build(rows, axes, outer, 0, SORTS[sort], totalMid, levels);
}

/** Every group id in the tree, depth-first. */
export function allGroupIds(groups: readonly EstimateGroup[]): string[] {
  return groups.flatMap((g) => [g.id, ...allGroupIds(g.children ?? [])]);
}

/**
 * The groups that start COLLAPSED: every leaf group, so the page opens on the trades and
 * their categories rather than on 1,500 rows. "Ranked" never collapses (its one group IS
 * the table), and an active filter expands everything, or a filter with matches would look
 * exactly like one with none.
 */
export function defaultCollapsed(
  groups: readonly EstimateGroup[], outer: GroupKey, filtered = false,
): Set<string> {
  if (outer === "none" || filtered) return new Set();
  const leaves = (list: readonly EstimateGroup[]): string[] =>
    list.flatMap((g) => (g.children ? leaves(g.children) : [g.id]));
  return new Set(leaves(groups));
}

/** Running share of the construction total down a ranked list, as fractions. */
export function cumulativeShares(
  rows: readonly EstimateRow[], total: EnginePriceRange | null | undefined,
): number[] {
  const denominator = total ? (total.low + total.high) / 2 : 0;
  let running = 0;
  return rows.map((row) => {
    running += row.mid;
    return denominator ? running / denominator : 0;
  });
}
