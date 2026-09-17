// Plan symbols for things placed *on* the floor rather than built into it: a draggable wall
// node handle, a placeable's footprint (with its rotate handle and alignment guide), and the
// clearance envelopes a fixture claims around itself.
//
// Split out of components/Canvas2D.tsx. All three own a live pointer gesture, which is exactly
// why they are separate components: each keeps its own drag state so a drag re-renders one
// symbol rather than the whole plan. The two that are drawn once per record are memo()'d for
// the same reason: a storey's worth of footprints must not re-render because a wall was hovered.
import { memo, useEffect, useRef, useState } from "react";
import type { CanvasObject, CanvasObjectType, Model, Vec2, Wall } from "../../model/types";
import { openingHostWall } from "../../model/geometry";
import { draggedCenter, exceedsDragThreshold, grabOffsetFor } from "./objectDrag";
import { DEFAULT_FOOTPRINT_M, PlaceableGlyph } from "./PlaceableGlyph";
import { ROTATE_HANDLE_SNAP_DEG, WALL_SNAP_CONFIG } from "./editorConfig";
import { slideAlongWall, snapToWall, wallFrame } from "./wallSnap";
import type { PlaceableDrop } from "./canvasTypes";
import type { PendingTransform } from "../../state/pending";
import { NORDIC_ACCENT } from "../../nordic/palette";
import { PLAN_INK_TEXT_HALO, PlanLabel } from "./PlanLabelLayer";
import { useStore } from "../../state/store";
import type { LabelMode, Selection } from "../../state/vocabulary";

// A drag is a writeback: the engine has to find an editable plan file hosting this object's
// constructor. When it can't, the edit is rejected (422) — so refuse the gesture up front and
// say why, the same way deleteSelection refuses derived geometry, instead of letting the
// object follow the pointer and then snap back.
export function placeableDragBlockedReason(item: CanvasObject, createdThisSession = false): string | null {
  const p = item.provenance;
  if (p === undefined) return null; // older model.json: no provenance published, allow
  // The engine captures provenance for an object added in this session only when its source
  // writeback reconciles, which does not bump the revision; this UI wrote it to an editable
  // list, so its null record is "not yet captured", and the commit still rejects if wrong.
  if (p === null && createdThisSession) return null;
  if (p === null) return `${item.tag} has no authored source to write a move back to`;
  if (p.editable === false) return `${item.tag} is authored in ${p.file} — edit it in code to move it`;
  return null;
}

export function NodeHandle({ world, project, onStart, onMove, onEnd }: {
  world: Vec2;
  project: (p: Vec2) => Vec2;
  onStart: () => void;
  onMove: (clientX: number, clientY: number) => void;
  onEnd: () => void;
}) {
  const dragging = useRef(false);
  const raf = useRef<number | null>(null);
  const [x, y] = project(world);
  // A generous transparent halo (r=13 → 26px) carries the pointer gesture so the endpoint is
  // easy to grab on touch and at a glance, while the visible dot stays small and uncluttered.
  return (
    <g style={{ cursor: "grab" }}
      onPointerDown={(e) => {
        e.stopPropagation();
        (e.currentTarget as Element).setPointerCapture(e.pointerId);
        dragging.current = true;
        onStart();
      }}
      onPointerMove={(e) => {
        if (!dragging.current) return;
        e.stopPropagation();
        const { clientX, clientY } = e;
        if (raf.current == null) {
          raf.current = requestAnimationFrame(() => { raf.current = null; onMove(clientX, clientY); });
        }
      }}
      onPointerUp={(e) => {
        if (!dragging.current) return;
        e.stopPropagation();
        dragging.current = false;
        if (raf.current != null) { cancelAnimationFrame(raf.current); raf.current = null; }
        onEnd();
      }}
    >
      <circle cx={x} cy={y} r={13} fill="transparent" />
      <circle cx={x} cy={y} r={7} fill="var(--canvas-white)" stroke={NORDIC_ACCENT} strokeWidth={2.5}
        pointerEvents="none" />
    </g>
  );
}

