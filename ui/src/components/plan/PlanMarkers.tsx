// Non-element SVG layers of the floorplan: resolved slab outlines, the plain node dots and
// their heal affordance, the clickable diagnostic markers, the wall tool's draft rubber-band
// and snap indicator, and the DOCUMENT workspace's detail (D-tag) markers. Split from
// components/Canvas2D.tsx — each layer is a pure projection of model + gesture state handed
// in as props; no store subscriptions live here.
import type { PreviewGeometry } from "../../engine/EngineClient";
import type { PlanWarningMarker } from "../../model/planWarnings";
import { projectedExtentPx, spaceLabel, spaceLabelLineBudget } from "../../model/spaceLabels";
import type { Model, Room, Solid, Vec2, Wall } from "../../model/types";
import {
  formatFtIn, snapWorld, type Node as GeoNode,
} from "../../model/geometry";
import { NORDIC_ACCENT, NORDIC_INK, NORDIC_LINE } from "../../nordic/palette";
import { collinearAt } from "./PlanChrome";
import type { RubberBand, WallDraft } from "./canvasTypes";

// Rooms (tinted fills, behind walls) — a live drag's preview cascades into neighboring
// rooms' clear-face polygons, matched by tag against the last preview. Labels drop from the
// bottom up (name → id → area) as the space runs out of room on screen.
export function RoomLayer({ rooms, previewGeom, tool, showSpaceLabels, project, onSelect }: {
  rooms: Room[];
  previewGeom: PreviewGeometry | null;
  tool: string;
  showSpaceLabels: boolean;
  project: (p: Vec2) => Vec2;
  onSelect: (room: Room) => void;
}) {
  return (
    <>
      {rooms.map((r) => {
        const clearFace = previewGeom?.rooms.find((x) => x.tag === r.tag)?.clear_face
          ?? r.clear_face;
        return (
          <g key={r.uid} onClick={() => tool === "select" && onSelect(r)}
            style={{ cursor: tool === "select" ? "pointer" : undefined }}>
            <polygon points={clearFace.map(project).map((p) => p.join(",")).join(" ")}
              fill="var(--canvas-selection)" stroke="none" />
            {showSpaceLabels && clearFace.length > 0 && (() => {
              // Name (occupancy) on top, then the id a plan edit references, then area —
              // dropped from the bottom up as the space runs out of room on screen.
              const label = spaceLabel(r);
              const [widthPx, heightPx] = projectedExtentPx(clearFace, project);
              const lines = spaceLabelLineBudget(widthPx, heightPx);
              if (lines === 0) return null;
              const centroid: Vec2 = [
                clearFace.reduce((sum, point) => sum + point[0], 0) / clearFace.length,
                clearFace.reduce((sum, point) => sum + point[1], 0) / clearFace.length,
              ];
              const [x, y] = project(centroid);
              return <text x={x} y={y - (lines - 1) * 7} textAnchor="middle" pointerEvents="none"
                fill="var(--canvas-ink)" fontSize={12} fontWeight={700}
                style={{ paintOrder: "stroke", stroke: "var(--canvas-white)", strokeWidth: 3 }}>
                <tspan x={x}>{lines >= 2 ? label.name : label.id}</tspan>
                {lines >= 2 && (
                  <tspan x={x} dy={14} fontSize={10} fontWeight={600} className="space-label-id">
                    {label.id}
                  </tspan>
                )}
                {lines >= 3 && (
                  <tspan x={x} dy={13} fontSize={10} fontWeight={500}>{label.area}</tspan>
                )}
              </text>;
            })()}
          </g>
        );
      })}
    </>
  );
}

// Resolved slabs on the active storey, drawn under the rooms the way the sheet emitters draw
// them (emit/draw/foundationplan.py::_emit_slabs): the plan outline as a concrete-toned edge
// with a whisper of fill, and every void (a stairwell, a sump pit) as a dashed inner ring.
// Purely graphical — slabs are derived geometry, selected and inspected in 3D, so the layer
// never intercepts the plan's pointer gestures.
export function SlabOutlines({ slabs, project }: {
  slabs: Solid[];
  project: (p: Vec2) => Vec2;
}) {
  const ring = (outline: Vec2[]) => outline.map(project).map((p) => p.join(",")).join(" ");
  return (
    <g pointerEvents="none">
      {slabs.map((slab) => (
        <g key={slab.uid}>
          <polygon points={ring(slab.outline)} fill="var(--material-concrete)"
            fillOpacity={0.12} stroke="var(--material-concrete)" strokeWidth={1.5} />
          {(slab.voids ?? []).filter((v) => v.length >= 3).map((v, i) => (
            <polygon key={i} points={ring(v)} fill="var(--bg)" fillOpacity={0.6}
              stroke="var(--material-concrete)" strokeWidth={1} strokeDasharray="5 3" />
          ))}
        </g>
      ))}
    </g>
  );
}

