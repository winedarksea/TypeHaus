// The wall's own local frame, and the arch-head circle math that rides in it.
//
// Split out of builders/walls.ts on 2026-08-21, when the voussoir arch rings in
// builders/archRing.ts needed the same frame and the same soffit circle. Keeping these in
// walls.ts would have made the two modules import each other; walls.ts re-exports the arch
// helpers so callers and tests that already knew them there still find them.
//
// "Local" here means the frame ExtrudeGeometry works in and `wallLocalToSceneMatrix` maps
// out of: x runs ALONG the wall axis from its start node, y is absolute elevation, and z is
// distance ACROSS the wall measured inward from its maximum-across face.
import * as THREE from "three";
import type { Wall } from "../../model/types";
import type { PlanCenter } from "../planGeometry";

/** The datum every sill is measured up from.
 *
 * A framed wall whose skin was dropped to lap the foundation below it carries a `z0_m`
 * under its own floor — the cladding reaches down over the mudsill and rim, the framing
 * does not (→ resolve/platform.py::extend_walls_to_foundation). `plate_base_z_m` is where
 * the framing starts, so it, not `z0_m`, is the floor an opening's `sill_m` rises from.
 * Mirrors `ResolvedWall.base_ref_z_m`; using `z0_m` here drops every opening on an
 * extended wall by the mudsill+rim depth while its framing stays put.
 */
export function baseRefZ(w: Wall): number {
  return w.plate_base_z_m ?? w.z0_m;
}


// Arch tessellation for one continuous viewer mesh; no internal wall-piece seams are emitted.
// The segment count is derived per arch from its radius (archSoffitSegmentCount) so that a
// soffit facet never strays further than this from the true circle, whatever the arch's size.
export const ARCH_SOFFIT_CHORD_TOLERANCE_M = 0.0005;
export const ARCH_SOFFIT_MIN_SEGMENT_COUNT = 24;
export const ARCH_SOFFIT_MAX_SEGMENT_COUNT = 192;
// Junction resolution splits a layer ring's straight edges at every crossing wall. A vertex
// this far off the chord between its neighbours is a real corner; anything closer is padding.
export const COLLINEAR_VERTEX_TOLERANCE_M = 1e-6;

// Drop vertices that sit on the straight line between their neighbours. Junction resolution
// splits a wall layer's long edges at every crossing wall, so an authored rectangle serializes
// as five, six or eight points (the 16" sunken-garden arch wall arrives as six). Anything that
// needs to *recognise* a rectangle has to reduce first. Mirrors `_without_collinear_vertices`
// in packages/engine/src/typehaus/emit/gltf/emitter.py — keep the two in step.
export function withoutCollinearVertices(
  polygon: readonly (readonly [number, number])[],
  toleranceM: number = COLLINEAR_VERTEX_TOLERANCE_M,
): [number, number][] {
  const ring: [number, number][] = [];
  for (const [x, y] of polygon) {
    const last = ring[ring.length - 1];
    if (!last || Math.hypot(x - last[0], y - last[1]) > toleranceM) ring.push([x, y]);
  }
  while (ring.length > 1 && Math.hypot(ring[0][0] - ring[ring.length - 1][0],
    ring[0][1] - ring[ring.length - 1][1]) <= toleranceM) ring.pop();
  if (ring.length < 3) return ring;
  const corners: [number, number][] = [];
  for (let index = 0; index < ring.length; index++) {
    const [px, py] = ring[(index - 1 + ring.length) % ring.length];
    const [cx, cy] = ring[index];
    const [nextX, nextY] = ring[(index + 1) % ring.length];
    const spanX = nextX - px, spanY = nextY - py;
    const span = Math.hypot(spanX, spanY);
    // Perpendicular distance, in metres, of this vertex from the chord between its neighbours.
    const offset = span < toleranceM
      ? Math.hypot(cx - px, cy - py)
      : Math.abs((cx - px) * spanY - (cy - py) * spanX) / span;
    if (offset > toleranceM) corners.push([cx, cy]);
  }
  return corners;
}

/**
 * A wall layer's footprint expressed in the wall's own frame: the axis start and its unit
 * vectors, plus the layer's extent along and across. `null` when the footprint is not a
 * plain rectangle in that frame — a junction-mitered or otherwise non-rectangular layer,
 * which neither the swept-arch path nor the arch ring can be built against.
 */
export interface WallLocalFrame {
  startX: number; startY: number;
  alongX: number; alongY: number;
  acrossX: number; acrossY: number;
  minAlong: number; maxAlong: number;
  minAcross: number; maxAcross: number;
}

