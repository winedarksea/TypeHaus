// Solid framing-member rendering (→ 21 §3D panel WP8). Replaces the old zero-width
// LineSegments pass: every member gets a real box built from its serialized
// shape/width_m/depth_m/orient (never re-parses `profile` — that's the engine's job,
// → server/model_json.py._member_json). Three buckets, each ~1-3 draw calls so a
// trade with hundreds of members still costs a handful of draws:
//   1. Rect prismatic, non-raked -> one InstancedMesh (unit box, per-instance matrix+color).
//   2. Raked (z0_end_m != null: raked plates, rafters) -> one merged BufferGeometry with
//      the exact 8-vertex box (vertical ends, sloped top/bottom), mirroring
//      emit/gltf/emitter.py's add_member_box so the 3D panel and the glTF agree.
//   3. I-joists -> three InstancedMeshes (top flange, bottom flange, web) sharing the
//      member's axis transform; a sloped i-joist rafter (none in the current catalog)
//      would render level rather than raked — square-cut, plumb ends not modeled.
import * as THREE from "three";
import type { Member } from "../model/types";

// Mirrors emit/gltf/emitter.py's _PALETTE (member-category keys only; layer-function
// colors live in nordic/palette.ts for wall fills).
const CATEGORY_COLOR: Record<string, number> = {
  stud: 0xb3854f,
  plate: 0xa87a4c,
  header: 0x996b41,
  raked_plate: 0xa87a4c,
  corner: 0xa3763f,
  stringer: 0x996b41,
  tread: 0xb3854f,
  joist: 0xb88c5c,
  rim: 0xa87a4c,
  ridge_beam: 0x8c6238,
  king: 0xb3854f,
  jack: 0xb3854f,
  cripple: 0xb3854f,
  sill: 0xa87a4c,
  winder: 0xb3854f,
  bearing_stiffener: 0x996b41,
};
const CATEGORY_FALLBACK = 0xb0b0b0;

export function categoryColor(category: string): number {
  return CATEGORY_COLOR[category] ?? CATEGORY_FALLBACK;
}

const UP = new THREE.Vector3(0, 1, 0);
const _m = new THREE.Matrix4();
const _pos = new THREE.Vector3();
const _color = new THREE.Color();

// A unit box: X,Z in [-0.5, 0.5] (the two cross-section axes), Y in [0, 1] (the run/length
// axis, base at the local origin) — every rect/i-joist instance is this geometry, scaled +
// rotated + translated per instance.
const UNIT_BOX = new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0);

// Lying-flat members (plates) put their wide face (depth_m) across the wall; on-edge
// members (headers/joists/rims/beams) put their thin face (width_m) across instead —
// both trust the engine's own z1-z0 for the vertical extent rather than re-deriving it.
function crossWidth(m: Member): number {
  return m.category === "plate" || m.category === "raked_plate" ? m.depth_m : m.width_m;
}

// Sets instance `index` of `mesh` to a box with local X along `xAxis` (scale xScale),
// local Y along `yAxis` (scale yScale, base at `origin`), local Z along `zAxis` (scale
// zScale). The three axes must already be mutually orthogonal unit vectors.
function setBoxInstance(mesh: THREE.InstancedMesh, index: number, origin: THREE.Vector3,
  xAxis: THREE.Vector3, xScale: number, yAxis: THREE.Vector3, yScale: number,
  zAxis: THREE.Vector3, zScale: number, color: number) {
  _m.makeBasis(xAxis, yAxis, zAxis);
  _m.scale(new THREE.Vector3(xScale, Math.max(yScale, 1e-4), Math.max(zScale, 1e-4)));
  _m.setPosition(origin);
  mesh.setMatrixAt(index, _m);
  mesh.setColorAt(index, _color.setHex(color));
}

