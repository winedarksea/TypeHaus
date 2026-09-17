// Wall-face maths for a placeable: snap a free object flush to the nearest wall face on
// release, and slide a wall-attached object along its host. The face offset is read from the
// resolved layer polygons, the same rule resolve/placeables.py::_resolve_location uses, so a
// snapped object lands where an attachment to that face would put it. Snapping does not
// create an attachment.
import type { Vec2, Wall } from "../../model/types";
import type { WallSnapConfig } from "./editorConfig";

export interface WallFrame {
  origin: Vec2;
  tangent: Vec2;
  left: Vec2; // left normal of the axis
  length: number;
  angleDeg: number;
}

export function wallFrame(wall: Wall): WallFrame | null {
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return null;
  const tangent: Vec2 = [(x1 - x0) / length, (y1 - y0) / length];
  return {
    origin: [x0, y0], tangent, left: [-tangent[1], tangent[0]], length,
    angleDeg: Math.atan2(tangent[1], tangent[0]) * 180 / Math.PI,
  };
}

const dot = (a: Vec2, b: Vec2) => a[0] * b[0] + a[1] * b[1];
const sub = (a: Vec2, b: Vec2): Vec2 => [a[0] - b[0], a[1] - b[1]];

// Metres along the axis from its start, clamped onto the wall.
export function stationOnWall(frame: WallFrame, point: Vec2): number {
  return Math.min(frame.length, Math.max(0, dot(sub(point, frame.origin), frame.tangent)));
}

export function pointOnWall(frame: WallFrame, station: number, normalOffset: number): Vec2 {
  return [
    frame.origin[0] + frame.tangent[0] * station + frame.left[0] * normalOffset,
    frame.origin[1] + frame.tangent[1] * station + frame.left[1] * normalOffset,
  ];
}

// A wall-attached object dragged to `cursorCentre` keeps its distance off the wall and moves
// only along it: the station is what `slide_placeable` commits.
export function slideAlongWall(frame: WallFrame, currentCentre: Vec2, cursorCentre: Vec2): { station: number; centre: Vec2 } {
  const station = stationOnWall(frame, cursorCentre);
  const offset = dot(sub(currentCentre, frame.origin), frame.left);
  return { station, centre: pointOnWall(frame, station, offset) };
}

export interface WallSnap {
  wall: Wall;
  centre: Vec2; // where the object sits flush against the face
  rotation: number; // squared to the wall
  facePoint: Vec2; // the face point opposite the object, for the guide line
  gapM: number; // signed distance from the object's wallward edge to the face (+ = in the room)
  snapped: boolean; // within the snap band
}

function footprintCorners(footprint: [number, number], rotationDeg: number): Vec2[] {
  const [w, d] = footprint;
  const radians = rotationDeg * Math.PI / 180;
  const cos = Math.cos(radians);
  const sin = Math.sin(radians);
  return ([[-w / 2, -d / 2], [w / 2, -d / 2], [w / 2, d / 2], [-w / 2, d / 2]] as Vec2[])
    .map(([px, py]) => [px * cos - py * sin, px * sin + py * cos]);
}

// The nearest wall face within the guide band, or null. Only an object already within
// `parallelDeg` of square to a wall snaps to it; a deliberately skewed object is left alone.
export function snapToWall(
  centre: Vec2, rotation: number, footprint: [number, number], walls: Wall[], cfg: WallSnapConfig,
): WallSnap | null {
  let best: WallSnap | null = null;
  for (const wall of walls) {
    const frame = wallFrame(wall);
    if (!frame) continue;
    const along = dot(sub(centre, frame.origin), frame.tangent);
    if (along < 0 || along > frame.length) continue;
    const relative = rotation - frame.angleDeg;
    const quarter = Math.round(relative / 90) * 90;
    if (Math.abs(relative - quarter) > cfg.parallelDeg) continue;
    const squared = rotation + (quarter - relative);
    const offsets = wall.layers.flatMap((layer) => layer.polygon.map((p) => dot(sub(p, frame.origin), frame.left)));
    const centreOffset = dot(sub(centre, frame.origin), frame.left);
    const side = centreOffset >= 0 ? 1 : -1;
    const faceOffset = offsets.length ? (side > 0 ? Math.max(...offsets) : Math.min(...offsets)) : 0;
    const projections = footprintCorners(footprint, squared).map((corner) => dot(corner, frame.left));
    const wallward = side > 0 ? Math.min(...projections) : Math.max(...projections);
    const flushOffset = faceOffset - wallward;
    const gapM = side * (centreOffset - flushOffset);
    if (Math.abs(gapM) > cfg.guideM) continue;
    if (best && Math.abs(best.gapM) <= Math.abs(gapM)) continue;
    best = {
      wall, rotation: squared, gapM, snapped: Math.abs(gapM) <= cfg.snapM,
      centre: pointOnWall(frame, along, flushOffset),
      facePoint: pointOnWall(frame, along, faceOffset),
    };
  }
  return best;
}

// An arrow nudge on an attached object: the signed slide when the nudge runs along the wall,
// null when it points across it (that would be a detach).
export function slideForNudge(frame: WallFrame, nudge: Vec2): number | null {
  const length = Math.hypot(nudge[0], nudge[1]);
  if (length < 1e-12) return null;
  const along = dot(nudge, frame.tangent);
  return Math.abs(along) >= length * Math.SQRT1_2 ? Math.sign(along) * length : null;
}
