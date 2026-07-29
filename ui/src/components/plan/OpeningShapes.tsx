// Opening and stair plan symbols, plus the host-resolution predicates the placement tool uses
// to decide which wall a click belongs to.
//
// Split out of components/Canvas2D.tsx. The door/window symbol is the fiddliest drawing in the
// plan — hinge side, swing side, arc sweep, the sill/head line weights — and memoizing it is
// what keeps a pan from redrawing every door in the house.
import { memo, useRef } from "react";
import type { DoorOperation, Model, Opening, Stair, Vec2, Wall, WindowOperation } from "../../model/types";
import { doorStrokeGlyph, hostWallThicknessM, windowStrokeGlyph } from "../../model/doorSymbols";
import { openingHostWall, pointAlong } from "../../model/geometry";
import { swingArcSweepFlag } from "../../three/planGeometry";
import { NORDIC_ACCENT, NORDIC_INK } from "../../nordic/palette";
import type { Selection } from "../../state/vocabulary";

export function hostStorey(model: Model, opening: Opening): string {
  return openingHostWall(model.walls, opening)?.storey ?? "";
}

// Even-odd ray cast — used to resolve a select-tool tap that lands inside a filled shape
// (e.g. a stair footprint) since the viewport's pointer capture swallows child <g> clicks.
export function pointInPolygon(point: Vec2, polygon: Vec2[]): boolean {
  const [x, y] = point;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

export function nearestOpeningHost(walls: Wall[], storey: string, point: Vec2):
  { wall: Wall; along_m: number; distance_m: number } | null {
  let best: { wall: Wall; along_m: number; distance_m: number } | null = null;
  for (const wall of walls) {
    if (wall.storey !== storey) continue;
    const [a, b] = wall.axis;
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const length = Math.hypot(dx, dy);
    if (length < 1e-9) continue;
    const raw = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / (length * length);
    const t = Math.max(0, Math.min(1, raw));
    const projected: Vec2 = [a[0] + t * dx, a[1] + t * dy];
    const distance_m = Math.hypot(point[0] - projected[0], point[1] - projected[1]);
    if (best === null || distance_m < best.distance_m) best = { wall, along_m: t * length, distance_m };
  }
  return best;
}

export const OpeningShape = memo(function OpeningShape({ o, host, project, scale, selected, operation, onSelect, onEdit,
  toWorld, onMove, onPreview, onPreviewEnd, preview }: {
  o: Opening;
  host: Wall;
  project: (p: Vec2) => Vec2;
  scale: number;
  selected: boolean;
  // The host type's operation: a `DoorOperation` for a door, a `WindowOperation` for a
  // window. One prop rather than two because the caller already knows which kind it holds
  // (`o.is_door`) and the two vocabularies are disjoint.
  operation?: DoorOperation | WindowOperation;
  onSelect: (kind: Selection["kind"], uid: string) => void;
  onEdit: (o: Opening, screen: Vec2) => void;
  toWorld: (clientX: number, clientY: number) => Vec2;
  onMove: (opening: Opening, host: Wall, position: Vec2) => void;
  onPreview?: (opening: Opening, host: Wall, position: Vec2) => void;
  onPreviewEnd?: () => void;
  preview?: "valid" | "invalid";
}) {
  const center = pointAlong(host, o.center_along_m);
  const [cx, cy] = project(center);
  const halfPx = (o.width_m / 2) * scale;
  const [a, b] = host.axis;
  const ang = Math.atan2(-(b[1] - a[1]), b[0] - a[0]);
  const dx = Math.cos(ang) * halfPx;
  const dy = Math.sin(ang) * halfPx;
  const hingeDirection = o.flip_hinge ? -1 : 1;
  const hingeX = cx + hingeDirection * dx;
  const hingeY = cy + hingeDirection * dy;
  const swingSign = o.flip_swing ? -1 : 1;
  // SVG's y axis is inverted from plan coordinates, so the screen-space +90° normal is
  // [sin(angle), -cos(angle)].  It matches the shared drawing IR's handed plan symbol.
  const leafX = hingeX + swingSign * Math.sin(ang) * o.width_m * scale;
  const leafY = hingeY - swingSign * Math.cos(ang) * o.width_m * scale;
  const wallArcX = hingeX - hingeDirection * 2 * dx;
  const wallArcY = hingeY - hingeDirection * 2 * dy;
  const windowTick = Math.min(6, Math.max(3, scale * 0.08));
  // Null for the hinged operations, which draw a leaf plus a swing arc instead.
  const strokeGlyph = o.is_door ? doorStrokeGlyph({
    operation: operation as DoorOperation | undefined,
    center: [cx, cy], angleRadians: ang, operatingSign: swingSign,
    parkJambSign: hingeDirection, widthM: o.width_m, heightM: o.height_m,
    hostWallThicknessM: hostWallThicknessM(host.layers), pixelsPerMeter: scale,
  }) : null;
  // Empty for a fixed (picture) unit and for an unknown operation: a sash tick is drawn
  // only when the catalog actually says the window opens.
  const sashGlyph = o.is_door ? [] : windowStrokeGlyph({
    operation: operation as WindowOperation | undefined,
    center: [cx, cy], angleRadians: ang, operatingSign: swingSign,
    parkJambSign: hingeDirection, widthM: o.width_m, pixelsPerMeter: scale,
  });
  // Press → drag vs. click discrimination (mirrors CanvasObjectFootprint): the ghost
  // preview only follows once the pointer has been captured AND moved past a small px
  // threshold, so a bare hover never drifts the symbol. A press that never crosses the
  // threshold is a click → select + open settings; one that does → commit the move.
  const downRef = useRef<Vec2 | null>(null);
  const movedRef = useRef(false);
  const DRAG_THRESHOLD_PX = 4;
  return (
    <g onDoubleClick={() => !preview && onEdit(o, [cx, cy])}
      onPointerDown={(event) => {
        if (preview) return;
        event.stopPropagation(); event.currentTarget.setPointerCapture(event.pointerId);
        downRef.current = [event.clientX, event.clientY];
        movedRef.current = false;
      }}
      onPointerMove={(event) => {
        if (preview) return;
        if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
        if (!movedRef.current && downRef.current &&
          Math.hypot(event.clientX - downRef.current[0], event.clientY - downRef.current[1]) < DRAG_THRESHOLD_PX) return;
        movedRef.current = true;
        onPreview?.(o, host, toWorld(event.clientX, event.clientY));
      }}
      onPointerUp={(event) => {
        if (preview) return;
        if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
        event.currentTarget.releasePointerCapture(event.pointerId);
        downRef.current = null;
        onPreviewEnd?.();
        if (movedRef.current) {
          const next = toWorld(event.clientX, event.clientY);
          if (Math.hypot(next[0] - center[0], next[1] - center[1]) > 0.001) onMove(o, host, next);
        } else {
          onSelect("opening", o.uid);
          onEdit(o, [cx, cy]);
        }
        movedRef.current = false;
      }}
      onPointerCancel={() => { if (!preview) { downRef.current = null; movedRef.current = false; onPreviewEnd?.(); } }}
      pointerEvents={preview ? "none" : undefined}
      opacity={preview ? .65 : 1}
      style={{ cursor: preview ? undefined : "pointer" }}>
      <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
        stroke={selected ? NORDIC_ACCENT : "var(--canvas-white)"} strokeWidth={selected ? 6 : 5} />
      <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
      stroke={o.is_door ? "var(--canvas-wood)" : NORDIC_ACCENT} strokeWidth={2}
        strokeDasharray={o.is_door ? undefined : "3 2"} />
      {o.is_door ? (strokeGlyph ? <>
        {/* The non-swinging operations — overhead, bifold, slider, pocket — are pure
            stroke glyphs resolved by the shared symbol module, arc-free by construction. */}
        {strokeGlyph.map((stroke, index) => (
          <polyline key={index} points={stroke.points.map((point) => point.join(",")).join(" ")}
            fill="none" stroke="var(--canvas-wood)" strokeWidth={stroke.dashed ? 1 : 1.5}
            strokeDasharray={stroke.dashed ? "4 3" : undefined} />
        ))}
      </> : operation === "double_swing" ? <>
        {/* French/double door — two half-width leaves hinged at the jambs, meeting at
            a centre mullion. Both leaves swing to the same side. */}
        {([-1, 1] as const).map((side) => {
          const jx = cx + side * dx;
          const jy = cy + side * dy;
          const lx = jx + swingSign * Math.sin(ang) * halfPx;
          const ly = jy - swingSign * Math.cos(ang) * halfPx;
          return (
            <g key={side}>
              <line x1={jx} y1={jy} x2={lx} y2={ly}
                stroke="var(--canvas-wood)" strokeWidth={1.5} />
              {/* Arc pivots on the jamb (jx,jy); its two leaves mirror across the mullion,
                  so each resolves to the sweep flag that keeps that jamb as the centre. */}
              <path d={`M ${cx} ${cy} A ${halfPx} ${halfPx} 0 0 ${swingArcSweepFlag([jx, jy], [cx, cy], [lx, ly])} ${lx} ${ly}`}
                fill="none" stroke="var(--canvas-wood)" strokeWidth={1} />
            </g>
          );
        })}
      </> : <>
        <line x1={hingeX} y1={hingeY} x2={leafX} y2={leafY}
          stroke="var(--canvas-wood)" strokeWidth={1.5} />
        {/* Swing arc pivots on the hinge; the closed leaf lies along the wall at the far
            jamb (wallArc) and opens to leaf. The flag must keep the hinge as the arc
            centre so the arc bows concave toward the hinge, not convex away from it. */}
        <path d={`M ${wallArcX} ${wallArcY} A ${o.width_m * scale} ${o.width_m * scale} 0 0 ${swingArcSweepFlag([hingeX, hingeY], [wallArcX, wallArcY], [leafX, leafY])} ${leafX} ${leafY}`}
          fill="none" stroke="var(--canvas-wood)" strokeWidth={1} />
      </>) : <>
        <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
          stroke={NORDIC_ACCENT} strokeWidth={3} />
        <line x1={cx - Math.sin(ang) * windowTick} y1={cy + Math.cos(ang) * windowTick}
          x2={cx + Math.sin(ang) * windowTick} y2={cy - Math.cos(ang) * windowTick}
          stroke="var(--canvas-white)" strokeWidth={1.2} />
        {/* Sash notation — a casement tick, an awning chevron, a hung check-rail or a
            slider track. A fixed unit contributes nothing here, which is precisely how a
            picture window reads as one: the plain sill/head line above and no hardware. */}
        {sashGlyph.map((stroke, index) => (
          <polyline key={index} points={stroke.points.map((point) => point.join(",")).join(" ")}
            fill="none" stroke={NORDIC_ACCENT} strokeWidth={stroke.dashed ? 1 : 1.5}
            strokeDasharray={stroke.dashed ? "4 3" : undefined} />
        ))}
        <text x={cx - Math.sin(ang) * 14} y={cy + Math.cos(ang) * 14} textAnchor="middle"
          fill={NORDIC_ACCENT} fontSize={9} fontWeight={700}
          style={{ paintOrder: "stroke", stroke: "var(--canvas-white)", strokeWidth: 3 }}>{o.tag}</text>
      </>}
      {selected && <circle cx={cx} cy={cy} r={5} fill={NORDIC_ACCENT} />}
      {preview && <circle cx={cx} cy={cy} r={Math.max(6, scale * .08)} fill="none"
        stroke={preview === "valid" ? "var(--success)" : "var(--error)"} strokeWidth={2} />}
    </g>
  );
});

export const StairShape = memo(function StairShape({ stair, project, selected, hovered, onSelect, onHover }: {
  stair: Stair;
  project: (p: Vec2) => Vec2;
  selected: boolean;
  hovered: boolean;
  onSelect: (kind: Selection["kind"], uid: string) => void;
  onHover: (uid: string | null) => void;
}) {
  if (stair.outline.length < 3) return null;
  const outline = stair.outline.map(project).map((point) => point.join(",")).join(" ");
  const xs = stair.outline.map((point) => point[0]);
  const ys = stair.outline.map((point) => point[1]);
  const minX = Math.min(...xs); const maxX = Math.max(...xs);
  const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const start: Vec2 = stair.run_direction === "x"
    ? [minX, (minY + maxY) / 2] : [(minX + maxX) / 2, minY];
  const end: Vec2 = stair.run_direction === "x"
    ? [maxX, (minY + maxY) / 2] : [(minX + maxX) / 2, maxY];
  const [directionStart, directionEnd] = stair.run_reversed ? [end, start] : [start, end];
  const [labelX, labelY] = project([(minX + maxX) / 2, (minY + maxY) / 2]);
  const stroke = selected ? NORDIC_ACCENT : hovered ? NORDIC_INK : "var(--canvas-wood)";
  const [arrowStartX, arrowStartY] = project(directionStart);
  const [arrowEndX, arrowEndY] = project(directionEnd);
  return <g onClick={() => onSelect("stair", stair.uid)}
    onPointerEnter={() => onHover(stair.uid)} onPointerLeave={() => onHover(null)}
    style={{ cursor: "pointer" }}>
    <polygon points={outline} fill="var(--canvas-wood-soft)" stroke={stroke}
      strokeWidth={selected ? 2.5 : 1.25} />
    {stair.members.filter((member) => (member.category === "tread" || member.category === "winder" || member.category === "landing")
      // A vertical member (landing post / newel) is a point in plan, not a line.
      && (member.p0[0] !== member.p1[0] || member.p0[1] !== member.p1[1])).map((member) => {
      if (member.plan_outline && member.plan_outline.length >= 3) {
        return <polygon key={member.key} points={member.plan_outline.map(project).map((point) => point.join(",")).join(" ")}
          fill="none" stroke={stroke} strokeWidth={1} />;
      }
      const [x0, y0] = project(member.p0); const [x1, y1] = project(member.p1);
      return <line key={member.key} x1={x0} y1={y0} x2={x1} y2={y1} stroke={stroke} strokeWidth={1} />;
    })}
    <line x1={arrowStartX} y1={arrowStartY} x2={arrowEndX} y2={arrowEndY} stroke={stroke}
      strokeWidth={1.5} markerEnd="url(#stair-arrow)" />
    <text x={labelX} y={labelY - 5} textAnchor="middle" fontSize={10} fill={stroke}
      style={{ paintOrder: "stroke" }} stroke="var(--canvas-white)" strokeWidth={3}>UP {stair.riser_count} R</text>
  </g>;
});
