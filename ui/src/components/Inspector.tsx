import { useEffect, useRef, useState } from "react";
import { useStore } from "../state/store";
import type { Model, Opening, Stair, Wall } from "../model/types";
import { formatFtIn, openingHostWall, openingStartFromCenter, wallLength } from "../model/geometry";
import { SectionCard } from "./SectionCard";
import { DetailViewer } from "./DetailViewer";
import { StairDesigner } from "./StairDesigner";
import { Provenance } from "./Provenance";
import { FloorInspector, FootingBeddingInspector, MemberInspector, RoofInspector, SolarPanelInspector, SolidInspector } from "./DerivedInspectors";
import { locateMember } from "../model/memberIdentity";

// Strict contextual inspector (Phase 3): answers only "what can I change about the selected
// thing?" — hidden when nothing is selected. Extracted from the retired Sidebar; the
// dashboards + pickers now live in the ProjectDrawer. Resizable 320–400px.
const INSPECTOR_WIDTH_KEY = "typehaus.inspector-width";
const MIN_W = 320;
const MAX_W = 400;

function savedWidth(): number {
  try {
    const v = Number(window.localStorage.getItem(INSPECTOR_WIDTH_KEY));
    return Number.isFinite(v) && v >= MIN_W && v <= MAX_W ? v : MIN_W;
  } catch {
    return MIN_W;
  }
}

export function Inspector() {
  const model = useStore((s) => s.model);
  const selection = useStore((s) => s.selection);
  const setHover = useStore((s) => s.setHover);
  // The condition key the detail viewer should open at — the junction of the *selected* wall,
  // not whatever sorts first in the index. `null` = closed.
  const [detailKey, setDetailKey] = useState<string | null>(null);
  const [width, setWidth] = useState(savedWidth);
  const [dragging, setDragging] = useState(false);
  const widthRef = useRef(width);
  widthRef.current = width;

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: PointerEvent) => {
      // The panel is anchored to the right; dragging its left edge leftward widens it.
      const next = Math.min(MAX_W, Math.max(MIN_W, window.innerWidth - e.clientX - 12));
      setWidth(next);
    };
    const onUp = () => {
      setDragging(false);
      try {
        window.localStorage.setItem(INSPECTOR_WIDTH_KEY, String(widthRef.current));
      } catch {
        /* private browsing */
      }
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [dragging]);

  // Strict: no selection → no panel.
  if (!model || !selection.uid) return null;

  return (
    <aside
      className="inspector"
      style={{ width }}
      onMouseEnter={() => setHover(selection.uid)}
      onMouseLeave={() => setHover(null)}
    >
      <div
        className="inspector-resizer"
        onPointerDown={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        title="Drag to resize"
      />
      <SelectionInspector
        model={model}
        kind={selection.kind}
        uid={selection.uid}
        onShowDetails={setDetailKey}
      />
      {detailKey !== null && <DetailViewer initialKey={detailKey} onClose={() => setDetailKey(null)} />}
    </aside>
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
  onShowDetails: (conditionKey: string) => void;
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
      </div>
    );
  }
  if (kind === "stair") {
    const stair = (model.stairs ?? []).find((item) => item.uid === uid);
    if (!stair) return null;
    return <StairInspector model={model} stair={stair} />;
  }
  if (kind === "canvas_object") {
    const item = (model.canvas_objects ?? []).find((object) => object.uid === uid);
    if (!item) return null;
    return <CanvasObjectInspector model={model} item={item} />;
  }
  // Derived geometry, selectable in 3D since B7 (→ components/DerivedInspectors.tsx).
  if (kind === "solid") {
    const solid = (model.solids ?? []).find((item) => item.uid === uid);
    if (solid) return <SolidInspector solid={solid} />;
    // Solar panels register their picks as "solid" derived geometry but live in their
    // own model.json family.
    const panel = (model.solar_panels ?? []).find((item) => item.uid === uid);
    return panel ? <SolarPanelInspector panel={panel} /> : null;
  }
  if (kind === "footing_bedding") {
    const bedding = (model.footing_beddings ?? []).find((item) => item.uid === uid);
    return bedding ? <FootingBeddingInspector bedding={bedding} /> : null;
  }
  if (kind === "roof") {
    const roof = (model.roofs ?? []).find((item) => item.uid === uid);
    return roof ? <RoofInspector model={model} roof={roof} /> : null;
  }
  if (kind === "floor") {
    const floor = (model.floors ?? []).find((item) => item.uid === uid);
    return floor ? <FloorInspector floor={floor} /> : null;
  }
  if (kind === "member") {
    const located = locateMember(model, uid);
    return located ? <MemberInspector located={located} /> : null;
  }
  return null;
}

