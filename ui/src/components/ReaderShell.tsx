import { useCallback, useMemo, useRef, useState, type ReactNode } from "react";
import { Icon } from "../icons/Icon";
import { useStore } from "../state/store";
import { uidByTag } from "../model/tagIndex";
import type { Model } from "../model/types";

// The chrome the two full-width readers share (assembly details, bill of materials). Same
// focus-mode treatment as the Workbench — canvas dims behind a breadcrumb back — because both
// are read-and-return surfaces, not inspectors you keep open while editing.
export function ReaderShell({ title, subtitle, onClose, toolbar, children }: {
  title: string;
  subtitle: string;
  onClose: () => void;
  toolbar?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="workbench-backdrop">
      <div className="workbench" role="dialog" aria-label={title}>
        <div className="workbench-bread">
          <button className="btn" onClick={onClose} title="Back to canvas"><Icon name="arrow-left" size={18} /> Back</button>
          <span className="workbench-title">{title}</span>
          <span className="muted reader-subtitle">{subtitle}</span>
          <span className="spacer" style={{ flex: 1 }} />
          {toolbar}
        </div>
        <div className="workbench-body">{children}</div>
      </div>
    </div>
  );
}

// A labelled block inside a reader. `count` is shown next to the heading so a section that is
// empty for this house says so rather than looking broken.
export function ReaderSection({ title, note, count, children }: {
  title: string;
  note: string;
  count: number;
  children: ReactNode;
}) {
  return (
    <section className="reader-section">
      <h3 className="reader-section-title">
        {title} <span className="muted">· {count}</span>
      </h3>
      <p className="muted reader-section-note">{note}</p>
      {count === 0 ? <div className="muted">Nothing in this model.</div> : children}
    </section>
  );
}

// --- the wiring every trade reader repeats -----------------------------------------------
//
// PlumbingView / CircuitsView / LightingView / HvacView each opened with the same twenty-odd
// lines: the same three store selectors, the same `uidByTag` memo, the same filter state, the
// same `jump`, the same filter input, the same "no data for this trade" early return. Four
// copies meant four places to fix a bug in the zoom contract and four chances for one reader to
// drift from the others. BomView already keeps its arrangement out of the component
// (model/engineBom.ts); this is the same move for the wiring.

/** What a reader needs from the store, wired once. */
export interface Reader<T> {
  /** null while the model is still loading — the reader renders nothing. */
  model: Model | null;
  /** The trade block `select` picked, or null when this house has none. */
  data: T | null;
  /** tag → uid, for `jump` and for greying out a tag with nothing to zoom to. */
  index: Map<string, string>;
  filter: string;
  setFilter: (next: string) => void;
  /** `filter`, trimmed and lowercased — what every reader actually matches against. */
  needle: string;
  /** Zoom the plan to a tag, then get out of the way. The shared reader zoom contract. */
  jump: (tag: string) => void;
  close: () => void;
}

/**
 * `select` picks the trade block out of the model; `aliases` optionally widens the tag index
 * for records whose scene geometry is tagged differently from the record (a plumbing run is
 * drawn as per-segment solids, so its own tag resolves to nothing without an alias).
 */
export function useReader<T>(
  select: (model: Model) => T | null | undefined,
  aliases?: (base: Map<string, string>, data: T) => Map<string, string>,
): Reader<T> {
  const model = useStore((s) => s.model);
  const setDetailView = useStore((s) => s.setDetailView);
  const zoomToUid = useStore((s) => s.zoomToUid);
  const [filter, setFilter] = useState("");

  const data = model ? select(model) ?? null : null;
  const base = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  // Read the alias builder through a ref: callers write it inline, so it is a fresh function
  // every render and would defeat the memo it is a dependency of.
  const aliasRef = useRef(aliases);
  aliasRef.current = aliases;
  const index = useMemo(
    () => (data && aliasRef.current ? aliasRef.current(base, data) : base),
    [base, data],
  );

  const close = useCallback(() => setDetailView("none"), [setDetailView]);
  const jump = useCallback((tag: string) => {
    const uid = index.get(tag);
    if (!uid) return;
    zoomToUid(uid);
    setDetailView("none");
  }, [index, zoomToUid, setDetailView]);

  return { model, data, index, filter, setFilter, needle: filter.trim().toLowerCase(),
    jump, close };
}

/** The filter box every reader hangs in its ReaderShell toolbar. */
export function ReaderFilter({ value, onChange, placeholder, label }: {
  value: string;
  onChange: (next: string) => void;
  placeholder: string;
  label: string;
}) {
  return (
    <input
      value={value}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
      aria-label={label}
      style={{ padding: "5px 7px", minWidth: 180 }}
    />
  );
}

