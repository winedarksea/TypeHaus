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
// The symmetry is the point: with every axis centred there is no special slot in the matrix
// composer to get wrong — a base-at-origin axis would make world-up in one of the centred
// slots draw a member spanning z0 ± depth/2 instead of z0 → z1, half its own depth too low.
// The caller states the box centre once, and each axis is a symmetric ±extent/2.
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

// Two triangles per quad, six quads per box. Kept for the box case; picking no longer divides
// by it (→ memberPicking.ts), because a merge may now hold members of different shapes.
export const TRIANGLES_PER_MEMBER_BOX = BOX_FACES.length * 2;

export function pushBoxIndices(indices: number[], base: number) {
  for (const [a, b, c, d] of BOX_FACES) {
    indices.push(base + a, base + c, base + b, base + a, base + d, base + c);
  }
}

type Corner = [number, number, number];

/** A birdsmouthed member's notched elevation in (s along the run, z), and its scene frame. */
interface SeatedProfile {
  points: [number, number][];
  /** The same outline as convex pieces (tail, seat, main run), so a band clip cannot bridge. */
  pieces: [number, number][][];
  near: THREE.Vector3;
  ux: number;
  uz: number;
  /** Soffit at the bearing end and its rise per metre of run: the line plies are offset from. */
  soffit: number;
  slope: number;
}

/**
 * Mirrors `resolve/geometry_members.py::_seated_sweep` — the member less one triangle: the
 * plumb heel cut on the plate's outer face, and the flat seat inward from it to where the
 * underside meets the plate top. Walking: bearing-end top, far top, far bottom, seat's inner
 * end, heel's foot, heel's head, bearing-end bottom, coincident points dropped. Null when the
 * member carries no seat, has no plan run, or nothing lies below the plate top to cut.
 */
function seatedProfile(m: Member, center: PlanCenter): SeatedProfile | null {
  const seat = m.seat;
  if (!seat) return null;
  const a = projectPointToScene(m.p0, 0, center);
  const b = projectPointToScene(m.p1, 0, center);
  const run = Math.hypot(m.p1[0] - m.p0[0], m.p1[1] - m.p0[1]);
  if (run < MIN_PLAN_RUN_M) return null;
  // Which end bears: the one the heel sits nearer to, in the plan frame.
  const d0 = Math.hypot(seat.heel[0] - m.p0[0], seat.heel[1] - m.p0[1]);
  const d1 = Math.hypot(seat.heel[0] - m.p1[0], seat.heel[1] - m.p1[1]);
  const nearP0 = d0 <= d1;
  const near = nearP0 ? a : b;
  const far = nearP0 ? b : a;
  const z0Near = nearP0 ? m.z0_m : (m.z0_end_m ?? m.z0_m);
  const z1Near = nearP0 ? m.z1_m : (m.z1_end_m ?? m.z1_m);
  const z0Far = nearP0 ? (m.z0_end_m ?? m.z0_m) : m.z0_m;
  const z1Far = nearP0 ? (m.z1_end_m ?? m.z1_m) : m.z1_m;
  const slope = (z0Far - z0Near) / run;
  const heelS = Math.min(d0, d1);
  const endS = heelS + seat.seat_run_m;
  const top = seat.plate_top_z_m;
  const bottom = (s: number) => z0Near + slope * s;
  if (bottom(heelS) >= top - MIN_EXTENT_M || endS >= run) return null;
  const points = dedupe([
    [0, z1Near], [run, z1Far], [run, z0Far], [endS, bottom(endS)],
    [endS, top], [heelS, top], [heelS, bottom(heelS)], [0, z0Near],
  ]);
  const upper = (s: number) => z1Near + (z1Far - z1Near) * s / run;
  const pieces = [
    [[0, z0Near], [heelS, bottom(heelS)], [heelS, upper(heelS)], [0, z1Near]],
    [[heelS, top], [endS, top], [endS, upper(endS)], [heelS, upper(heelS)]],
    [[endS, bottom(endS)], [run, z0Far], [run, z1Far], [endS, upper(endS)]],
  ] as [number, number][][];
  return { points, pieces, near, ux: (far.x - near.x) / run, uz: (far.z - near.z) / run,
    soffit: z0Near, slope };
}

function dedupe(points: [number, number][]): [number, number][] {
  const out: [number, number][] = [];
  const apart = (p: number[], q: number[]) => Math.hypot(p[0] - q[0], p[1] - q[1]) > MIN_EXTENT_M;
  for (const point of points) if (!out.length || apart(point, out[out.length - 1])) out.push(point);
  if (out.length > 1 && !apart(out[0], out[out.length - 1])) out.pop();
  return out;
}