function CanvasObjectInspector({ model, item }: { model: Model; item: NonNullable<Model["canvas_objects"]>[number] }) {
  const applyOps = useStore((state) => state.applyOps);
  const runMacro = useStore((state) => state.runMacro);
  const toast = useStore((state) => state.toast);
  const setDetailView = useStore((state) => state.setDetailView);
  const type = model.catalog?.canvas_object_types?.find((candidate) => candidate.tag === item.type);
  const compatibleTypes = (model.catalog?.canvas_object_types ?? []).filter((candidate) => candidate.kind === item.kind);
  const [rotation, setRotation] = useState(String(item.rotation ?? 0));
  const [freeRotation, setFreeRotation] = useState(false);
  const [wall, setWall] = useState(item.attachment?.wall ?? "");
  const [face, setFace] = useState<"left" | "right">(item.attachment?.face === "right" ? "right" : "left");
  const [distance, setDistance] = useState("0");
  const [x, setX] = useState(String(item.position_m?.[0] ?? 0));
  const [y, setY] = useState(String(item.position_m?.[1] ?? 0));
  const [room, setRoom] = useState(item.room ?? "");
  const updateRotation = async () => {
    const degrees = Number(rotation);
    if (!Number.isFinite(degrees)) return toast("Rotation must be numeric", "error");
    const result = await runMacro({ macro: "rotate_placeable", storey: item.storey, tag: item.tag, degrees, free_rotation: freeRotation });
    if (!result) toast("Could not rotate object", "error");
  };
  const attach = async () => {
    const numericDistance = Number(distance);
    if (!wall || !Number.isFinite(numericDistance)) return toast("Choose a wall and distance in metres", "error");
    const result = await runMacro({ macro: "attach_placeable", storey: item.storey, tag: item.tag,
      wall, face, distance: numericDistance });
    if (!result) toast("Could not attach object", "error");
  };
  const move = async () => {
    if (!Number.isFinite(Number(x)) || !Number.isFinite(Number(y))) return toast("Position must be numeric metres", "error");
    const result = await runMacro({ macro: "move_placeable", storey: item.storey, tag: item.tag, position: [x, y] });
    if (!result) toast("Could not move object", "error");
  };
  const assignRoom = async () => {
    const result = await runMacro({ macro: "assign_placeable_room", storey: item.storey, tag: item.tag,
      room: room || null });
    if (!result) toast("Could not update room", "error");
  };
  const changeType = async (typeRef: string) => {
    if (!typeRef || typeRef === item.type) return;
    const ok = await applyOps([{ op: "update", type: item.kind, tag: item.tag, fields: { type_ref: typeRef } }]);
    if (!ok) toast("Could not change object type", "error");
  };
  const lightingControls = model.electrical?.lighting?.controls ?? [];
  const controlledBy = lightingControls.find((row) => row.tag === item.tag)?.switches ?? [];
  const controls = lightingControls
    .filter((row) => row.switches.includes(item.tag))
    .map((row) => row.tag);
  return <div>
    <h3>{type?.name ?? item.kind} · {item.tag}</h3>
    <div className="kv">
      <span className="k">Category</span><span>{item.domain}</span>
      <span className="k">Type</span><span>{item.type ?? "—"}</span>
      <span className="k">Room</span><span>{item.room ?? "unassigned"}</span>
      {item.circuit && <>
        <span className="k">Circuit</span>
        <span>
          <button className="badge" style={{ cursor: "pointer" }} title="Open the panel schedule"
            onClick={() => setDetailView("circuits")}>{item.circuit}</button>
        </span>
      </>}
      {/* The control edge, read from the same lighting take-off the E-602 sheet prints:
          a luminaire shows what switches it, a switch shows what it drives. Both directions
          come off one derivation, so the inspector cannot disagree with the schedule. */}
      {controlledBy.length > 0 && <>
        <span className="k">Controlled by</span>
        <span>
          {controlledBy.map((tag) => (
            <button key={tag} className="badge" style={{ cursor: "pointer" }}
              title="Open the lighting schedule" onClick={() => setDetailView("lighting")}>
              {tag}
            </button>
          ))}
        </span>
      </>}
      {controls.length > 0 && <>
        <span className="k">Controls</span>
        <span>
          {controls.map((tag) => (
            <button key={tag} className="badge" style={{ cursor: "pointer" }}
              title="Open the lighting schedule" onClick={() => setDetailView("lighting")}>
              {tag}
            </button>
          ))}
        </span>
      </>}
      <span className="k">Mount</span><span>{item.attachment ? `attached to ${item.attachment.wall} (${item.attachment.face})` : "free"}</span>
      <span className="k">Ports</span><span>{type?.ports.map((port) => port.service).join(", ") || "—"}</span>
      <span className="k">Source</span><span><Provenance p={item.provenance ?? null} /></span>
    </div>
    <label className="field">Product type
      <select value={item.type ?? ""} onChange={(event) => void changeType(event.target.value)}>
        {compatibleTypes.map((candidate) => <option key={candidate.tag} value={candidate.tag}>
          {candidate.tag} · {candidate.name}
        </option>)}
      </select>
    </label>
    <label className="field">Rotation ° <input value={rotation} inputMode="decimal" onChange={(event) => setRotation(event.target.value)} />
      <button className="btn" onClick={() => void updateRotation()}>Apply</button></label>
    <label className="muted" style={{ display: "block", fontSize: 11 }}><input type="checkbox" checked={freeRotation} onChange={(event) => setFreeRotation(event.target.checked)} /> Free rotation (otherwise snaps to 15°)</label>
    <div className="field" style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 4, marginTop: 8 }}>
      <input aria-label="X position in metres" value={x} inputMode="decimal" onChange={(event) => setX(event.target.value)} />
      <input aria-label="Y position in metres" value={y} inputMode="decimal" onChange={(event) => setY(event.target.value)} />
      <button className="btn" onClick={() => void move()}>Move</button>
    </div>
    <label className="field" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 4, marginTop: 8 }}>Room
      <span><select value={room} onChange={(event) => setRoom(event.target.value)}><option value="">Unassigned</option>
        {model.rooms.filter((candidate) => candidate.storey === item.storey).map((candidate) => <option key={candidate.uid} value={candidate.tag}>{candidate.tag}</option>)}</select>
        <button className="btn" onClick={() => void assignRoom()}>Apply</button></span>
    </label>
    <div className="field" style={{ display: "grid", gap: 4, marginTop: 8 }}>
      <span>Wall attachment</span>
      <select value={wall} onChange={(event) => setWall(event.target.value)}>
        <option value="">Choose wall…</option>{model.walls.filter((candidate) => candidate.storey === item.storey)
          .map((candidate) => <option key={candidate.uid} value={candidate.tag}>{candidate.tag}</option>)}</select>
      <select value={face} onChange={(event) => setFace(event.target.value as "left" | "right")}><option value="left">Left face</option><option value="right">Right face</option></select>
      <input value={distance} inputMode="decimal" aria-label="Distance from wall start in metres" onChange={(event) => setDistance(event.target.value)} />
      <button className="btn" onClick={() => void attach()}>Attach</button>
      {item.attachment && <button className="btn" onClick={() => void runMacro({ macro: "detach_placeable", storey: item.storey, tag: item.tag })}>Detach</button>}
    </div>
  </div>;
}

