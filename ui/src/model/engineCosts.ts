// Cost decoration for the engine BOM view — pure arrangement, no DOM, no fetch (the twin
// of engineBom.ts). The engine owns every number: the estimate comes from prices.toml via
// `estimate_costs`, the check-off state from costs.toml via `costs_payload`, and the
// (section, key) join is served in the payload (`join`, authored once in ESTIMATE_PLANS) so
// nothing here re-guesses which column identifies a row.

import type {
  EngineCostEntry,
  EngineCosts,
  EngineEstimateRow,
  EnginePriceRange,
  EngineExtraItem,
} from "../engine/EngineClient";
import type { BomGroup, BomSection, BomTable } from "./engineBom";

/** "$1,234.00" or "$1,200.00 – $1,500.00"; null when there is nothing to say. */
export function formatRange(range: EnginePriceRange | null | undefined): string | null {
  if (!range) return null;
  const dollars = (v: number) =>
    `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (Math.abs(range.high - range.low) < 1e-9) return dollars(range.low);
  return `${dollars(range.low)} – ${dollars(range.high)}`;
}

/** Separates a price key from its trade in a costs.toml entry key (→ takeoff/costs.py). */
export const TRADE_SEPARATOR = "@";

/** The costs.toml key for (key, trade): bare unless a second trade bills the same key. */
export function entryKey(key: string, trade?: string | null): string {
  return trade ? `${key}${TRADE_SEPARATOR}${trade}` : key;
}

// Per-row cost identity: which costs (section, key) a BOM table row joins, plus what is
// known about it. `key` is null on rows whose key cell was empty — nothing to check off.
// A key two trades bill becomes one row per trade: `trade` names it and `entryKey` is the
// "key@trade" every read and write of its entry uses; otherwise `entryKey === key`.
export interface RowCost {
  section: string;
  key: string | null;
  trade: string | null;
  entryKey: string | null;
  entry: EngineCostEntry | null;
  estimate: EngineEstimateRow | null;
}

export interface CostedTable extends BomTable {
  // Parallel to `rows`; present only on tables that join a costs section.
  readonly rowCosts?: readonly RowCost[];
}
export interface CostedSection extends BomSection {
  readonly table: CostedTable;
  // The costs section this BOM section joins (e.g. structural_solids → "concrete").
  readonly costSection?: string;
}
export interface CostedGroup extends Omit<BomGroup, "sections"> {
  readonly sections: readonly CostedSection[];
}

// The cost columns appended to a joined table, in reading order. Values are display
// strings/booleans so BomView's formatCell renders them; the interactive cells (paid,
// product) are re-rendered from `rowCosts` by the view.
export const COST_COLUMNS = ["trade", "unit_price", "est_cost", "actual_cost", "product",
  "paid"] as const;

/** One trade's estimate rows under a key as a single row: quantity and cost summed. */
function mergeRows(rows: readonly EngineEstimateRow[]): EngineEstimateRow {
  if (rows.length === 1) return rows[0];
  const cost = {
    low: rows.reduce((n, r) => n + r.cost.low, 0),
    high: rows.reduce((n, r) => n + r.cost.high, 0),
  };
  return { ...rows[0], quantity: rows.reduce((n, r) => n + r.quantity, 0), cost,
    cost_fmt: formatRange(cost) ?? "" };
}

/**
 * Decorate `groupBom(bom)`'s output with cost columns wherever the payload's join says a
 * section's rows are priceable. Tables that join no costs section pass through untouched —
 * decoration must never change what the BOM says, only append what is known about paying
 * for it.
 */
export function decorateWithCosts(groups: BomGroup[], costs: EngineCosts): CostedGroup[] {
  // bom_key → costs sections. Mostly one apiece and identically named (structural_solids
  // → "concrete"), but a BOM table can feed two: `placeables` feeds both "placeables" and
  // "furnishings". Keeping only the last one written would blank the cost columns for
  // every row priced in the other, so the whole list is kept and rows resolve per key.
  const sectionsByBomKey = new Map<string, string[]>();
  for (const [section, join] of Object.entries(costs.join)) {
    const seen = sectionsByBomKey.get(join.bom_key);
    if (seen) seen.push(section);
    else sectionsByBomKey.set(join.bom_key, [section]);
  }
  return groups.map((group) => ({
    ...group,
    sections: group.sections.map((section): CostedSection => {
      const costSections = sectionsByBomKey.get(section.key);
      if (!costSections || section.table.kind !== "rows") return section;
      // Sections sharing a bom_key share its key field; the first is the section a row
      // falls back to when nothing priced or checked it off.
      const costSection = costSections[0];
      const keyField = costs.join[costSection].key_field;
      const keyIndex = section.table.columns.indexOf(keyField);
      if (keyIndex < 0) return section;
      const estimateRows = new Map<string, { section: string; rows: EngineEstimateRow[] }>();
      for (const from of costSections) {
        const inSection = new Map<string, EngineEstimateRow[]>();
        for (const row of costs.estimate?.sections[from]?.rows ?? []) {
          inSection.set(row.key, [...(inSection.get(row.key) ?? []), row]);
        }
        for (const [key, rows] of inSection) estimateRows.set(key, { section: from, rows });
      }
      const quantityIndex = section.table.columns.indexOf(costs.join[costSection].quantity_field);
      const rows: (readonly unknown[])[] = [];
      const rowCosts: RowCost[] = [];
      for (const row of section.table.rows) {
        const raw = row[keyIndex];
        const key = raw === null || raw === undefined ? null : String(raw);
        const priced = key !== null ? estimateRows.get(key) ?? null : null;
        // A check-off can exist without a price, so the entry is looked up across every
        // section reading this table rather than only the one that priced the row.
        const from = key === null ? costSection
          : priced?.section ?? costSections.find((s) => costs.entries[s]?.[key]) ?? costSection;
        // A key two trades bill files one entry per trade. A bare entry on such a key
        // belongs to no trade row (the CSV ignores it too); tasks/visits still read it.
        const byTrade = new Map<string, EngineEstimateRow[]>();
        for (const r of priced?.rows ?? []) {
          if (r.trade) byTrade.set(r.trade, [...(byTrade.get(r.trade) ?? []), r]);
        }
        const split = key !== null && byTrade.size > 1;
        const parts: { trade: string | null; estimate: EngineEstimateRow | null }[] = split
          ? [...byTrade].map(([trade, group]) => ({ trade, estimate: mergeRows(group) }))
          : [{ trade: null, estimate: priced ? mergeRows(priced.rows) : null }];
        for (const part of parts) {
          const name = key === null ? null : entryKey(key, part.trade);
          // A trade row shows that trade's quantity, not the BOM row's whole one.
          const quantity = part.trade !== null ? part.estimate?.quantity : undefined;
          rows.push(quantityIndex >= 0 && quantity !== undefined && Number.isFinite(quantity)
            ? row.map((cell, i) => (i === quantityIndex ? quantity : cell)) : row);
          rowCosts.push({ section: from, key, trade: part.trade, entryKey: name,
            entry: name !== null ? costs.entries[from]?.[name] ?? null : null,
            estimate: part.estimate });
        }
      }
      const table: CostedTable = {
        ...section.table,
        columns: [...section.table.columns, ...COST_COLUMNS],
        headers: [...section.table.headers, "trade", "unit price", "est. cost", "actual cost",
          "product", "paid"],
        rows: rows.map((row, index) => {
          const rc = rowCosts[index];
          return [
            ...row,
            rc.trade,
            formatRange(rc.estimate?.unit_price),
            formatRange(rc.estimate?.cost),
            rc.entry?.actual_cost ?? null,
            rc.entry?.product ?? null,
            rc.entry?.paid ?? false,
          ];
        }),
        rowCosts,
      };
      return { ...section, costSection, table };
    }),
  }));
}

export interface ExtraTable extends BomTable {
  // Parallel to rows: the extra item behind each row, for edit/delete wiring.
  readonly items: readonly EngineExtraItem[];
}

/** The non-modeled line items as a table shaped like every other BOM table. */
export function buildExtraTable(costs: EngineCosts): ExtraTable {
  const columns = ["name", "category", "cost", "product", "note", "paid"];
  return {
    kind: "rows",
    columns,
    headers: ["name", "category", "cost", "product", "note", "paid"],
    rows: costs.extra.map((item) => [
      item.name, item.category, formatRange(item.cost), item.product, item.note, item.paid,
    ]),
    items: costs.extra,
  };
}

export interface StaleEntry {
  section: string;
  key: string;
  entry: EngineCostEntry | null;
}

/** The check-offs whose BOM row no longer exists — the plan moved on under them. */
export function staleEntries(costs: EngineCosts): StaleEntry[] {
  return costs.stale.map(({ section, key }) => ({
    section,
    key,
    entry: costs.entries[section]?.[key] ?? null,
  }));
}

/** One line for the view's subtitle: totals plus how much of the BOM is still unpriced. */
export function costsSubtitle(costs: EngineCosts): string {
  const parts: string[] = [];
  const totals = costs.totals as {
    combined?: EnginePriceRange; estimate?: EnginePriceRange; extra?: EnginePriceRange;
    excluded?: EnginePriceRange; actual_paid?: number; paid_entries?: number;
  };
  if (totals.combined) parts.push(`est. ${formatRange(totals.combined)}`);
  else if (totals.estimate) parts.push(`est. ${formatRange(totals.estimate)}`);
  // Beside the build number, never folded into it. A zero here means no furnishing is
  // priced yet, which is not worth a subtitle slot.
  if (totals.excluded?.high) parts.push(`+ furnishings ${formatRange(totals.excluded)}`);
  if (totals.actual_paid) {
    parts.push(`paid ${formatRange({ low: totals.actual_paid, high: totals.actual_paid })}`);
  }
  const unpriced = costs.estimate?.unpriced.length ?? 0;
  if (costs.prices_loaded && unpriced) parts.push(`${unpriced} unpriced`);
  if (!costs.prices_loaded) parts.push("no prices.toml");
  return parts.join(" · ");
}
