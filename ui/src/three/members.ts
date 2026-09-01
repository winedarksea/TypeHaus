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
import {
  authoredAppearance, familyOf, finishBaseColor, materialColor, type MaterialAppearance,
  type ResolvedNordicPalette, statesOwnColor,
} from "../nordic/palette";
import {
  createStandingSeamMaterial, isStandingSeam, type MetalPanelProfile,
  metalPanelProfileForFinish, panelTileSizeM, SEAM_PROFILE,
} from "./materials";
import {
  composeCenteredBoxMatrix, composeMemberBoxMatrix, isRakedMember, isVerticalMember,
  MIN_EXTENT_M, pushBoxIndices, pushSweepIndices, rakedBoxVertices, seatedProfileVertices,
  TRIANGLES_PER_MEMBER_BOX, UNIT_BOX,
} from "./memberBox";
import {
  memberUidsFor, tagInstancedMemberIdentity, tagMergedMemberIdentity,
} from "./memberPicking";
import { projectPlanDirectionToScene, projectPointToScene, type PlanCenter } from "./planGeometry";
import { makeSurfaceMesh, markShadowCaster, standardMaterial } from "./surfaces";
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

/**
 * Whether a member is a derived *skin* band rather than a stick of lumber.
 *
 * The question is the member's category, never whether it names a material: a truss wall's
 * blocks, tabs, bucks and jamb fillers all carry one (spf, kdat, struct-1-plywood) and every
 * one of them is wood a carpenter cuts. Asking `m.material` instead put the whole Swinburne
 * pack on the Walls trade and out of the framing view (→ builders/walls.ts).
 */
export function isSkinMember(m: Member): boolean {
  return ROOF_SKIN_CATEGORIES.has(m.category.toLowerCase());
}

export function isRoofFramingMember(m: Member): boolean {
  return !isSkinMember(m);
}

// A member that names a material *the palette can resolve* is envelope skin, not lumber:
// colour it the way the wall and roof layer stacks colour that same material, or a
// standing-seam closure band reads as the generic grey fallback rather than as the white
// metal it continues. The resolved palette is required: without it materialColor falls back
// to CSS var() strings, which THREE.Color cannot parse (it logs "unknown color" for every
// skin member on every rebuild).
//
// "Can resolve" is the whole rule, and it is why this is not a bare `m.material ? …`. A
// member carries a material ref but no catalog, so `materialColor` here sees only a named
// finish and the substring family guess — and a ref that hits neither returns the neutral
// grey `material.fallback`, which is a worse answer than the category tone the member
// already had. The truss wall's outrigger band is 590 members on "kdat": no needle in
// familyOf matches it, so every strapping, ladder-blocking and jamb-filler stick in the
// house rendered pale grey next to the lumber it is screwed to. Falling back to the
// category also puts this back in step with the .glb, whose member path
// (emit/gltf/members.py -> _material_finish_color with authored=None) has always ended at
// `_color(category)` for exactly the same refs.
export function memberColor(m: Member, palette: ResolvedNordicPalette,
  materials?: readonly MaterialAppearance[]): THREE.ColorRepresentation {
  return m.material && (statesOwnColor(m.material, materials) || familyOf(m.material) !== null)
    ? materialColor(m.material, palette, materials)
    : categoryColor(m.category);
}

// Standing-seam skin members get the real finish (procedural seam/oil-canning normal map),
// not a flat fill, so a gable closure band matches the wall and roof panels it meets. The
// formed metal trim runs are the same painted stock as the panels they cap and are derived
// carrying the roofing's own material_ref, so they belong on the same finish: without this
// the ridge cap falls through to materialColor("standing-seam") -> family metal -> #6b7076
// and reads dark grey against the white roof it sits on.
const SEAM_TRIM_CATEGORIES = new Set(["cladding", "ridge_cap", "corner_trim", "gutter"]);

// The metal-panel profile a skin member finishes as, or null for a member that is neither a
// seam nor a declared ribbed panel. A member carries the SAME material ref its host layer
// does (roof_edge.py/roof_trim.py thread it straight off the wall's own layer), so it takes
// the identical declared-finish-first dispatch `builders/walls.ts` uses for that layer:
// `pbr-panel-26` has no "seam" in its tag on purpose, and without reading its authored
// `finish: "ribbed-panel"` here a gable closure in that panel rendered flat grey next to the
// wall cladding it continues.
export function metalPanelProfileFor(m: Member,
  materials?: readonly MaterialAppearance[]): MetalPanelProfile | null {
  const declared = metalPanelProfileForFinish(authoredAppearance(m.material, materials)?.finish);
  return declared ?? (isStandingSeam(m.material) ? SEAM_PROFILE : null);
}

