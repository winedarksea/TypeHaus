// A swept run — a handrail, a drain, a raceway — as one merged BufferGeometry.
//
// The port of `packages/engine/src/typehaus/resolve/sweep.py`, vertex for vertex. That module
// is the authority; this file must not diverge from it, and `tubeGeometry.test.ts` pins the
// two against a shared fixture so it cannot silently.
//
// Why the run is one thing: a plan ring extruded straight up in Z cannot rake or slope, so
// without a sweep a raked or sloped run has to be faked as a stack of level pieces. A `sweep`
// on the solid says "I am a section carried along a 3D polyline", and this builds the mitred
// tube that describes.
//
// FRAME CONVENTION (must match sweep.py's docstring exactly): a leg's local "up" is world +Z
// projected perpendicular to the leg axis, so a rectangular rail's flat face stays level on a
// rake instead of rolling with the slope; a vertical leg has no such projection and falls
// back to world +Y. "right" is `up × d`, which makes (right, up, d) right-handed, so a
// profile wound counter-clockwise in (u, v) comes out facing outward.
import * as THREE from "three";
import type { Solid, Vec2 } from "../model/types";
import { projectPointToScene, type PlanCenter } from "./planGeometry";

export type Vec3 = [number, number, number];

// Past this much deviation from straight, an interior vertex stops being a mitre and starts
// being a fitting: a 90° turn in a drain is an elbow you buy, and a 90° mitre in a rail is a
// spike four diameters long. Legs either side of such a vertex butt square instead.
export const MAX_MITER_DEG = 80;

// Two path points closer than this (in 3D) are the same point.
const EPS_M = 1e-9;

const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec3, b: Vec3): Vec3 =>
  [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: Vec3) => Math.sqrt(dot(a, a));

function unit(a: Vec3): Vec3 {
  const n = norm(a);
  return n < 1e-15 ? [0, 0, 0] : [a[0] / n, a[1] / n, a[2] / n];
}

/** The path with consecutive duplicate points dropped — mirrors sweep.py `clean_path`. */
export function cleanPath(path: readonly (readonly number[])[]): Vec3[] {
  const out: Vec3[] = [];
  for (const raw of path) {
    const point: Vec3 = [raw[0], raw[1], raw[2]];
    if (out.length && norm(sub(point, out[out.length - 1])) <= EPS_M) continue;
    out.push(point);
  }
  return out;
}

/** `[right, up]` for a leg running along `direction` — see the frame convention above. */
export function legFrame(direction: Vec3): [Vec3, Vec3] {
  const d = unit(direction);
  let up: Vec3 = [-d[0] * d[2], -d[1] * d[2], 1 - d[2] * d[2]];
  if (norm(up) < 1e-9) up = [-d[0] * d[1], 1 - d[1] * d[1], -d[2] * d[1]];
  up = unit(up);
  return [cross(up, d), up];
}

// The leg's profile placed at `vertex` and cut by the plane with `planeNormal`. Each profile
// point slides ALONG THE LEG AXIS until it meets the plane: with planeNormal === direction
// the slide is zero and the ring is square to the leg (the butt joint); with the bisector it
// is the mitre. Both legs at a vertex slide onto the same plane from frames that share world
// +Z, so their rings land on the same points and the tube closes.
function ringAt(vertex: Vec3, direction: Vec3, right: Vec3, up: Vec3,
  profile: readonly Vec2[], planeNormal: Vec3): Vec3[] {
  const denominator = dot(direction, planeNormal);
  return profile.map(([u, v]) => {
    const offset: Vec3 = [right[0] * u + up[0] * v, right[1] * u + up[1] * v,
      right[2] * u + up[2] * v];
    const t = Math.abs(denominator) < 1e-9 ? 0 : -dot(offset, planeNormal) / denominator;
    return [vertex[0] + offset[0] + direction[0] * t,
      vertex[1] + offset[1] + direction[1] * t,
      vertex[2] + offset[2] + direction[2] * t] as Vec3;
  });
}

/** One `[startRing, endRing]` pair per leg — mirrors sweep.py `sweep_legs`. */
export function sweepLegs(path: readonly (readonly number[])[],
  profile: readonly Vec2[]): [Vec3[], Vec3[]][] {
  const points = cleanPath(path);
  if (points.length < 2 || profile.length < 3) return [];
  const dirs = points.slice(0, -1).map((p, i) => unit(sub(points[i + 1], p)));
  const frames = dirs.map(legFrame);
  const cosLimit = Math.cos((MAX_MITER_DEG * Math.PI) / 180);
  const normals: Vec3[] = [dirs[0]];
  for (let i = 1; i < dirs.length; i++) {
    const before = dirs[i - 1];
    const current = dirs[i];
    normals.push(dot(before, current) >= cosLimit
      ? unit([before[0] + current[0], before[1] + current[1], before[2] + current[2]])
      : [0, 0, 0]); // butt: each leg squares off on its own axis
  }
  normals.push(dirs[dirs.length - 1]);
  return dirs.map((direction, i) => {
    const [right, up] = frames[i];
    const startNormal = norm(normals[i]) > 1e-9 ? normals[i] : direction;
    const endNormal = norm(normals[i + 1]) > 1e-9 ? normals[i + 1] : direction;
    return [ringAt(points[i], direction, right, up, profile, startNormal),
      ringAt(points[i + 1], direction, right, up, profile, endNormal)];
  });
}

/**
 * One merged, scene-space BufferGeometry for every leg of a swept solid.
 *
 * The triangulation is `emit/gltf/mesh.py::add_gbox`'s, per leg: a reversed bottom cap, a top
 * cap, and one quad per profile edge. Positions are duplicated per leg rather than shared at
 * the joints, so `computeVertexNormals` faces each facet flat — which is what a faceted pipe
 * or a square rail should read as, and what the glTF export does.
 */
export function createSweepGeometry(solid: Solid, center: PlanCenter): THREE.BufferGeometry | null {
  const sweep = solid.sweep;
  if (!sweep) return null;
  const legs = sweepLegs(sweep.path, sweep.profile as Vec2[]);
  if (!legs.length) return null;
  const positions: number[] = [];
  const indices: number[] = [];
  for (const [start, end] of legs) {
    const base = positions.length / 3;
    const count = start.length;
    for (const ring of [start, end]) {
      for (const [x, y, z] of ring) {
        const scene = projectPointToScene([x, y], z, center);
        positions.push(scene.x, scene.y, scene.z);
      }
    }
    for (let i = 1; i < count - 1; i++) {
      indices.push(base, base + i + 1, base + i);
      indices.push(base + count, base + count + i, base + count + i + 1);
    }
    for (let i = 0; i < count; i++) {
      const next = (i + 1) % count;
      indices.push(base + i, base + next, base + count + next);
      indices.push(base + i, base + count + next, base + count + i);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}