export function wallLocalFrame(
  wall: Wall, polygon: readonly (readonly [number, number])[],
): WallLocalFrame | null {
  const [[sx, sy], [ex, ey]] = wall.axis;
  const length = Math.hypot(ex - sx, ey - sy);
  if (length < 1e-9) return null;
  const ux = (ex - sx) / length, uy = (ey - sy) / length;
  const nx = -uy, ny = ux;
  // A padded ring is still a rectangle; only its *corners* decide whether it can be swept.
  const footprint = withoutCollinearVertices(polygon);
  if (footprint.length !== 4) return null;
  const local = footprint.map(([x, y]) => [
    (x - sx) * ux + (y - sy) * uy,
    (x - sx) * nx + (y - sy) * ny,
  ] as const);
  const alongs = local.map(([along]) => along), acrosses = local.map(([, across]) => across);
  const minAlong = Math.min(...alongs), maxAlong = Math.max(...alongs);
  const minAcross = Math.min(...acrosses), maxAcross = Math.max(...acrosses);
  const corners = new Set(local.map(([along, across]) => `${along.toFixed(8)},${across.toFixed(8)}`));
  if (corners.size !== 4 || ![
    [minAlong, minAcross], [minAlong, maxAcross], [maxAlong, minAcross], [maxAlong, maxAcross],
  ].every(([along, across]) => corners.has(`${along.toFixed(8)},${across.toFixed(8)}`))) return null;
  return {
    startX: sx, startY: sy, alongX: ux, alongY: uy, acrossX: nx, acrossY: ny,
    minAlong, maxAlong, minAcross, maxAcross,
  };
}

// Map local (along, elevation, inward-from-max-across) into scene space. Building from the
// maximum-across face toward the minimum-across face is what keeps this matrix right-handed
// while project north maps to scene -Z.
export function wallLocalToSceneMatrix(frame: WallLocalFrame, center: PlanCenter): THREE.Matrix4 {
  const { startX, startY, alongX, alongY, acrossX, acrossY, maxAcross } = frame;
  return new THREE.Matrix4().set(
    alongX, 0, -acrossX, startX + acrossX * maxAcross - center[0],
    0, 1, 0, 0,
    -alongY, 0, acrossY, center[1] - startY - acrossY * maxAcross,
    0, 0, 0, 1,
  );
}

// Segments for a half-circle soffit sampled at even angular steps. One step's mid-chord sagitta
// is r·(1 − cos(π/2n)), so inverting it ties tessellation to the arch's actual size instead of a
// flat guess: an 8'-wide garden arch and a small niche head come out equally smooth. Mirrors
// `_arch_soffit_segment_count` in the glTF emitter.
export function archSoffitSegmentCount(radiusM: number, halfAngleRad = Math.PI / 2): number {
  if (!(radiusM > ARCH_SOFFIT_CHORD_TOLERANCE_M)) return ARCH_SOFFIT_MIN_SEGMENT_COUNT;
  const halfStep = Math.acos(Math.max(-1, 1 - ARCH_SOFFIT_CHORD_TOLERANCE_M / radiusM));
  return Math.min(ARCH_SOFFIT_MAX_SEGMENT_COUNT,
    Math.max(ARCH_SOFFIT_MIN_SEGMENT_COUNT, Math.ceil(halfAngleRad / halfStep)));
}

// The circle through both springlines and the crown of an arch of half-span `halfSpanM` rising
// `riseM` above them: [radius, half-angle, how far the centre sits below the springline].
//
// This is what makes a *segmental* arch possible. The soffit used to be hard-wired to a
// half-circle of width/2, so `arch_rise_m` only chose where the springline sat and every head
// came out semicircular however shallow the rise said it was. A rise at or above the half-span
// is the semicircle and is clamped to it. Mirrors `arch_soffit_circle` in the engine
// (resolve/geometry_prims.py) — keep the two in step.
export function archSoffitCircle(
  halfSpanM: number, riseM: number,
): { radiusM: number; halfAngleRad: number; depthM: number } {
  const span = Math.max(halfSpanM, 1e-9);
  const rise = Math.min(Math.max(riseM, 1e-9), span);
  const radiusM = (span * span + rise * rise) / (2 * rise);
  return {
    radiusM,
    halfAngleRad: Math.asin(Math.max(-1, Math.min(1, span / radiusM))),
    depthM: radiusM - rise,
  };
}

// One soffit sample as (offset from the arch centreline, height above the springline). The arc
// is walked by *angle*: stepping evenly in x collapses near the springlines, where a semicircle
// turns vertical, so the last step alone dropped ~40 cm on the catlin arches — the striping.
// Mirrors `_arch_soffit_sample` in the glTF emitter.
// Sweeping −halfAngle..+halfAngle and subtracting the circle's depth below the springline
// generalises this to a segmental arch; at the default π/2 the depth is zero and this is the
// same half-circle it always was, merely parameterised from the centre out.
export function archSoffitSample(
  segment: number, segmentCount: number, radiusM: number, halfAngleRad = Math.PI / 2,
): { offsetM: number; heightM: number } {
  const angle = -halfAngleRad + 2 * halfAngleRad * segment / segmentCount;
  return {
    offsetM: radiusM * Math.sin(angle),
    heightM: radiusM * Math.cos(angle) - radiusM * Math.cos(halfAngleRad),
  };
}