function OpeningInspector({ model, opening }: { model: Model; opening: Opening }) {
  const applyOps = useStore((state) => state.applyOps);
  const runMacro = useStore((state) => state.runMacro);
  const toast = useStore((state) => state.toast);
  const host = openingHostWall(model.walls, opening);
  const rough = opening.kind === "rough_opening";
  const types = rough ? [] : opening.is_door ? model.catalog?.door_types ?? [] : model.catalog?.window_types ?? [];
  const [along, setAlong] = useState(() => formatFtIn(
    openingStartFromCenter(opening.center_along_m, opening.width_m),
  ));
  const [sill, setSill] = useState(() => formatFtIn(opening.sill_m));
  const [targetHost, setTargetHost] = useState(opening.host);

  const update = async (fields: Record<string, unknown>) => {
    const ok = await applyOps([{
      op: "update", type: rough ? "RoughOpening" : opening.is_door ? "Door" : "Window", tag: opening.tag, fields,
    }]);
    if (ok) toast(`${opening.tag} updated`);
  };
  const move = async () => {
    if (!host) return;
    const result = await runMacro({ macro: "move_opening", storey: host.storey, tag: opening.tag, along });
    if (result) toast(`${opening.tag} position updated`);
  };
  const remove = async () => {
    const ok = await applyOps([{ op: "delete", type: rough ? "RoughOpening" : opening.is_door ? "Door" : "Window", tag: opening.tag }]);
    if (ok) toast(`${opening.tag} deleted`);
  };
  const rehost = async () => {
    if (!host) return;
    const result = await runMacro({ macro: "rehost_opening", storey: host.storey, tag: opening.tag,
      host: targetHost, along });
    if (result) toast(`${opening.tag} rehosted to ${targetHost}`);
  };

  return <div>
    <h3>{rough ? "Rough opening" : opening.is_door ? "Door" : "Window"} · {opening.tag}</h3>
    <div className="kv">
      <span className="k">Host wall</span><span>{host?.tag ?? opening.host}</span>
      <span className="k">Width</span><span>{formatFtIn(opening.width_m)}</span>
      <span className="k">Height</span><span>{formatFtIn(opening.height_m)}</span>
    </div>
    <label className="field-label">Start-jamb station along wall
      <span><input value={along} onChange={(event) => setAlong(event.target.value)} />
        <button className="btn" onClick={() => void move()} disabled={!host}>Move</button></span>
    </label>
    <label className="field-label">Host wall
      <span><select value={targetHost} onChange={(event) => setTargetHost(event.target.value)}>
        {model.walls.filter((wall) => wall.storey === host?.storey).map((wall) => <option key={wall.uid} value={wall.tag}>{wall.tag}</option>)}</select>
        <button className="btn" onClick={() => void rehost()} disabled={!host || targetHost === opening.host}>Rehost</button></span>
    </label>
    <label className="field-label">{opening.is_door ? "Threshold" : "Sill height"}
      <span><input value={sill} onChange={(event) => setSill(event.target.value)} />
        <button className="btn" onClick={() => void update({ sill_height: sill })}>Apply</button></span>
    </label>
    {!rough && <label className="field-label">Product type
      <select value={opening.type_ref ?? ""} onChange={(event) => void update({ type_ref: event.target.value })}>
        {types.map((type) => <option key={type.tag} value={type.tag}>{type.tag} · {formatFtIn(type.width_m)}×{formatFtIn(type.height_m)}</option>)}
      </select>
    </label>}
    {opening.is_door && <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
      <button className="btn" onClick={() => void update({ flip_hinge: !opening.flip_hinge })}>
        Flip hinge
      </button>
      <button className="btn" onClick={() => void update({ flip_swing: !opening.flip_swing })}>
        Flip swing
      </button>
    </div>}
    <button className="btn" style={{ marginTop: 8, color: "var(--error)" }} onClick={() => void remove()}>
      Delete {rough ? "rough opening" : opening.is_door ? "door" : "window"}
    </button>
    <Provenance p={opening.provenance} />
  </div>;
}