export const CanvasObjectFootprint = memo(function CanvasObjectFootprint({ item, type, project, scale, walls, selected, labelMode = "all", pending, onSelect, toWorld, onDrop, onRotate }: {
  item: CanvasObject;
  type?: CanvasObjectType;
  project: (point: Vec2) => Vec2;
  scale: number;
  walls: Wall[];
  selected: boolean;
  labelMode?: LabelMode;
  // A committed transform the engine has not caught up with yet (→ state/pending.ts).
  pending?: PendingTransform;
  onSelect: (kind: Selection["kind"], uid: string) => void;
  toWorld: (clientX: number, clientY: number) => Vec2;
  onDrop: (item: CanvasObject, drop: PlaceableDrop) => void;
  onRotate: (item: CanvasObject, degrees: number, freeRotation: boolean) => void;
}) {
  const [draggedPosition, setDraggedPosition] = useState<Vec2 | null>(null);
  const [draggedRotation, setDraggedRotation] = useState<number | null>(null);
  const [guide, setGuide] = useState<{ point: Vec2; solid: boolean } | null>(null);
  // Hover lives in the component, not the store: hovering every object in a dense plan through
  // the store would re-render the whole canvas (see the memoization notes in
  // useCanvasInteractions.ts).
  const [hovered, setHovered] = useState(false);
  const createdThisSession = useStore((s) => s.sessionEdits.created.includes(item.tag));
  // One gesture's worth of state. A ref, not state: the threshold has to be readable inside the
  // very pointermove that crosses it, before any re-render.
  const gesture = useRef<{ downScreen: Vec2; grabOffset: Vec2; dragging: boolean } | null>(null);
  const rotating = useRef(false);
  const cancel = () => {
    gesture.current = null;
    rotating.current = false;
    setDraggedPosition(null);
    setDraggedRotation(null);
    setGuide(null);
  };
  // Esc mid-gesture restores the pre-drag pose with no commit. Capture phase, so the app's
  // own Esc (which would also clear the selection) never sees it.
  const gestureActive = draggedPosition !== null || draggedRotation !== null;
  useEffect(() => {
    if (!gestureActive) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      cancel();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [gestureActive]);
  if (!item.position_m) return null;
  const restingPosition = pending?.position_m ?? item.position_m;
  const restingRotation = pending?.rotation ?? item.rotation ?? 0;
  const position = draggedPosition ?? restingPosition;
  const [x, y] = project(position);
  const footprintM = type?.footprint_m ?? DEFAULT_FOOTPRINT_M;
  const depth = footprintM[1] * scale;
  const rotation = draggedRotation ?? restingRotation;
  const strokes = type?.plan_svg ? [] : type?.plan_strokes ?? [];
  const dragBlocked = placeableDragBlockedReason(item, createdThisSession);
  const hostFrame = item.attachment
    ? (() => { const host = walls.find((wall) => wall.tag === item.attachment!.wall); return host ? wallFrame(host) : null; })()
    : null;

  // Where a drag to `cursorCentre` would put the object: along its host when attached, else
  // free with the wall snap evaluated (Alt skips it).
  const dropFor = (cursorCentre: Vec2, altKey: boolean): { drop: PlaceableDrop; guide: typeof guide } => {
    if (hostFrame) {
      const slide = slideAlongWall(hostFrame, restingPosition, cursorCentre);
      return { drop: { kind: "slide", position: slide.centre, station: slide.station }, guide: null };
    }
    const snap = altKey ? null : snapToWall(cursorCentre, restingRotation, footprintM, walls, WALL_SNAP_CONFIG);
    if (snap?.snapped) {
      const rotated = Math.abs(snap.rotation - restingRotation) > 0.01 ? snap.rotation : undefined;
      return { drop: { kind: "move", position: snap.centre, rotation: rotated }, guide: { point: snap.facePoint, solid: true } };
    }
    return { drop: { kind: "move", position: cursorCentre }, guide: snap ? { point: snap.facePoint, solid: false } : null };
  };

  return <g opacity={dragBlocked ? 0.55 : 0.92} style={{ cursor: dragBlocked ? "not-allowed" : "grab" }}
    onPointerDown={(event) => {
      // Under a drawing tool the tap belongs to the plan (a lamp placed on a table).
      if (useStore.getState().tool !== "select") return;
      event.stopPropagation();
      onSelect("canvas_object", item.uid);
      // Selection still works on a non-editable object (the inspector shows its provenance);
      // only the pointer capture that starts the drag is withheld.
      if (dragBlocked) { useStore.getState().toast(dragBlocked); return; }
      gesture.current = {
        downScreen: [event.clientX, event.clientY],
        grabOffset: grabOffsetFor(restingPosition, toWorld(event.clientX, event.clientY)),
        dragging: false,
      };
      event.currentTarget.setPointerCapture(event.pointerId);
    }}
    onPointerEnter={() => setHovered(true)}
    onPointerLeave={() => setHovered(false)}
    // Double-click opens the object's details (Inspector), matching the door/window affordance
    // and guaranteeing the panel opens even if a stray drag swallowed the pointer-up select.
    onDoubleClick={(event) => { event.stopPropagation(); onSelect("canvas_object", item.uid); }}
    onPointerMove={(event) => {
      const active = gesture.current;
      if (!active || !event.currentTarget.hasPointerCapture(event.pointerId)) return;
      // Below the threshold this is still a click in progress: leave the object where it is.
      if (!active.dragging) {
        if (!exceedsDragThreshold(active.downScreen, [event.clientX, event.clientY])) return;
        active.dragging = true;
      }
      const cursorCentre = draggedCenter(active.grabOffset, toWorld(event.clientX, event.clientY));
      const next = dropFor(cursorCentre, event.altKey);
      // A free object follows the cursor and only snaps on release; the solid guide says it will.
      setDraggedPosition(next.drop.kind === "slide" ? next.drop.position : cursorCentre);
      setGuide(next.guide);
    }}
    onPointerUp={(event) => {
      const active = gesture.current;
      if (!active || !event.currentTarget.hasPointerCapture(event.pointerId)) return;
      event.currentTarget.releasePointerCapture(event.pointerId);
      gesture.current = null;
      // Never dragged → a pure select, and crucially no writeback: a plain click would
      // otherwise commit whatever sub-millimetre delta the pointer happened to land on.
      if (active.dragging) {
        const { drop } = dropFor(draggedCenter(active.grabOffset, toWorld(event.clientX, event.clientY)), event.altKey);
        // Commit first: the pending overlay must be in the store before the local drag state
        // clears, or the glyph flashes back to where it started.
        onDrop(item, drop);
      }
      setDraggedPosition(null);
      setGuide(null);
    }}
    onPointerCancel={cancel}>
    <PlaceableGlyph type={type} domain={item.domain} x={x} y={y} scale={scale} rotation={rotation} selected={selected} />
    {/* A centred label sits on top of the glyph and hides it, so a drawn symbol pushes its
        name below the footprint instead. A selected object always names itself, whatever the
        label mode — you asked for that one. */}
    {(labelMode === "all" || selected || (labelMode === "hover" && hovered)) &&
      <PlanLabel>
        {/* Hoisted out of this <g>, so it no longer inherits the group's 0.92/0.55 opacity:
            a drag-blocked object keeps a dimmed glyph but names itself crisply. */}
        <text x={x} y={strokes.length ? y + depth / 2 + 11 : y + 3} textAnchor="middle" fontSize={9}
          fill="var(--ink)" pointerEvents="none" style={PLAN_INK_TEXT_HALO}>
          {(type?.name ?? item.type ?? item.kind).replace(/^[A-Z]+-/, "")}
        </text>
      </PlanLabel>}
    {/* Rotation is a writeback too, so a non-editable object shows no rotate handle. */}
    {selected && !dragBlocked && <g>
      <line x1={x} y1={y - depth / 2} x2={x} y2={y - depth / 2 - 18}
        stroke="var(--ink)" strokeWidth={1.2} pointerEvents="none" />
      <circle cx={x} cy={y - depth / 2 - 23} r={5} fill="var(--canvas-selection)" stroke="var(--ink)"
        strokeWidth={1.2} style={{ cursor: "crosshair" }}
        onPointerDown={(event) => {
          event.stopPropagation();
          rotating.current = true;
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!rotating.current || !event.currentTarget.hasPointerCapture(event.pointerId)) return;
          setDraggedRotation(handleAngle(toWorld(event.clientX, event.clientY), position, event.shiftKey));
        }}
        onPointerUp={(event) => {
          if (!rotating.current || !event.currentTarget.hasPointerCapture(event.pointerId)) return;
          event.currentTarget.releasePointerCapture(event.pointerId);
          rotating.current = false;
          const next = handleAngle(toWorld(event.clientX, event.clientY), position, event.shiftKey);
          if (Math.abs(next - restingRotation) > 0.01) onRotate(item, next, event.shiftKey);
          setDraggedRotation(null);
        }}
        onPointerCancel={cancel} />
    </g>}
    {guide && draggedPosition && (() => {
      const [ax, ay] = project(guide.point);
      return <line x1={x} y1={y} x2={ax} y2={ay} stroke={NORDIC_ACCENT}
        strokeWidth={guide.solid ? 2 : 1.5} strokeDasharray={guide.solid ? undefined : "4 3"} pointerEvents="none" />;
    })()}
  </g>;
});

