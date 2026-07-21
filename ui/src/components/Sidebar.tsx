import { useState } from "react";
import { findingsFor, useStore, visibleFindings } from "../state/store";
import type { Finding, Model, Opening, Stair, Wall } from "../model/types";
import { formatFtIn, openingHostWall, wallLength } from "../model/geometry";
import { SectionCard } from "./SectionCard";
import { BuildingScienceDashboard } from "./BuildingScienceDashboard";
import { SpaceDashboard } from "./SpaceDashboard";
import { RoofDesigner } from "./RoofDesigner";
import { StairDesigner } from "./StairDesigner";
import { AssemblyEditor } from "./AssemblyEditor";
import { DetailViewer } from "./DetailViewer";

// The right-hand inspector: selection details + provenance + inline findings, the
// assembly section card for a selected wall (→ 21 §Assembly inspector), the assembly
// picker + editor (WP2.4d/e authoring), and the global findings list.
export function Sidebar() {
  const model = useStore((s) => s.model);
  const selection = useStore((s) => s.selection);
  const [editingAssemblies, setEditingAssemblies] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="sidebar">
      {model && selection.uid ? (
        <SelectionInspector model={model} kind={selection.kind} uid={selection.uid} onShowDetails={() => setShowDetails(true)} />
      ) : (
        <div className="muted">Tap an element to inspect it.</div>
      )}
      {model && (
        <div style={{ marginTop: 12 }}>
          <button className="btn" onClick={() => setShowDetails(true)}>Transition details…</button>
        </div>
      )}
      {model && <AssemblyPicker model={model} onEdit={() => setEditingAssemblies(true)} />}
      {model && <BuildingScienceDashboard science={model.building_science} />}
      {model && <SpaceDashboard summary={model.space_summary} />}
      {model && <StairDesigner model={model} />}
      {model && <RoofDesigner model={model} />}
      {model && <FindingsPanel findings={model.findings} />}
      {editingAssemblies && <AssemblyEditor onClose={() => setEditingAssemblies(false)} />}
      {showDetails && <DetailViewer onClose={() => setShowDetails(false)} />}
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
  onShowDetails,
}: {
  model: Model;
  kind: string | null;
  uid: string;
  onShowDetails: () => void;
}) {
  if (kind === "wall") {
    const w = model.walls.find((x) => x.uid === uid);
    if (!w) return null;
    return <WallInspector model={model} w={w} onShowDetails={onShowDetails} />;
  }
  if (kind === "opening") {
    const o = model.openings.find((x) => x.uid === uid);
    if (!o) return null;
    return <OpeningInspector key={o.uid} model={model} opening={o} />;
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
  if (kind === "stair") {
    const stair = (model.stairs ?? []).find((item) => item.uid === uid);
    if (!stair) return null;
    return <StairInspector model={model} stair={stair} />;
  }
  return null;
}

function OpeningInspector({ model, opening }: { model: Model; opening: Opening }) {
  const applyOps = useStore((state) => state.applyOps);
  const runMacro = useStore((state) => state.runMacro);
  const toast = useStore((state) => state.toast);
  const host = openingHostWall(model.walls, opening);
  const types = opening.is_door ? model.catalog?.door_types ?? [] : model.catalog?.window_types ?? [];
  const [along, setAlong] = useState(() => formatFtIn(opening.center_along_m));
  const [sill, setSill] = useState(() => formatFtIn(opening.sill_m));

  const update = async (fields: Record<string, unknown>) => {
    const ok = await applyOps([{
      op: "update", type: opening.is_door ? "Door" : "Window", tag: opening.tag, fields,
    }]);
    if (ok) toast(`${opening.tag} updated`);
  };
  const move = async () => {
    if (!host) return;
    const result = await runMacro({ macro: "move_opening", storey: host.storey, tag: opening.tag, along });
    if (result) toast(`${opening.tag} position updated`);
  };
  const remove = async () => {
    const ok = await applyOps([{ op: "delete", type: opening.is_door ? "Door" : "Window", tag: opening.tag }]);
    if (ok) toast(`${opening.tag} deleted`);
  };

  return <div>
    <h3>{opening.is_door ? "Door" : "Window"} · {opening.tag}</h3>
    <div className="kv">
      <span className="k">Host wall</span><span>{host?.tag ?? opening.host}</span>
      <span className="k">Width</span><span>{formatFtIn(opening.width_m)}</span>
      <span className="k">Height</span><span>{formatFtIn(opening.height_m)}</span>
    </div>
    <label className="field-label">Position along wall
      <span><input value={along} onChange={(event) => setAlong(event.target.value)} />
        <button className="btn" onClick={() => void move()} disabled={!host}>Move</button></span>
    </label>
    <label className="field-label">{opening.is_door ? "Threshold" : "Sill height"}
      <span><input value={sill} onChange={(event) => setSill(event.target.value)} />
        <button className="btn" onClick={() => void update({ sill_height: sill })}>Apply</button></span>
    </label>
    <label className="field-label">Product type
      <select value={opening.type_ref ?? ""} onChange={(event) => void update({ type_ref: event.target.value })}>
        {types.map((type) => <option key={type.tag} value={type.tag}>{type.tag} · {formatFtIn(type.width_m)}×{formatFtIn(type.height_m)}</option>)}
      </select>
    </label>
    {opening.is_door && <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
      <button className="btn" onClick={() => void update({ flip_hinge: !opening.flip_hinge })}>
        Flip hinge
      </button>
      <button className="btn" onClick={() => void update({ flip_swing: !opening.flip_swing })}>
        Flip swing
      </button>
    </div>}
    <button className="btn" style={{ marginTop: 8, color: "var(--error)" }} onClick={() => void remove()}>
      Delete {opening.is_door ? "door" : "window"}
    </button>
    <Provenance p={opening.provenance} />
    <InlineFindings model={model} uid={opening.uid} />
  </div>;
}

function StairInspector({ model, stair }: { model: Model; stair: Stair }) {
  const rise = storeyRise(model, stair);
  return <div>
    <h3>Stair · {stair.tag}</h3>
    <div className="kv">
      <span className="k">Route</span><span>{stair.storey} → {stair.to_storey}</span>
      <span className="k">Rise</span><span>{formatFtIn(rise)}</span>
      <span className="k">Resolved</span><span>{stair.riser_count} risers · {formatFtIn(stair.tread_depth_m)} tread · {stair.layout.replaceAll("_", " ")}{stair.winder_count ? ` · ${stair.winder_count} winders` : ""}</span>
      <span className="k">Framing</span><span>{stair.members.length} members</span>
    </div>
    <Provenance p={stair.provenance} />
    <InlineFindings model={model} uid={stair.uid} />
  </div>;
}

function WallInspector({ model, w, onShowDetails }: { model: Model; w: Wall; onShowDetails: () => void }) {
  const select = useStore((s) => s.select);
  // Does this wall participate in any derived boundary condition? (→ 11b transition details)
  const inCondition = (model.conditions ?? []).some((c) => c.elements.includes(w.tag));
  const applyOps = useStore((s) => s.applyOps);
  const toast = useStore((s) => s.toast);
  const confirmed = w.assembly && w.assembly !== "UNCONFIGURED";
  const assemblies = model.catalog?.assemblies ?? [];
  const assignAssembly = async (tag: string) => {
    const ok = await applyOps([{ op: "update", type: "Wall", tag: w.tag, fields: { assembly: tag } }]);
    if (ok) toast(`${w.tag} → ${tag}`);
  };
  return (
    <div>
      <h3>Wall · {w.tag}</h3>
      <div className="kv">
        <span className="k">Assembly</span>
        <span>
          {assemblies.length > 0 ? (
            <select value={w.assembly || ""} onChange={(e) => void assignAssembly(e.target.value)}>
              {!w.assembly && <option value="">—</option>}
              {assemblies.map((a) => <option key={a.tag} value={a.tag}>{a.tag}</option>)}
            </select>
          ) : (w.assembly || "—")}{" "}
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
      {inCondition && (
        <div style={{ marginTop: 6 }}>
          <button className="btn" onClick={onShowDetails}>View junction detail…</button>
        </div>
      )}
      <InlineFindings model={model} uid={w.uid} />
      <div style={{ marginTop: 8 }}>
        <span className="muted">Openings hosted: </span>
        {model.openings.filter((o) => o.host === w.tag).length === 0 ? (
          <span className="muted">none</span>
        ) : (
          model.openings
            .filter((o) => o.host === w.tag)
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

function AssemblyPicker({ model, onEdit }: { model: Model; onEdit: () => void }) {
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Assemblies</h3>
        <button className="btn" onClick={onEdit}>Edit</button>
      </div>
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
  const visible = visibleFindings(findings);
  if (visible.length === 0)
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
          : (model.stairs ?? []).some((stair) => stair.uid === uid)
            ? "stair"
            : null;
    if (kind) select(kind, uid);
  };
  return (
    <div style={{ marginTop: 16 }}>
      <h3>Checks · {visible.length}</h3>
      {visible.map((f, i) => (
        <div key={i} className={`finding ${f.severity}`} onClick={() => jump(f)}>
          {f.code && <b>{f.code} </b>}
          {f.message}
        </div>
      ))}
    </div>
  );
}

function storeyRise(model: Model, stair: Stair): number {
  const from = model.storeys.find((storey) => storey.tag === stair.storey);
  const to = model.storeys.find((storey) => storey.tag === stair.to_storey);
  return from && to ? to.elevation_m - from.elevation_m : 0;
}