function StairInspector({ model, stair }: { model: Model; stair: Stair }) {
  return <div>
    <h3>Stair · {stair.tag}</h3>
    <StairDesigner model={model} focus={stair} />
    <Provenance p={stair.provenance} />
  </div>;
}

function WallInspector({ model, w, onShowDetails }: { model: Model; w: Wall; onShowDetails: (key: string) => void }) {
  const select = useStore((s) => s.select);
  const setHover = useStore((s) => s.setHover);
  // Which derived boundary conditions this wall participates in (→ 11b transition details).
  // Deduped by key, because that is the granularity the engine draws at: a wall meeting the
  // same roof at two openings is one detail, not two. Each key gets its own button so the
  // viewer opens on *that* junction rather than the first one in the index.
  const conditions = [...new Map((model.conditions ?? [])
    .filter((c) => c.elements.includes(w.tag))
    .map((c) => [c.key, c] as const)).values()];
  const applyOps = useStore((s) => s.applyOps);
  const toast = useStore((s) => s.toast);
  const setWorkbench = useStore((s) => s.setWorkbench);
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
      <div style={{ marginTop: 6 }}>
        <button className="btn" onClick={() => setWorkbench("assembly")}>Edit assembly…</button>
      </div>
      {conditions.length > 0 && (
        <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 4 }}>
          {conditions.map((c) => (
            <button key={c.key} className="btn" onClick={() => onShowDetails(c.key)} title={c.key}>
              {conditions.length === 1 ? "View junction detail…" : `Detail · ${c.kind}`}
            </button>
          ))}
        </div>
      )}
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
                onMouseEnter={() => setHover(o.uid)}
                onMouseLeave={() => setHover(null)}
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

export function storeyRise(model: Model, stair: Stair): number {
  const from = model.storeys.find((storey) => storey.tag === stair.storey);
  const to = model.storeys.find((storey) => storey.tag === stair.to_storey);
  return from && to ? to.elevation_m - from.elevation_m : 0;
}
