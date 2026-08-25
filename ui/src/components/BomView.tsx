import { useCallback, useEffect, useMemo, useState } from "react";
import { useStore } from "../state/store";
import type { CostsOp, EngineBom, EngineCosts } from "../engine/EngineClient";
import { formatCell, groupBom } from "../model/engineBom";
import {
  buildExtraTable,
  costsSubtitle,
  decorateWithCosts,
  formatRange,
  staleEntries,
  type CostedGroup,
  type CostedTable,
  type RowCost,
} from "../model/engineCosts";
import { ReaderFilter, ReaderSection, ReaderShell } from "./ReaderShell";

// "BOM of all parts" (→ TODO Editor): what is in this house, and how much of it.
//
// The arithmetic is the engine's and only the engine's. This view used to call
// `buildBillOfMaterials(model)` — a second implementation in the browser that billed some
// families the engine did not, missed others, and had nothing testing that the two agreed
// (TODO item 2). It now fetches `takeoff/bom.py::bill_of_materials` through the client, which
// works on both surfaces: `/bom` from `haus serve`, and the same function in-process under the
// offline pyodide engine. Everything here is arrangement — grouping, columns, formatting — and
// the arrangement itself lives in model/engineBom.ts + model/engineCosts.ts so it is testable
// without a DOM.
//
// Cost tracking (→ takeoff/costs.py): rows joined by `costs.join` grow unit-price / cost /
// product / paid columns; the paid checkbox and product cell edit costs.toml through
// `patchCosts` (never the plan journal — paying a bill is not a plan edit). Offline, the
// payload still renders but edits reject, so the checkboxes revert.

interface CostActions {
  togglePaid: (rc: RowCost, next: boolean) => void;
  editProduct: (rc: RowCost) => void;
}