export function isSeamMember(m: Member, materials?: readonly MaterialAppearance[]): boolean {
  return SEAM_TRIM_CATEGORIES.has(m.category) && metalPanelProfileFor(m, materials) !== null;
}

/** A plan line as `[origin, a point along it]`. */
export type SkinAxis = readonly [readonly [number, number], readonly [number, number]];

/**
 * One wall, as far as a skin band is concerned: the axis a band is *matched* to, and the
 * facade datum its panel module is *measured* from.
 *
 * The two are not the same line and the difference is the whole point. A band belongs to the
 * wall whose layer stack it caps, which is a question about proximity to that wall's own axis;
 * but the panel module belongs to the facade, so it is measured from the wall's `layout_axis`
 * (→ resolve/layout_lines.py), exactly as `builders/walls.ts` measures the wall's own cladding.
 */
export interface SkinLine {
  readonly axis: SkinAxis;
  readonly datum: SkinAxis;
}

// How far off a wall's axis a band may sit and still be that wall's. A closure band is offset
// from the axis by its own layer's place in the stack — half a wall thickness at most, so a
// tenth of a metre on this house — and the nearest wall wins, never the first: the garage's
// brick screen walls stand 4 5/8" outboard of W-G-E and run parallel to it, and their layout
// line is nearer to the closure band than W-G-E's own is. Matching on the LAYOUT line rather
// than the axis is what handed the gable band the brick's datum, and with it a phase 1.7
// corrugations off the wall it continues — the residue left after the tile-size fix below.
const SKIN_LINE_TOLERANCE_M = 0.5;

/**
 * Where a band's two ends sit along its facade, in metres from that facade's origin.
 *
 * This is the band's `u` datum, and it exists because the panel module has to be continuous
 * across the wall→roof joint: the closure band IS the wall's own sheet carried up past the top
 * plate, so its ribs have to land where the wall's ribs land. Measuring `u` from the band's own
 * `p0` (what this did) restarts the module at every band — a layer thickness off at the mitred
 * corner where the band overhangs the wall axis, and a fresh arbitrary phase for the second
 * half of a gable, which splits at the ridge. Both read as a jog in the ribs at the joint.
 *
 * Falls back to the band's own run for a trim piece that stands on no wall (an eave fascia or a
 * rake band hung off the roof edge), which has no wall panel under it to line up with.
 */
