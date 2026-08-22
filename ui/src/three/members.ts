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
// The box math itself lives in three/memberBox.ts, shared with the pick highlight.
//
// Every bucket records the member uids it drew, in draw order, so a click resolves to one
// member (→ three/memberPicking.ts) instead of to the wall/floor/roof that owns it.
import * as THREE from "three";
import type { Member } from "../model/types";
import { materialColor, type ResolvedNordicPalette } from "../nordic/palette";
import { createStandingSeamMaterial, isStandingSeam, SEAM_TILE_SIZE_M } from "./materials";
import {
  composeCenteredBoxMatrix, composeMemberBoxMatrix, isRakedMember, isVerticalMember,
  MIN_EXTENT_M, pushBoxIndices, pushSweepIndices, rakedBoxVertices, seatedProfileVertices,
  TRIANGLES_PER_MEMBER_BOX, UNIT_BOX,
} from "./memberBox";
import {
  memberUidsFor, tagInstancedMemberIdentity, tagMergedMemberIdentity,
} from "./memberPicking";
import { projectPlanDirectionToScene, projectPointToScene, type PlanCenter } from "./planGeometry";
import { standardMaterial } from "./surfaces";
import vocabulary from "../generated/vocabulary.json";

// Generated from emit/gltf/palette.py's `_PALETTE` (member-category keys; layer-function
// colors live in nordic/palette.ts for wall fills) — see
// packages/engine/src/typehaus/emit/vocabulary_manifest.py. The per-category rationale
// (why a sistered ply is a shade darker than the joist it doubles, why the roof-stick
// categories exist at all, why a skin member falls back to its layer-function color) lives
// as comments on `_PALETTE` in that file now, not here: this table has no literal of its own
// left to comment on. Change a color there and regenerate
// ui/src/generated/vocabulary.json — do not hand-edit this file or the JSON.
const CATEGORY_COLOR: Record<string, number> = vocabulary.memberColors;
export const CATEGORY_FALLBACK = 0xb0b0b0;

export function categoryColor(category: string): number {
  return CATEGORY_COLOR[category] ?? CATEGORY_FALLBACK;
}

// A roof carries two kinds of member: sticks (rafters, truss chords/webs, gable studs,
// outlookers, barge rafters, the fascia nailed to the rafter tails) and skin (the wall->roof
// closure bands, the derived soffit, the roof-edge cladding). The sticks belong under the
// framing toggle with every other stick in the building; the skin belongs with the roof shell
// it finishes. Fascia is trim by category but framing by trade (a nailer on the rafter tails),
// so it counts as framing here. Mirrors ROOF_SKIN_CATEGORIES in emit/gltf/members.py — keep
// the two in step.
const ROOF_SKIN_CATEGORIES = new Set([
  "sheathing", "membrane", "insulation", "furring", "cladding", "airgap", "air_gap",
  "lining", "finish", "soffit", "gutter", "ridge_cap", "corner_trim",
]);

export function isRoofFramingMember(m: Member): boolean {
  return !ROOF_SKIN_CATEGORIES.has(m.category.toLowerCase());
}

// A member that names a material is envelope skin, not lumber: colour it the way the wall and
// roof layer stacks colour that same material, or a standing-seam closure band reads as the
// generic grey fallback rather than as the white metal it continues. The resolved palette is
// required: without it materialColor falls back to CSS var() strings, which THREE.Color
// cannot parse (it logs "unknown color" for every skin member on every rebuild).
export function memberColor(m: Member, palette: ResolvedNordicPalette): THREE.ColorRepresentation {
  return m.material ? materialColor(m.material, palette) : categoryColor(m.category);
}

// Standing-seam skin members get the real finish (procedural seam/oil-canning normal map),
// not a flat fill, so a gable closure band matches the wall and roof panels it meets. The
// formed metal trim runs are the same painted stock as the panels they cap and are derived
// carrying the roofing's own material_ref, so they belong on the same finish: without this
// the ridge cap falls through to materialColor("standing-seam") -> family metal -> #6b7076
// and reads dark grey against the white roof it sits on.
const SEAM_TRIM_CATEGORIES = new Set(["cladding", "ridge_cap", "corner_trim", "gutter"]);

export function isSeamMember(m: Member): boolean {
  return SEAM_TRIM_CATEGORIES.has(m.category) && isStandingSeam(m.material);
}

const _m = new THREE.Matrix4();
const _color = new THREE.Color();

// Sets instance `index` of `mesh` to the box `composeCenteredBoxMatrix` describes.
function setCenteredBoxInstance(mesh: THREE.InstancedMesh, index: number, boxCenter: THREE.Vector3,
  xAxis: THREE.Vector3, xExtent: number, yAxis: THREE.Vector3, yExtent: number,
  zAxis: THREE.Vector3, zExtent: number, color: THREE.ColorRepresentation) {
  composeCenteredBoxMatrix(_m, boxCenter, xAxis, xExtent, yAxis, yExtent, zAxis, zExtent);
  mesh.setMatrixAt(index, _m);
  mesh.setColorAt(index, _color.set(color));
}

interface Buckets {
  rect: Member[];
  raked: Member[];
  ijoist: Member[];
  seam: Member[];
}

