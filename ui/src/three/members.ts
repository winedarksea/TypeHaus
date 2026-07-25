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
import { materialColor } from "../nordic/palette";
import { createStandingSeamMaterial, isStandingSeam, SEAM_TILE_SIZE_M } from "./materials";
import { projectPlanDirectionToScene, projectPointToScene, type PlanCenter } from "./planGeometry";

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
  // Stair carriage framing (→ resolve/envelope.py _stair_members). Without these the
  // U-stair well partition fell through to the grey fallback and read as a wall.
  // Landing platforms + the well partition read as framing lumber; the concrete-wall
  // hanger/ledger band is galvanized grey like the engine's "connector".
  partition: 0xb3854f,
  trimmer: 0xa87a4c,
  landing: 0xb88c5c,
  newel: 0x996b41, // = header, as engine-side: the winder newel is a post, not tread lumber
  hanger: 0x595c61,
  // Roof sticks. `rafter`/`blocking`/`outlooker`/`barge_rafter` had no entry in either
  // table; the truss keys existed engine-side only. Together that was ~470 members reading
  // as the neutral gray fallback (the "garage truss should visualize as wood" report).
  rafter: 0xad7f4f,
  blocking: 0xa3763f,
  outlooker: 0xb88c5c,
  barge_rafter: 0x8c6238,
  top_chord: 0xb3854f, // = stud, as engine-side
  bottom_chord: 0xa87a4c, // = plate
  truss_web: 0xbd9161,
  truss_heel: 0x996b41, // = header
  seat_cut: 0x94663d,
  // Layer-function keys. A skin member normally colours by its *material*
  // (`memberColor`), but a derived band that names none must not drop to the fallback —
  // these mirror the same keys in the engine's _PALETTE.
  structure: 0x9e7347,
  sheathing: 0xb8b8b3,
  insulation: 0xedbd5c,
  cladding: 0x8c9499,
  membrane: 0x4d738c,
  furring: 0xad8557,
  lining: 0xe6e3db,
  finish: 0xe6e3db,
  fascia: 0xebebe6,
  soffit: 0xe0e0d9,
  gutter: 0xd9dbde,
};
export const CATEGORY_FALLBACK = 0xb0b0b0;

export function categoryColor(category: string): number {
  return CATEGORY_COLOR[category] ?? CATEGORY_FALLBACK;
}

// A roof carries two kinds of member: sticks (rafters, truss chords/webs, gable studs,
// outlookers, barge rafters) and skin (the wall->roof closure bands, derived fascia/soffit,
// the roof-edge cladding). The sticks belong under the framing toggle with every other stick
// in the building; the skin belongs with the roof shell it finishes. Mirrors
// ROOF_SKIN_CATEGORIES in emit/gltf/emitter.py — keep the two in step.
const ROOF_SKIN_CATEGORIES = new Set([
  "sheathing", "membrane", "insulation", "furring", "cladding", "airgap", "air_gap",
  "lining", "finish", "fascia", "soffit", "gutter",
]);

export function isRoofFramingMember(m: Member): boolean {
  return !ROOF_SKIN_CATEGORIES.has(m.category.toLowerCase());
}

// A member that names a material is envelope skin, not lumber: colour it the way the wall and
// roof layer stacks colour that same material, or a standing-seam closure band reads as the
// generic grey fallback rather than as the white metal it continues.
export function memberColor(m: Member): THREE.ColorRepresentation {
  return m.material ? materialColor(m.material) : categoryColor(m.category);
}

// Standing-seam skin members get the real finish (procedural seam/oil-canning normal map),
// not a flat fill, so a gable closure band matches the wall and roof panels it meets.
function isSeamMember(m: Member): boolean {
  return m.category === "cladding" && isStandingSeam(m.material);
}

const UP = new THREE.Vector3(0, 1, 0);
const _m = new THREE.Matrix4();
const _scale = new THREE.Vector3();
const _color = new THREE.Color();
// Degenerate extents would collapse the instance matrix (and its normals); 0.1 mm is far
// below any real member dimension but keeps the basis invertible.
const MIN_EXTENT_M = 1e-4;

// A unit box centred on its local origin in ALL THREE axes — every rect/i-joist instance is
// this geometry, scaled + rotated + translated per instance.
//
// The symmetry is the point. This box used to be base-at-origin on local Y only, which made
// the three axis slots of the instance setter non-interchangeable: passing world-up into one
// of the two centred slots silently drew a member spanning z0 ± depth/2 instead of z0 → z1,
// i.e. half its own depth too low. That is exactly what happened to every horizontal member
// (11.875" rim bands ~6" low; the stair well partition plunging through the foundation).
// With every axis centred there is no special slot to get wrong: the caller states the box
// centre once, and each axis is a symmetric ±extent/2.
const UNIT_BOX = new THREE.BoxGeometry(1, 1, 1);

// Lying-flat members (plates) put their wide face (depth_m) across the wall; on-edge
// members (headers/joists/rims/beams) put their thin face (width_m) across instead —
// both trust the engine's own z1-z0 for the vertical extent rather than re-deriving it.
function crossWidth(m: Member): number {
  return m.category === "plate" || m.category === "raked_plate" ? m.depth_m : m.width_m;
}

