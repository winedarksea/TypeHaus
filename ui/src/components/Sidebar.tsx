import { findingsFor, useStore } from "../state/store";
import type { Finding, Model, Wall } from "../model/types";
import { formatFtIn, wallLength } from "../model/geometry";
import { SectionCard } from "./SectionCard";
import { BuildingScienceDashboard } from "./BuildingScienceDashboard";
import { SpaceDashboard } from "./SpaceDashboard";
import { RoofDesigner } from "./RoofDesigner";

// The right-hand inspector: selection details + provenance + inline findings, the
// assembly section card for a selected wall (→ 21 §Assembly inspector), the assembly
// picker, and the global findings list. Authoring (the editor mode, WP2.4d/e) attaches
// here later; this is the read affordance.
export function Sidebar() {
  const model = useStore((s) => s.model);
  const selection = useStore((s) => s.selection);

  return (
    <div className="sidebar">
      {model && selection.uid ? (
        <SelectionInspector model={model} kind={selection.kind} uid={selection.uid} />
      ) : (
        <div className="muted">Tap an element to inspect it.</div>
      )}
      {model && <AssemblyPicker model={model} />}
      {model && <BuildingScienceDashboard science={model.building_science} />}
      {model && <SpaceDashboard summary={model.space_summary} />}
      {model && <RoofDesigner model={model} />}
      {model && <FindingsPanel findings={model.findings} />}
    </div>
  );
}

function Provenance({ p }: { p: { file: string; line: number } | null }) {
  if (!p) return <span className="badge">edit in code</span>;
  return (
    <span className="prov">
      {p.file}:{p.line}
    </span>
  );
}

function InlineFindings({ model, uid }: { model: Model; uid: string }) {
  const fs = findingsFor(model, uid);
  if (fs.length === 0) return null;
  return (
    <div style={{ marginTop: 8 }}>
      {fs.map((f, i) => (
        <div key={i} className={`finding ${f.severity}`}>
          {f.message}
        </div>
      ))}
    </div>
  );
}

function SelectionInspector({
  model,
  kind,
  uid,
}: {
  model: Model;
  kind: string | null;
  uid: string;
}) {
  if (kind === "wall") {
    const w = model.walls.find((x) => x.uid === uid);
    if (!w) return null;
    return <WallInspector model={model} w={w} />;
  }
  if (kind === "opening") {
    const o = model.openings.find((x) => x.uid === uid);
    if (!o) return null;
    return (
      <div>
        <h3>{o.is_door ? "Door" : "Window"}</h3>
        <div className="kv">
          <span className="k">Tag</span>
          <span>{o.tag}</span>
          <span className="k">Width</span>
          <span>{formatFtIn(o.width_m)}</span>
          <span className="k">Height</span>
          <span>{formatFtIn(o.height_m)}</span>
          <span className="k">Sill</span>
          <span>{formatFtIn(o.sill_m)}</span>
        </div>
        <Provenance p={o.provenance} />
        <InlineFindings model={model} uid={uid} />
      </div>
    );
  }
  if (kind === "room") {
    const r = model.rooms.find((x) => x.uid === uid);
    if (!r) return null;
    const sf = (r.area_m2 * 10.7639).toFixed(0);
    return (
      <div>
        <h3>Room · {r.tag}</h3>
        <div className="kv">
          <span className="k">Occupancy</span>
          <span>{r.occupancy}</span>
          <span className="k">Area</span>
          <span>{sf} sf</span>
          <span className="k">Conditioned</span>
          <span>{r.conditioned ? "yes" : "no"}</span>
          <span className="k">Floor</span>
          <span>{r.floor_finish ?? "—"}</span>
        </div>
        <Provenance p={r.provenance} />
        <InlineFindings model={model} uid={uid} />
      </div>
    );
  }
  return null;
}

function WallInspector({ model, w }: { model: Model; w: Wall }) {
  const select = useStore((s) => s.select);
  const confirmed = w.assembly && w.assembly !== "UNCONFIGURED";
  return (
    <div>
      <h3>Wall · {w.tag}</h3>
      <div className="kv">
        <span className="k">Assembly</span>
        <span>
          {w.assembly || "—"}{" "}
          {!confirmed && <span className="badge confirm">confirm</span>}
        </span>
        <span className="k">Length</span>
        <span>{formatFtIn(wallLength(w))}</span>
        <span className="k">Height</span>
        <span>{formatFtIn(w.z1_m - w.z0_m)}</span>
        <span className="k">Storey</span>
        <span>{w.storey}</span>
        <span className="k">Members</span>
        <span>{w.members.length}</span>
      </div>
      <Provenance p={w.provenance} />
      <div style={{ height: 10 }} />
      <SectionCard layers={w.layers} title={w.assembly || "Assembly"}
        condensation={model.building_science?.condensation.find((item) => item.assembly === w.assembly)} />
      <InlineFindings model={model} uid={w.uid} />
      <div style={{ marginTop: 8 }}>
        <span className="muted">Openings hosted: </span>
        {model.openings.filter((o) => o.host === w.uid).length === 0 ? (
          <span className="muted">none</span>
        ) : (
          model.openings
            .filter((o) => o.host === w.uid)
            .map((o) => (
              <button
                key={o.uid}
                className="badge"
                onClick={() => select("opening", o.uid)}
                style={{ marginRight: 4, cursor: "pointer" }}
              >
                {o.tag}
              </button>
            ))
        )}
      </div>
    </div>
  );
}

function AssemblyPicker({ model }: { model: Model }) {
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  // Group walls by assembly with a computed representative layer count. Live R-value would
  // come from the section card feed; here we list assemblies present in the plan.
  const byAssembly = new Map<string, Wall[]>();
  for (const w of model.walls) {
    const key = w.assembly || "UNCONFIGURED";
    (byAssembly.get(key) ?? byAssembly.set(key, []).get(key)!).push(w);
  }
  return (
    <div style={{ marginTop: 16 }}>
      <h3>Assemblies</h3>
      {[...byAssembly.entries()].map(([name, walls]) => (
        <div
          key={name}
          className="finding info"
          onClick={() => select("wall", walls[0].uid)}
          style={{
            outline:
              selection.kind === "wall" &&
              walls.some((w) => w.uid === selection.uid)
                ? "2px solid var(--accent)"
                : "none",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>{name}</span>
            <span className="muted">×{walls.length}</span>
          </div>
          <span className="muted">{walls[0].layers.length} layers</span>
        </div>
      ))}
    </div>
  );
}

function FindingsPanel({ findings }: { findings: Finding[] }) {
  const select = useStore((s) => s.select);
  const model = useStore((s) => s.model);
  if (findings.length === 0)
    return (
      <div style={{ marginTop: 16 }}>
        <h3>Checks</h3>
        <span className="muted">All checks pass.</span>
      </div>
    );
  const jump = (f: Finding) => {
    const uid = f.element ?? f.elements?.[0] ?? null;
    if (!uid || !model) return;
    const kind = model.walls.some((w) => w.uid === uid)
      ? "wall"
      : model.openings.some((o) => o.uid === uid)
        ? "opening"
        : model.rooms.some((r) => r.uid === uid)
          ? "room"
          : null;
    if (kind) select(kind, uid);
  };
  return (
    <div style={{ marginTop: 16 }}>
      <h3>Checks · {findings.length}</h3>
      {findings.map((f, i) => (
        <div key={i} className={`finding ${f.severity}`} onClick={() => jump(f)}>
          {f.code && <b>{f.code} </b>}
          {f.message}
        </div>
      ))}
    </div>
  );
}