// Vertical member (p0 == p1): the free axis is world-up (its height). `orient` supplies
// the in-plan axis the solver placed it along (its width_m face); the through-member
// axis (depth_m) is perpendicular to that, both horizontal.
function setVerticalInstance(mesh: THREE.InstancedMesh, index: number, m: Member,
  cx: number, cz: number) {
  const [ox, oz] = m.orient ?? [1, 0];
  const orient = new THREE.Vector3(ox, 0, oz).normalize();
  const perp = new THREE.Vector3(-orient.z, 0, orient.x);
  const origin = _pos.set(m.p0[0] - cx, m.z0_m, m.p0[1] - cz).clone();
  setBoxInstance(mesh, index, origin, orient, m.width_m, UP, m.z1_m - m.z0_m, perp, m.depth_m,
    categoryColor(m.category));
}

// Horizontal member (p0 != p1): the free axis is its own p0->p1 direction (length_m).
// The through-member axis is in-plan perpendicular to that; the vertical axis is world-up,
// scaled by the engine's own z1-z0 (already the physically correct depth for this member,
// whether it's lying flat or standing on edge — see crossWidth for the horizontal face).
function setHorizontalInstance(mesh: THREE.InstancedMesh, index: number, m: Member,
  cx: number, cz: number) {
  const dx = m.p1[0] - m.p0[0];
  const dz = m.p1[1] - m.p0[1];
  const runLen = Math.hypot(dx, dz);
  const run = runLen > 1e-9 ? new THREE.Vector3(dx / runLen, 0, dz / runLen) : new THREE.Vector3(1, 0, 0);
  const across = new THREE.Vector3(-run.z, 0, run.x);
  const origin = _pos.set(m.p0[0] - cx, m.z0_m, m.p0[1] - cz).clone();
  setBoxInstance(mesh, index, origin, across, crossWidth(m), run, runLen, UP, m.z1_m - m.z0_m,
    categoryColor(m.category));
}

interface Buckets {
  rect: Member[];
  raked: Member[];
  ijoist: Member[];
}

function isVertical(m: Member): boolean {
  return m.p0[0] === m.p1[0] && m.p0[1] === m.p1[1];
}

function bucket(members: Member[]): Buckets {
  const out: Buckets = { rect: [], raked: [], ijoist: [] };
  for (const m of members) {
    if (m.shape === "i_joist") out.ijoist.push(m);
    else if (m.z0_end_m != null || m.z1_end_m != null) out.raked.push(m);
    else out.rect.push(m);
  }
  return out;
}

function buildRectInstances(group: THREE.Group, members: Member[], cx: number, cz: number,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const material = new THREE.MeshStandardMaterial({
    roughness: mode === "nordic" ? 0.85 : 1, flatShading: mode === "schematic",
  });
  const mesh = new THREE.InstancedMesh(UNIT_BOX, material, members.length);
  members.forEach((m, i) => {
    if (isVertical(m)) setVerticalInstance(mesh, i, m, cx, cz);
    else setHorizontalInstance(mesh, i, m, cx, cz);
  });
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  group.add(mesh);
}

// Exact 8-vertex raked box: vertical ends, sloped top/bottom — mirrors
// emit/gltf/emitter.py's add_member_box. One merged geometry (vertex colors) per trade.
function buildRakedMesh(group: THREE.Group, members: Member[], cx: number, cz: number,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const positions: number[] = [];
  const indices: number[] = [];
  const colors: number[] = [];
  const faces = [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]];
  for (const m of members) {
    const ax = m.p0[0] - cx, ay = m.p0[1] - cz;
    const bx = m.p1[0] - cx, by = m.p1[1] - cz;
    const az0 = m.z0_m, az1 = m.z1_m;
    const bz0 = m.z0_end_m ?? m.z0_m, bz1 = m.z1_end_m ?? m.z1_m;
    const dx = bx - ax, dy = by - ay;
    const run = Math.hypot(dx, dy);
    if (run < 1e-9) continue;
    const half = crossWidth(m) / 2;
    const nx = (-dy / run) * half, ny = (dx / run) * half;
    const verts: [number, number, number][] = [
      [ax + nx, az0, ay + ny], [bx + nx, bz0, by + ny], [bx - nx, bz0, by - ny], [ax - nx, az0, ay - ny],
      [ax + nx, az1, ay + ny], [bx + nx, bz1, by + ny], [bx - nx, bz1, by - ny], [ax - nx, az1, ay - ny],
    ];
    const base = positions.length / 3;
    const col = new THREE.Color(categoryColor(m.category));
    for (const v of verts) {
      positions.push(v[0], v[1], v[2]);
      colors.push(col.r, col.g, col.b);
    }
    for (const [a, b, c, d] of faces) indices.push(base + a, base + b, base + c, base + a, base + c, base + d);
  }
  if (!positions.length) return;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  const material = new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: mode === "nordic" ? 0.85 : 1, flatShading: mode === "schematic",
  });
  group.add(new THREE.Mesh(geo, material));
}