// Plain nodes; heal affordance on collinear 2-wall joints (select tool).
export function PlanNodesLayer({ nodes, openEnds, model, tool, project, nearestNodeTag, onHeal }: {
  nodes: Map<string, GeoNode>;
  openEnds: Set<string>;
  model: Model;
  tool: string;
  project: (p: Vec2) => Vec2;
  nearestNodeTag: (p: Vec2) => string | null;
  onHeal: (tag: string) => void;
}) {
  return (
    <>
      {[...nodes.values()].filter((n) => !openEnds.has(n.id)).map((n) => {
        const [x, y] = project(n.p);
        const tag = tool === "select" ? nearestNodeTag(n.p) : null;
        const healable = tool === "select" && n.walls.length === 2 && collinearAt(n, model);
        return (
          <g key={n.id}>
            <circle
              cx={x} cy={y} r={healable ? 6 : 3.5}
              fill={healable ? NORDIC_ACCENT : NORDIC_LINE}
              opacity={healable ? 0.85 : 0.5}
              style={{ cursor: healable ? "pointer" : "default" }}
              onClick={healable && tag ? () => onHeal(tag) : undefined}
            />
            {healable && <title>Heal joint</title>}
          </g>
        );
      })}
    </>
  );
}

// Diagnostic markers. These used to be an unexplained glowing red dot; now each one names
// itself on click, and a *declared* open end reads as advisory rather than as an error
// (→ model/planWarnings.ts).
export function WarningMarkerLayer({ markers, activeKey, project, onOpen }: {
  markers: PlanWarningMarker[];
  activeKey: string | null;
  project: (p: Vec2) => Vec2;
  onOpen: (marker: PlanWarningMarker, event: React.MouseEvent) => void;
}) {
  return (
    <>
      {markers.map((marker) => {
        const [x, y] = project(marker.position);
        const active = activeKey === marker.key;
        const color = marker.tier === "error" ? "var(--error)"
          : marker.tier === "warn" ? "var(--warn, var(--error))" : NORDIC_ACCENT;
        return (
          <g key={marker.key} style={{ cursor: "pointer" }}
            onClick={(event) => onOpen(marker, event)}>
            <circle cx={x} cy={y} r={9} fill="transparent" />
            <circle cx={x} cy={y} r={active ? 8 : 6.5} fill={color}
              opacity={marker.tier === "info" ? 0.65 : 0.9}
              stroke="var(--canvas-white)" strokeWidth={1.5} />
            <text x={x} y={y + 3} fontSize={9} fontWeight={800} textAnchor="middle"
              fill="var(--canvas-white)" pointerEvents="none">?</text>
            <title>{marker.title} · {marker.id} — click for details</title>
          </g>
        );
      })}
    </>
  );
}

// Wall draft (start marker + rubber band + live length) and the snap indicator for the wall
// tool's next click.
export function WallDraftLayer({ draft, rubber, cursor, snapNodes, tolM, gridM, project }: {
  draft: WallDraft | null;
  rubber: RubberBand | null;
  cursor: Vec2 | null;
  snapNodes: Map<string, GeoNode>;
  tolM: number;
  gridM: number | null;
  project: (p: Vec2) => Vec2;
}) {
  return (
    <>
      {draft && (() => {
        const [sx, sy] = project(draft.start);
        const end = rubber?.end ?? draft.start;
        const [ex, ey] = project(end);
        const [mx, my] = [(sx + ex) / 2, (sy + ey) / 2];
        return (
          <g pointerEvents="none">
            <line x1={sx} y1={sy} x2={ex} y2={ey} stroke={NORDIC_ACCENT} strokeWidth={2}
              strokeDasharray="6 4" />
            <circle cx={sx} cy={sy} r={5} fill={NORDIC_ACCENT} />
            <circle cx={ex} cy={ey} r={5} fill="var(--canvas-white)" stroke={NORDIC_ACCENT} strokeWidth={2} />
            {rubber && rubber.len > 0.01 && (
              <text x={mx} y={my - 8} fill={NORDIC_INK} fontSize={12} textAnchor="middle"
                style={{ paintOrder: "stroke" }} stroke="var(--canvas-white)" strokeWidth={3}>
                {formatFtIn(rubber.len)}
              </text>
            )}
          </g>
        );
      })()}
      {cursor && (() => {
        const snap = snapWorld(cursor, snapNodes, tolM, gridM);
        if (!snap.nodeId && !gridM) return null;
        const [x, y] = project(snap.point);
        return <circle cx={x} cy={y} r={snap.nodeId ? 7 : 4} fill="none"
          stroke={snap.nodeId ? "var(--error)" : NORDIC_ACCENT} strokeWidth={1.5} pointerEvents="none" />;
      })()}
    </>
  );
}

// Detail markers (Phase 8): D-tags at junctions, shown in the DOCUMENT workspace.
export function DetailMarkerLayer({ model, activeStorey, project, onSelectWall }: {
  model: Model;
  activeStorey: string | null;
  project: (p: Vec2) => Vec2;
  onSelectWall: (wall: Wall) => void;
}) {
  return (
    <>
      {(model.conditions ?? []).map((c, i) => {
        const wall = model.walls.find((w) => c.elements.includes(w.tag) && w.storey === activeStorey);
        if (!wall) return null;
        const mid: Vec2 = [(wall.axis[0][0] + wall.axis[1][0]) / 2, (wall.axis[0][1] + wall.axis[1][1]) / 2];
        const [x, y] = project(mid);
        return (
          <g key={`detail-${c.key}`} pointerEvents="auto" style={{ cursor: "pointer" }}
            onClick={() => onSelectWall(wall)}>
            <circle cx={x} cy={y} r={9} fill="var(--canvas-white)" stroke={NORDIC_ACCENT} strokeWidth={1.5} />
            <text x={x} y={y + 3} fill={NORDIC_ACCENT} fontSize={9} textAnchor="middle" fontWeight={700}>
              D{i + 1}
            </text>
          </g>
        );
      })}
    </>
  );
}
