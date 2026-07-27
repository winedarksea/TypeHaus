import { useEffect, useMemo, useState } from "react";
import { useStore } from "../state/store";
import type { EngineBom } from "../engine/EngineClient";
import { formatCell, groupBom, type BomTable } from "../model/engineBom";
import { ReaderSection, ReaderShell } from "./ReaderShell";

// "BOM of all parts" (→ TODO Editor): what is in this house, and how much of it.
//
// The arithmetic is the engine's and only the engine's. This view used to call
// `buildBillOfMaterials(model)` — a second implementation in the browser that billed some
// families the engine did not, missed others, and had nothing testing that the two agreed
// (TODO item 2). It now fetches `takeoff/bom.py::bill_of_materials` through the client, which
// works on both surfaces: `/bom` from `haus serve`, and the same function in-process under the
// offline pyodide engine. Everything here is arrangement — grouping, columns, formatting — and
// the arrangement itself lives in model/engineBom.ts so it is testable without a DOM.

function BomTableView({ table }: { table: BomTable }) {
  if (!table.rows.length) return <p className="muted">No rows.</p>;
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
          {table.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td
                  key={table.columns[cellIndex]}
                  className={typeof cell === "number" ? "num-col" : "reader-mono"}
                >
                  {formatCell(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function BomView() {
  const model = useStore((s) => s.model);
  const client = useStore((s) => s.client);
  const setDetailView = useStore((s) => s.setDetailView);
  const [filter, setFilter] = useState("");
  const [bom, setBom] = useState<EngineBom | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    return () => { cancelled = true; };
  }, [client, model]);

  const groups = useMemo(() => (bom ? groupBom(bom) : []), [bom]);
  const needle = filter.trim().toLowerCase();
  // The filter matches stringified cells, so it finds a tag, a material name or a room alike
  // without this view having to know which column carries which.
  const filtered = useMemo(() => groups.map((group) => ({
    ...group,
    sections: group.sections.map((section) => ({
      ...section,
      table: needle
        ? {
          ...section.table,
          rows: section.table.rows.filter((row) =>
            row.some((cell) => formatCell(cell).toLowerCase().includes(needle))),
        }
        : section.table,
    })).filter((section) => !needle || section.table.rows.length),
  })).filter((group) => group.sections.length), [groups, needle]);
  const rowsIn = (group: (typeof filtered)[number]) =>
    group.sections.reduce((n, section) => n + section.table.rows.length, 0);
  const totalRows = filtered.reduce((sum, group) => sum + rowsIn(group), 0);

  if (!model) return null;

  const subtitle = error !== null ? `${model.project.name} · bill of materials unavailable`
    : bom === null ? `${model.project.name} · computing…`
      : `${model.project.name} · ${totalRows} line items`;

  return (
    <ReaderShell
      title="Bill of materials"
      subtitle={subtitle}
      onClose={() => setDetailView("none")}
      toolbar={
        <input
          value={filter}
          placeholder="Filter parts…"
          onChange={(event) => setFilter(event.target.value)}
          aria-label="Filter bill of materials"
          style={{ padding: "5px 7px", minWidth: 180 }}
        />
      }
    >
      {error !== null && (
        <p className="muted" role="alert">
          The engine could not build a bill of materials: {error}
        </p>
      )}
      {error === null && bom === null && <p className="muted">Computing bill of materials…</p>}
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
              <BomTableView table={section.table} />
            </div>
          ))}
        </ReaderSection>
      ))}
    </ReaderShell>
  );
}