// Three shared InstancedMeshes (top flange, bottom flange, web), one instance per member.
// The run axis includes its resolved rise, so roof I-joists follow the roof plane instead
// of appearing flat in the model.
function buildIJoists(group: THREE.Group, members: Member[], cx: number, cz: number,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const mkMesh = () => new THREE.InstancedMesh(
    UNIT_BOX,
    new THREE.MeshStandardMaterial({ roughness: mode === "nordic" ? 0.85 : 1, flatShading: mode === "schematic" }),
    members.length,
  );
  const top = mkMesh();
  const bottom = mkMesh();
  const web = mkMesh();
  members.forEach((m, i) => {
    const dx = m.p1[0] - m.p0[0];
    const dz = m.p1[1] - m.p0[1];
    const runLen = Math.hypot(dx, dz);
    const horizontalRun = runLen > 1e-9 ? new THREE.Vector3(dx / runLen, 0, dz / runLen) : new THREE.Vector3(1, 0, 0);
    const rise = (m.z0_end_m ?? m.z0_m) - m.z0_m;
    const run = new THREE.Vector3(dx, rise, dz).normalize();
    const across = new THREE.Vector3(-horizontalRun.z, 0, horizontalRun.x);
    const normal = new THREE.Vector3().crossVectors(across, run).normalize();
    const depth = m.z1_m - m.z0_m;
    const flangeT = m.flange_thickness_m ?? depth * 0.1;
    const flangeW = m.flange_width_m ?? m.width_m;
    const webT = m.web_thickness_m ?? Math.min(flangeW, 0.01);
    const color = categoryColor(m.category);
    const base = _pos.set(m.p0[0] - cx, m.z0_m, m.p0[1] - cz).clone();
    const slopedLength = Math.hypot(runLen, rise);

    setBoxInstance(bottom, i, base, across, flangeW, run, slopedLength, normal, flangeT, color);
    setBoxInstance(top, i, base.clone().addScaledVector(normal, depth - flangeT), across, flangeW,
      run, slopedLength, normal, flangeT, color);
    setBoxInstance(web, i, base.clone().addScaledVector(normal, flangeT), across, webT,
      run, slopedLength, normal, Math.max(depth - 2 * flangeT, 1e-4), color);
  });
  for (const mesh of [top, bottom, web]) {
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    group.add(mesh);
  }
}

export function buildMembers(group: THREE.Group, members: Member[], cx: number, cz: number,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const buckets = bucket(members);
  buildRectInstances(group, buckets.rect, cx, cz, mode);
  buildRakedMesh(group, buckets.raked, cx, cz, mode);
  buildIJoists(group, buckets.ijoist, cx, cz, mode);
}

export function disposeGroup(root: THREE.Object3D) {
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (mesh.geometry && mesh.geometry !== UNIT_BOX) mesh.geometry.dispose();
    const material = mesh.material;
    if (Array.isArray(material)) material.forEach((mat) => mat.dispose());
    else material?.dispose();
  });
}