// Sets instance `index` of `mesh` to a box centred on `boxCenter`, extending ±extent/2 along
// each of `xAxis`/`yAxis`/`zAxis` (which must already be mutually orthogonal unit vectors).
// Every axis behaves identically — see UNIT_BOX for why that symmetry is load-bearing.
function setCenteredBoxInstance(mesh: THREE.InstancedMesh, index: number, boxCenter: THREE.Vector3,
  xAxis: THREE.Vector3, xExtent: number, yAxis: THREE.Vector3, yExtent: number,
  zAxis: THREE.Vector3, zExtent: number, color: THREE.ColorRepresentation) {
  _m.makeBasis(xAxis, yAxis, zAxis);
  _m.scale(_scale.set(Math.max(xExtent, MIN_EXTENT_M), Math.max(yExtent, MIN_EXTENT_M),
    Math.max(zExtent, MIN_EXTENT_M)));
  _m.setPosition(boxCenter);
  mesh.setMatrixAt(index, _m);
  mesh.setColorAt(index, _color.set(color));
}

// Vertical member (p0 == p1): the free axis is world-up (its height). `orient` supplies
// the in-plan axis the solver placed it along (its width_m face); the through-member
// axis (depth_m) is perpendicular to that, both horizontal.
function setVerticalInstance(mesh: THREE.InstancedMesh, index: number, m: Member,
  center: PlanCenter) {
  const [ox, oz] = m.orient ?? [1, 0];
  const orient = projectPlanDirectionToScene([ox, oz]).normalize();
  const perp = new THREE.Vector3(-orient.z, 0, orient.x);
  const boxCenter = projectPointToScene(m.p0, (m.z0_m + m.z1_m) / 2, center);
  setCenteredBoxInstance(mesh, index, boxCenter, orient, m.width_m, UP, m.z1_m - m.z0_m,
    perp, m.depth_m, memberColor(m));
}

// Horizontal member (p0 != p1): the free axis is its own p0->p1 direction (length_m).
// The through-member axis is in-plan perpendicular to that; the vertical axis is world-up,
// scaled by the engine's own z1-z0 (already the physically correct depth for this member,
// whether it's lying flat or standing on edge — see crossWidth for the horizontal face).
// The box centre is therefore the plan midpoint of p0->p1 at the member's mid-depth, so it
// occupies exactly z0..z1 the way emit/gltf/emitter.py's add_member_box does.
function setHorizontalInstance(mesh: THREE.InstancedMesh, index: number, m: Member,
  center: PlanCenter) {
  const dx = m.p1[0] - m.p0[0];
  const dz = m.p1[1] - m.p0[1];
  const runLen = Math.hypot(dx, dz);
  const run = runLen > 1e-9 ? projectPlanDirectionToScene([dx / runLen, dz / runLen]) : new THREE.Vector3(1, 0, 0);
  const across = new THREE.Vector3(-run.z, 0, run.x);
  const boxCenter = projectPointToScene(
    [(m.p0[0] + m.p1[0]) / 2, (m.p0[1] + m.p1[1]) / 2], (m.z0_m + m.z1_m) / 2, center);
  setCenteredBoxInstance(mesh, index, boxCenter, across, crossWidth(m), run, runLen,
    UP, m.z1_m - m.z0_m, memberColor(m));
}

interface Buckets {
  rect: Member[];
  raked: Member[];
  ijoist: Member[];
  seam: Member[];
}

function isVertical(m: Member): boolean {
  return m.p0[0] === m.p1[0] && m.p0[1] === m.p1[1];
}

function bucket(members: Member[]): Buckets {
  const out: Buckets = { rect: [], raked: [], ijoist: [], seam: [] };
  for (const m of members) {
    // Seam first: a standing-seam band needs its own textured material, so it can't share
    // the vertex-coloured merge with the lumber around it.
    if (isSeamMember(m) && !isVertical(m)) out.seam.push(m);
    else if (m.shape === "i_joist") out.ijoist.push(m);
    else if (m.z0_end_m != null || m.z1_end_m != null) out.raked.push(m);
    else out.rect.push(m);
  }
  return out;
}

