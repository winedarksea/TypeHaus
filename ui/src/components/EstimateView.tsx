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
import type { EngineCosts, EngineEstimate } from "../engine/EngineClient";
import { levelsOf } from "../model/levels";
import {
  displayName,
  estimateSubtitle,
  flattenEstimate,
  maxHigh,
  type EstimateRow,
} from "../model/engineEstimate";
import {
  GROUPS,
  SORTS,
  SORT_KEYS,
  allGroupIds,
  categoryLabel,
  cumulativeShares,
  defaultCollapsed,
  groupTree,
  tradeLabel,
  type EstimateGroup,
  type SortKey,
} from "../model/estimateGroups";
import { SummaryStrip, UnpricedBlock } from "./EstimateSummary";
import { EstimateRowDetail } from "./EstimateRowDetail";
import { GroupHeader, rowColumns } from "./EstimateRows";
import {
  ReaderFilter,
  ReaderSection,
  ReaderShell,
  ReaderTable,
  type ReaderColumn,
  type ReaderSort,
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

/** What the filter box matches a row against: every name the page prints for it. */
function haystack(row: EstimateRow): string {
  return [row.key, displayName(row), row.description ?? "", row.section, row.trade ?? "",
    tradeLabel(row.trade), categoryLabel(row.category), row.level ?? ""].join(" ").toLowerCase();
}

/** Shared by every level of the tree, so one prop list does not ripple through the recursion. */
interface TreeContext {
  estimate: EngineEstimate;
  columns: ReaderColumn<EstimateRow>[];
  sort: ReaderSort;
  collapsed: ReadonlySet<string>;
  toggleGroup: (id: string) => void;
  opened: ReadonlySet<string>;
  toggleRow: (id: string) => void;
  /** False under Ranked, where the one in-total group IS the table and has no header. */
  headed: (group: EstimateGroup) => boolean;
  scale: number;
  grossSf: number | null;
}

const rowId = (row: EstimateRow) => `${row.section}:${row.key}`;

function GroupBlock({ group, ctx }: { group: EstimateGroup; ctx: TreeContext }) {
  const headed = ctx.headed(group);
  // A group with no header has no control to reopen it, so it is never closed.
  const isCollapsed = headed && ctx.collapsed.has(group.id);
  return (
    <div className={`estimate-group depth-${group.depth}`}>
      {headed && (
        <GroupHeader
          group={group}
          collapsed={isCollapsed}
          onToggle={() => ctx.toggleGroup(group.id)}
          scale={ctx.scale}
          grossSf={ctx.grossSf}
        />
      )}
      {!isCollapsed && (group.children
        ? <div className="estimate-children">
          {group.children.map((child) => <GroupBlock key={child.id} group={child} ctx={ctx} />)}
        </div>
        : <ReaderTable
          columns={ctx.columns}
          rows={group.rows}
          expand={{
            isOpen: (row) => ctx.opened.has(rowId(row)),
            onToggle: (row) => ctx.toggleRow(rowId(row)),
            label: (row) => displayName(row),
            render: (row) => (
              <EstimateRowDetail
                row={row}
                section={ctx.estimate.sections[row.section]}
                sectionName={row.section}
              />
            ),
          }}
          // Index-suffixed: (section, key) is NOT unique — one key can price several BOM rows.
          rowKey={(row, index) => `${rowId(row)}:${index}`}
          sort={ctx.sort}
        />)}
    </div>
  );
}

function toggled(prev: ReadonlySet<string>, id: string): Set<string> {
  const next = new Set(prev);
  if (!next.delete(id)) next.add(id);
  return next;
}

export function EstimateView() {
  const model = useStore((s) => s.model);
  const client = useStore((s) => s.client);
  const closeReader = useStore((s) => s.closeReader);
  // Group and sort live in the store (and the URL), read by both the segmented controls and
  // the sortable headers, so the two can never disagree about the table's order.
  const view = useStore((s) => s.estimateView);
  const setView = useStore((s) => s.setEstimateView);
  const [costs, setCosts] = useState<EngineCosts | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  // Open detail panels by `section:key`, not table index: the order changes under every sort.
  const [opened, setOpened] = useState<ReadonlySet<string>>(() => new Set());
  // Collapsed groups by path id; separate from `opened`, so closing a trade keeps its panels.
  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(() => new Set());

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
    ? rows.filter((row) => haystack(row).includes(needle)) : rows, [rows, needle]);
  const levels = useMemo(() => (model ? levelsOf(model) : []).map((level) => ({
    key: level.key, label: level.key.charAt(0).toUpperCase() + level.key.slice(1),
  })), [model]);
  const groups = useMemo(
    () => groupTree(filtered, view.group, view.sort, estimate?.total ?? null, levels),
    [filtered, view, estimate, levels]);
  // One denominator for every range bar on screen, so bars compare across groups.
  const widest = useMemo(() => maxHigh(filtered), [filtered]);
  const ranked = view.group === "none";
  const cumulative = useMemo(() => {
    if (!ranked || !groups[0]?.inTotal) return null;
    const shares = cumulativeShares(groups[0].rows, estimate?.total);
    return new Map(groups[0].rows.map((row, i) => [row, shares[i]]));
  }, [ranked, groups, estimate]);
  const columns = useMemo(
    () => rowColumns({ widest, total: estimate?.total ?? null, cumulative }),
    [widest, estimate, cumulative]);
  // Re-seeded on a grouping or filter change, and once rows first arrive; never on a sort,
  // which would slam shut the group the reader just opened.
  const hasRows = rows.length > 0;
  useEffect(() => {
    setCollapsed(defaultCollapsed(groups, view.group, needle !== ""));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view.group, needle, hasRows]);

  if (!model) return null;

  const subtitle = error !== null ? `${model.project.name} · estimate unavailable`
    : costs === null ? `${model.project.name} · pricing…`
      : estimateSubtitle(estimate, model.project.name);
  const anyOpen = collapsed.size < allGroupIds(groups).length;

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
        onChange={(group) => setView({ group })}
      />
      <Segmented
        label="Sort rows by"
        value={view.sort}
        options={SORT_KEYS.map((key) => ({ key, label: SORTS[key].label }))}
        onChange={(sort) => setView({ sort })}
      />
      {!ranked && (
        <button
          className="btn"
          onClick={() => setCollapsed(anyOpen ? new Set(allGroupIds(groups)) : new Set())}
        >
          {anyOpen ? "Collapse all" : "Expand all"}
        </button>
      )}
    </>
  );

  const sort: ReaderSort = {
    key: view.sort,
    descending: SORTS[view.sort].descending,
    onSort: (key: string) => setView({ sort: key as SortKey }),
  };

  const ctx: TreeContext | null = estimate && {
    estimate,
    columns,
    sort,
    collapsed,
    toggleGroup: (id) => setCollapsed((prev) => toggled(prev, id)),
    opened,
    toggleRow: (id) => setOpened((prev) => toggled(prev, id)),
    headed: (group) => !ranked || !group.inTotal,
    scale: groups.reduce((acc, g) => Math.max(acc, g.mid), 0),
    grossSf: estimate.areas?.gross ?? null,
  };

  return (
    <ReaderShell
      title="Estimate"
      subtitle={subtitle}
      onClose={closeReader}
      toolbar={toolbar}
      wide
      className="estimate-reader"
    >
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
      {estimate && ctx && (
        <>
          <SummaryStrip estimate={estimate} />
          <ReaderSection
            title="Rows"
            note="The bar on a group is its share of the total, on one scale. Under a row, the
              bar's position is what it costs and its width how much is still unknown. Open a
              row for its split, its waste, and the accounts it books to."
            count={filtered.length}
          >
            {groups.map((group) => <GroupBlock key={group.id} group={group} ctx={ctx} />)}
          </ReaderSection>
          <UnpricedBlock estimate={estimate} />
        </>
      )}
    </ReaderShell>
  );
}
