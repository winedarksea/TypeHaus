// Reinforcing bars as geometry (decision #75): straight bars are instances of one unit
// cylinder; hooked bars, L-dowels and closed hoops are merged tubes swept with the same
// `sweepLegs` port as rails and drains (→ tubeGeometry.ts, resolve/sweep.py). Both buckets
// record the bar uids they drew, so a click resolves to ONE bar (→ memberPicking.ts).
import * as THREE from "three";
import type { RebarBar, RebarSet, Vec2 } from "../model/types";
import { memberUid } from "../model/memberIdentity";
import { tagInstancedMemberIdentity, tagMergedMemberIdentity } from "./memberPicking";
import { projectPointToScene, type PlanCenter } from "./planGeometry";
import { standardMaterial } from "./surfaces";
import { pushSweepLegs, sweepLegs, type Vec3 } from "./tubeGeometry";

// Mirrors emit/gltf/palette.py::_REBAR_COATING (linear RGB, as glTF's baseColorFactor).
const COATING_RGB: Record<string, [number, number, number]> = {
  "hdg-a767": [0.70, 0.72, 0.74],
  "hdg-a1094": [0.70, 0.72, 0.74],
  black: [0.33, 0.25, 0.21],
  epoxy: [0.30, 0.52, 0.30],
  stainless: [0.80, 0.81, 0.82],
  gfrp: [0.78, 0.70, 0.36],
};

export function rebarColor(coating: string, out = new THREE.Color()): THREE.Color {
  const [r, g, b] = COATING_RGB[coating] ?? COATING_RGB.black;
  return out.setRGB(r, g, b);
}

// Eight sides: a #4 is half an inch, and a round section reads as round at any zoom that can
// see it. The unit cylinder has radius 0.5 and height 1 along +Y.
const SIDES = 8;
export const UNIT_CYLINDER = new THREE.CylinderGeometry(0.5, 0.5, 1, SIDES, 1, false);

function circleProfile(diameterM: number): Vec2[] {
  const r = diameterM / 2;
  return Array.from({ length: SIDES }, (_, i) => {
    const a = (2 * Math.PI * i) / SIDES;
    return [r * Math.cos(a), r * Math.sin(a)] as Vec2;
  });
}

/** Straight bars draw as instances; every other path is a tube. */
export function isStraightBar(bar: RebarBar): boolean {
  return !bar.closed && bar.path.length === 2;
}

/** A tube's path: a closed loop repeats its first point so the sweep closes the ring. */
export function tubePath(bar: RebarBar): Vec3[] {
  const path = bar.path.map(([x, y, z]) => [x, y, z] as Vec3);
  return bar.closed && path.length > 2 ? [...path, path[0]] : path;
}

const _m = new THREE.Matrix4();
const _q = new THREE.Quaternion();
const _s = new THREE.Vector3();
const _color = new THREE.Color();
const Y_UP = new THREE.Vector3(0, 1, 0);

/** The unit cylinder's transform onto a straight bar, scaled by `grow` across its section. */
export function straightBarMatrix(bar: RebarBar, center: PlanCenter, grow = 1,
  out = new THREE.Matrix4()): THREE.Matrix4 {
  const [a, b] = bar.path;
  const p0 = projectPointToScene([a[0], a[1]], a[2], center);
  const p1 = projectPointToScene([b[0], b[1]], b[2], center);
  const axis = p1.clone().sub(p0);
  const length = axis.length();
  if (length > 1e-9) _q.setFromUnitVectors(Y_UP, axis.divideScalar(length));
  else _q.identity();
  const d = bar.width_m * grow;
  return out.compose(p0.add(p1).multiplyScalar(0.5), _q, _s.set(d, Math.max(length, 1e-4), d));
}

/** One merged tube geometry over `bars`, with per-vertex colour and per-bar triangle starts. */
export function tubeGeometry(bars: readonly RebarBar[], center: PlanCenter, grow = 1):
  { geometry: THREE.BufferGeometry; drawn: RebarBar[]; triangleStarts: number[] } | null {
  const positions: number[] = [];
  const indices: number[] = [];
  const colors: number[] = [];
  const drawn: RebarBar[] = [];
  const triangleStarts: number[] = [0];
  for (const bar of bars) {
    const legs = sweepLegs(tubePath(bar), circleProfile(bar.width_m * grow));
    if (!legs.length) continue;
    const before = positions.length;
    const triangles = pushSweepLegs(positions, indices, legs, center);
    rebarColor(bar.rebar.coating, _color);
    for (let i = before; i < positions.length; i += 3) colors.push(_color.r, _color.g, _color.b);
    drawn.push(bar);
    triangleStarts.push(triangleStarts[triangleStarts.length - 1] + triangles);
  }
  if (!drawn.length) return null;
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return { geometry, drawn, triangleStarts };
}

/** Every bar of `sets` as at most two draw calls, each tagged with per-bar identity. */
export function buildRebarMeshes(sets: readonly RebarSet[], center: PlanCenter,
  mode: "nordic" | "schematic"): THREE.Mesh[] {
  const bars = sets.flatMap((set) => set.members);
  const uidOf = (bar: RebarBar) => memberUid(bar.parent_uid, bar.key);
  const out: THREE.Mesh[] = [];
  const straight = bars.filter(isStraightBar);
  if (straight.length) {
    const mesh = new THREE.InstancedMesh(UNIT_CYLINDER, standardMaterial(undefined, mode,
      { metalness: 0.3 }), straight.length);
    straight.forEach((bar, i) => {
      mesh.setMatrixAt(i, straightBarMatrix(bar, center, 1, _m));
      mesh.setColorAt(i, rebarColor(bar.rebar.coating, _color));
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.computeBoundingSphere();
    tagInstancedMemberIdentity(mesh, straight.map(uidOf));
    out.push(mesh);
  }
  const tubes = tubeGeometry(bars.filter((bar) => !isStraightBar(bar)), center);
  if (tubes) {
    const mesh = new THREE.Mesh(tubes.geometry, standardMaterial(undefined, mode,
      { vertexColors: true, metalness: 0.3 }));
    tagMergedMemberIdentity(mesh, tubes.drawn.map(uidOf), tubes.triangleStarts);
    out.push(mesh);
  }
  for (const mesh of out) mesh.castShadow = mesh.receiveShadow = true;
  return out;
}

/** A disposable outline of one picked bar: a fattened copy drawn over everything. */
export function buildRebarHighlight(bar: RebarBar, center: PlanCenter,
  color: THREE.ColorRepresentation): THREE.Object3D {
  const material = new THREE.MeshBasicMaterial({
    color, transparent: true, opacity: 0.7, depthTest: false, depthWrite: false,
  });
  let mesh: THREE.Mesh;
  if (isStraightBar(bar)) {
    mesh = new THREE.Mesh(UNIT_CYLINDER.clone(), material);
    mesh.geometry.applyMatrix4(straightBarMatrix(bar, center, 1.8));
  } else {
    const tube = tubeGeometry([bar], center, 1.8);
    mesh = new THREE.Mesh(tube?.geometry ?? new THREE.BufferGeometry(), material);
  }
  mesh.renderOrder = 999;
  return mesh;
}