/** A reader opened against a house whose model carries nothing for that trade. */
export function ReaderEmpty({ title, subtitle, onClose, children }: {
  title: string;
  subtitle: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <ReaderShell title={title} subtitle={subtitle} onClose={onClose}>
      <div className="muted">{children}</div>
    </ReaderShell>
  );
}

/**
 * A tag that zooms the plan to what it names — the readers' single most repeated control
 * (twenty-odd copies of the same five-line button). Disabled when the tag resolves to no
 * scene record, so a dead zoom reads as dead rather than as a click that did nothing.
 */
export function TagCell({ tag, index, onJump, title, mono = false, className, children }: {
  tag: string;
  index: Map<string, string>;
  onJump: (tag: string) => void;
  title: string;
  /** Table cells set the tag in the mono face; chips in a tag cloud do not. */
  mono?: boolean;
  className?: string;
  /** Label override, for a chip that prints more than the tag ("R-3 · 12 lf"). */
  children?: ReactNode;
}) {
  const label = children ?? tag;
  return (
    <button
      className={className ? `reader-tag ${className}` : "reader-tag"}
      onClick={() => onJump(tag)}
      disabled={!index.has(tag)}
      title={title}
    >
      {mono ? <span className="reader-mono">{label}</span> : label}
    </button>
  );
}

/**
 * One column of a ReaderTable: its heading, and how a row becomes a cell.
 *
 * `num` is the numeric-column treatment the readers already used (`num-col` on both the th and
 * the td, right-aligning the column); `cellClass` carries the rest (`reader-mono`,
 * `reader-mono muted`) so a column's presentation is declared once rather than repeated per row.
 */
export interface ReaderColumn<Row> {
  key: string;
  header: ReactNode;
  num?: boolean;
  cellClass?: string;
  cell: (row: Row) => ReactNode;
  /**
   * The sort this column's header selects, when the table is given a `sort`. Named
   * separately from `key` because several columns can read the same measure (a cost column
   * and the bar drawn from it both sort by "cost") and because a column with no sortKey is
   * simply not clickable.
   */
  sortKey?: string;
}

/** A ReaderTable's sort state, owned by the view so a toolbar control and the headers
 *  can never disagree about what the table is currently ordered by. */
export interface ReaderSort {
  key: string;
  descending: boolean;
  onSort: (key: string) => void;
}

/**
 * The readers' scrollable table, declared as columns instead of hand-rolled markup.
 *
 * The four trade readers between them wrote out `<div className="reader-table-scroll"><table
 * className="reader-table"><thead>…` a dozen times, each with its own `<th>`/`<td>` class
 * spellings — which is how a numeric column ended up right-aligned in one reader and not in
 * its twin. Complex tables (an expandable panel schedule, a table with colspan detail rows)
 * still build their own markup; this is for the plain ones, which is most of them.
 */
export function ReaderTable<Row>({ columns, rows, rowKey, empty, sort }: {
  columns: ReaderColumn<Row>[];
  rows: readonly Row[];
  rowKey: (row: Row, index: number) => string;
  /** Rendered instead of an empty table body. Omit to render the empty table. */
  empty?: ReactNode;
  /** Makes every column that declares a `sortKey` a button, and marks the active one with
   *  `aria-sort`. Omit for the tables that are in payload order and mean to stay there. */
  sort?: ReaderSort;
}) {
  if (empty !== undefined && rows.length === 0) return <>{empty}</>;
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            {columns.map((column, index) => {
              const sortable = sort && column.sortKey;
              const active = sortable && sort.key === column.sortKey;
              // Two columns may select the same sort (a cost column and the bar drawn from
              // it), and both are clickable — but only one may carry aria-sort, or a
              // screen reader is told the table is sorted by two different columns at once.
              const announced = active
                && columns.findIndex((other) => other.sortKey === sort!.key) === index;
              return (
                <th
                  key={column.key}
                  className={column.num ? "num-col" : undefined}
                  aria-sort={announced
                    ? (sort!.descending ? "descending" : "ascending") : undefined}
                >
                  {sortable ? (
                    <button
                      className={active ? "reader-sort is-active" : "reader-sort"}
                      onClick={() => sort!.onSort(column.sortKey!)}
                    >
                      {column.header}
                      <span aria-hidden="true" className="reader-sort-caret">
                        {active ? (sort!.descending ? "▾" : "▴") : ""}
                      </span>
                    </button>
                  ) : column.header}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowKey(row, rowIndex)}>
              {columns.map((column) => (
                <td key={column.key} className={column.num ? "num-col" : column.cellClass}>
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