function bucket(members: Member[]): Buckets {
  const out: Buckets = { rect: [], raked: [], ijoist: [], seam: [] };
  for (const m of members) {
    // Seam first: a standing-seam band needs its own textured material, so it can't share
    // the vertex-coloured merge with the lumber around it.
    if (isSeamMember(m) && !isVerticalMember(m)) out.seam.push(m);
    else if (m.shape === "i_joist") out.ijoist.push(m);
    else if (isRakedMember(m)) out.raked.push(m);
    else out.rect.push(m);
  }
  return out;
}

// Standing-seam skin bands (gable closure cladding, roof-edge cladding) merged into one mesh
// carrying the shared seam finish. Each band gets world-scaled UVs off its own run, matching
// applyStandingSeamWallUv, so the 16" pan module stays at true scale and the seams line up
// with the wall and roof panels the band meets.
function buildSeamMesh(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", ownerUid: string) {
  if (!members.length) return;
  const positions: number[] = [];
  const indices: number[] = [];
  const uvs: number[] = [];
  const drawn: Member[] = [];
  const triangleStarts: number[] = [0];
  for (const m of members) {
    const verts = rakedBoxVertices(m, center);
    if (!verts) continue;
    const base = positions.length / 3;
    for (const v of verts) positions.push(v[0], v[1], v[2]);
    pushBoxIndices(indices, base);
    triangleStarts.push(triangleStarts[triangleStarts.length - 1] + TRIANGLES_PER_MEMBER_BOX);
    drawn.push(m);
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
  const mesh = new THREE.Mesh(geo, createStandingSeamMaterial(mode, [1, 1], 0xE8E8E2, true));
  tagMergedMemberIdentity(mesh, memberUidsFor(ownerUid, drawn), triangleStarts);
  group.add(mesh);
}

function buildRectInstances(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string) {
  if (!members.length) return;
  // No colour: every instance sets its own via `setColorAt`.
  const material = standardMaterial(undefined, mode);
  const mesh = new THREE.InstancedMesh(UNIT_BOX, material, members.length);
  members.forEach((m, i) => {
    mesh.setMatrixAt(i, composeMemberBoxMatrix(_m, m, center));
    mesh.setColorAt(i, _color.set(memberColor(m, palette)));
  });
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  tagInstancedMemberIdentity(mesh, memberUidsFor(ownerUid, members));
  group.add(mesh);
}

// Exact 8-vertex raked box: vertical ends, sloped top/bottom — mirrors
// emit/gltf/emitter.py's add_member_box. One merged geometry (vertex colors) per trade.
function buildRakedMesh(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string) {
  if (!members.length) return;
  const positions: number[] = [];
  const indices: number[] = [];
  const colors: number[] = [];
  const drawn: Member[] = [];
  // Prefix sums of the triangles each member contributed. A birdsmouthed rafter is not a
  // 12-triangle box, so picking cannot divide by a constant (→ memberPicking.ts).
  const triangleStarts: number[] = [0];
  for (const m of members) {
    const seated = seatedProfileVertices(m, center);
    const verts = seated ?? rakedBoxVertices(m, center);
    if (!verts) continue;
    const base = positions.length / 3;
    const col = new THREE.Color(memberColor(m, palette));
    for (const v of verts) {
      positions.push(v[0], v[1], v[2]);
      colors.push(col.r, col.g, col.b);
    }
    const triangles = seated
      ? pushSweepIndices(indices, base, verts.length / 2)
      : (pushBoxIndices(indices, base), TRIANGLES_PER_MEMBER_BOX);
    triangleStarts.push(triangleStarts[triangleStarts.length - 1] + triangles);
    drawn.push(m);
  }
  if (!positions.length) return;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  const material = standardMaterial(undefined, mode, { vertexColors: true });
  const mesh = new THREE.Mesh(geo, material);
  tagMergedMemberIdentity(mesh, memberUidsFor(ownerUid, drawn), triangleStarts);
  group.add(mesh);
}

// Three shared InstancedMeshes (top flange, bottom flange, web), one instance per member.
// The run axis includes its resolved rise, so roof I-joists follow the roof plane instead
// of appearing flat in the model.
function buildIJoists(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string) {
  if (!members.length) return;
  const mkMesh = () => new THREE.InstancedMesh(
    UNIT_BOX,
    standardMaterial(undefined, mode),
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
    const color = memberColor(m, palette);
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
  const uids = memberUidsFor(ownerUid, members);
  for (const mesh of [top, bottom, web]) {
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    // All three plies share one instance index per member, so any of them picks the same stick.
    tagInstancedMemberIdentity(mesh, uids);
    group.add(mesh);
  }
}

/**
 * Draw `members` into `group`. `ownerUid` is the uid of the wall / roof / floor / stair the
 * resolver framed them for — half of each member's identity (→ model/memberIdentity.ts), and
 * the reason every bucket can hand a picked index back as a stable member uid.
 */
export function buildMembers(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string) {
  const boxMembers = members.filter((member) => !member.plan_outline?.length);
  if (!boxMembers.length) return;
  const buckets = bucket(boxMembers);
  buildRectInstances(group, buckets.rect, center, mode, palette, ownerUid);
  buildRakedMesh(group, buckets.raked, center, mode, palette, ownerUid);
  buildIJoists(group, buckets.ijoist, center, mode, palette, ownerUid);
  buildSeamMesh(group, buckets.seam, center, mode, ownerUid);
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