// The 8 corners of a member's box, in scene space: vertical ends, sloped top/bottom. Shared
// by the vertex-coloured merge and the standing-seam merge so the two agree exactly.
function rakedBoxVertices(m: Member, center: PlanCenter): [number, number, number][] | null {
  const a = projectPointToScene(m.p0, 0, center);
  const b = projectPointToScene(m.p1, 0, center);
  const ax = a.x, ay = a.z, bx = b.x, by = b.z;
  const az0 = m.z0_m, az1 = m.z1_m;
  const bz0 = m.z0_end_m ?? m.z0_m, bz1 = m.z1_end_m ?? m.z1_m;
  const dx = bx - ax, dy = by - ay;
  const run = Math.hypot(dx, dy);
  if (run < 1e-9) return null;
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

function pushBoxIndices(indices: number[], base: number) {
  for (const [a, b, c, d] of BOX_FACES) {
    indices.push(base + a, base + c, base + b, base + a, base + d, base + c);
  }
}

// Standing-seam skin bands (gable closure cladding, roof-edge cladding) merged into one mesh
// carrying the shared seam finish. Each band gets world-scaled UVs off its own run, matching
// applyStandingSeamWallUv, so the 16" pan module stays at true scale and the seams line up
// with the wall and roof panels the band meets.
function buildSeamMesh(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const positions: number[] = [];
  const indices: number[] = [];
  const uvs: number[] = [];
  for (const m of members) {
    const verts = rakedBoxVertices(m, center);
    if (!verts) continue;
    const base = positions.length / 3;
    for (const v of verts) positions.push(v[0], v[1], v[2]);
    pushBoxIndices(indices, base);
    // Per-member UVs, not one shared axis: eave bands run one way and rake bands the other,
    // so a single frame would smear the pans on half of them. u runs along the band (its two
    // end faces are the only distinct values), v is elevation — the same world-scaled frame
    // applyStandingSeamWallUv gives a wall, so bands and walls share one seam rhythm.
    const length = Math.hypot(m.p1[0] - m.p0[0], m.p1[1] - m.p0[1]);
    for (let index = 0; index < verts.length; index++) {
      const atEnd = index === 1 || index === 2 || index === 5 || index === 6;
      uvs.push((atEnd ? length : 0) / SEAM_TILE_SIZE_M, verts[index][1] / SEAM_TILE_SIZE_M);
    }
  }
  if (!positions.length) return;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  group.add(new THREE.Mesh(geo, createStandingSeamMaterial(mode, [1, 1], 0xE8E8E2, true)));
}

function buildRectInstances(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const material = new THREE.MeshStandardMaterial({
    roughness: mode === "nordic" ? 0.85 : 1, flatShading: mode === "schematic",
  });
  const mesh = new THREE.InstancedMesh(UNIT_BOX, material, members.length);
  members.forEach((m, i) => {
    if (isVertical(m)) setVerticalInstance(mesh, i, m, center);
    else setHorizontalInstance(mesh, i, m, center);
  });
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  group.add(mesh);
}

// Exact 8-vertex raked box: vertical ends, sloped top/bottom — mirrors
// emit/gltf/emitter.py's add_member_box. One merged geometry (vertex colors) per trade.
function buildRakedMesh(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const positions: number[] = [];
  const indices: number[] = [];
  const colors: number[] = [];
  for (const m of members) {
    const verts = rakedBoxVertices(m, center);
    if (!verts) continue;
    const base = positions.length / 3;
    const col = new THREE.Color(memberColor(m));
    for (const v of verts) {
      positions.push(v[0], v[1], v[2]);
      colors.push(col.r, col.g, col.b);
    }
    pushBoxIndices(indices, base);
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
function buildIJoists(group: THREE.Group, members: Member[], center: PlanCenter,
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
    const horizontalRun = runLen > 1e-9 ? projectPlanDirectionToScene([dx / runLen, dz / runLen]) : new THREE.Vector3(1, 0, 0);
    const rise = (m.z0_end_m ?? m.z0_m) - m.z0_m;
    const run = projectPlanDirectionToScene([dx, dz]).setY(rise).normalize();
    const across = new THREE.Vector3(-horizontalRun.z, 0, horizontalRun.x);
    const normal = new THREE.Vector3().crossVectors(across, run).normalize();
    const depth = m.z1_m - m.z0_m;
    const flangeT = m.flange_thickness_m ?? depth * 0.1;
    const flangeW = m.flange_width_m ?? m.width_m;
    const webT = m.web_thickness_m ?? Math.min(flangeW, 0.01);
    const color = memberColor(m);
    const webDepth = Math.max(depth - 2 * flangeT, MIN_EXTENT_M);
    const slopedLength = Math.hypot(runLen, rise);
    // p0/z0 is the joist soffit at the near end; the three plies share that run centre and
    // differ only in how far their own mid-thickness sits up the section from the soffit.
    const runCenter = projectPointToScene(m.p0, m.z0_m, center)
      .addScaledVector(run, slopedLength / 2);
    const plyCenter = (offsetFromSoffit: number) =>
      runCenter.clone().addScaledVector(normal, offsetFromSoffit);

    setCenteredBoxInstance(bottom, i, plyCenter(flangeT / 2), across, flangeW,
      run, slopedLength, normal, flangeT, color);
    setCenteredBoxInstance(web, i, plyCenter(flangeT + webDepth / 2), across, webT,
      run, slopedLength, normal, webDepth, color);
    setCenteredBoxInstance(top, i, plyCenter(depth - flangeT / 2), across, flangeW,
      run, slopedLength, normal, flangeT, color);
  });
  for (const mesh of [top, bottom, web]) {
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    group.add(mesh);
  }
}

export function buildMembers(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic") {
  if (!members.length) return;
  const buckets = bucket(members);
  buildRectInstances(group, buckets.rect, center, mode);
  buildRakedMesh(group, buckets.raked, center, mode);
  buildIJoists(group, buckets.ijoist, center, mode);
  buildSeamMesh(group, buckets.seam, center, mode);
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
