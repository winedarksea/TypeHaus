import { useMemo, useState } from "react";
import type {
  Plumbing, PlumbingCastInRow, PlumbingFittingRow, PlumbingFixtureRow, PlumbingPipeGroup,
  PlumbingRiserRun, PlumbingRunLoadRow,
} from "../model/types";
import {
  ReaderEmpty, ReaderFilter, ReaderSection, ReaderShell, ReaderTable, TagCell, useReader,
  type ReaderColumn,
} from "./ReaderShell";

// "Plumbing" — the sixth reader: the isometric riser, the fixture-unit ledger, and the
// takeoff with the pour-day cast-in list. Presentation only, like every reader beside it.
// Every number is carried whole from model.json's `plumbing` block (takeoff/plumbing.py
// verbatim), whose fixture-unit arithmetic is the same takeoff/plumbing_calc.py call
// mep.pipe_sizing grades with — the reader and the finding cannot drift apart. Nothing is
// recomputed here beyond a projection; a value the engine did not author reads "—".

// Riser-diagram colors, mirroring the engine's per-system pipe solids
// (emit/gltf/palette.py pipe_* and three/solidMaterials.ts — change one, change all).
const SYSTEM_COLOR: Record<string, string> = {
  drain: "#333338",
  vent: "#8f8f88",
  water_hot: "#cc4038",
  water_cold: "#3366bf",
  gas: "#d9bf33",
  radon: "#8c9499",
};
const SYSTEM_LABEL: Record<string, string> = {
  drain: "drain",
  vent: "vent",
  water_hot: "hot",
  water_cold: "cold",
  gas: "gas",
  radon: "radon",
};

// PipeAccessoryKind → what a plumbing sheet calls it. Mirrors the engine enum
// (packages/engine/src/typehaus/model/enums.py::PipeAccessoryKind); an unmapped kind falls
// through to its raw value rather than disappearing.
const ACCESSORY_LABEL: Record<string, string> = {
  main_shutoff: "main shutoff",
  shutoff: "isolation valve",
  backflow_preventer: "backflow preventer",
  vacuum_breaker: "vacuum breaker",
  water_hammer_arrestor: "water-hammer arrestor",
  ro_stub: "RO tap provision (capped)",
  penetration_seal: "envelope penetration seal",
};

// True isometric (30° axonometric) — the classic plumbing-riser projection. The authored
// geometry is drawn exactly as routed; overlapping lines are honest, not a layout defect.
const COS30 = Math.cos(Math.PI / 6);
const SIN30 = 0.5;

function project(x: number, y: number, z: number): [number, number] {
  return [(x - y) * COS30, -(z + (x + y) * SIN30)];
}