export function skinUvSpanM(m: Member, lines?: readonly SkinLine[]): [number, number] {
  const dx = m.p1[0] - m.p0[0];
  const dy = m.p1[1] - m.p0[1];
  const run = Math.hypot(dx, dy);
  if (!lines?.length || run < 1e-9) return [0, run];
  const ux = dx / run;
  const uy = dy / run;
  let best: SkinAxis | null = null;
  let bestOffset = SKIN_LINE_TOLERANCE_M;
  for (const line of lines) {
    const [[ox, oy], [px, py]] = line.axis;
    const len = Math.hypot(px - ox, py - oy);
    if (len < 1e-9) continue;
    const vx = (px - ox) / len;
    const vy = (py - oy) / len;
    if (Math.abs(vx * uy - vy * ux) > 1e-6) continue;   // not this wall's direction
    const offset = Math.abs((m.p0[1] - oy) * vx - (m.p0[0] - ox) * vy);
    if (offset >= bestOffset) continue;                 // a nearer wall already claimed it
    bestOffset = offset;
    best = line.datum;
  }
  if (!best) return [0, run];
  const [[ox, oy], [px, py]] = best;
  const len = Math.hypot(px - ox, py - oy) || 1;
  const vx = (px - ox) / len;
  const vy = (py - oy) / len;
  // The datum may run the other way down the same facade (W-G-N's axis runs -x, its layout
  // line +x), so the band's far end is its near end plus a SIGNED run.
  const start = (m.p0[0] - ox) * vx + (m.p0[1] - oy) * vy;
  return [start, start + run * (ux * vx + uy * vy)];
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

function bucket(members: Member[], materials?: readonly MaterialAppearance[]): Buckets {
  const out: Buckets = { rect: [], raked: [], ijoist: [], seam: [] };
  for (const m of members) {
    // Seam first: a standing-seam or declared ribbed-panel band needs its own textured
    // material, so it can't share the vertex-coloured merge with the lumber around it.
    if (isSeamMember(m, materials) && !isVerticalMember(m)) out.seam.push(m);
    else if (m.shape === "i_joist") out.ijoist.push(m);
    else if (isRakedMember(m)) out.raked.push(m);
    else out.rect.push(m);
  }
  return out;
}

// One merge target: every member sharing a metal-panel profile and paint gets one mesh, so a
// batch of skin members drawn from several walls (a roof's closure family spans every wall
// under it) doesn't force a ribbed PBR band and a standing-seam one into the same texture.
function seamGroupsFor(members: Member[], materials?: readonly MaterialAppearance[]):
  Map<string, { profile: MetalPanelProfile; paint: number; members: Member[] }> {
  const groups = new Map<string, { profile: MetalPanelProfile; paint: number; members: Member[] }>();
  for (const m of members) {
    const profile = metalPanelProfileFor(m, materials);
    if (!profile) continue;
    // The coil white default, exactly as builders/walls.ts resolves it: a paint named by the
    // member's own authored finish wins, everything else keeps the standard 0xE8E8E2 coil.
    const paintHex = finishBaseColor(authoredAppearance(m.material, materials)?.finish);
    const paint = paintHex ? new THREE.Color(paintHex).getHex() : 0xE8E8E2;
    const key = `${profile.key}|${paint}`;
    const g = groups.get(key) ?? { profile, paint, members: [] };
    g.members.push(m);
    groups.set(key, g);
  }
  return groups;
}

// Standing-seam / ribbed-panel skin bands (gable closure cladding, roof-edge cladding) merged
// per finish group, each carrying its own procedural normal map. Each band gets world-scaled
// UVs off its own run, matching applyStandingSeamWallUv, so the module stays at true scale and
// the seams line up with the wall and roof panels the band meets.
function buildSeamMesh(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", ownerUid: string, materials?: readonly MaterialAppearance[],
  lines?: readonly SkinLine[]) {
  if (!members.length) return;
  for (const { profile, paint, members: groupMembers } of seamGroupsFor(members, materials).values()) {
    // The band's OWN module, not the seam pan's. `SEAM_TILE_SIZE_M` (16" pans) stood here for
    // every profile, so a band finished in something else was drawn at the seam's scale and
    // stretched by the ratio between them — 1.33x for the house's 12" PBR rib, and 6x for the
    // garage's 2-2/3" corrugation, which is what made those closures read as smeared metal
    // beside the wall they continue.
    const tileM = panelTileSizeM(profile);
    const positions: number[] = [];
    const indices: number[] = [];
    const uvs: number[] = [];
    const drawn: Member[] = [];
    const triangleStarts: number[] = [0];
    for (const m of groupMembers) {
      const verts = rakedBoxVertices(m, center);
      if (!verts) continue;
      const base = positions.length / 3;
      for (const v of verts) positions.push(v[0], v[1], v[2]);
      pushBoxIndices(indices, base);
      triangleStarts.push(triangleStarts[triangleStarts.length - 1] + TRIANGLES_PER_MEMBER_BOX);
      drawn.push(m);
      // Per-member UVs, not one shared axis: eave bands run one way and rake bands the other,
      // so a single frame would smear the pans on half of them. u runs along the band's facade
      // from that facade's own origin (→ skinUvSpanM), v is elevation — the same world-scaled
      // frame applyStandingSeamWallUv gives a wall, so bands and walls share one seam rhythm
      // and one phase.
      const [startM, endM] = skinUvSpanM(m, lines);
      for (let index = 0; index < verts.length; index++) {
        const atEnd = index === 1 || index === 2 || index === 5 || index === 6;
        uvs.push((atEnd ? endM : startM) / tileM, verts[index][1] / tileM);
      }
    }
    if (!positions.length) continue;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    const mesh = makeSurfaceMesh(geo, createStandingSeamMaterial(mode, [1, 1], paint, true, profile));
    tagMergedMemberIdentity(mesh, memberUidsFor(ownerUid, drawn), triangleStarts);
    group.add(mesh);
  }
}

function buildRectInstances(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string,
  materials?: readonly MaterialAppearance[]) {
  if (!members.length) return;
  // No colour: every instance sets its own via `setColorAt`.
  const material = standardMaterial(undefined, mode);
  const mesh = markShadowCaster(new THREE.InstancedMesh(UNIT_BOX, material, members.length));
  members.forEach((m, i) => {
    mesh.setMatrixAt(i, composeMemberBoxMatrix(_m, m, center));
    mesh.setColorAt(i, _color.set(memberColor(m, palette, materials)));
  });
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  tagInstancedMemberIdentity(mesh, memberUidsFor(ownerUid, members));
  group.add(mesh);
}

// Exact 8-vertex raked box: vertical ends, sloped top/bottom — mirrors
// emit/gltf/emitter.py's add_member_box. One merged geometry (vertex colors) per trade.
function buildRakedMesh(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string,
  materials?: readonly MaterialAppearance[]) {
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
    const col = new THREE.Color(memberColor(m, palette, materials));
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
  const mesh = makeSurfaceMesh(geo, material);
  tagMergedMemberIdentity(mesh, memberUidsFor(ownerUid, drawn), triangleStarts);
  group.add(mesh);
}

// Three shared InstancedMeshes (top flange, bottom flange, web), one instance per member.
// The run axis includes its resolved rise, so roof I-joists follow the roof plane instead
// of appearing flat in the model.
function buildIJoists(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string,
  materials?: readonly MaterialAppearance[]) {
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
    const slopedLength = Math.hypot(runLen, rise);
    // `z0_m`/`z1_m` bound a member VERTICALLY — the same convention `rakedBoxVertices` draws
    // a raked 2x to (vertical ends, sloped top and bottom faces), and the one the engine
    // sizes a rafter in: `z1_m` IS the deck plane, and the assembly's sheathing/membrane/
    // roofing stack starts there. The three plies below are stacked PERPENDICULAR to the run,
    // so that vertical extent has to be foreshortened by cos(theta) before it can be spent as
    // a section depth. Without this the roof redesign's 11-7/8" I-joist rafters stood 1-3/8"
    // proud of their own `z1_m` on this 6:12 roof and pushed their top flange up through the
    // sheathing, the membrane and the standing seam above them (2026-08-31).
    const cosTheta = slopedLength > 1e-9 ? runLen / slopedLength : 1;
    const depth = (m.z1_m - m.z0_m) * cosTheta;
    const flangeT = m.flange_thickness_m ?? depth * 0.1;
    const flangeW = m.flange_width_m ?? m.width_m;
    const webT = m.web_thickness_m ?? Math.min(flangeW, 0.01);
    const color = memberColor(m, palette, materials);
    const webDepth = Math.max(depth - 2 * flangeT, MIN_EXTENT_M);
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
    markShadowCaster(mesh);
    // All three plies share one instance index per member, so any of them picks the same stick.
    tagInstancedMemberIdentity(mesh, uids);
    group.add(mesh);
  }
}

