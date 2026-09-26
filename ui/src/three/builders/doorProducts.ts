// Door products beyond the four-piece frame: the concealed (trimless) frame and lever sets.
// Mirrors resolve/geometry_door_products.py box for box — change both. Every box is laid out
// in the wall frame: `along` from the opening centre, `normal` along the wall's LEFT normal.
//
// Handing: unflipped, the leaf hangs on the END-node jamb and sweeps toward the left normal.
import type { Opening, Wall } from "../../model/types";

export type AddBox = (width: number, height: number, thickness: number, along: number,
  elevation: number, normalOffset: number) => void;

// --- concealed frame (EzyJamb-type: flush on the pull side, rebated on the push side) ------
const CONCEALED_JAMB_M = 0.016;
const SHADOW_GAP_M = 0.003;
const CONCEALED_STOP_M = 0.013;
const SHADOW_STRIP_DEPTH_M = 0.006;
const CONCEALED_UNDERCUT_M = 0.019;
const CONCEALED_LEAF_THICKNESS_M = 0.045;

// --- lever set (square rose, lever returning toward the hinge) ----------------------------
const LEVER_HEIGHT_M = 0.914;
const LEVER_BACKSET_M = 0.060;
const ROSE_SIZE_M = 0.064;
const ROSE_PROUD_M = 0.010;
const LEVER_STANDOFF_M = 0.055;
const LEVER_LENGTH_M = 0.120;
const LEVER_SECTION_M = 0.016;
const LEVER_NECK_M = 0.014;

/** `[low, high]` normal offsets of the wall's two outermost faces, or null. */
export function finishFaces(wall: Wall): [number, number] | null {
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  const layers = wall.layers.filter((layer) => !layer.is_cavity);
  if (length < 1e-9 || !layers.length) return null;
  const nx = -(y1 - y0) / length, ny = (x1 - x0) / length;
  const offsets = layers.flatMap((layer) =>
    layer.polygon.map(([px, py]) => (px - x0) * nx + (py - y0) * ny));
  return offsets.length ? [Math.min(...offsets), Math.max(...offsets)] : null;
}

/** `[hingeSign, swingSign]`: hinge on the +along jamb and swing toward +normal at +1. */
export function handing(opening: Opening): [number, number] {
  return [opening.flip_hinge ? -1 : 1, opening.flip_swing ? -1 : 1];
}

/** `[leafWidth, leafHeight, bottomZ, flushFace, backFace]` of a concealed-frame leaf. */
export function concealedLeaf(faces: [number, number], swingSign: number, width: number,
  baseZ: number, height: number): [number, number, number, number, number] {
  const flush = swingSign > 0 ? faces[1] : faces[0];
  const back = flush - swingSign * CONCEALED_LEAF_THICKNESS_M;
  const bottom = baseZ + CONCEALED_UNDERCUT_M;
  const top = baseZ + height - CONCEALED_JAMB_M - SHADOW_GAP_M;
  return [width - 2 * (CONCEALED_JAMB_M + SHADOW_GAP_M), top - bottom, bottom, flush, back];
}

/** Liner, leaf, stop and shadow strips; each group goes to its own `AddBox`. */
export function buildConcealedFrame(faces: [number, number], swingSign: number, width: number,
  baseZ: number, height: number,
  add: { liner: AddBox; leaf: AddBox; stop: AddBox; shadow: AddBox }) {
  const [lo, hi] = faces;
  const depth = hi - lo, mid = (hi + lo) / 2;
  const j = CONCEALED_JAMB_M, g = SHADOW_GAP_M, p = CONCEALED_STOP_M;
  const [leafW, leafH, leafZ0, flush, back] = concealedLeaf(faces, swingSign, width, baseZ, height);
  const push = swingSign > 0 ? lo : hi;
  const headZ = baseZ + height;
  add.liner(j, height, depth, -width / 2 + j / 2, baseZ + height / 2, mid);
  add.liner(j, height, depth, width / 2 - j / 2, baseZ + height / 2, mid);
  add.liner(width - 2 * j, j, depth, 0, headZ - j / 2, mid);
  add.leaf(leafW, leafH, CONCEALED_LEAF_THICKNESS_M, 0, leafZ0 + leafH / 2, (flush + back) / 2);
  const stripFar = back - swingSign * SHADOW_STRIP_DEPTH_M;
  const stripT = Math.abs(stripFar - back), stripN = (stripFar + back) / 2;
  const stopT = Math.abs(push - stripFar), stopN = (push + stripFar) / 2;
  const stopH = headZ - j - leafZ0;
  const inner = width / 2 - j;
  for (const side of [-1, 1]) {
    add.shadow(g, stopH - g, stripT, side * (inner - g / 2), leafZ0 + (stopH - g) / 2, stripN);
    add.stop(p, stopH, stopT, side * (inner - p / 2), leafZ0 + stopH / 2, stopN);
  }
  add.shadow(2 * inner, g, stripT, 0, headZ - j - g / 2, stripN);
  add.stop(2 * (inner - p), p, stopT, 0, headZ - j - p / 2, stopN);
}

/** A rose, neck and lever on each face of one leaf, the lever pointing at the hinge. */
export function buildLeverSet(add: AddBox, latchAlong: number, towardHinge: number,
  leafFaces: [number, number], floorZ: number) {
  const roseAlong = latchAlong + towardHinge * LEVER_BACKSET_M;
  const z = floorZ + LEVER_HEIGHT_M;
  const lo = Math.min(...leafFaces), hi = Math.max(...leafFaces);
  const neckLen = LEVER_STANDOFF_M - ROSE_PROUD_M - LEVER_SECTION_M / 2;
  for (const [face, out] of [[hi, 1], [lo, -1]] as const) {
    add(ROSE_SIZE_M, ROSE_SIZE_M, ROSE_PROUD_M, roseAlong, z, face + out * ROSE_PROUD_M / 2);
    add(LEVER_NECK_M, LEVER_NECK_M, neckLen, roseAlong, z,
      face + out * (ROSE_PROUD_M + neckLen / 2));
    add(LEVER_LENGTH_M, LEVER_SECTION_M, LEVER_SECTION_M,
      roseAlong + towardHinge * (LEVER_LENGTH_M / 2 - LEVER_NECK_M / 2), z,
      face + out * LEVER_STANDOFF_M);
  }
}