// The rotate handle's angle about the object's centre: 15° steps, free under Shift.
function handleAngle(pointer: Vec2, centre: Vec2, free: boolean): number {
  const raw = Math.atan2(pointer[1] - centre[1], pointer[0] - centre[0]) * 180 / Math.PI;
  return free ? raw : Math.round(raw / ROTATE_HANDLE_SNAP_DEG) * ROTATE_HANDLE_SNAP_DEG;
}

// memo()'d alongside CanvasObjectFootprint: it walks every fixture, furniture record, resolved
// placeable and swing/bumper polygon in the model, which is the plan's most expensive derived
// pass, and none of its inputs move when a hover or a selection does.
export const ClearanceOverlays = memo(function ClearanceOverlays({ model, storey, project, scale }: {
  model: Model;
  storey: string | null;
  project: (point: Vec2) => Vec2;
  scale: number;
}) {
  const legacyItems = [
    ...(model.fixtures ?? []).map((item) => ({ ...item, kind: "fixture" as const })),
    ...(model.furniture ?? []).map((item) => ({ ...item, kind: "furniture" as const })),
  ].filter((item) => (!storey || item.storey === storey) && item.clearance_m);
  const resolvedItems = (model.canvas_objects ?? []).filter((item) =>
    (!storey || item.storey === storey) && ((item.required_clearances?.length ?? 0) > 0 || (item.recommended_clearances?.length ?? 0) > 0));
  const openingOverlays = model.openings.filter((opening) => {
    const host = openingHostWall(model.walls, opening);
    return (!storey || host?.storey === storey) && ((opening.swing_clearance?.length ?? 0) > 0 ||
      (opening.framing_bumper?.length ?? 0) > 0);
  });
  return <g pointerEvents="none">{resolvedItems.flatMap((item) => [
    ...(item.required_clearances ?? []).map((polygon, index) => ({ item, polygon, required: true, index })),
    ...(item.recommended_clearances ?? []).map((polygon, index) => ({ item, polygon, required: false, index })),
  ]).map(({ item, polygon, required, index }) => <polygon key={`resolved-clearance-${item.uid}-${index}`}
    points={polygon.map((point) => project(point).join(",")).join(" ")}
    fill={required ? "var(--canvas-selection)" : "var(--canvas-wood-soft)"}
    fillOpacity={0.22} stroke={required ? "var(--error)" : "var(--canvas-wood)"}
    strokeDasharray="4 3" strokeWidth={required ? 1.4 : 1} />)}
  {openingOverlays.map((opening) => <g key={`opening-overlay-${opening.uid}`}>
    {opening.swing_clearance && <polygon points={opening.swing_clearance.map((point) => project(point).join(",")).join(" ")}
      fill="var(--canvas-wood-soft)" fillOpacity={.22} stroke="var(--canvas-wood)" strokeDasharray="4 3" strokeWidth={1} />}
    {opening.framing_bumper && <polygon points={opening.framing_bumper.map((point) => project(point).join(",")).join(" ")}
      fill="none" stroke={NORDIC_ACCENT} strokeDasharray="2 2" strokeWidth={1} />}
  </g>)}
  {legacyItems.map((item) => {
    const [front, back, left, right] = item.clearance_m!;
    const [x, y] = project(item.position);
    const width = (item.footprint_m[0] + left + right) * scale;
    const depth = (item.footprint_m[1] + front + back) * scale;
    return <rect key={`clearance-${item.uid}`} x={x - width / 2} y={y - depth / 2}
      width={width} height={depth} fill="var(--canvas-wood-soft)" stroke="var(--error)"
      strokeDasharray="4 3" strokeWidth={1} />;
  })}</g>;
});
