import { useMemo, useState } from "react";
import { useStore } from "../state/store";
import { BOM_UNIT_LABEL, buildBillOfMaterials, type BomRow } from "../model/bom";
import { ReaderSection, ReaderShell } from "./ReaderShell";

// "BOM of all parts" (→ TODO Editor). Replaces one of the two topbar workspace buttons with a
// surface that actually answers a question: what is in this house, and how much of it. The
// arithmetic lives in model/bom.ts so it is testable without a DOM; this file is presentation.

// Quantities span six orders of magnitude (2 cu yd of footing, 40 000 sq ft of membrane), so
// fixed decimals would either lose small rows or bury large ones in noise.
function formatQuantity(value: number): string {
  if (value >= 1000) return Math.round(value).toLocaleString();
  if (value >= 10) return value.toFixed(0);
  if (value >= 1) return value.toFixed(1);
  return value.toFixed(2);
}

function BomTable({ rows }: { rows: BomRow[] }) {
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Part</th>
            <th>Where</th>
            <th className="num-col">Count</th>
            <th className="num-col">Quantity</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td className="reader-mono">{row.label}</td>
              <td className="muted">{row.qualifier}</td>
              <td className="num-col">{row.pieces === null ? "—" : row.pieces.toLocaleString()}</td>
              <td className="num-col">
                {formatQuantity(row.quantity)} <span className="muted">{BOM_UNIT_LABEL[row.unit]}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function BomView() {
  const model = useStore((s) => s.model);
  const setDetailView = useStore((s) => s.setDetailView);
  const [filter, setFilter] = useState("");

  const sections = useMemo(() => (model ? buildBillOfMaterials(model) : []), [model]);
  const needle = filter.trim().toLowerCase();
  const filtered = useMemo(
    () => sections.map((section) => ({
      ...section,
      rows: needle
        ? section.rows.filter((row) => `${row.label} ${row.qualifier}`.toLowerCase().includes(needle))
        : section.rows,
    })),
    [sections, needle],
  );
  const totalRows = filtered.reduce((sum, section) => sum + section.rows.length, 0);

  if (!model) return null;

  return (
    <ReaderShell
      title="Bill of materials"
      subtitle={`${model.project.name} · ${totalRows} line items`}
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
      {filtered.map((section) => (
        <ReaderSection key={section.id} title={section.title} note={section.note} count={section.rows.length}>
          <BomTable rows={section.rows} />
        </ReaderSection>
      ))}
    </ReaderShell>
  );
}
