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

// Per-row cost identity: which costs (section, key) a BOM table row joins, plus what is
// known about it. `key` is null on rows whose key cell was empty — nothing to check off.
export interface RowCost {
  section: string;
  key: string | null;
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
export const COST_COLUMNS = ["unit_price", "est_cost", "actual_cost", "product", "paid"] as const;

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
      const estimateRows = new Map<string, { section: string; row: EngineEstimateRow }>();
      for (const from of costSections) {
        for (const row of costs.estimate?.sections[from]?.rows ?? []) {
          estimateRows.set(row.key, { section: from, row });
        }
      }
      const rowCosts: RowCost[] = section.table.rows.map((row) => {
        const raw = row[keyIndex];
        const key = raw === null || raw === undefined ? null : String(raw);
        const priced = key !== null ? estimateRows.get(key) ?? null : null;
        // A check-off can exist without a price, so the entry is looked up across every
        // section reading this table rather than only the one that priced the row.
        const from = key === null ? null
          : priced?.section ?? costSections.find((s) => costs.entries[s]?.[key]) ?? costSection;
        return {
          section: from ?? costSection,
          key,
          entry: key !== null && from !== null ? costs.entries[from]?.[key] ?? null : null,
          estimate: priced?.row ?? null,
        };
      });
      const table: CostedTable = {
        ...section.table,
        columns: [...section.table.columns, ...COST_COLUMNS],
        headers: [...section.table.headers, "unit price", "est. cost", "actual cost",
          "product", "paid"],
        rows: section.table.rows.map((row, index) => {
          const rc = rowCosts[index];
          return [
            ...row,
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
