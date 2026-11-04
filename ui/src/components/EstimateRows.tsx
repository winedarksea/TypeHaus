// The Estimate reader's group headers and row columns. Split out of EstimateView so both stay
// inside the repo's 500-line rule; every number is read off the row or the group.

import type { ReactNode } from "react";
import type { EnginePriceRange } from "../engine/EngineClient";
import { formatRange } from "../model/engineCosts";
import { barWidths, displayName, shareOfTotal, type EstimateRow } from "../model/engineEstimate";
import type { EstimateGroup } from "../model/estimateGroups";
import type { ReaderColumn } from "./ReaderShell";

/** Whole dollars: a header or a row of a $1M estimate has no use for cents. */
export function dollars(value: number): string {
  return `$${Math.round(value).toLocaleString()}`;
}

function rangeText(range: EnginePriceRange): string {
  return Math.abs(range.high - range.low) < 0.5
    ? dollars(range.low) : `${dollars(range.low)}–${dollars(range.high)}`;
}

function pct(fraction: number): string {
  return `${(fraction * 100).toFixed(fraction < 0.1 ? 1 : 0)}%`;
}

const BASIS_BADGE: Record<string, string> = {
  material: "material", labour: "labour", installed: "installed",
};

export function rowColumns({ widest, total, cumulative }: {
  widest: number;
  total: EnginePriceRange | null;
  /** Running share per row, for the Ranked list; null elsewhere. */
  cumulative: Map<EstimateRow, number> | null;
}): ReaderColumn<EstimateRow>[] {
  const columns: ReaderColumn<EstimateRow>[] = [
    {
      key: "key", header: "item", sortKey: "key",
      cell: (row) => {
        const name = displayName(row);
        return (
          <div className="estimate-key">
            <span>{name}</span>
            {name !== row.key && <span className="muted reader-mono estimate-desc">{row.key}</span>}
          </div>
        );
      },
    },
    {
      key: "quantity", header: "qty", num: true, sortKey: "quantity",
      cell: (row) => `${row.quantity.toLocaleString()} ${row.unit}`,
    },
    {
      key: "unit_price", header: "unit price", num: true,
      cell: (row) => formatRange(row.unit_price) ?? "—",
    },
    {
      // The mid figure the "Expected" sort ranks by; the bar under it is the range on one
      // scale across the page (position is magnitude, width is uncertainty).
      key: "cost", header: "expected", num: true, sortKey: "cost",
      cell: (row) => {
        const bar = barWidths(row, widest);
        return (
          <div className="estimate-cost">
            <span className="estimate-cost-mid">
              {dollars(row.mid)}
              {row.basis && (
                <span className={`estimate-basis-badge is-${row.basis}`}>
                  {BASIS_BADGE[row.basis] ?? row.basis}
                </span>
              )}
            </span>
            <span className="estimate-bar" title={formatRange(row.cost) ?? undefined}>
              <span
                className="estimate-bar-fill"
                style={{ marginLeft: `${bar.left}%`, width: `${bar.width}%` }}
              />
            </span>
            <span className="muted estimate-cost-range">{rangeText(row.cost)}</span>
          </div>
        );
      },
    },
    {
      key: "share", header: "% of total", num: true,
      cell: (row) => row.inTotal ? pct(shareOfTotal(row, total)) : <span className="muted">—</span>,
    },
  ];
  if (cumulative) {
    columns.push({
      key: "cumulative", header: "cumulative", num: true,
      cell: (row) => {
        const value = cumulative.get(row);
        return value === undefined ? <span className="muted">—</span> : pct(value);
      },
    });
  }
  return columns;
}

/**
 * One group's headline, and the control that opens it. The share bar is on one scale across
 * every group on the page (`scale`, the biggest top-level group), so trades compare by eye.
 */
export function GroupHeader({ group, collapsed, onToggle, scale, grossSf }: {
  group: EstimateGroup;
  collapsed: boolean;
  onToggle: () => void;
  scale: number;
  grossSf: number | null;
}) {
  const facts: ReactNode[] = [];
  facts.push(<span key="range" className="muted reader-mono estimate-group-range">{rangeText(group.subtotal)}</span>);
  facts.push(
    <span key="share" className="muted estimate-group-share">
      {group.inTotal ? `${pct(group.share)} of total` : "beside the total"}
    </span>);
  if (grossSf && group.inTotal) {
    facts.push(<span key="gsf" className="muted estimate-group-gsf">{`$${(group.mid / grossSf).toFixed(2)}/gsf`}</span>);
  }
  if (group.allowance > 0) {
    facts.push(
      <span key="allow" className="estimate-allowance-chip" title="Placeholder money in [allowances]">
        {dollars(group.allowance)} allowance
      </span>);
  }
  facts.push(<span key="count" className="muted">{group.rows.length} {group.rows.length === 1 ? "row" : "rows"}</span>);
  return (
    <button
      type="button"
      className={`estimate-group-head depth-${group.depth}`}
      aria-expanded={!collapsed}
      onClick={onToggle}
    >
      <span className="estimate-group-caret" aria-hidden="true">
        {collapsed ? "▸" : "▾"}
      </span>
      <span className="estimate-group-label">{group.label}</span>
      <span className="estimate-share-bar" aria-hidden="true">
        <span
          className="estimate-share-fill"
          style={{ width: `${scale ? Math.min(100, (group.mid / scale) * 100) : 0}%` }}
        />
      </span>
      <span className="reader-mono estimate-group-mid">{dollars(group.mid)}</span>
      {facts}
    </button>
  );
}
