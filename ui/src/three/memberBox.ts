// The box a framing member occupies in scene space — the one piece of geometry every member
// surface agrees on. Extracted so the solid builders (three/members.ts) and the per-member
// pick highlight (three/memberPicking.ts) cannot drift apart: a highlight outline that does
// not sit exactly on the stud it outlines is worse than no highlight.
//
// Mirrors emit/gltf/emitter.py's add_member_box — vertical ends, sloped top/bottom for a
// raked member, a plain prism otherwise.
import * as THREE from "three";
import { crossWidth, isVerticalMember, MIN_PLAN_RUN_M } from "../model/memberFootprint";
import type { Member } from "../model/types";
import { projectPlanDirectionToScene, projectPointToScene, type PlanCenter } from "./planGeometry";

// Re-exported so the 3D layer keeps one import site for "which face does this member show":
// the rules themselves live in model/memberFootprint.ts, where the 2D plan reads them too.
export { crossWidth, isVerticalMember };

// Degenerate extents would collapse the instance matrix (and its normals); 0.1 mm is far
// below any real member dimension but keeps the basis invertible.
export const MIN_EXTENT_M = 1e-4;

// A unit box centred on its local origin in ALL THREE axes — every rect/i-joist instance is
// this geometry, scaled + rotated + translated per instance.
//
// The symmetry is the point. This box used to be base-at-origin on local Y only, which made
// the three axis slots of the matrix composer non-interchangeable: passing world-up into one
// of the two centred slots silently drew a member spanning z0 ± depth/2 instead of z0 → z1,
// i.e. half its own depth too low. That is exactly what happened to every horizontal member
// (11.875" rim bands ~6" low; the stair well partition plunging through the foundation).
// With every axis centred there is no special slot to get wrong: the caller states the box
// centre once, and each axis is a symmetric ±extent/2.
export const UNIT_BOX = new THREE.BoxGeometry(1, 1, 1);

const UP = new THREE.Vector3(0, 1, 0);
const _scale = new THREE.Vector3();

/** A member whose two ends sit at different elevations — a rafter, a raked plate. */
export function isRakedMember(m: Member): boolean {
  return m.z0_end_m != null || m.z1_end_m != null;
}

/**
 * Compose `target` as a box centred on `boxCenter`, extending ±extent/2 along each of
 * `xAxis`/`yAxis`/`zAxis` (which must already be mutually orthogonal unit vectors).
 * Every axis behaves identically — see UNIT_BOX for why that symmetry is load-bearing.
 */
export function composeCenteredBoxMatrix(
  target: THREE.Matrix4, boxCenter: THREE.Vector3,
  xAxis: THREE.Vector3, xExtent: number, yAxis: THREE.Vector3, yExtent: number,
  zAxis: THREE.Vector3, zExtent: number,
): THREE.Matrix4 {
  target.makeBasis(xAxis, yAxis, zAxis);
  target.scale(_scale.set(Math.max(xExtent, MIN_EXTENT_M), Math.max(yExtent, MIN_EXTENT_M),
    Math.max(zExtent, MIN_EXTENT_M)));
  target.setPosition(boxCenter);
  return target;
}

// Vertical member (p0 == p1): the free axis is world-up (its height). `orient` supplies
// the in-plan axis the solver placed it along (its width_m face); the through-member
// axis (depth_m) is perpendicular to that, both horizontal.
function composeVerticalBoxMatrix(target: THREE.Matrix4, m: Member, center: PlanCenter) {
  const [ox, oz] = m.orient ?? [1, 0];
  const orient = projectPlanDirectionToScene([ox, oz]).normalize();
  const perp = new THREE.Vector3(-orient.z, 0, orient.x);
  const boxCenter = projectPointToScene(m.p0, (m.z0_m + m.z1_m) / 2, center);
  return composeCenteredBoxMatrix(target, boxCenter, orient, m.width_m, UP, m.z1_m - m.z0_m,
    perp, m.depth_m);
}