/** The profile's ring twice, `width` apart across the run: the vertex layout sweeps index. */
function extrudeAcross(p: SeatedProfile, points: [number, number][], width: number): Corner[] {
  const half = width / 2;
  const nx = -p.uz * half, nz = p.ux * half;
  const ring = points.map(([s, y]): Corner => [p.near.x + p.ux * s, y, p.near.z + p.uz * s]);
  return [
    ...ring.map(([x, y, z]): Corner => [x + nx, y, z + nz]),
    ...ring.map(([x, y, z]): Corner => [x - nx, y, z - nz]),
  ];
}

/** The corners of a birdsmouthed member: its notched profile across its own width. */
export function seatedProfileVertices(m: Member, center: PlanCenter): Corner[] | null {
  const profile = seatedProfile(m, center);
  return profile ? extrudeAcross(profile, profile.points, crossWidth(m)) : null;
}

/**
 * A birdsmouthed I-joist as its three plies — bottom flange, web, top flange — each the notched
 * profile's convex pieces clipped to its band of the section, so the seat cut reads AND the
 * joist still reads as an I. Bands are measured perpendicular to the run off the soffit, as
 * `buildIJoists` stacks them. Null when the member is not seated.
 */
export function seatedIJoistParts(m: Member, center: PlanCenter): Corner[][] | null {
  const p = seatedProfile(m, center);
  if (!p) return null;
  const cos = 1 / Math.hypot(1, p.slope);
  const depth = (m.z1_m - m.z0_m) * cos;
  const flangeT = m.flange_thickness_m ?? depth * 0.1;
  const flangeW = m.flange_width_m ?? m.width_m;
  const webT = m.web_thickness_m ?? Math.min(flangeW, 0.01);
  const bands: [number, number, number][] = [
    [0, flangeT, flangeW], [flangeT, depth - flangeT, webT], [depth - flangeT, depth, flangeW]];
  const offset = ([s, z]: [number, number]) => (z - p.soffit - p.slope * s) * cos;
  const parts: Corner[][] = [];
  for (const [lo, hi, width] of bands) {
    for (const piece of p.pieces) {
      const ring = dedupe(clipBand(clipBand(piece, (q) => offset(q) - lo), (q) => hi - offset(q)));
      if (ring.length >= 3) parts.push(extrudeAcross(p, ring, width));
    }
  }
  return parts;
}

/**
 * The swept bodies a member draws as when it is not a plain raked box: a seated I-joist's three
 * plies (one pick identity), else its elevation profile, seat cut or formed ring. Null for a box.
 */
export function memberSweeps(m: Member, center: PlanCenter): Corner[][] | null {
  const plies = m.shape === "i_joist" && !m.elevation_profile && !m.section_ring
    ? seatedIJoistParts(m, center) : null;
  if (plies) return plies;
  const one = elevationProfileVertices(m, center)
    ?? seatedProfileVertices(m, center) ?? sectionRingVertices(m, center);
  return one ? [one] : null;
}

/** Sutherland-Hodgman against one half-plane, `inside(q) >= 0`; the plane is linear in q. */
function clipBand(points: [number, number][], inside: (q: [number, number]) => number) {
  const out: [number, number][] = [];
  points.forEach((q, i) => {
    const prev = points[(i + points.length - 1) % points.length];
    const fq = inside(q), fp = inside(prev);
    if ((fq >= 0) !== (fp >= 0)) {
      const t = fp / (fp - fq);
      out.push([prev[0] + (q[0] - prev[0]) * t, prev[1] + (q[1] - prev[1]) * t]);
    }
    if (fq >= 0) out.push(q);
  });
  return out;
}

/**
 * The corners of a formed section (`Member.section_ring`): the ring at `p0`, then again at
 * `p1` risen by the run's own rise. Mirrors `resolve/geometry_members.py::_ring_sweep` — the
 * ring is in the run's (left-normal, up) frame from the axis at `z0_m`, wound
 * counter-clockwise about the run. Null when the member has no ring or no plan run.
 */
export function sectionRingVertices(
  m: Member, center: PlanCenter,
): [number, number, number][] | null {
  const ring = m.section_ring;
  if (!ring || ring.length < 3) return null;
  const dx = m.p1[0] - m.p0[0], dy = m.p1[1] - m.p0[1];
  const run = Math.hypot(dx, dy);
  if (run < MIN_PLAN_RUN_M) return null;
  const nx = -dy / run, ny = dx / run;
  let area = 0;
  for (let i = 0; i < ring.length; i++) {
    const [s0, t0] = ring[i], [s1, t1] = ring[(i + 1) % ring.length];
    area += s0 * t1 - s1 * t0;
  }
  const points = area > 0 ? ring : [...ring].reverse();
  const rise = (m.z0_end_m ?? m.z0_m) - m.z0_m;
  const at = (x: number, y: number, s: number, t: number): [number, number, number] => {
    const v = projectPointToScene([x + nx * s, y + ny * s], m.z0_m + t, center);
    return [v.x, v.y, v.z];
  };
  return [
    ...points.map(([s, t]) => at(m.p0[0], m.p0[1], s, t)),
    ...points.map(([s, t]) => at(m.p1[0], m.p1[1], s, t + rise)),
  ];
}

