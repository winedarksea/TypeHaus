// The Place tool's cursor ghost: the armed type's glyph at half opacity under the pointer,
// with the same wall guide a drag shows (solid = a tap here lands flush on that face).
// Client-side only; nothing is sent until the tap.
import type { CanvasObjectType, Vec2, Wall } from "../../model/types";
import { NORDIC_ACCENT } from "../../nordic/palette";
import { WALL_SNAP_CONFIG } from "./editorConfig";
import { DEFAULT_FOOTPRINT_M, PlaceableGlyph } from "./PlaceableGlyph";
import { snapToWall } from "./wallSnap";

export function PlaceableGhost({ type, cursor, rotation, walls, project, scale }: {
  type: CanvasObjectType;
  cursor: Vec2;
  rotation: number;
  walls: Wall[];
  project: (point: Vec2) => Vec2;
  scale: number;
}) {
  const [x, y] = project(cursor);
  const snap = snapToWall(cursor, rotation, type.footprint_m ?? DEFAULT_FOOTPRINT_M, walls, WALL_SNAP_CONFIG);
  const guideEnd = snap ? project(snap.facePoint) : null;
  return <g pointerEvents="none" data-placeable-ghost={type.tag}>
    <g opacity={0.5}>
      <PlaceableGlyph type={type} domain={type.domain} x={x} y={y} scale={scale} rotation={rotation} />
    </g>
    {guideEnd && <line x1={x} y1={y} x2={guideEnd[0]} y2={guideEnd[1]} stroke={NORDIC_ACCENT}
      strokeWidth={snap!.snapped ? 2 : 1.5} strokeDasharray={snap!.snapped ? undefined : "4 3"} />}
  </g>;
}
