// The Estimate reader: what this house is estimated to cost, ranked by what moves the number.
//
// `prices.toml` is 1,879 hand-authored lines and 440 priced rows, and until this page the
// only way to review it was `haus takeoff` in a terminal. Everything shown here is the
// engine's arithmetic, served whole on `GET /costs` — this view fetches, filters, and hands
// the ranking to model/engineEstimate.ts, which is where every ordering decision lives so it
// is testable without a DOM (the same split as BomView / engineBom.ts).
//
// Read-only by design. prices.toml carries four research passes of hand-written provenance in
// its comments; a writeback path from a browser table is how that gets quietly flattened. The
// check-off flow against costs.toml stays where it is, in the BOM.

import { useEffect, useMemo, useState } from "react";
import { useStore } from "../state/store";
import type { EngineCosts } from "../engine/EngineClient";
import { formatRange } from "../model/engineCosts";
import {
  GROUPS,
  SORTS,
  SORT_KEYS,
  barWidths,
  flattenEstimate,
  groupRows,
  maxHigh,
  rowDescription,
  estimateSubtitle,
  type EstimateGroup,
  type EstimateRow,
  type GroupKey,
  type SortKey,
} from "../model/engineEstimate";
import { BasisBlock, LadderBlock, TotalsBlock, UnpricedBlock } from "./EstimateSummary";
import {
  ReaderColumn,
  ReaderFilter,
  ReaderSection,
  ReaderShell,
  ReaderTable,
} from "./ReaderShell";

/** MD3 segmented button. The selected segment carries the same secondary-container tint the
 *  nav rail's indicator uses, so "this one is chosen" reads the same across the app. */