// Horizontal member (p0 != p1): the free axis is its own p0->p1 direction. The through-member
// axis is in-plan perpendicular to that; the vertical axis is world-up, scaled by the engine's
// own z1-z0 (already the physically correct depth for this member, whether it's lying flat or
// standing on edge — see crossWidth for the horizontal face). The box centre is therefore the
// plan midpoint of p0->p1 at the member's mid-depth, so it occupies exactly z0..z1 the way
// emit/gltf/emitter.py's add_member_box does.
function composeHorizontalBoxMatrix(target: THREE.Matrix4, m: Member, center: PlanCenter) {
  const dx = m.p1[0] - m.p0[0];
  const dz = m.p1[1] - m.p0[1];
  const runLen = Math.hypot(dx, dz);
  const run = runLen > MIN_PLAN_RUN_M
    ? projectPlanDirectionToScene([dx / runLen, dz / runLen])
    : new THREE.Vector3(1, 0, 0);
  const across = new THREE.Vector3(-run.z, 0, run.x);
  const boxCenter = projectPointToScene(
    [(m.p0[0] + m.p1[0]) / 2, (m.p0[1] + m.p1[1]) / 2], (m.z0_m + m.z1_m) / 2, center);
  return composeCenteredBoxMatrix(target, boxCenter, across, crossWidth(m), run, runLen,
    UP, m.z1_m - m.z0_m);
}

/** The prismatic box of `m` as a full transform of UNIT_BOX — vertical or horizontal. */
export function composeMemberBoxMatrix(
  target: THREE.Matrix4, m: Member, center: PlanCenter,
): THREE.Matrix4 {
  return isVerticalMember(m)
    ? composeVerticalBoxMatrix(target, m, center)
    : composeHorizontalBoxMatrix(target, m, center);
}

/**
 * The 8 corners of a member's box in scene space: vertical ends, sloped top/bottom. Shared by
 * the vertex-coloured merge, the standing-seam merge and the pick highlight so all three
 * agree exactly. Null for a member with no plan run — a vertical member is a prism, so
 * composeMemberBoxMatrix describes it and this does not.
 */
export function rakedBoxVertices(m: Member, center: PlanCenter): [number, number, number][] | null {
  const a = projectPointToScene(m.p0, 0, center);
  const b = projectPointToScene(m.p1, 0, center);
  const ax = a.x, ay = a.z, bx = b.x, by = b.z;
  const az0 = m.z0_m, az1 = m.z1_m;
  const bz0 = m.z0_end_m ?? m.z0_m, bz1 = m.z1_end_m ?? m.z1_m;
  const dx = bx - ax, dy = by - ay;
  const run = Math.hypot(dx, dy);
  if (run < MIN_PLAN_RUN_M) return null;
  const half = crossWidth(m) / 2;
  const nx = (-dy / run) * half, ny = (dx / run) * half;
  return [
    [ax + nx, az0, ay + ny], [bx + nx, bz0, by + ny], [bx - nx, bz0, by - ny], [ax - nx, az0, ay - ny],
    [ax + nx, az1, ay + ny], [bx + nx, bz1, by + ny], [bx - nx, bz1, by - ny], [ax - nx, az1, ay - ny],
  ];
}

// These quads were authored for the old reflected project frame. Reverse their winding now
// that project-to-scene preserves handedness.
const BOX_FACES = [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]];

// Two triangles per quad, six quads per box. The merged member meshes lay their triangles out
// in exactly this order, which is what lets a raycast faceIndex divide back to a member.
export const TRIANGLES_PER_MEMBER_BOX = BOX_FACES.length * 2;

export function pushBoxIndices(indices: number[], base: number) {
  for (const [a, b, c, d] of BOX_FACES) {
    indices.push(base + a, base + c, base + b, base + a, base + d, base + c);
  }
}

/** A standalone BufferGeometry for one raked box — the pick highlight's outline source. */
export function rakedBoxGeometry(
  m: Member, center: PlanCenter,
): THREE.BufferGeometry | null {
  const verts = rakedBoxVertices(m, center);
  if (!verts) return null;
  const positions: number[] = [];
  for (const v of verts) positions.push(v[0], v[1], v[2]);
  const indices: number[] = [];
  pushBoxIndices(indices, 0);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}