function RiserSvg({ runs, onZoom, index }: {
  runs: PlumbingRiserRun[];
  onZoom: (tag: string) => void;
  index: Map<string, string>;
}) {
  const [hover, setHover] = useState<string | null>(null);
  const drawable = runs.filter((run) => run.vertices.length >= 2);
  const projected = useMemo(() => {
    return drawable.map((run) => ({
      run,
      points: run.vertices.map(([x, y, z]) => project(x, y, z ?? 0)),
      hasZ: run.vertices.every((v) => v[2] !== null),
    }));
  }, [drawable]);

  const bounds = useMemo(() => {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const { points } of projected) {
      for (const [sx, sy] of points) {
        minX = Math.min(minX, sx); maxX = Math.max(maxX, sx);
        minY = Math.min(minY, sy); maxY = Math.max(maxY, sy);
      }
    }
    if (!isFinite(minX)) return { minX: 0, minY: 0, w: 1, h: 1 };
    const pad = Math.max(maxX - minX, maxY - minY) * 0.06 + 0.3;
    return { minX: minX - pad, minY: minY - pad,
             w: maxX - minX + 2 * pad, h: maxY - minY + 2 * pad };
  }, [projected]);

  if (projected.length === 0) {
    return <div className="muted">No routed runs to draw.</div>;
  }
  // Stroke width ∝ diameter, normalized so a 3" stack reads clearly at any model size.
  const stroke = (diameterIn: number) => (0.5 + diameterIn * 0.35) * (bounds.w / 100);

  return (
    <svg
      viewBox={`${bounds.minX} ${bounds.minY} ${bounds.w} ${bounds.h}`}
      style={{ width: "100%", maxHeight: 460, display: "block" }}
      role="img"
      aria-label="Isometric plumbing riser diagram"
    >
      {projected.map(({ run, points, hasZ }) => {
        const color = SYSTEM_COLOR[run.system] ?? "#888";
        const d = points.map(([sx, sy], i) => `${i === 0 ? "M" : "L"}${sx.toFixed(3)},${sy.toFixed(3)}`).join(" ");
        const dim = hover !== null && hover !== run.tag;
        return (
          <g key={run.tag}
            onMouseEnter={() => setHover(run.tag)}
            onMouseLeave={() => setHover(null)}
            onClick={() => index.has(run.tag) && onZoom(run.tag)}
            style={{ cursor: index.has(run.tag) ? "pointer" : "default" }}
          >
            <path d={d} fill="none" stroke={color}
              strokeWidth={stroke(run.diameter_in)}
              strokeLinecap="round" strokeLinejoin="round"
              strokeDasharray={run.system === "vent" ? `${bounds.w / 60} ${bounds.w / 90}` : undefined}
              opacity={dim ? 0.25 : hasZ ? 1 : 0.55}
            >
              <title>{`${run.tag} — ${SYSTEM_LABEL[run.system] ?? run.system} Ø${run.diameter_in}" ${run.length_ft} lf${hasZ ? "" : " (no authored inverts — drawn flat)"}`}</title>
            </path>
            {/* fixture connections: a small circle at the run's first vertex */}
            <circle cx={points[0][0]} cy={points[0][1]} r={stroke(run.diameter_in) * 0.9}
              fill={color} opacity={dim ? 0.25 : 1} />
            {hover === run.tag && (
              <text x={points[Math.floor(points.length / 2)][0]}
                y={points[Math.floor(points.length / 2)][1] - bounds.w / 80}
                fontSize={bounds.w / 45} fill="currentColor" textAnchor="middle"
                style={{ pointerEvents: "none", fontFamily: "monospace" }}>
                {run.tag}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

function statusBadge(status: string | null): { label: string; className: string } {
  if (status === "pass") return { label: "sized", className: "" };
  if (status === "fail") return { label: "undersized", className: "confirm" };
  return { label: "unknown", className: "confirm" };
}

export function PlumbingView() {
  const { model, data: plumbing, index, filter, setFilter, needle, jump, close } =
    useReader<Plumbing>((m) => m.plumbing,
      // A routed run has no record of its own in the scene — its geometry arrives as
      // per-segment solids tagged `<RUN>-S1[B1]`. Alias each run tag to its first segment
      // solid so the riser's zoom buttons land somewhere real.
      (base, data) => {
        const aliased = new Map(base);
        for (const run of data.riser) {
          if (aliased.has(run.tag)) continue;
          for (const [tag, uid] of base) {
            if (tag.startsWith(`${run.tag}-S`)) {
              aliased.set(run.tag, uid);
              break;
            }
          }
        }
        return aliased;
      });

  const riser = useMemo(() => {
    const rows = plumbing?.riser ?? [];
    return needle
      ? rows.filter((row) =>
          `${row.tag} ${row.system} ${row.material ?? ""} ${row.serves.join(" ")} ${row.wall_refs.join(" ")}`
            .toLowerCase().includes(needle))
      : rows;
  }, [plumbing, needle]);

  if (!model) return null;

  if (!plumbing) {
    return (
      <ReaderEmpty title="Plumbing" subtitle="no plumbing data" onClose={close}>
        This model carries no plumbing take-off — rebuild with a current engine.
      </ReaderEmpty>
    );
  }

  const { fixture_units: units, takeoff } = plumbing;
  const runTag = (title: string): ReaderColumn<{ tag: string }> => ({
    key: "tag", header: "Run",
    cell: (row) => <TagCell tag={row.tag} index={index} onJump={jump} title={title} mono />,
  });
  const systems = Array.from(new Set(plumbing.riser.map((run) => run.system)));

  return (
    <ReaderShell
      title="Plumbing"
      subtitle={`${plumbing.riser.length} runs · ${units.fixtures.length} fixtures · ${takeoff.cast_in.length} cast-in sleeves`}
      onClose={close}
      toolbar={<ReaderFilter value={filter} onChange={setFilter}
        placeholder="Filter runs…" label="Filter plumbing runs" />}
    >
      <ReaderSection
        title="Isometric riser"
        note="The authored routing, projected at 30° — drawn exactly as routed, never re-laid-out. Line width follows diameter; vents are dashed; a faded run has no authored inverts and is drawn flat at its storey. Click a run to zoom the plan."
        count={riser.length}
      >
        <div className="reader-card">
          <RiserSvg runs={riser} onZoom={jump} index={index} />
          <div className="reader-tag-cloud" aria-label="Riser legend">
            {systems.map((system) => (
              <span key={system} className="reader-chip" style={{ borderColor: SYSTEM_COLOR[system] ?? "#888" }}>
                <span style={{ color: SYSTEM_COLOR[system] ?? "#888" }}>●</span>{" "}
                {SYSTEM_LABEL[system] ?? system}
              </span>
            ))}
          </div>
        </div>
        <ReaderTable<PlumbingRiserRun> rows={riser} rowKey={(run) => run.tag} columns={[
          runTag("Zoom to run"),
          { key: "storey", header: "Storey", cellClass: "reader-mono", cell: (r) => r.storey },
          { key: "system", header: "System", cellClass: "reader-mono",
            cell: (r) => SYSTEM_LABEL[r.system] ?? r.system },
          { key: "material", header: "Material", cellClass: "reader-mono",
            cell: (r) => r.material ?? "—" },
          { key: "dia", header: "Ø", num: true, cell: (r) => `${r.diameter_in}"` },
          { key: "length", header: "Length", num: true, cell: (r) => `${r.length_ft} lf` },
          { key: "hosted", header: "Hosted in", cellClass: "reader-mono muted",
            cell: (r) => r.wall_refs.length > 0 ? r.wall_refs.join(", ") : "—" },
          { key: "serves", header: "Serves", cellClass: "reader-mono muted",
            cell: (r) => r.serves.length > 0 ? r.serves.join(", ") : "—" },
        ]} />
      </ReaderSection>

      <ReaderSection
        title="Fixture units"
        note="MN Plumbing Code (UPC) Tables 702.1 / 610.3, per fixture, and each run's load against Table 703.2 / 610.4 sizing — the same tables mep.pipe_sizing grades with. Drain loads roll up every run that discharges into this one (derived from the routed geometry), so a drain row's Serves lists its whole upstream subtree; supply rows list their authored fixtures. A fixture with no table row reads —, and any run serving it reads unknown, never a partial sum."
        count={units.fixtures.length}
      >
        <div className="reader-card">
          <div className="kv">
            <span className="k">Whole-house drainage load</span>
            <span>{units.total_dfu === null ? "—" : `${units.total_dfu} DFU`}</span>
            <span className="k">Whole-house supply load</span>
            <span>{units.total_wsfu === null ? "—" : `${units.total_wsfu} WSFU`}</span>
          </div>
        </div>
        {units.runs.length > 0 && (
          <ReaderTable<PlumbingRunLoadRow> rows={units.runs} rowKey={(row) => row.tag} columns={[
            runTag("Zoom to run"),
            { key: "system", header: "System", cellClass: "reader-mono",
              cell: (r) => SYSTEM_LABEL[r.system] ?? r.system },
            { key: "dia", header: "Ø", num: true, cell: (r) => `${r.diameter_in}"` },
            { key: "load", header: "Load", num: true,
              cell: (r) => r.load === null ? "—" : `${r.load} ${r.unit}` },
            { key: "required", header: "Required", num: true,
              cell: (r) => r.required_in === null ? "—" : `${r.required_in}"` },
            { key: "status", header: "Status", cell: (r) => {
              const badge = statusBadge(r.status);
              return <span className={`badge ${badge.className}`}>{badge.label}</span>;
            } },
            { key: "serves", header: "Serves", cellClass: "reader-mono muted", cell: (r) => <>
              {r.serves.join(", ")}
              {r.unresolved.length > 0 && ` (no table row: ${r.unresolved.join(", ")})`}
            </> },
          ]} />
        )}
        <ReaderTable<PlumbingFixtureRow> rows={units.fixtures} rowKey={(row) => row.tag} columns={[
          { key: "tag", header: "Fixture", cell: (r) =>
            <TagCell tag={r.tag} index={index} onJump={jump} title="Zoom to fixture" mono /> },
          { key: "kind", header: "Kind", cellClass: "reader-mono", cell: (r) => r.symbol },
          { key: "room", header: "Room", cellClass: "reader-mono muted", cell: (r) => r.room ?? "—" },
          { key: "dfu", header: "DFU", num: true, cell: (r) => r.dfu ?? "—" },
          { key: "wsfu", header: "WSFU", num: true, cell: (r) => r.wsfu_total ?? "—" },
          { key: "hot", header: "hot", num: true, cell: (r) => r.wsfu_hot ?? "—" },
          { key: "cold", header: "cold", num: true, cell: (r) => r.wsfu_cold ?? "—" },
        ]} />
      </ReaderSection>

      <ReaderSection
        title="Cast-in concrete"
        note="The pour-day list: every sleeve that must be set before concrete, with its exact coordinates. mep.sleeve_alignment and mep.sleeve_coverage grade these positions — an offset here is a defect the pour makes permanent."
        count={takeoff.cast_in.length}
      >
        <ReaderTable<PlumbingCastInRow> rows={takeoff.cast_in} rowKey={(row) => row.tag} columns={[
          { key: "tag", header: "Sleeve", cell: (r) =>
            <TagCell tag={r.tag} index={index} onJump={jump} title="Zoom to sleeve" mono /> },
          { key: "host", header: "Host", cellClass: "reader-mono",
            cell: (r) => <>{r.host} <span className="muted">({r.host_category})</span></> },
          { key: "axis", header: "Axis", cellClass: "reader-mono", cell: (r) => r.axis },
          { key: "purpose", header: "Purpose", cellClass: "reader-mono", cell: (r) => r.purpose },
          { key: "x", header: "x", num: true, cell: (r) => `${r.x_ft}'` },
          { key: "y", header: "y", num: true, cell: (r) => `${r.y_ft}'` },
          { key: "z", header: "center z", num: true,
            cell: (r) => r.center_z_ft === null ? "—" : `${r.center_z_ft}'` },
          { key: "pipe", header: "pipe", num: true, cell: (r) => `${r.pipe_in}"` },
          { key: "sleeve", header: "sleeve", num: true, cell: (r) => `${r.sleeve_in}"` },
          { key: "serves", header: "Serves", cellClass: "reader-mono muted", cell: (r) => r.serves ?? "—" },
          { key: "offset", header: "offset", num: true,
            cell: (r) => r.offset_in === null ? "—" : `${r.offset_in}"` },
        ]} />
      </ReaderSection>

      <ReaderSection
        title="Takeoff"
        note="Pipe by the lineal foot, grouped by system, material, and diameter — what an estimator orders. Fittings are estimated from the routed geometry (bends → elbows, shared vertices → tees); no fitting element exists in the model, so the counts say so."
        count={takeoff.pipe.length}
      >
        <ReaderTable<PlumbingPipeGroup> rows={takeoff.pipe}
          rowKey={(row) => `${row.system}-${row.material}-${row.finish}-${row.diameter_in}`}
          columns={[
            { key: "system", header: "System", cellClass: "reader-mono",
              cell: (r) => SYSTEM_LABEL[r.system] ?? r.system },
            { key: "material", header: "Material", cellClass: "reader-mono", cell: (r) => r.material },
            { key: "finish", header: "Finish", cellClass: "reader-mono muted", cell: (r) => r.finish },
            { key: "dia", header: "Ø", num: true, cell: (r) => `${r.diameter_in}"` },
            { key: "runs", header: "Runs", num: true, cell: (r) => r.runs },
            { key: "length", header: "Length", num: true, cell: (r) => `${r.length_ft} lf` },
            { key: "tags", header: "Tags", cellClass: "reader-mono muted", cell: (r) => r.tags.join(", ") },
          ]} />
        {takeoff.fittings.length > 0 && (
          <ReaderTable<PlumbingFittingRow> rows={takeoff.fittings}
            rowKey={(row) => `${row.system}-${row.diameter_in}-${row.fitting}`}
            columns={[
              { key: "fitting", header: "Fitting", cell: (r) => r.fitting },
              { key: "system", header: "System", cellClass: "reader-mono",
                cell: (r) => SYSTEM_LABEL[r.system] ?? r.system },
              { key: "dia", header: "Ø", num: true, cell: (r) => `${r.diameter_in}"` },
              { key: "count", header: "Count", num: true, cell: (r) => r.count },
            ]} />
        )}
        {takeoff.hydrants.length > 0 && (
          <div className="reader-card">
            <div className="reader-card-head">
              <span className="reader-card-title">Frost-free hydrants</span>
              <span className="muted">{takeoff.hydrants.length}</span>
            </div>
            {takeoff.hydrants.map((row) => (
              <div className="kv" key={row.tag}>
                <span className="k">
                  <TagCell tag={row.tag} index={index} onJump={jump} title="Zoom to hydrant" mono />
                </span>
                <span>
                  {row.type_ref ?? "—"} · fed by{" "}
                  {row.supply_runs.length > 0 ? row.supply_runs.join(", ") : "no supply run"}
                </span>
              </div>
            ))}
          </div>
        )}
        {takeoff.accessories.length > 0 && (
          <div className="reader-card">
            <div className="reader-card-head">
              <span className="reader-card-title">In-line devices</span>
              <span className="muted">{takeoff.accessories.length}</span>
            </div>
            {takeoff.accessories.map((row) => (
              <div className="kv" key={row.tag}>
                <span className="k">
                  <TagCell tag={row.tag} index={index} onJump={jump} title="Zoom to device" mono />
                </span>
                <span>
                  {ACCESSORY_LABEL[row.kind] ?? row.kind}
                  {row.model ? ` · ${row.model}` : ""}
                  {row.pipe_ref ? ` · on ${row.pipe_ref}` : ""}
                  {row.accessible ? " · accessible" : ""}
                  {row.install_parts.length > 0
                    ? ` · kit: ${row.install_parts.join(", ")}`
                    : ""}
                </span>
              </div>
            ))}
          </div>
        )}
      </ReaderSection>
    </ReaderShell>
  );
}