/** Engine-resolved miter/corner silhouette, swept across the member's actual plan width. */
export function elevationProfileVertices(
  m: Member, center: PlanCenter,
): [number, number, number][] | null {
  const profile = m.elevation_profile;
  if (!profile || profile.length < 3) return null;
  const dx = m.p1[0] - m.p0[0], dy = m.p1[1] - m.p0[1];
  const run = Math.hypot(dx, dy);
  if (run < MIN_PLAN_RUN_M) return null;
  const ux = dx / run, uy = dy / run;
  const half = (m.plan_width_m ?? m.depth_m) / 2;
  const area = profile.reduce((sum, [s0, z0], index) => {
    const [s1, z1] = profile[(index + 1) % profile.length];
    return sum + s0 * z1 - s1 * z0;
  }, 0);
  const points = area > 0 ? [...profile].reverse() : profile;
  const at = (side: number, s: number, z: number): [number, number, number] => {
    const point = projectPointToScene([
      m.p0[0] + ux * s - side * uy * half,
      m.p0[1] + uy * s + side * ux * half,
    ], z, center);
    return [point.x, point.y, point.z];
  };
  return [...points.map(([s, z]) => at(-1, s, z)),
    ...points.map(([s, z]) => at(1, s, z))];
}

/**
 * Triangles for a swept profile laid out as [near ring, far ring]: two caps plus one quad
 * per profile edge. Returns how many triangles it pushed, which is what the picking table
 * needs — a seated member is not a 12-triangle box.
 */
export function pushSweepIndices(indices: number[], base: number, profileCount: number,
  vertices: readonly [number, number, number][]): number {
  const before = indices.length;
  const origin = new THREE.Vector3(...vertices[0]);
  const ring = vertices.slice(0, profileCount).map((v) => new THREE.Vector3(...v).sub(origin));
  const normal = new THREE.Vector3();
  for (let i = 0; i < ring.length; i++) {
    normal.add(new THREE.Vector3().crossVectors(ring[i], ring[(i + 1) % ring.length]));
  }
  const magnitudes = [Math.abs(normal.x), Math.abs(normal.y), Math.abs(normal.z)];
  const drop = magnitudes.indexOf(Math.max(...magnitudes));
  const contour = ring.map((v) => {
    const coords = v.toArray().filter((_, axis) => axis !== drop);
    return new THREE.Vector2(coords[0], coords[1]);
  });
  const area = contour.reduce((sum, point, i) => {
    const next = contour[(i + 1) % contour.length];
    return sum + point.x * next.y - next.x * point.y;
  }, 0);
  for (const triangle of THREE.ShapeUtils.triangulateShape(contour, [])) {
    const [a, rawB, rawC] = triangle;
    const signed = new THREE.Vector2().subVectors(contour[rawB], contour[a])
      .cross(new THREE.Vector2().subVectors(contour[rawC], contour[a]));
    const [b, c] = signed * area < 0 ? [rawC, rawB] : [rawB, rawC];
    indices.push(base + a, base + c, base + b);
    indices.push(base + profileCount + a, base + profileCount + b, base + profileCount + c);
  }
  for (let i = 0; i < profileCount; i++) {
    const next = (i + 1) % profileCount;
    indices.push(base + i, base + next, base + profileCount + next);
    indices.push(base + i, base + profileCount + next, base + profileCount + i);
  }
  return (indices.length - before) / 3;
}

/**
 * A standalone BufferGeometry for one raked box — the pick highlight's outline source. A
 * formed section outlines its own swept ring rather than its bounding box.
 */
export function rakedBoxGeometry(
  m: Member, center: PlanCenter,
): THREE.BufferGeometry | null {
  const ringed = elevationProfileVertices(m, center) ?? sectionRingVertices(m, center);
  const verts = ringed ?? rakedBoxVertices(m, center);
  if (!verts) return null;
  const positions: number[] = [];
  for (const v of verts) positions.push(v[0], v[1], v[2]);
  const indices: number[] = [];
  if (ringed) pushSweepIndices(indices, 0, verts.length / 2, verts);
  else pushBoxIndices(indices, 0);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}
