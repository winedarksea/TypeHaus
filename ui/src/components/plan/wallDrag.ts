// Wall-body drag maths (P5): a wall moves only along its own normal, so both nodes translate
// by one perpendicular vector. Pure, so the gesture is testable without a DOM.
import type { Vec2 } from "../../model/types";

/** Snap step when no grid is active: 1/2" (the precision `_point_expr_m` round-trips). */
export const WALL_DRAG_FALLBACK_STEP_M = 0.0127;

/** Unit normal of the axis (left of start → end); null for a degenerate axis. */
export function wallNormal(axis: [Vec2, Vec2]): Vec2 | null {
  const dx = axis[1][0] - axis[0][0];
  const dy = axis[1][1] - axis[0][1];
  const len = Math.hypot(dx, dy);
  return len < 1e-9 ? null : [-dy / len, dx / len];
}

/** Signed travel of the pointer (from → to) along the wall's normal, in metres. */
export function perpendicularOffset(axis: [Vec2, Vec2], from: Vec2, to: Vec2): number {
  const n = wallNormal(axis);
  return n ? (to[0] - from[0]) * n[0] + (to[1] - from[1]) * n[1] : 0;
}

/** Round an offset to the grid (or the fallback step); -0 folds to 0. */
export function snapOffset(offset: number, gridM: number | null): number {
  const step = gridM && gridM > 0 ? gridM : WALL_DRAG_FALLBACK_STEP_M;
  return Math.round(offset / step) * step || 0;
}

/** The move_nodes delta for an offset along the normal. */
export function offsetDelta(axis: [Vec2, Vec2], offset: number): Vec2 {
  const n = wallNormal(axis);
  return n ? [n[0] * offset, n[1] * offset] : [0, 0];
}

/** Axis spans (metres along the wall) left grabbable around hosted openings, so a tap on a
 * door or window in the selected wall still reaches the opening underneath. */
export function bodySpans(length: number, openings: { center_along_m: number; width_m: number }[]): [number, number][] {
  const gaps = openings
    .map((o) => [o.center_along_m - o.width_m / 2, o.center_along_m + o.width_m / 2] as [number, number])
    .sort((a, b) => a[0] - b[0]);
  const spans: [number, number][] = [];
  let at = 0;
  for (const [g0, g1] of gaps) {
    if (g0 > at) spans.push([at, Math.min(g0, length)]);
    at = Math.max(at, g1);
  }
  if (at < length) spans.push([at, length]);
  return spans.filter(([a, b]) => b - a > 1e-6);
}
