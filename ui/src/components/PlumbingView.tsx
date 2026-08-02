import { useMemo, useState } from "react";
import { useStore } from "../state/store";
import { uidByTag } from "../model/tagIndex";
import type { Plumbing, PlumbingRiserRun } from "../model/types";
import { ReaderSection, ReaderShell } from "./ReaderShell";

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
  const model = useStore((s) => s.model);
  const setDetailView = useStore((s) => s.setDetailView);
  const zoomToUid = useStore((s) => s.zoomToUid);
  const [filter, setFilter] = useState("");

  const baseIndex = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const plumbing: Plumbing | null = model?.plumbing ?? null;

  // A routed run has no record of its own in the scene — its geometry arrives as
  // per-segment solids tagged `<RUN>-S1[B1]`. Alias each run tag to its first segment
  // solid so the riser's zoom buttons land somewhere real.
  const index = useMemo(() => {
    const aliased = new Map(baseIndex);
    for (const run of plumbing?.riser ?? []) {
      if (aliased.has(run.tag)) continue;
      for (const [tag, uid] of baseIndex) {
        if (tag.startsWith(`${run.tag}-S`)) {
          aliased.set(run.tag, uid);
          break;
        }
      }
    }
    return aliased;
  }, [baseIndex, plumbing]);

  const needle = filter.trim().toLowerCase();
  const riser = useMemo(() => {
    const rows = plumbing?.riser ?? [];
    return needle
      ? rows.filter((row) =>
          `${row.tag} ${row.system} ${row.material ?? ""} ${row.serves.join(" ")} ${row.wall_refs.join(" ")}`
            .toLowerCase().includes(needle))
      : rows;
  }, [plumbing, needle]);

  if (!model) return null;

  // Same jump contract as the other readers: zoom the plan, then get out of its way.
  const jump = (tag: string) => {
    const uid = index.get(tag);
    if (uid) {
      zoomToUid(uid);
      setDetailView("none");
    }
  };

  if (!plumbing) {
    return (
      <ReaderShell title="Plumbing" subtitle="no plumbing data" onClose={() => setDetailView("none")}>
        <div className="muted">
          This model carries no plumbing take-off — rebuild with a current engine.
        </div>
      </ReaderShell>
    );
  }

  const { fixture_units: units, takeoff } = plumbing;
  const systems = Array.from(new Set(plumbing.riser.map((run) => run.system)));

  return (
    <ReaderShell
      title="Plumbing"
      subtitle={`${plumbing.riser.length} runs · ${units.fixtures.length} fixtures · ${takeoff.cast_in.length} cast-in sleeves`}
      onClose={() => setDetailView("none")}
      toolbar={
        <input
          value={filter}
          placeholder="Filter runs…"
          onChange={(event) => setFilter(event.target.value)}
          aria-label="Filter plumbing runs"
          style={{ padding: "5px 7px", minWidth: 180 }}
        />
      }
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
        <div className="reader-table-scroll">
          <table className="reader-table">
            <thead>
              <tr>
                <th>Run</th><th>Storey</th><th>System</th><th>Material</th>
                <th className="num-col">Ø</th><th className="num-col">Length</th>
                <th>Hosted in</th><th>Serves</th>
              </tr>
            </thead>
            <tbody>
              {riser.map((run) => (
                <tr key={run.tag}>
                  <td>
                    <button className="reader-tag" onClick={() => jump(run.tag)}
                      disabled={!index.has(run.tag)} title="Zoom to run">
                      <span className="reader-mono">{run.tag}</span>
                    </button>
                  </td>
                  <td className="reader-mono">{run.storey}</td>
                  <td className="reader-mono">{SYSTEM_LABEL[run.system] ?? run.system}</td>
                  <td className="reader-mono">{run.material ?? "—"}</td>
                  <td className="num-col">{run.diameter_in}"</td>
                  <td className="num-col">{run.length_ft} lf</td>
                  <td className="reader-mono muted">{run.wall_refs.length > 0 ? run.wall_refs.join(", ") : "—"}</td>
                  <td className="reader-mono muted">{run.serves.length > 0 ? run.serves.join(", ") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
          <div className="reader-table-scroll">
            <table className="reader-table">
              <thead>
                <tr>
                  <th>Run</th><th>System</th><th className="num-col">Ø</th>
                  <th className="num-col">Load</th><th className="num-col">Required</th>
                  <th>Status</th><th>Serves</th>
                </tr>
              </thead>
              <tbody>
                {units.runs.map((row) => {
                  const badge = statusBadge(row.status);
                  return (
                    <tr key={row.tag}>
                      <td>
                        <button className="reader-tag" onClick={() => jump(row.tag)}
                          disabled={!index.has(row.tag)} title="Zoom to run">
                          <span className="reader-mono">{row.tag}</span>
                        </button>
                      </td>
                      <td className="reader-mono">{SYSTEM_LABEL[row.system] ?? row.system}</td>
                      <td className="num-col">{row.diameter_in}"</td>
                      <td className="num-col">{row.load === null ? "—" : `${row.load} ${row.unit}`}</td>
                      <td className="num-col">{row.required_in === null ? "—" : `${row.required_in}"`}</td>
                      <td><span className={`badge ${badge.className}`}>{badge.label}</span></td>
                      <td className="reader-mono muted">
                        {row.serves.join(", ")}
                        {row.unresolved.length > 0 && ` (no table row: ${row.unresolved.join(", ")})`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <div className="reader-table-scroll">
          <table className="reader-table">
            <thead>
              <tr>
                <th>Fixture</th><th>Kind</th><th>Room</th>
                <th className="num-col">DFU</th><th className="num-col">WSFU</th>
                <th className="num-col">hot</th><th className="num-col">cold</th>
              </tr>
            </thead>
            <tbody>
              {units.fixtures.map((row) => (
                <tr key={row.tag}>
                  <td>
                    <button className="reader-tag" onClick={() => jump(row.tag)}
                      disabled={!index.has(row.tag)} title="Zoom to fixture">
                      <span className="reader-mono">{row.tag}</span>
                    </button>
                  </td>
                  <td className="reader-mono">{row.symbol}</td>
                  <td className="reader-mono muted">{row.room ?? "—"}</td>
                  <td className="num-col">{row.dfu ?? "—"}</td>
                  <td className="num-col">{row.wsfu_total ?? "—"}</td>
                  <td className="num-col">{row.wsfu_hot ?? "—"}</td>
                  <td className="num-col">{row.wsfu_cold ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ReaderSection>

      <ReaderSection
        title="Cast-in concrete"
        note="The pour-day list: every sleeve that must be set before concrete, with its exact coordinates. mep.sleeve_alignment and mep.sleeve_coverage grade these positions — an offset here is a defect the pour makes permanent."
        count={takeoff.cast_in.length}
      >
        <div className="reader-table-scroll">
          <table className="reader-table">
            <thead>
              <tr>
                <th>Sleeve</th><th>Host</th><th>Axis</th><th>Purpose</th>
                <th className="num-col">x</th><th className="num-col">y</th>
                <th className="num-col">center z</th>
                <th className="num-col">pipe</th><th className="num-col">sleeve</th>
                <th>Serves</th><th className="num-col">offset</th>
              </tr>
            </thead>
            <tbody>
              {takeoff.cast_in.map((row) => (
                <tr key={row.tag}>
                  <td>
                    <button className="reader-tag" onClick={() => jump(row.tag)}
                      disabled={!index.has(row.tag)} title="Zoom to sleeve">
                      <span className="reader-mono">{row.tag}</span>
                    </button>
                  </td>
                  <td className="reader-mono">{row.host} <span className="muted">({row.host_category})</span></td>
                  <td className="reader-mono">{row.axis}</td>
                  <td className="reader-mono">{row.purpose}</td>
                  <td className="num-col">{row.x_ft}'</td>
                  <td className="num-col">{row.y_ft}'</td>
                  <td className="num-col">{row.center_z_ft === null ? "—" : `${row.center_z_ft}'`}</td>
                  <td className="num-col">{row.pipe_in}"</td>
                  <td className="num-col">{row.sleeve_in}"</td>
                  <td className="reader-mono muted">{row.serves ?? "—"}</td>
                  <td className="num-col">{row.offset_in === null ? "—" : `${row.offset_in}"`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ReaderSection>

      <ReaderSection
        title="Takeoff"
        note="Pipe by the lineal foot, grouped by system, material, and diameter — what an estimator orders. Fittings are estimated from the routed geometry (bends → elbows, shared vertices → tees); no fitting element exists in the model, so the counts say so."
        count={takeoff.pipe.length}
      >
        <div className="reader-table-scroll">
          <table className="reader-table">
            <thead>
              <tr>
                <th>System</th><th>Material</th><th>Finish</th><th className="num-col">Ø</th>
                <th className="num-col">Runs</th><th className="num-col">Length</th><th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {takeoff.pipe.map((row) => (
                <tr key={`${row.system}-${row.material}-${row.finish}-${row.diameter_in}`}>
                  <td className="reader-mono">{SYSTEM_LABEL[row.system] ?? row.system}</td>
                  <td className="reader-mono">{row.material}</td>
                  <td className="reader-mono muted">{row.finish}</td>
                  <td className="num-col">{row.diameter_in}"</td>
                  <td className="num-col">{row.runs}</td>
                  <td className="num-col">{row.length_ft} lf</td>
                  <td className="reader-mono muted">{row.tags.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {takeoff.fittings.length > 0 && (
          <div className="reader-table-scroll">
            <table className="reader-table">
              <thead>
                <tr><th>Fitting</th><th>System</th><th className="num-col">Ø</th><th className="num-col">Count</th></tr>
              </thead>
              <tbody>
                {takeoff.fittings.map((row) => (
                  <tr key={`${row.system}-${row.diameter_in}-${row.fitting}`}>
                    <td>{row.fitting}</td>
                    <td className="reader-mono">{SYSTEM_LABEL[row.system] ?? row.system}</td>
                    <td className="num-col">{row.diameter_in}"</td>
                    <td className="num-col">{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
                  <button className="reader-tag" onClick={() => jump(row.tag)}
                    disabled={!index.has(row.tag)} title="Zoom to hydrant">
                    <span className="reader-mono">{row.tag}</span>
                  </button>
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
                  <button className="reader-tag" onClick={() => jump(row.tag)}
                    disabled={!index.has(row.tag)} title="Zoom to device">
                    <span className="reader-mono">{row.tag}</span>
                  </button>
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
