import { Fragment, useEffect, useRef, useState } from "react";
import { useStore } from "../state/store";
import type { Model, Opening, Stair, Wall } from "../model/types";
import { formatFtIn, openingHostWall, openingStartFromCenter, wallLength } from "../model/geometry";
import { SectionCard } from "./SectionCard";
import { DetailViewer } from "./DetailViewer";
import { StairDesigner } from "./StairDesigner";
import { Provenance } from "./Provenance";
import { ProductRows } from "./ProductRows";
import { productFor } from "../model/products";
import { FloorInspector, FootingBeddingInspector, LightRunInspector, MemberUidInspector, RoofInspector, SolarPanelInspector, SolidInspector } from "./DerivedInspectors";
import { locateUid } from "../state/locate";
import { useIsCompact } from "../hooks/useBreakpoint";
import { Sheet } from "./ui/Sheet";
import { CanvasObjectInspector } from "./inspector/CanvasObjectInspector";
import { WallPinControls } from "./inspector/WallPinControls";

// Strict contextual inspector (Phase 3): answers only "what can I change about the selected
// thing?" — hidden when nothing is selected. Extracted from the retired Sidebar; the
// dashboards + pickers now live in the ProjectDrawer. Resizable 320–400px.
const INSPECTOR_WIDTH_KEY = "typehaus.inspector-width";
const MIN_W = 320;
const MAX_W = 400;
/** Gutter between the panel and the shell's right edge — mirrors --gutter. */
const GUTTER_PX = 12;
/** The drawing must never be squeezed to a strip, whatever the viewport. */
const MIN_CANVAS_PX = 320;

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
  const asideRef = useRef<HTMLElement>(null);
  const isCompact = useIsCompact();
  const select = useStore((s) => s.select);
  const [dragging, setDragging] = useState(false);
  const widthRef = useRef(width);
  widthRef.current = width;

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: PointerEvent) => {
      // Measure the shell, not the window: the gutter varies per breakpoint, so a fixed offset
      // from the window edge would drift. Also cap against the canvas so a drag can never
      // squeeze the drawing away entirely.
      const shell = asideRef.current?.offsetParent?.getBoundingClientRect();
      const shellRight = shell?.right ?? window.innerWidth;
      const shellWidth = shell?.width ?? window.innerWidth;
      const maxWidth = Math.min(MAX_W, Math.max(MIN_W, shellWidth - MIN_CANVAS_PX));
      setWidth(Math.min(maxWidth, Math.max(MIN_W, shellRight - e.clientX - GUTTER_PX)));
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

  const visible = model !== null && selection.uid !== null;

  // Publish the live width so chrome that must clear this panel can position off it — anything
  // anchored to the right edge reads --inspector-w rather than hardcoding the panel's minimum.
  //
  // Reverts to the token default while the panel is hidden: the reserved gutter is only
  // honest about a panel that is actually on screen.
  useEffect(() => {
    const root = document.documentElement.style;
    if (!visible) return;
    root.setProperty("--inspector-w", `${width}px`);
    return () => { root.removeProperty("--inspector-w"); };
  }, [width, visible]);

  // Strict: no selection → no panel.
  if (!model || !selection.uid) return null;

  // A params-generated element has no writeback destination: every field edit and macro in
  // this panel would 422 on commit. Say so and disable the controls, rather than offering
  // affordances that can only fail. `editable === null` (no provenance captured) is unknown,
  // not forbidden — those panels stay live and fail at commit as before.
  const located = locateUid(model, selection.uid);
  const readOnly = located?.editable === false;

  const body = (
    <SelectionInspector
      model={model}
      kind={selection.kind}
      uid={selection.uid}
      onShowDetails={setDetailKey}
    />
  );
  // One fieldset rather than a `disabled` prop threaded through a dozen sub-inspectors: it
  // covers every control natively and can't drift as new fields are added.
  const guarded = readOnly ? (
    <>
      <p className="inspector-readonly" role="note">
        Params-generated — edit {located?.source ?? "its source"} to change this.
      </p>
      <fieldset className="inspector-readonly-fields" disabled>{body}</fieldset>
    </>
  ) : body;

  // On a phone the inspector is a sheet like the other panels. Closing it clears the
  // selection, because a selection you cannot see is the thing that makes the next tap
  // do something unexpected.
  if (isCompact) {
    return (
      <>
        <Sheet title="Selection" onClose={() => select(null, null)}>{guarded}</Sheet>
        {detailKey !== null && <DetailViewer initialKey={detailKey} onClose={() => setDetailKey(null)} />}
      </>
    );
  }

  return (
    <aside
      ref={asideRef}
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
      {guarded}
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
    // A room's floor is not always one finish. Zones cut their own area out of the field, so
    // the field row reads NET of them — otherwise the panel says "lvp" over a room where 411
    // of 766 sf is polished concrete. `source_ref` names the slab a derived zone came from,
    // which is the answer to "why is this band different".
    const zones = r.finish_zones ?? [];
    const zoneSf = zones.reduce((total, zone) => total + zone.area_m2, 0) * 10.7639;
    const fieldSf = Math.max(r.area_m2 * 10.7639 - zoneSf, 0);
    return (
      <div>
        <h3>Room · {r.tag}</h3>
        <div className="kv">
          <span className="k">Occupancy</span>
          <span>{r.occupancy}</span>
          <span className="k">Area</span>
          <span>{sf} sf</span>
          {/* A raked room is two areas: the floor that gets built, and the part of it with
              5'-0" over it. Only shown where a roof actually takes some away. */}
          {r.head_limited_area_m2 != null && r.area_m2 - r.head_limited_area_m2 > 0.5 && (
            <>
              <span className="k">Over 5'-0" head</span>
              <span>{(r.head_limited_area_m2 * 10.7639).toFixed(0)} sf</span>
            </>
          )}
          <span className="k">Conditioned</span>
          <span>{r.conditioned ? "yes" : "no"}</span>
          <span className="k">Floor</span>
          <span>
            {r.floor_finish ?? "—"}
            {zones.length > 0 && r.floor_finish ? ` · ${fieldSf.toFixed(0)} sf field` : ""}
          </span>
          {zones.map((zone, index) => (
            <Fragment key={`${zone.material_ref}-${index}`}>
              <span className="k">↳ zone</span>
              <span>
                {zone.material_ref} · {(zone.area_m2 * 10.7639).toFixed(0)} sf
                {zone.source_ref ? ` · from ${zone.source_ref}` : ""}
              </span>
            </Fragment>
          ))}
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
    return <CanvasObjectInspector key={item.uid} model={model} item={item} />;
  }
  // Derived geometry, selectable in 3D since B7 (→ components/DerivedInspectors.tsx).
  if (kind === "solid") {
    const solid = (model.solids ?? []).find((item) => item.uid === uid);
    if (solid) return <SolidInspector solid={solid} />;
    // Solar panels and light runs register their picks as "solid" derived geometry but
    // live in their own model.json families.
    const panel = (model.solar_panels ?? []).find((item) => item.uid === uid);
    if (panel) return <SolarPanelInspector panel={panel} />;
    const run = (model.light_runs ?? []).find((item) => item.uid === uid);
    return run ? <LightRunInspector run={run} /> : null;
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
    return <MemberUidInspector model={model} uid={uid} />;
  }
  return null;
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
  // `types` is already the right catalog for this opening's family, so the unit's own
  // entry — and the product it names — comes out of it rather than a second lookup.
  const openingType = types.find((candidate) => candidate.tag === opening.type_ref);

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
      <ProductRows product={productFor(model.catalog, openingType?.product_ref)} />
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
    {/* The delete action owns its row: <Provenance> is an inline span, so a bare button
        before it left the source path sitting alongside "Delete door". */}
    <div style={{ marginTop: 8 }}>
      <button className="btn" style={{ color: "var(--error)" }} onClick={() => void remove()}>
        Delete {rough ? "rough opening" : opening.is_door ? "door" : "window"}
      </button>
    </div>
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
    const ok = await applyOps([
      { op: "update", type: w.kind ?? "Wall", tag: w.tag, fields: { assembly: tag } },
    ]);
    if (ok) toast(`${w.tag} → ${tag}`);
  };
  return (
    <div>
      <h3>Wall · {w.tag}</h3>
      {/* The assembly picker is a control, not a fact, so it gets a labelled field of its
          own rather than a cell in the kv grid: a <select> cannot shrink below its widest
          option, and inside a grid cell that starved the key column to 0px and painted
          every label underneath its own value. */}
      {assemblies.length > 0 ? (
        <label className="field-label">
          <span className="field-label-head">
            Assembly
            {!confirmed && <span className="badge confirm">confirm</span>}
          </span>
          <span>
            <select value={w.assembly || ""} onChange={(e) => void assignAssembly(e.target.value)}>
              {!w.assembly && <option value="">—</option>}
              {assemblies.map((a) => <option key={a.tag} value={a.tag}>{a.tag}</option>)}
            </select>
          </span>
        </label>
      ) : (
        <div className="kv">
          <span className="k">Assembly</span>
          <span>{w.assembly || "—"}{" "}
            {!confirmed && <span className="badge confirm">confirm</span>}</span>
        </div>
      )}
      <div className="kv">
        <span className="k">Length</span>
        <span>{formatFtIn(wallLength(w))}</span>
        <span className="k">Height</span>
        <span>{formatFtIn(w.z1_m - w.z0_m)}</span>
        <span className="k">Storey</span>
        <span>{w.storey}</span>
        <span className="k">Members</span>
        <span>{w.members.length}</span>
      </div>
      <WallPinControls model={model} w={w} />
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