/**
 * Draw `members` into `group`. `ownerUid` is the uid of the wall / roof / floor / stair the
 * resolver framed them for — half of each member's identity (→ model/memberIdentity.ts), and
 * the reason every bucket can hand a picked index back as a stable member uid. `materials` is
 * the model's catalog, so a skin member (cladding closure, trim run) that carries its host
 * layer's material ref gets the same declared-finish-first colour and metal-panel dispatch a
 * wall layer gets in builders/walls.ts, instead of guessing from the ref alone. `lines` is the
 * facade datums the model's walls are laid out on, which is what a metal-panel skin band takes
 * its module phase from so the ribs run through the wall→roof joint unbroken (→ skinUvSpanM).
 */
export function buildMembers(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string,
  materials?: readonly MaterialAppearance[], lines?: readonly SkinLine[]) {
  const boxMembers = members.filter((member) => !member.plan_outline?.length);
  if (!boxMembers.length) return;
  const buckets = bucket(boxMembers, materials);
  buildRectInstances(group, buckets.rect, center, mode, palette, ownerUid, materials);
  buildRakedMesh(group, buckets.raked, center, mode, palette, ownerUid, materials);
  buildIJoists(group, buckets.ijoist, center, mode, palette, ownerUid, materials);
  buildSeamMesh(group, buckets.seam, center, mode, ownerUid, materials, lines);
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