function Segmented<T extends string>({ label, value, options, onChange }: {
  label: string;
  value: T;
  options: readonly { key: T; label: string }[];
  onChange: (next: T) => void;
}) {
  return (
    <div className="estimate-seg" role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.key}
          className={option.key === value ? "estimate-seg-btn is-on" : "estimate-seg-btn"}
          aria-pressed={option.key === value}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

const BASIS_BADGE: Record<string, string> = {
  material: "material", labour: "labour", installed: "installed",
};

function rowColumns(widest: number): ReaderColumn<EstimateRow>[] {
  return [
    {
      key: "key", header: "item", sortKey: "key",
      cell: (row) => (
        <div className="estimate-key">
          <span className="reader-mono">{row.key}</span>
          {rowDescription(row)
            && <span className="muted estimate-desc">{rowDescription(row)}</span>}
        </div>
      ),
    },
    {
      key: "trade", header: "trade",
      cell: (row) => row.trade
        ? <span className="reader-chip estimate-trade">{row.trade}</span>
        : <span className="muted">—</span>,
    },
    {
      key: "section", header: "block", cellClass: "reader-mono muted",
      // The prices.toml block to open to change this row — the reason the page is
      // reviewable against the file rather than only against itself.
      cell: (row) => row.section,
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
      key: "bar", header: "range", sortKey: "cost",
      cell: (row) => {
        const bar = barWidths(row, widest);
        return (
          <span className="estimate-bar" title={formatRange(row.cost) ?? undefined}>
            <span
              className="estimate-bar-fill"
              style={{ marginLeft: `${bar.left}%`, width: `${bar.width}%` }}
            />
          </span>
        );
      },
    },
    {
      // Leads with the single number the "Expected" sort actually ranks by — a bare
      // low-high range gave no way to tell, on a wide-spread row, what value put it where
      // it landed in the order. The range moves to a muted line underneath, still there for
      // the reader who wants both ends.
      key: "cost", header: "expected", num: true, sortKey: "cost",
      cell: (row) => (
        <div className="estimate-cost">
          <span className="estimate-cost-mid">
            {formatRange({ low: row.mid, high: row.mid })}
          </span>
          {row.basis && (
            <span className={`estimate-basis-badge is-${row.basis}`}>
              {BASIS_BADGE[row.basis] ?? row.basis}
            </span>
          )}
          <span className="muted estimate-cost-range">{formatRange(row.cost)}</span>
        </div>
      ),
    },
    {
      key: "spread", header: "spread", num: true, sortKey: "spread",
      cell: (row) => row.spread
        ? <>
          {formatRange({ low: row.spread, high: row.spread })}
          <span className="muted estimate-spread-pct">
            {" "}{Math.round(row.spreadPct * 100)}%
          </span>
        </>
        : <span className="muted">exact</span>,
    },
  ];
}

function GroupHeader({ group, showLabel }: { group: EstimateGroup; showLabel: boolean }) {
  if (!showLabel) return null;
  return (
    <div className="estimate-group-head">
      <span className="estimate-group-label">{group.label}</span>
      <span className="reader-mono">
        {formatRange({ low: group.mid, high: group.mid })}
        <span className="muted"> ({formatRange(group.subtotal)})</span>
      </span>
      <span className="muted">
        {group.inTotal ? `${(group.share * 100).toFixed(1)}% of total`
          : "beside the total"}
      </span>
      <span className="muted">{group.rows.length} rows</span>
    </div>
  );
}

export function EstimateView() {
  const model = useStore((s) => s.model);
  const client = useStore((s) => s.client);
  const setDetailView = useStore((s) => s.setDetailView);
  const [costs, setCosts] = useState<EngineCosts | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  // Group and sort live in ONE piece of state, read by both the segmented controls and the
  // sortable column headers — so the control and the headers can never disagree about what
  // the table is ordered by.
  const [view, setView] = useState<{ group: GroupKey; sort: SortKey }>(
    { group: "trade", sort: "cost" });

  useEffect(() => {
    let cancelled = false;
    setError(null);
    client.getCosts().then(
      (payload) => { if (!cancelled) setCosts(payload); },
      (cause: unknown) => {
        if (!cancelled) {
          setCosts(null);
          setError(cause instanceof Error ? cause.message : String(cause));
        }
      },
    );
    return () => { cancelled = true; };
  }, [client, model]);

  const estimate = costs?.estimate ?? null;
  const rows = useMemo(() => flattenEstimate(estimate), [estimate]);
  const needle = filter.trim().toLowerCase();
  const filtered = useMemo(() => needle
    ? rows.filter((row) => `${row.key} ${row.description ?? ""} ${row.section} ${row.trade ?? ""}`
      .toLowerCase().includes(needle))
    : rows, [rows, needle]);
  const groups = useMemo(
    () => groupRows(filtered, view.group, view.sort, estimate?.total ?? null),
    [filtered, view, estimate]);
  // One denominator for every bar on screen, so bars stay comparable across groups. Taken
  // from the filtered set: a filter that leaves only small rows should still use the width.
  const widest = useMemo(() => maxHigh(filtered), [filtered]);
  const columns = useMemo(() => rowColumns(widest), [widest]);

  if (!model) return null;

  const close = () => setDetailView("none");
  const subtitle = error !== null ? `${model.project.name} · estimate unavailable`
    : costs === null ? `${model.project.name} · pricing…`
      : estimateSubtitle(estimate, model.project.name);

  const toolbar = (
    <>
      <ReaderFilter
        value={filter}
        onChange={setFilter}
        placeholder="Filter rows…"
        label="Filter estimate rows"
      />
      <Segmented
        label="Group rows by"
        value={view.group}
        options={GROUPS}
        onChange={(group) => setView((prev) => ({ ...prev, group }))}
      />
      <Segmented
        label="Sort rows by"
        value={view.sort}
        options={SORT_KEYS.map((key) => ({ key, label: SORTS[key].label }))}
        onChange={(sort) => setView((prev) => ({ ...prev, sort }))}
      />
    </>
  );

  const sort = {
    key: view.sort,
    descending: SORTS[view.sort].descending,
    onSort: (key: string) => setView((prev) => ({ ...prev, sort: key as SortKey })),
  };

  return (
    <ReaderShell title="Estimate" subtitle={subtitle} onClose={close} toolbar={toolbar} wide>
      {error !== null && (
        <p className="estimate-warn">Could not load the estimate: {error}</p>
      )}
      {costs !== null && !costs.prices_loaded && (
        <p className="muted">
          This house carries no <span className="reader-mono">prices.toml</span>, so there is
          nothing to estimate. Quantities are the product; dollars are opt-in, and a house
          owns its own numbers.
        </p>
      )}
      {estimate && (
        <>
          <TotalsBlock estimate={estimate} />
          <BasisBlock estimate={estimate} />
          <LadderBlock estimate={estimate} />
          <ReaderSection
            title="Rows"
            note="Every priced row, ranked. The bar's position is what a row costs; its width
              is how much of that is still unknown."
            count={filtered.length}
          >
            {groups.map((group) => (
              <div key={group.id} className="estimate-group">
                <GroupHeader
                  group={group}
                  showLabel={view.group !== "none" || !group.inTotal}
                />
                <ReaderTable
                  columns={columns}
                  rows={group.rows}
                  // Index-suffixed: (section, key) is NOT unique here. One prices.toml key
                  // can price several BOM rows (`standing-seam-nailstrip` bills the garage
                  // roof and, until 2026-08-20, `standing-seam` billed wall and roof out of
                  // one [envelope_layers] line), and the colliding React
                  // keys rendered one of them twice.
                  rowKey={(row, index) => `${row.section}:${row.key}:${index}`}
                  sort={sort}
                />
              </div>
            ))}
          </ReaderSection>
          <UnpricedBlock estimate={estimate} />
        </>
      )}
    </ReaderShell>
  );
}