function BomTableView({ table, actions }: { table: CostedTable; actions?: CostActions }) {
  if (!table.rows.length) return <p className="muted">No rows.</p>;
  const paidIndex = table.rowCosts ? table.columns.indexOf("paid") : -1;
  const productIndex = table.rowCosts ? table.columns.indexOf("product") : -1;
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            {table.headers.map((header, index) => (
              <th key={table.columns[index]}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => {
            const rc = table.rowCosts?.[rowIndex];
            return (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => {
                  if (rc && rc.key !== null && actions && cellIndex === paidIndex) {
                    return (
                      <td key="paid">
                        <input
                          type="checkbox"
                          checked={rc.entry?.paid ?? false}
                          onChange={(event) => actions.togglePaid(rc, event.target.checked)}
                          aria-label={`Paid: ${rc.key}`}
                        />
                      </td>
                    );
                  }
                  if (rc && rc.key !== null && actions && cellIndex === productIndex) {
                    // Two different facts under one heading, and the distinction is the
                    // point: `estimate.product` is what the PLAN specifies (brand + model,
                    // derived from the model), `entry.product` is what was actually BOUGHT.
                    // The specified product shows through as a muted placeholder until
                    // someone records something different, so the field only ever asks for
                    // what differed — before this it asked for the whole answer over again,
                    // against nothing, which is why it stayed empty.
                    const specified = rc.estimate?.product ?? null;
                    const bought = rc.entry?.product ?? null;
                    return (
                      <td key="product" className="reader-mono">
                        <button
                          className="btn-link"
                          onClick={() => actions.editProduct(rc)}
                          title={specified && !bought
                            ? `Specified: ${specified}. Record what was actually bought.`
                            : "Record the exact product bought"}
                        >
                          {bought ?? (specified
                            ? <span className="muted">{specified}</span>
                            : "—")}
                        </button>
                      </td>
                    );
                  }
                  return (
                    <td
                      key={table.columns[cellIndex]}
                      className={typeof cell === "number" ? "num-col" : "reader-mono"}
                    >
                      {formatCell(cell)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function parseCostInput(raw: string): { low: number; high: number } | null {
  const text = raw.replace(/[$,\s]/g, "");
  if (!text) return null;
  const parts = text.split(/[-–]/).map(Number);
  if (parts.some((n) => !Number.isFinite(n) || n < 0)) return null;
  if (parts.length === 1) return { low: parts[0], high: parts[0] };
  if (parts.length === 2) return { low: Math.min(...parts), high: Math.max(...parts) };
  return null;
}

const today = () => new Date().toISOString().slice(0, 10);

export function BomView() {
  const model = useStore((s) => s.model);
  const client = useStore((s) => s.client);
  const setDetailView = useStore((s) => s.setDetailView);
  const [filter, setFilter] = useState("");
  const [bom, setBom] = useState<EngineBom | null>(null);
  const [costs, setCosts] = useState<EngineCosts | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [costsError, setCostsError] = useState<string | null>(null);

  // Re-fetch whenever the model changes: an edit that lands is an edit the BOM has to see.
  useEffect(() => {
    let cancelled = false;
    setError(null);
    client.getBom().then(
      (payload) => { if (!cancelled) setBom(payload); },
      (cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
      },
    );
    // Costs ride alongside; a house without the endpoint (or a malformed costs.toml)
    // degrades to the plain BOM rather than blanking it.
    client.getCosts().then(
      (payload) => { if (!cancelled) setCosts(payload); },
      (cause: unknown) => {
        if (!cancelled) {
          setCosts(null);
          setCostsError(cause instanceof Error ? cause.message : String(cause));
        }
      },
    );
    return () => { cancelled = true; };
  }, [client, model]);

  // All costs edits funnel here: apply, then adopt the server's fresh payload. Callers do
  // their own optimistic paint and revert when this reports failure (the DetailsNavigator
  // star pattern).
  const applyCostsOps = useCallback(async (ops: CostsOp[]): Promise<boolean> => {
    try {
      const fresh = await client.patchCosts(ops);
      setCosts(fresh);
      return true;
    } catch (cause) {
      setCostsError(cause instanceof Error ? cause.message : String(cause));
      return false;
    }
  }, [client]);

  const togglePaid = useCallback(async (rc: RowCost, next: boolean) => {
    if (rc.key === null) return;
    const { section, key } = rc;
    const previous = rc.entry;
    const optimistic = { ...(previous ?? {}), paid: next,
      paid_date: next ? (previous?.paid_date ?? today()) : null };
    const blank = { paid: false, paid_date: null, product: null, actual_cost: null,
      note: null };
    setCosts((prev) => prev ? {
      ...prev,
      entries: { ...prev.entries, [section]: { ...(prev.entries[section] ?? {}),
        [key]: { ...blank, ...optimistic } } },
    } : prev);
    const ok = await applyCostsOps([{ op: "set_entry", section, key, entry: optimistic }]);
    if (!ok) {
      setCosts((prev) => prev ? {
        ...prev,
        entries: { ...prev.entries, [section]: { ...(prev.entries[section] ?? {}),
          ...(previous ? { [key]: previous } : {}) } },
      } : prev);
    }
  }, [applyCostsOps]);

  const editProduct = useCallback(async (rc: RowCost) => {
    if (rc.key === null) return;
    // Prefilled with the specified product where the plan names one: the common edit is a
    // substitution, so the field starts from what was asked for rather than from blank.
    // Clearing it back to empty still deletes the record — the specification is the model's
    // and is never written into costs.toml by this dialog.
    const specified = rc.estimate?.product ?? "";
    const prompt = specified
      ? `Exact product bought for ${rc.key} (specified: ${specified}):`
      : `Exact product for ${rc.key}:`;
    const product = window.prompt(prompt, rc.entry?.product ?? specified);
    if (product === null) return;
    await applyCostsOps([{ op: "set_entry", section: rc.section, key: rc.key,
      entry: { ...(rc.entry ?? {}), product: product.trim() || null } }]);
  }, [applyCostsOps]);

  const addExtra = useCallback(async () => {
    const name = window.prompt("Extra line item (spend the model does not bill):", "");
    if (!name || !name.trim()) return;
    const rawCost = window.prompt("Cost ($ or $low-$high, blank if unknown):", "") ?? "";
    const cost = parseCostInput(rawCost);
    await applyCostsOps([{ op: "set_extra", item: { name: name.trim(),
      ...(cost ? { cost } : {}) } }]);
  }, [applyCostsOps]);

  const editExtra = useCallback(async (id: string) => {
    const item = costs?.extra.find((entry) => entry.id === id);
    if (!item) return;
    const name = window.prompt("Name:", item.name);
    if (name === null || !name.trim()) return;
    const rawCost = window.prompt("Cost ($ or $low-$high, blank to clear):",
      item.cost ? (item.cost.low === item.cost.high ? String(item.cost.low)
        : `${item.cost.low}-${item.cost.high}`) : "");
    if (rawCost === null) return;
    const cost = parseCostInput(rawCost);
    await applyCostsOps([{ op: "set_extra", item: { ...item, name: name.trim(),
      cost: cost ?? null } }]);
  }, [applyCostsOps, costs]);

  const toggleExtraPaid = useCallback(async (id: string, next: boolean) => {
    const item = costs?.extra.find((entry) => entry.id === id);
    if (!item) return;
    await applyCostsOps([{ op: "set_extra", item: { ...item, paid: next } }]);
  }, [applyCostsOps, costs]);

  const deleteExtra = useCallback(async (id: string) => {
    await applyCostsOps([{ op: "delete_extra", id }]);
  }, [applyCostsOps]);

  const removeStale = useCallback(async (section: string, key: string) => {
    await applyCostsOps([{ op: "set_entry", section, key, entry: {} }]);
  }, [applyCostsOps]);

  const groups: CostedGroup[] = useMemo(() => {
    if (!bom) return [];
    const plain = groupBom(bom);
    return costs ? decorateWithCosts(plain, costs) : plain;
  }, [bom, costs]);
  const stale = useMemo(() => (costs ? staleEntries(costs) : []), [costs]);
  const extraTable = useMemo(() => (costs ? buildExtraTable(costs) : null), [costs]);
  const needle = filter.trim().toLowerCase();
  // The filter matches stringified cells, so it finds a tag, a material name or a room alike
  // without this view having to know which column carries which.
  const filtered = useMemo(() => groups.map((group) => ({
    ...group,
    sections: group.sections.map((section) => {
      if (!needle) return section;
      const keep = section.table.rows.map((row) =>
        row.some((cell) => formatCell(cell).toLowerCase().includes(needle)));
      return {
        ...section,
        table: {
          ...section.table,
          rows: section.table.rows.filter((_row, index) => keep[index]),
          rowCosts: section.table.rowCosts?.filter((_rc, index) => keep[index]),
        },
      };
    }).filter((section) => !needle || section.table.rows.length),
  })).filter((group) => group.sections.length), [groups, needle]);
  const rowsIn = (group: (typeof filtered)[number]) =>
    group.sections.reduce((n, section) => n + section.table.rows.length, 0);
  const totalRows = filtered.reduce((sum, group) => sum + rowsIn(group), 0);

  if (!model) return null;

  const costsNote = costs ? costsSubtitle(costs) : "";
  const subtitle = error !== null ? `${model.project.name} · bill of materials unavailable`
    : bom === null ? `${model.project.name} · computing…`
      : `${model.project.name} · ${totalRows} line items${costsNote ? ` · ${costsNote}` : ""}`;

  const actions: CostActions = { togglePaid, editProduct };

  return (
    <ReaderShell
      title="Bill of materials"
      subtitle={subtitle}
      onClose={() => setDetailView("none")}
      toolbar={<ReaderFilter value={filter} onChange={setFilter}
        placeholder="Filter parts…" label="Filter bill of materials" />}
    >
      {error !== null && (
        <p className="muted" role="alert">
          The engine could not build a bill of materials: {error}
        </p>
      )}
      {error === null && bom === null && <p className="muted">Computing bill of materials…</p>}
      {costsError !== null && costs !== null && (
        <p className="muted" role="alert">Cost update failed: {costsError}</p>
      )}
      {stale.length > 0 && (
        <div className="bom-stale-alert" role="alert">
          <strong>Stale cost entries</strong> — these check-offs match no current BOM row
          (the plan moved on under them):
          <ul>
            {stale.map(({ section, key, entry }) => (
              <li key={`${section}:${key}`} className="reader-mono">
                {section} · {key}
                {entry?.paid ? " (PAID" : ""}
                {entry?.paid && entry.actual_cost !== null
                  ? ` ${formatRange({ low: entry.actual_cost, high: entry.actual_cost })})`
                  : entry?.paid ? ")" : ""}
                {" "}
                <button className="btn" onClick={() => removeStale(section, key)}>
                  remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {filtered.map((group) => (
        <ReaderSection
          key={group.id}
          title={group.title}
          note={group.note}
          count={rowsIn(group)}
        >
          {group.sections.map((section) => (
            <div key={section.key} className="bom-subsection">
              <h4 className="bom-subsection-title">{section.title}</h4>
              <BomTableView
                table={section.table}
                actions={section.table.rowCosts ? actions : undefined}
              />
            </div>
          ))}
        </ReaderSection>
      ))}
      {costs !== null && !needle && (
        <ReaderSection
          title="Extra line items"
          note="Real spend the model does not bill — permits, dumpsters, deliveries."
          count={costs.extra.length}
        >
          {extraTable && extraTable.rows.length > 0 ? (
            <div className="reader-table-scroll">
              <table className="reader-table">
                <thead>
                  <tr>
                    {extraTable.headers.map((header, index) => (
                      <th key={extraTable.columns[index]}>{header}</th>
                    ))}
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {extraTable.items.map((item, rowIndex) => (
                    <tr key={item.id}>
                      {extraTable.rows[rowIndex].map((cell, cellIndex) => {
                        const column = extraTable.columns[cellIndex];
                        if (column === "paid") {
                          return (
                            <td key="paid">
                              <input
                                type="checkbox"
                                checked={item.paid}
                                onChange={(event) =>
                                  toggleExtraPaid(item.id, event.target.checked)}
                                aria-label={`Paid: ${item.name}`}
                              />
                            </td>
                          );
                        }
                        return (
                          <td key={column} className="reader-mono">{formatCell(cell)}</td>
                        );
                      })}
                      <td>
                        <button className="btn" onClick={() => editExtra(item.id)}>edit</button>
                        {" "}
                        <button className="btn" onClick={() => deleteExtra(item.id)}>
                          delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="muted">No extra line items.</p>
          )}
          <button className="btn" onClick={addExtra}>Add line item…</button>
        </ReaderSection>
      )}
    </ReaderShell>
  );
}
