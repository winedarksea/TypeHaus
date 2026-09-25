// The inspector for a placed object (furniture, fixture, appliance, device). Rendered with
// `key={item.uid}` so selecting another object starts fresh; every editable field is a
// useSyncedField, so an edit made elsewhere (a drag, a nudge, the file) shows up here live.
import { useState } from "react";
import type { Impact } from "../../engine/EngineClient";
import type { CanvasObject, Model } from "../../model/types";
import { formatFtIn, parseFtIn } from "../../model/geometry";
import { productFor } from "../../model/products";
import { useStore } from "../../state/store";
import { ProductRows } from "../ProductRows";
import { Provenance } from "../Provenance";
import { stationOnWall, wallFrame } from "../plan/wallSnap";
import { useSyncedField } from "./useSyncedField";

const NO_IMPACTS: Impact[] = [];
const IMPACT_LABELS: Record<Impact["kind"], string> = {
  carried: "carried", left_behind: "left behind", needs_review: "needs review",
};

export function CanvasObjectInspector({ model, item }: { model: Model; item: CanvasObject }) {
  const runMacro = useStore((state) => state.runMacro);
  const commitTransform = useStore((state) => state.commitTransform);
  const toast = useStore((state) => state.toast);
  const setDetailView = useStore((state) => state.setDetailView);
  const pending = useStore((state) => state.pendingTransforms[item.uid]);
  const impacts = useStore((state) => state.sessionEdits.impacts[item.tag] ?? NO_IMPACTS);
  const type = model.catalog?.canvas_object_types?.find((candidate) => candidate.tag === item.type);
  const compatibleTypes = (model.catalog?.canvas_object_types ?? []).filter((candidate) => candidate.kind === item.kind);
  const position = pending?.position_m ?? item.position_m;
  const hostWall = item.attachment ? model.walls.find((candidate) => candidate.tag === item.attachment!.wall) : undefined;
  const hostFrame = hostWall ? wallFrame(hostWall) : null;

  // Every dimension in this panel is ft-in, like the rest of the app. Edits go back out as
  // *canonical* ft-in strings (parse to validate, format to normalize), not as metres: the
  // engine's Length.parse keeps the authored unit, so a plan file written in feet stays in
  // feet instead of gaining an `m(1.8796)` where an `ft(6, 2)` belongs.
  const [rotation, setRotation, rotationField] = useSyncedField(String(pending?.rotation ?? item.rotation ?? 0));
  const [freeRotation, setFreeRotation] = useState(false); // a gesture option, not model state
  const [x, setX, xField] = useSyncedField(formatFtIn(position?.[0] ?? 0));
  const [y, setY, yField] = useSyncedField(formatFtIn(position?.[1] ?? 0));
  const [wall, setWall, wallField] = useSyncedField(item.attachment?.wall ?? "");
  const [face, setFace, faceField] = useSyncedField(item.attachment?.face === "right" ? "right" : "left");
  const [distance, setDistance, distanceField] = useSyncedField(
    hostFrame && position ? formatFtIn(stationOnWall(hostFrame, position)) : "0\"");
  const mount = item.mount ?? null;
  // `z_m` is an *absolute* height (storey datum + mount), and this field speaks above-floor —
  // a basement fixture would otherwise read as a negative height. Prefill from the authored
  // elevation when there is one, else from the resolved height rebased onto its own storey
  // (a pendant authored as a drop below the ceiling has no elevation of its own).
  const storeyElevationM = model.storeys.find((candidate) => candidate.tag === item.storey)?.elevation_m ?? 0;
  const [elevation, setElevation, elevationField] = useSyncedField(
    formatFtIn(mount?.elevation_m ?? ((item.z_m ?? 0) - storeyElevationM)));
  const [room, setRoom, roomField] = useSyncedField(item.room ?? "");

  const updateRotation = async () => {
    const degrees = Number(rotation);
    if (!Number.isFinite(degrees)) return toast("Rotation must be numeric", "error");
    rotationField.reset();
    await commitTransform(item, { rotation: degrees },
      { macro: "rotate_placeable", storey: item.storey, tag: item.tag, degrees, free_rotation: freeRotation });
  };
  const attach = async () => {
    const distanceM = parseFtIn(distance);
    if (!wall || distanceM === null) return toast("Choose a wall and a distance like 3'-6\"", "error");
    wallField.reset(); faceField.reset(); distanceField.reset();
    await runMacro({ macro: "attach_placeable", storey: item.storey, tag: item.tag,
      wall, face: face === "right" ? "right" : "left", distance: formatFtIn(distanceM) });
  };
  const move = async () => {
    const [xm, ym] = [parseFtIn(x), parseFtIn(y)];
    if (xm === null || ym === null) return toast("Position must be a length like 12'-6\"", "error");
    xField.reset(); yField.reset();
    await commitTransform(item, { position_m: [xm, ym] },
      { macro: "move_placeable", storey: item.storey, tag: item.tag, position: [formatFtIn(xm), formatFtIn(ym)] });
  };
  // The one edit that had no path at all before: a wall sconce authored at 46" could only be
  // raised by hand-editing the plan file.
  const setMountHeight = async () => {
    const elevationM = parseFtIn(elevation);
    if (elevationM === null || elevationM < 0) return toast("Height must be a length like 6'-0\"", "error");
    elevationField.reset();
    await runMacro({ macro: "set_placeable_mount", storey: item.storey, tag: item.tag,
      elevation: formatFtIn(elevationM) });
  };
  const assignRoom = async () => {
    roomField.reset();
    await runMacro({ macro: "assign_placeable_room", storey: item.storey, tag: item.tag, room: room || null });
  };
  const changeType = async (typeRef: string) => {
    if (!typeRef || typeRef === item.type) return;
    // A macro, not a raw type_ref PATCH: the engine re-anchors a wall-backed unit's
    // mounted face under the footprint change and reports what the swap touched.
    await runMacro({ macro: "retype_placeable", storey: item.storey, tag: item.tag, type_ref: typeRef });
  };
  const onEnterMove = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") { event.preventDefault(); void move(); }
  };
  const lightingControls = model.electrical?.lighting?.controls ?? [];
  const controlledBy = lightingControls.find((row) => row.tag === item.tag)?.switches ?? [];
  const controls = lightingControls
    .filter((row) => row.switches.includes(item.tag))
    .map((row) => row.tag);
  const scheduleBadges = (tags: string[], view: "lighting") => tags.map((tag) => (
    <button key={tag} className="badge" style={{ cursor: "pointer" }}
      title="Open the lighting schedule" onClick={() => setDetailView(view)}>{tag}</button>
  ));
  return <div>
    <h3>{type?.name ?? item.kind} · {item.tag}</h3>
    <div className="kv">
      <span className="k">Category</span><span>{item.domain}</span>
      <span className="k">Type</span><span>{item.type ?? "—"}</span>
      {/* Brand and model, where the type names a chosen product. Absent — not blank —
          when it does not: most of a house is bought against a specification. */}
      <ProductRows product={productFor(model.catalog, type?.product_ref)} />
      <span className="k">Room</span><span>{item.room ?? "unassigned"}</span>
      {item.circuit && <>
        <span className="k">Circuit</span>
        <span>
          <button className="badge" style={{ cursor: "pointer" }} title="Open the panel schedule"
            onClick={() => setDetailView("circuits")}>{item.circuit}</button>
        </span>
      </>}
      {/* The control edge, read from the same lighting take-off the E-602 sheet prints:
          a luminaire shows what switches it, a switch shows what it drives. */}
      {controlledBy.length > 0 && <><span className="k">Controlled by</span><span>{scheduleBadges(controlledBy, "lighting")}</span></>}
      {controls.length > 0 && <><span className="k">Controls</span><span>{scheduleBadges(controls, "lighting")}</span></>}
      <span className="k">Mount</span><span>{item.attachment ? `attached to ${item.attachment.wall} (${item.attachment.face})` : "free"}</span>
      <span className="k">Ports</span><span>{type?.ports.map((port) => port.service).join(", ") || "—"}</span>
      <span className="k">Source</span><span><Provenance p={item.provenance ?? null} /></span>
    </div>
    {impacts.length > 0 && <div className="inspector-last-edit" data-last-edit>
      <div className="field-label">Last edit</div>
      <ul>
        {impacts.map((impact, index) => (
          <li key={`${impact.tag}-${index}`} className={`impact ${impact.kind}`}>
            <strong>{impact.tag}</strong> {IMPACT_LABELS[impact.kind]} — {impact.reason}
          </li>
        ))}
      </ul>
    </div>}
    <label className="field-label">Product type
      <select value={item.type ?? ""} onChange={(event) => void changeType(event.target.value)}>
        {compatibleTypes.map((candidate) => <option key={candidate.tag} value={candidate.tag}>
          {candidate.tag} · {candidate.name}
        </option>)}
      </select>
    </label>
    <label className="field-label">Rotation °
      <span><input value={rotation} inputMode="decimal" onChange={(event) => setRotation(event.target.value)}
        onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); void updateRotation(); } }} />
        <button className="btn" onClick={() => void updateRotation()}>Apply</button></span>
    </label>
    <label className="muted" style={{ display: "block", fontSize: 11 }}>
      <input type="checkbox" checked={freeRotation} onChange={(event) => setFreeRotation(event.target.checked)} />
      {" "}Free rotation (otherwise snaps to 15°)
    </label>
    {/* Mount height only appears on an object that has an authored mount to edit — a sofa
        sits on the floor and has no height to state. */}
    {mount && <label className="field-label">
      {mount.kind === "ceiling" ? "Height above floor (ceiling-mounted)" : mount.kind === "wall"
        ? "Mount height above floor" : "Height above floor"}
      <span><input value={elevation} onChange={(event) => setElevation(event.target.value)} />
        <button className="btn" onClick={() => void setMountHeight()}>Apply</button></span>
    </label>}
    <label className="field-label">Position X
      <span><input value={x} aria-label="Position X" onChange={(event) => setX(event.target.value)} onKeyDown={onEnterMove} /></span>
    </label>
    <label className="field-label">Position Y
      <span><input value={y} aria-label="Position Y" onChange={(event) => setY(event.target.value)} onKeyDown={onEnterMove} />
        <button className="btn" onClick={() => void move()}>Move</button></span>
    </label>
    <label className="field-label">Room
      <span><select value={room} onChange={(event) => setRoom(event.target.value)}><option value="">Unassigned</option>
        {model.rooms.filter((candidate) => candidate.storey === item.storey).map((candidate) => <option key={candidate.uid} value={candidate.tag}>{candidate.tag}</option>)}</select>
        <button className="btn" onClick={() => void assignRoom()}>Apply</button></span>
    </label>
    <div className="field-label">
      <span>Wall attachment</span>
      <select value={wall} onChange={(event) => setWall(event.target.value)}>
        <option value="">Choose wall…</option>{model.walls.filter((candidate) => candidate.storey === item.storey)
          .map((candidate) => <option key={candidate.uid} value={candidate.tag}>{candidate.tag}</option>)}</select>
      <select value={face} onChange={(event) => setFace(event.target.value)}><option value="left">Left face</option><option value="right">Right face</option></select>
      <input value={distance} aria-label="Distance from wall start" placeholder="3'-6&quot;"
        onChange={(event) => setDistance(event.target.value)} />
      <button className="btn" onClick={() => void attach()}>Attach</button>
      {item.attachment && <button className="btn" onClick={() => void runMacro({ macro: "detach_placeable", storey: item.storey, tag: item.tag,
        ...(position ? { position: [formatFtIn(position[0]), formatFtIn(position[1])] as [string, string] } : {}) })}>Detach</button>}
    </div>
  </div>;
}
