// The plan-view footprint of a framing member: the polygon it covers when the drawing looks
// straight down at it. The TS twin of resolve/framing/footprint.py's member_footprint, which
// the interference check already trusts for exactly this question.
//
// The vertical case is the reason this exists. A stud seen end-on has no plan run at all, so
// "the axis swept by half a width" degenerates to a point and the plan drew it as a
// zero-length line — the end-cut, the one thing a framing plan is *for*, was missing.

import type { Member, Vec2 } from "./types";

// Below this a plan run is no run at all: the member stands vertical (a stud, a post) and its
// mark is a rectangle around p0 rather than a band along p0->p1.
export const MIN_PLAN_RUN_M = 1e-9;

/** A member standing vertical — p0 and p1 are the same point in plan. */
export function isVerticalMember(m: Member): boolean {
  return m.p0[0] === m.p1[0] && m.p0[1] === m.p1[1];
}

// How far a member's vertical extent may miss its section thickness and still count as
// flat-laid. Mirrors FLAT_LAID_TOLERANCE_M in resolve/framing/profiles.py — the house's flat
// members land within 1e-8 m of their thickness and the nearest on-edge member is 0.021 m
// away, so 0.1 mm separates the two with three orders of margin on both sides.
export const FLAT_LAID_TOLERANCE_M = 1e-4;

// Lying-flat members (plates, rough sills, blocking courses) put their wide face (depth_m)
// across the wall; on-edge members (headers/joists/rims/beams) put their thin face (width_m)
// across instead. For a vertical member this is also its thin plan dimension — the one a
// level-of-detail switch has to measure, because it is the first to fall below a pixel.
//
// The member's own vertical extent states which way it was laid, so read that — naming flat
// *categories* instead misses any flat category nobody remembered to list, and drifts again
// each time the solver grows a category.
// The Python twin is plan_cross_section_m in resolve/framing/profiles.py.
export function crossWidth(m: Member): number {
  // z0_m..z1_m is the extent at one station, not the rise of a raked member end to end: a
  // rafter climbs meters along its run while its section never changes.
  return Math.abs(m.z1_m - m.z0_m - m.width_m) <= FLAT_LAID_TOLERANCE_M ? m.depth_m : m.width_m;
}

/**
 * A member's plan footprint ring, in model meters. Empty only for a degenerate member with
 * no usable cross-section; every caller should be prepared to fall back to the centreline.
 */
export function memberFootprint(m: Member): Vec2[] {
  // The resolver already cut this shape (a bevelled rafter tail, a mitred trim band): trust it.
  if (m.plan_outline && m.plan_outline.length >= 3) return m.plan_outline;

  const [x0, y0] = m.p0;
  const [x1, y1] = m.p1;
  const run = Math.hypot(x1 - x0, y1 - y0);
  const halfWidth = m.width_m / 2;
  const halfDepth = m.depth_m / 2;

  if (run < MIN_PLAN_RUN_M) {
    // Vertical member: an oriented width_m x depth_m rectangle centred on p0. Per the engine's
    // profile convention `orient` is the *thickness* (width) axis — for a stud that is the
    // wall-run direction (1.5" along the wall), with the wide depth face (5.5") running
    // perpendicular, through the wall. Putting depth along `orient` instead would draw every
    // stud rotated 90°, so a king/jack pack would read as a smear across the wall face.
    const [ox, oy] = m.orient ?? [0, 0];
    const orientLength = Math.hypot(ox, oy);
    if (orientLength > MIN_PLAN_RUN_M) {
      const ux = ox / orientLength, uy = oy / orientLength; // width axis — along the wall
      const px = -uy, py = ux;                              // depth axis — through the wall
      return [
        [x0 + ux * halfWidth + px * halfDepth, y0 + uy * halfWidth + py * halfDepth],
        [x0 - ux * halfWidth + px * halfDepth, y0 - uy * halfWidth + py * halfDepth],
        [x0 - ux * halfWidth - px * halfDepth, y0 - uy * halfWidth - py * halfDepth],
        [x0 + ux * halfWidth - px * halfDepth, y0 + uy * halfWidth - py * halfDepth],
      ];
    }
    // No orientation to align to — an axis-aligned rectangle is the honest fallback.
    return [
      [x0 - halfWidth, y0 - halfDepth], [x0 + halfWidth, y0 - halfDepth],
      [x0 + halfWidth, y0 + halfDepth], [x0 - halfWidth, y0 + halfDepth],
    ];
  }

  // Horizontal/sloped member: a band of its plan-visible cross dimension along p0->p1.
  const half = crossWidth(m) / 2;
  const nx = (-(y1 - y0) / run) * half;
  const ny = ((x1 - x0) / run) * half;
  return [[x0 - nx, y0 - ny], [x0 + nx, y0 + ny], [x1 + nx, y1 + ny], [x1 - nx, y1 - ny]];
}
