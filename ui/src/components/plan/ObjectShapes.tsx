// Plan symbols for things placed *on* the floor rather than built into it: a draggable wall
// node handle, a placeable's footprint (with its rotate handle and alignment guide), and the
// clearance envelopes a fixture claims around itself.
//
// Split out of components/Canvas2D.tsx. All three own a live pointer gesture, which is exactly
// why they are separate components: each keeps its own drag state so a drag re-renders one
// symbol rather than the whole plan. The two that are drawn once per record are memo()'d for
// the same reason: a storey's worth of footprints must not re-render because a wall was hovered.
import { memo, useRef, useState } from "react";
import type { CanvasObject, CanvasObjectType, Model, Vec2, Wall } from "../../model/types";
import { nearestWallHit, openingHostWall } from "../../model/geometry";
import { draggedCenter, exceedsDragThreshold, grabOffsetFor } from "./objectDrag";
import { NORDIC_ACCENT } from "../../nordic/palette";
import { PLAN_INK_TEXT_HALO, PlanLabel } from "./PlanLabelLayer";
import { useStore } from "../../state/store";
import type { LabelMode, Selection } from "../../state/vocabulary";

// A drag is a writeback: the engine has to find an editable plan file hosting this object's
// constructor. When it can't, the edit is rejected (422) — so refuse the gesture up front and
// say why, the same way deleteSelection refuses derived geometry, instead of letting the
// object follow the pointer and then snap back.
export function placeableDragBlockedReason(item: CanvasObject): string | null {
  const p = item.provenance;
  if (p === undefined) return null; // older model.json: no provenance published, allow
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

export const CanvasObjectFootprint = memo(function CanvasObjectFootprint({ item, type, project, scale, walls, selected, labelMode = "all", onSelect, toWorld, onMove, onRotate }: {
  item: CanvasObject;
  type?: CanvasObjectType;
  project: (point: Vec2) => Vec2;
  scale: number;
  walls: Wall[];
  selected: boolean;
  labelMode?: LabelMode;
  onSelect: (kind: Selection["kind"], uid: string) => void;
  toWorld: (clientX: number, clientY: number) => Vec2;
  onMove: (item: CanvasObject, position: Vec2) => void;
  onRotate: (item: CanvasObject, degrees: number, freeRotation: boolean) => void;
}) {
  const [draggedPosition, setDraggedPosition] = useState<Vec2 | null>(null);
  const [draggedRotation, setDraggedRotation] = useState<number | null>(null);
  const [alignmentPoint, setAlignmentPoint] = useState<Vec2 | null>(null);
  // Hover lives in the component, not the store: hovering every object in a dense plan through
  // the store would re-render the whole canvas (see the memoization notes in
  // useCanvasInteractions.ts).
  const [hovered, setHovered] = useState(false);
  // One gesture's worth of state. A ref, not state: the threshold has to be readable inside the
  // very pointermove that crosses it, before any re-render.
  const gesture = useRef<{ downScreen: Vec2; grabOffset: Vec2; dragging: boolean } | null>(null);
  if (!item.position_m) return null;
  const position = draggedPosition ?? item.position_m;
  const [x, y] = project(position);
  const [widthM, depthM] = type?.footprint_m ?? [0.45, 0.45];
  const width = widthM * scale;
  const depth = depthM * scale;
  const rotation = draggedRotation ?? item.rotation ?? 0;
  const colors: Record<string, [string, string]> = {
    furniture: ["var(--canvas-wood-soft)", "var(--canvas-wood)"],
    plumbing: ["var(--canvas-selection)", "var(--accent)"],
    electrical: ["#fff2bd", "#a66f00"],
    mechanical: ["#dceafb", "#37658d"],
    appliance: ["#e5e7eb", "#4b5563"],
  };
  const [fill, stroke] = colors[item.domain] ?? ["#e5e7eb", "#4b5563"];
  // Precedence: an imported plan SVG wins, then the engine-generated glyph, then the plain
  // footprint rect. The first generated stroke is the object outline and carries selection.
  const strokes = type?.plan_svg ? [] : type?.plan_strokes ?? [];
  const dragBlocked = placeableDragBlockedReason(item);
  return <g opacity={dragBlocked ? 0.55 : 0.92} style={{ cursor: dragBlocked ? "not-allowed" : "grab" }}
    onPointerDown={(event) => {
      event.stopPropagation();
      onSelect("canvas_object", item.uid);
      // Selection still works on a non-editable object (the inspector shows its provenance);
      // only the pointer capture that starts the drag is withheld.
      if (dragBlocked) { useStore.getState().toast(dragBlocked); return; }
      gesture.current = {
        downScreen: [event.clientX, event.clientY],
        grabOffset: grabOffsetFor(item.position_m!, toWorld(event.clientX, event.clientY)),
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
      const next = draggedCenter(active.grabOffset, toWorld(event.clientX, event.clientY));
      setDraggedPosition(next);
      const hit = nearestWallHit(walls, next);
      setAlignmentPoint(hit && hit.dist_m <= .35 ? hit.point : null);
    }}
    onPointerUp={(event) => {
      const active = gesture.current;
      if (!active || !event.currentTarget.hasPointerCapture(event.pointerId)) return;
      event.currentTarget.releasePointerCapture(event.pointerId);
      gesture.current = null;
      setDraggedPosition(null);
      setAlignmentPoint(null);
      // Never dragged → a pure select, and crucially no writeback: a plain click would
      // otherwise commit whatever sub-millimetre delta the pointer happened to land on.
      if (!active.dragging) return;
      onMove(item, draggedCenter(active.grabOffset, toWorld(event.clientX, event.clientY)));
    }}
    onPointerCancel={() => { gesture.current = null; setDraggedPosition(null); setAlignmentPoint(null); }}>
    {type?.plan_svg ? <image href={type.plan_svg} x={x - width / 2} y={y - depth / 2} width={width} height={depth}
      transform={`rotate(${-rotation} ${x} ${y})`} />
      : strokes.length ? <g transform={`rotate(${-rotation} ${x} ${y})`}>
        {strokes.map((symbolStroke, index) => {
          // The engine owns the geometry; the UI only projects it. Screen y is inverted from
          // plan y, the same handedness doorSymbolPoint uses.
          const points = symbolStroke.points
            .map(([sx, sy]) => `${x + sx * scale},${y - sy * scale}`).join(" ");
          const outline = index === 0;
          return symbolStroke.closed
            ? <polygon key={index} points={points} fill={symbolStroke.fill ?? "none"}
              stroke={selected && outline ? "var(--ink)" : stroke}
              strokeWidth={(selected && outline ? 2.4 : 1.2) * symbolStroke.weight / 0.25} />
            : <polyline key={index} points={points} fill="none" stroke={stroke}
              strokeWidth={1.2 * symbolStroke.weight / 0.25} />;
        })}
      </g>
        : <rect x={x - width / 2} y={y - depth / 2} width={width} height={depth}
          fill={fill} stroke={selected ? "var(--ink)" : stroke} strokeWidth={selected ? 2.4 : 1.2}
          transform={`rotate(${-rotation} ${x} ${y})`} />}
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
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
          const [worldX, worldY] = toWorld(event.clientX, event.clientY);
          const raw = Math.atan2(worldY - position[1], worldX - position[0]) * 180 / Math.PI;
          setDraggedRotation(event.shiftKey ? raw : Math.round(raw / 15) * 15);
        }}
        onPointerUp={(event) => {
          if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
          event.currentTarget.releasePointerCapture(event.pointerId);
          const [worldX, worldY] = toWorld(event.clientX, event.clientY);
          const raw = Math.atan2(worldY - position[1], worldX - position[0]) * 180 / Math.PI;
          const next = event.shiftKey ? raw : Math.round(raw / 15) * 15;
          setDraggedRotation(null);
          if (Math.abs(next - (item.rotation ?? 0)) > 0.01) onRotate(item, next, event.shiftKey);
        }} />
    </g>}
    {alignmentPoint && draggedPosition && (() => {
      const [ax, ay] = project(alignmentPoint);
      return <line x1={x} y1={y} x2={ax} y2={ay} stroke={NORDIC_ACCENT}
        strokeWidth={1.5} strokeDasharray="4 3" pointerEvents="none" />;
    })()}
  </g>;
});

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
