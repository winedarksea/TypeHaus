// Wall and opening builders: the layer stack of every wall, the smooth arched soffits some of
// them carry, and the door/window fills cut into them.
//
// Split out of components/Panel3D.tsx — by far the largest builder family, and the one with
// real geometry of its own (arch tessellation, the piece decomposition around openings, the
// raked top of a gable or ToRoof wall) rather than a straight extrusion of a resolved polygon.
import * as THREE from "three";
import type { LayerVisibilityGroup } from "../../model/visibility";
import { layerVisibilityGroupOf } from "../../model/visibility";
import type { DoorOperation, MaterialSpec, Member, Opening, Wall } from "../../model/types";
import {
  authoredAppearance, finishBaseColor, materialColor, type ResolvedNordicPalette,
} from "../../nordic/palette";
import {
  applyMasonryWallUv, applyStandingSeamWallUv, createMasonryMaterial,
  createStandingSeamMaterial, isMasonry, isStandingSeam, masonryStyleFor, masonryTileSizeM,
  metalPanelProfileForFinish, SEAM_PROFILE,
} from "../materials";
import { buildMembers, categoryColor, isSkinMember, type SkinLine } from "../members";
import {
  applyPlankWallUv, createPlankMaterial, isWoodPlank, plankStyleFor, plankTileSizeM,
} from "../plankMaterial";
import {
  createPlanPrismGeometry, createRakedPlanPrismGeometry, projectPointToScene, type PlanCenter,
} from "../planGeometry";
import { makeSurfaceMesh, NORDIC_ROUGHNESS, standardMaterial } from "../surfaces";
import { registerMemberPicks, registerSelectable, tagLayerGroup } from "./registry";
import type { Trade } from "../../state/vocabulary";
import { createArchRingGeometry } from "./archRing";
import { wallBandShapes, type ArchSoffitCylinder } from "./wallBandShape";
// The wall's local frame and the arch-head circle live in ./wallFrame, shared with the
// voussoir rings. Re-exported here because callers and tests knew them at this path first.
import {
  archSoffitCircle, archSoffitSample, archSoffitSegmentCount, baseRefZ, wallLocalFrame,
  wallLocalToSceneMatrix,
} from "./wallFrame";
export {
  ARCH_SOFFIT_CHORD_TOLERANCE_M, ARCH_SOFFIT_MAX_SEGMENT_COUNT, ARCH_SOFFIT_MIN_SEGMENT_COUNT,
  COLLINEAR_VERTEX_TOLERANCE_M, archSoffitCircle, archSoffitSample, archSoffitSegmentCount,
  baseRefZ,
  withoutCollinearVertices,
} from "./wallFrame";

// A vertex counts as being on the soffit circle within this distance of it. The samples are
// computed from the circle, so the only slack needed is ExtrudeGeometry's float32 storage
// (~3e-7 m at house coordinates); anything beyond was clipped away by the wall top.
const ARCH_SOFFIT_RING_TOLERANCE_M = 1e-5;
// ExtrudeGeometry gives its front/back caps normals along the sweep axis and its swept side
// walls normals in the shape plane; only the latter can belong to an arch soffit.
const ARCH_SOFFIT_SWEPT_FACE_MAX_AXIAL_NORMAL = 0.5;

export function rakedTopAt(w: Wall, x: number, y: number): number {
  if (w.top_z0_m == null && w.top_z1_m == null) return w.z1_m;
  const start = w.top_z0_m ?? w.z1_m;
  const end = w.top_z1_m ?? w.z1_m;
  const [[x0, y0], [x1, y1]] = w.axis;
  const dx = x1 - x0, dy = y1 - y0;
  const len2 = dx * dx + dy * dy;
  const t = len2 < 1e-9 ? 0 : Math.min(1, Math.max(0, ((x - x0) * dx + (y - y0) * dy) / len2));
  return start + (end - start) * t;
}

// Extrude a layer polygon between z0 and a per-vertex raked top (rather than a flat height) —
// a wall under a sloped roof (gable end, ToRoof) must stop at its actual rake, or its full
// bounding-height rectangle engulfs the roof geometry and hides it from outside (#WP-roof-hide).
// Build one wall: an extruded prism per layer polygon (→ "walls" trade) + its solid framing
// members (→ "framing" trade, WP8). World plan (x,y) maps to three (x, z); height runs
// along +Y. Centered on (cx,cz). Raked (ToRoof) walls extrude to their actual sloped top,
// not the flat bounding height, so the roof they carry stays visible from outside.
export function buildWall(
  tradeGroups: Record<Trade, THREE.Group>,
  w: Wall,
  openings: Opening[],
  center: PlanCenter,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
  materials?: MaterialSpec[],
) {
  const mats: THREE.Material[] = [];
  for (const ly of w.layers) {
    const layerGroup = layerVisibilityGroupOf(ly.function);
    const layerFirstChildIndex = tradeGroups.walls.children.length;
    if (ly.polygon.length < 3) continue;
    // Cavity fill shares its host structure layer's polygon — extruding it would only
    // z-fight with the studs it lives between.
    if (ly.is_cavity) continue;
    const appearance = authoredAppearance(ly.material, materials);
    // A metal panel finish is DECLARED first and guessed second. `metalPanelProfileForFinish`
    // reads the material's authored `finish` — "ribbed-panel" for the house's exposed-fastener
    // PBR, "standing-seam" for anything that says so — and only a material that declares
    // nothing falls back to `isStandingSeam`, which is a substring test on the ref and cannot
    // tell a rib from a fold. `pbr-panel-26` has no "seam" in its tag on purpose, so without
    // this branch it would render as flat grey.
    const declaredPanel = metalPanelProfileForFinish(appearance?.finish);
    const seamProfile = ly.function === "cladding"
      ? (declaredPanel ?? (isStandingSeam(ly.material) ? SEAM_PROFILE : null))
      : null;
    const seam = seamProfile !== null;
    // Masonry (brick/CMU/stone) gets coursing + recessed mortar, not a flat fill — a brick
    // veneer or CMU wythe otherwise read like painted drywall. The style (module + mortar +
    // jitter) comes from the material's authored `finish`, so CMU reads as 16"×8" grey block
    // and white brick as whitewash over grey mortar; only a material that declares nothing
    // falls back to guessing from its tag.
    const masonryStyle = !seam && isMasonry(ly.material)
      ? masonryStyleFor(ly.material, appearance?.finish) : null;
    // Wood boards get the same treatment for the same reason: the sauna's basswood T&G liner
    // and the study's walnut wainscot are boards, and a flat fill made a lined room read as
    // tan drywall. `ly.board_run` is derived by the engine from the furring behind the layer
    // (resolve/topology.py `_board_run`), so the boards land the way they are fastened.
    const plankStyle = !seam && !masonryStyle && isWoodPlank(ly.material)
      ? plankStyleFor(ly.material, appearance?.finish) : null;
    // The coil white is the DEFAULT, not the only option (2026-08-26). A metal panel that
    // declares a finish naming its own paint gets that paint; everything else keeps
    // 0xE8E8E2, which is what all five of the house's white skins author (their catalog
    // `color` is the drawing hatch tone, not the paint, so it must not be read here).
    // Mirrors the declared-finish branch in emit/gltf/palette.py::_material_finish_color.
    const seamPaint = finishBaseColor(appearance?.finish);
    const mat = seam
      ? createStandingSeamMaterial(mode, [
        Math.hypot(w.axis[1][0] - w.axis[0][0], w.axis[1][1] - w.axis[0][1]),
        Math.max(0.1, w.z1_m - w.z0_m),
      ], seamPaint ? new THREE.Color(seamPaint).getHex() : 0xE8E8E2, true,
      seamProfile ?? SEAM_PROFILE)
      : masonryStyle
        ? createMasonryMaterial(mode, masonryStyle,
          materialColor(ly.material, palette, materials), appearance?.color)
        : plankStyle
          ? createPlankMaterial(mode, plankStyle,
            materialColor(ly.material, palette, materials))
          : standardMaterial(new THREE.Color(materialColor(ly.material, palette, materials)), mode);
    mats.push(mat);
    // A banded layer (`Layer.extent`, or one region of a split row via `Layer.slot`) covers
    // only part of the wall's height, and BOTH geometry paths have to honour that. Clamping
    // the strip path here rather than inside `wallLayerPieces` keeps the jamb/arch clipping
    // it does unchanged and simply trims the result; the swept path takes the band itself,
    // because its outline is built from the wall's own z-range and would otherwise hand back
    // a full-height solid per region — five coincident wythes z-fighting for the same face,
    // which is what the sunken garden's Ishtar wall showed until 2026-08-20. Its arched door
    // and window are what put it on the swept path in the first place.
    const smoothArchGeometry = createSmoothArchedWallLayerGeometry(w, ly.polygon, openings, center, ly);
    const geometries: (THREE.BufferGeometry | null)[] = smoothArchGeometry
      ? [smoothArchGeometry]
      : clampPiecesToBand(wallLayerPieces(w, ly.polygon, openings), ly).map((piece) => piece.topIsRaked
        ? createRakedPlanPrismGeometry(piece.polygon, piece.z0_m,
          (point) => rakedTopAt(w, point[0], point[1]), center)
        : createPlanPrismGeometry(piece.polygon, piece.z0_m, piece.z1_m, [], center));
    for (const geo of geometries) {
      if (!geo) continue;
      // The line, not the wall: the pan module belongs to the facade, and the outriggers it
      // clips to are laid out on that same line (resolve/framing/furring.py).
      if (seam) applyStandingSeamWallUv(geo, w.layout_axis ?? w.axis, center, seamProfile ?? SEAM_PROFILE);
      else if (masonryStyle) {
        // Course from the wall's own base, not project zero — see applyMasonryWallUv.
        applyMasonryWallUv(geo, w.axis, center, masonryTileSizeM(masonryStyle), w.z0_m);
      } else if (plankStyle) {
        // Same datum argument as the masonry course: boards start at the corner and at the
        // floor, and only the last one is cut.
        applyPlankWallUv(geo, w.axis, center, plankTileSizeM(plankStyle), w.z0_m,
          ly.board_run ?? null);
      }
      const mesh = makeSurfaceMesh(geo, mat);
      mesh.userData.uid = w.uid;
      mesh.userData.selectionKind = "wall";
      mesh.userData.tag = w.tag;
      tradeGroups.walls.add(mesh);
      picks.push(mesh);

      // Nordic outlines, except on the cladding. `wallLayerPieces` splits a layer at every
      // opening jamb, so outlining each piece drew a full-height line down the facade at every
      // window and a full-width one at every storey break — grid lines across a finish that has
      // no joints there. The finish carries its own definition (seam module, coursing) and the
      // building's corners come from the shading, so the outermost layer goes without; the
      // layers behind it keep theirs, where the piece boundary is a real edge.
      if (mode === "nordic" && ly.function !== "cladding") {
        tradeGroups.walls.add(new THREE.LineSegments(
          new THREE.EdgesGeometry(geo, 25),
          new THREE.LineBasicMaterial({ color: palette.edge, transparent: true, opacity: 0.35 }),
        ));
      }
    }
    // Voussoirs. A masonry layer's arched openings each get a ring of radiating bricks, so the
    // head reads as an arch instead of as a curve sliced out of running bond. Built once per
    // arch, in the layer band that holds the arch's SPRINGLINE — the split brick row on the
    // Ishtar wall is five layers deep, and without that rule the same ring would be built five
    // times, once per band. The springline is where the arch is born, so its band is the one
    // whose brick the arch would actually be turned in; on W-B-BRICK both arches spring inside
    // `brick-field-lo` and both rings come out lapis. The layer's own material does the rest —
    // the ring carries polar UVs into the very same tile, so `mat` is reused as it stands.
    if (masonryStyle) {
      for (const opening of openings) {
        if ((opening.arch_rise_m ?? 0) <= 1e-9) continue;
        const springline = baseRefZ(w) + opening.sill_m
          + Math.max(0, opening.height_m - (opening.arch_rise_m ?? 0));
        if (springline < Math.max(w.z0_m, ly.z0_m ?? -Infinity) - 1e-9 ||
            springline >= Math.min(w.z1_m, ly.z1_m ?? Infinity) - 1e-9) continue;
        const ring = createArchRingGeometry(opening, w, ly.polygon, center, masonryStyle);
        if (!ring) continue;
        const mesh = makeSurfaceMesh(ring, mat);
        mesh.userData.uid = w.uid;
        mesh.userData.selectionKind = "wall";
        mesh.userData.tag = w.tag;
        tradeGroups.walls.add(mesh);
        picks.push(mesh);
        // No Nordic outline: the ring's own joints are its definition, and an edge line per
        // facet would scribble over the coursing the ring exists to show.
      }
    }
    tagLayerGroup(tradeGroups.walls, layerFirstChildIndex, layerGroup);
  }
  const framingFirstIndex = tradeGroups.framing.children.length;
  const wallsSkinFirstIndex = tradeGroups.walls.children.length;
  buildWallSkinMembers(tradeGroups, w.uid, w.members, center, mode, palette, materials,
    [{ axis: w.axis, datum: w.layout_axis ?? w.axis }]);
  // A wall's studs are pickable as themselves; the wall body remains pickable through its
  // layer meshes above, so both "this wall" and "this stud" stay one click away.
  registerMemberPicks(tradeGroups.framing, framingFirstIndex, picks);
  registerMemberPicks(tradeGroups.walls, wallsSkinFirstIndex, picks);
  byUid.set(w.uid, mats);
}

// A skin member continuing the furring band (a truss wall's outrigger or girt closure) is
// still real lumber — the carpenter's work — so it stays with the studs on the Framing trade.
// Every other skin category (cladding, sheathing, membrane, insulation, airgap, finish) is
// envelope skin and belongs with the wall body it continues, on the Walls trade, or a cladding
// closure band running up to the roof reads as framing while the wall's own cladding prism
// below it reads as walls.
//
// The catlin truss (2026-08-26) put THREE furring closure bands on a wall where the Swinburne
// outrigger put one — the inner girt, the outer girt and, beside them, foam and vent-gap bands
// that are NOT furring and correctly stay on Walls. The rule did not have to change for that,
// which is the point of routing on the layer group rather than on a wall type.
const FRAMING_SKIN_GROUPS = new Set<LayerVisibilityGroup>(["furring"]);

/** Which trade draws one wall member: the stick trade, or the envelope the member continues.
 *
 * `isSkinMember` asks the member's *category*, and that is the whole of it. Naming a material
 * is not the test and never was: every piece of either truss pack names one — the Swinburne
 * block is spf, its outrigger and ladder blocking are kdat, its tab and buck are
 * struct-1-plywood; the catlin truss's block-1 and inner girt are spf, its block-2 and outer
 * girt are kdat — and all of them are lumber. Routing on `member.material` sent the entire
 * truss wall to the Walls trade under the "Other" layer group, which took it out of the
 * framing view: present in the model and in 2D, gone from 3D.
 */
function memberTrade(member: Member, tradeGroups: Record<Trade, THREE.Group>,
  group: LayerVisibilityGroup): THREE.Group {
  return !isSkinMember(member) || FRAMING_SKIN_GROUPS.has(group)
    ? tradeGroups.framing : tradeGroups.walls;
}

// Wall members split two ways for visibility: lumber and a furring skin band (the outrigger or
// girt closure) answer to the Framing trade, while every other skin band (a cladding/sheathing/
// membrane closure, a trim run) is a derived envelope skin and answers to the assembly-layer
// control that governs the layer it continues, on the Walls trade. Both halves still carry
// their layer-group tag, so a member that names a material stays reachable from the per-layer
// toggles whichever trade draws it. The split has to happen before the merge, since a merged
// mesh has one visibility flag for all of it.
function buildWallSkinMembers(
  tradeGroups: Record<Trade, THREE.Group>, wallUid: string, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, materials?: MaterialSpec[],
  lines?: readonly SkinLine[],
) {
  const lumber = members.filter((member) => !member.material);
  buildMembers(tradeGroups.framing, lumber, center, mode, palette, wallUid);
  // Bucketed by (trade, layer group), not by layer group alone: "other" collects both a
  // truss block and a corner-trim run, and those two answer to different trades.
  const skinByBucket = new Map<string, { parent: THREE.Group; group: LayerVisibilityGroup;
    members: Member[] }>();
  for (const member of members) {
    if (!member.material) continue;
    const group = layerVisibilityGroupOf(member.category);
    const parent = memberTrade(member, tradeGroups, group);
    const key = `${parent === tradeGroups.framing ? "framing" : "walls"}|${group}`;
    const bucket = skinByBucket.get(key) ?? { parent, group, members: [] };
    bucket.members.push(member);
    skinByBucket.set(key, bucket);
  }
  for (const { parent, group, members: skin } of skinByBucket.values()) {
    const firstChildIndex = parent.children.length;
    buildMembers(parent, skin, center, mode, palette, wallUid, materials, lines);
    tagLayerGroup(parent, firstChildIndex, group);
  }
}

export interface WallLayerPiece {
  polygon: [number, number][];
  z0_m: number;
  z1_m: number;
  topIsRaked: boolean;
}


// ExtrudeGeometry sweeps every hole edge as its own detached quad, so the soffit ships per-facet
// normals and shades as N flat strips however finely it is tessellated. Overwrite just the swept
// soffit ring with the analytic cylinder normal; jambs, wall ends and the front/back caps keep
// their extruded normals, so the prism's corners stay crisp. Runs in ExtrudeGeometry's local
// frame (shape in XY, sweep along Z), before the layer is placed into the scene.
function applySmoothArchSoffitNormals(
  geometry: THREE.BufferGeometry, soffits: readonly ArchSoffitCylinder[],
): void {
  if (soffits.length === 0) return;
  const position = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  if (!position || !normal) return;
  for (let index = 0; index < position.count; index++) {
    if (Math.abs(normal.getZ(index)) > ARCH_SOFFIT_SWEPT_FACE_MAX_AXIAL_NORMAL) continue;
    const along = position.getX(index), elevation = position.getY(index);
    for (const { centerAlongM, circleCenterM, radiusM } of soffits) {
      const dx = along - centerAlongM, dy = elevation - circleCenterM;
      const distance = Math.hypot(dx, dy);
      if (dy < -ARCH_SOFFIT_RING_TOLERANCE_M ||
        Math.abs(distance - radiusM) > ARCH_SOFFIT_RING_TOLERANCE_M) continue;
      // Replace the facet's direction only — its outward sense stays whatever the sweep
      // established, so the void keeps facing into the opening.
      const sign = normal.getX(index) * dx + normal.getY(index) * dy < 0 ? -1 : 1;
      normal.setXYZ(index, sign * dx / distance, sign * dy / distance, 0);
      break;
    }
  }
  normal.needsUpdate = true;
}

// A concrete arch should read as one continuous cast surface. Extruding the band's outline
// gives the soffit a single smooth mesh; the strip fallback below is retained for raked and
// junction-mitered wall layers whose non-rectangular plan footprint cannot be swept safely.
export function createSmoothArchedWallLayerGeometry(
  wall: Wall, polygon: readonly [number, number][], openings: Opening[], center: PlanCenter,
  band?: { z0_m?: number | null; z1_m?: number | null },
): THREE.BufferGeometry | null {
  if (!openings.some((opening) => (opening.arch_rise_m ?? 0) > 1e-9) ||
      wall.top_z0_m != null || wall.top_z1_m != null) return null;
  const frame = wallLocalFrame(wall, polygon);
  if (!frame) return null;
  const { minAlong, maxAlong, minAcross, maxAcross } = frame;

  // The layer's own vertical extent, intersected with the wall's. An unbanded layer gets the
  // wall back unchanged, so nothing authored before `Layer.extent` moves.
  const bandBottom = Math.max(wall.z0_m, band?.z0_m ?? -Infinity);
  const bandTop = Math.min(wall.z1_m, band?.z1_m ?? Infinity);
  if (bandTop - bandBottom <= 1e-9) return null;

  // The band's outline, with every opening notched, parted or holed as its reach demands —
  // see builders/wallBandShape.ts. A clamped hole edge would be swept as a strip lying on the
  // band boundary, right across the opening.
  const { shapes, soffits } = wallBandShapes(
    { minAlong, maxAlong, bandBottom, bandTop }, wall, openings);
  if (shapes.length === 0) return null;
  const geometry = new THREE.ExtrudeGeometry(shapes, {
    depth: maxAcross - minAcross, bevelEnabled: false, curveSegments: 1,
  });
  applySmoothArchSoffitNormals(geometry, soffits);
  geometry.applyMatrix4(wallLocalToSceneMatrix(frame, center));
  return geometry;
}

// Trim wall-layer pieces to a layer's own band, dropping the ones outside it entirely.
// `wallLayerPieces` works in the wall's full height because that is what a layer normally
// occupies; a banded layer is the exception, and this is where the exception is applied.
// A piece whose raked top is cut off by the band is no longer raked — its top is the band.
export function clampPiecesToBand(
  pieces: WallLayerPiece[], layer: { z0_m?: number | null; z1_m?: number | null },
): WallLayerPiece[] {
  const bandBottom = layer.z0_m ?? null;
  const bandTop = layer.z1_m ?? null;
  if (bandBottom == null && bandTop == null) return pieces;
  const out: WallLayerPiece[] = [];
  for (const piece of pieces) {
    const z0 = bandBottom == null ? piece.z0_m : Math.max(piece.z0_m, bandBottom);
    const z1 = bandTop == null ? piece.z1_m : Math.min(piece.z1_m, bandTop);
    if (z1 - z0 <= 1e-9) continue;
    out.push({ ...piece, z0_m: z0, z1_m: z1, topIsRaked: piece.topIsRaked && z1 >= piece.z1_m });
  }
  return out;
}

// Split an arbitrary junction-solved layer polygon at opening jamb stations. Clipping the
// actual ring (instead of rebuilding its local bounds) preserves mitered and butted ends.
export function wallLayerPieces(wall: Wall, polygon: readonly [number, number][], openings: Opening[]): WallLayerPiece[] {
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9 || polygon.length < 3) return [];
  const direction: [number, number] = [(x1 - x0) / length, (y1 - y0) / length];
  const normal: [number, number] = [-direction[1], direction[0]];
  const local = polygon.map(([x, y]) => {
    const px = x - x0, py = y - y0;
    return [px * direction[0] + py * direction[1], px * normal[0] + py * normal[1]] as const;
  });
  const minAlong = Math.min(...local.map(([along]) => along));
  const maxAlong = Math.max(...local.map(([along]) => along));
  const relevant = openings.map((opening) => ({
    opening,
    start: Math.max(minAlong, opening.center_along_m - opening.width_m / 2),
    end: Math.min(maxAlong, opening.center_along_m + opening.width_m / 2),
  })).filter(({ start, end }) => end - start > 1e-9);
  const boundaries = Array.from(new Set([minAlong, maxAlong, ...relevant.flatMap(({ start, end }) => [start, end])]))
    .sort((a, b) => a - b);
  const point = (along: number, across: number): [number, number] => [
    x0 + direction[0] * along + normal[0] * across,
    y0 + direction[1] * along + normal[1] * across,
  ];
  const clip = (
    ring: readonly (readonly [number, number])[],
    boundary: number,
    keepGreater: boolean,
  ): [number, number][] => {
    const output: [number, number][] = [];
    const inside = ([along]: readonly [number, number]) =>
      keepGreater ? along >= boundary - 1e-9 : along <= boundary + 1e-9;
    for (let index = 0; index < ring.length; index++) {
      const current = ring[index], next = ring[(index + 1) % ring.length];
      const currentInside = inside(current), nextInside = inside(next);
      if (currentInside) output.push([current[0], current[1]]);
      if (currentInside !== nextInside) {
        const denominator = next[0] - current[0];
        if (Math.abs(denominator) > 1e-12) {
          const fraction = (boundary - current[0]) / denominator;
          output.push([boundary, current[1] + (next[1] - current[1]) * fraction]);
        }
      }
    }
    return output;
  };
  const ring = (start: number, end: number): [number, number][] =>
    clip(clip(local, start, true), end, false).map(([along, across]) => point(along, across));
  const raked = wall.top_z0_m != null || wall.top_z1_m != null;
  const pieces: WallLayerPiece[] = [];
  for (let index = 0; index < boundaries.length - 1; index++) {
    const start = boundaries[index], end = boundaries[index + 1];
    const active = relevant.find(({ start: openingStart, end: openingEnd }) =>
      (start + end) / 2 >= openingStart && (start + end) / 2 <= openingEnd)?.opening;
    const strip = ring(start, end);
    if (strip.length < 3) continue;
    if (!active) {
      pieces.push({ polygon: strip, z0_m: wall.z0_m, z1_m: wall.z1_m, topIsRaked: raked });
      continue;
    }
    const openingBottom = baseRefZ(wall) + active.sill_m;
    const openingTop = openingBottom + active.height_m;
    if (openingBottom > wall.z0_m + 1e-9)
      pieces.push({ polygon: strip, z0_m: wall.z0_m, z1_m: openingBottom, topIsRaked: false });
    const archRise = active.arch_rise_m ?? 0;
    if (archRise > 1e-9) {
      const springline = openingBottom + Math.max(0, active.height_m - archRise);
      const { radiusM: radius, halfAngleRad, depthM } = archSoffitCircle(active.width_m / 2, archRise);
      // Angular steps here too: even-x strips leave a ~40 cm riser at each springline.
      const segmentCount = archSoffitSegmentCount(radius, halfAngleRad);
      for (let segment = 0; segment < segmentCount; segment++) {
        const segmentStart = active.center_along_m + archSoffitSample(segment, segmentCount, radius, halfAngleRad).offsetM;
        const segmentEnd = active.center_along_m + archSoffitSample(segment + 1, segmentCount, radius, halfAngleRad).offsetM;
        const clippedStart = Math.max(start, segmentStart);
        const clippedEnd = Math.min(end, segmentEnd);
        if (clippedEnd - clippedStart <= 1e-9) continue;
        const midpoint = (clippedStart + clippedEnd) / 2;
        const offset = midpoint - active.center_along_m;
        const curve = radius * radius - offset * offset;
        // Height above the springline, not above the circle's centre — they differ by
        // `depthM` on a segmental arch and coincide on a semicircle.
        const soffit = springline + Math.sqrt(Math.max(0, curve)) - depthM;
        if (wall.z1_m > soffit + 1e-9)
          pieces.push({ polygon: ring(clippedStart, clippedEnd), z0_m: soffit,
            z1_m: wall.z1_m, topIsRaked: raked });
      }
      continue;
    }
    const minTop = Math.min(...strip.map(([x, y]) => rakedTopAt(wall, x, y)));
    if (minTop > openingTop + 1e-9)
      pieces.push({ polygon: strip, z0_m: openingTop, z1_m: wall.z1_m, topIsRaked: raked });
  }
  return pieces;
}

// Exterior window casing — mirrors the exterior_trim part in resolve/geometry_openings.py
// (constants _WINDOW_TRIM_FACE_WIDTH_M / _WINDOW_TRIM_PROUD_DEPTH_M): a picture-frame of
// flat boards proud of the cladding plane, windows in clad walls only. The colour rides
// members.ts CATEGORY_COLOR ("window_trim"), keeping recolors a palette-only edit.
// 1 1/4" face: the visible width of standard J-channel/flat trim, chosen over a heavier
// 2 1/2" face that read as too heavy in 3D — casing and window frame are both charcoal
// here and blur into one band.
const WINDOW_TRIM_FACE_WIDTH_M = 0.032;
const WINDOW_TRIM_PROUD_DEPTH_M = 0.019;

// Mirrors resolve/geometry_openings.py::_exterior_face — the exterior cladding plane as a
// signed offset along the wall's right-hand normal, or null when the outermost depth layer
// is not cladding (a concrete wall or interior partition has no plane to sit a casing on).
function exteriorFace(wall: Wall): { plane: number; sign: number } | null {
  const layers = wall.layers.filter((layer) => !layer.is_cavity);
  if (layers.length < 2) return null;
  const outerLayer = layers[layers.length - 1];
  if (outerLayer.function.trim().toLowerCase() !== "cladding") return null;
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return null;
  const nx = -(y1 - y0) / length, ny = (x1 - x0) / length;
  const project = (ring: [number, number][]) =>
    ring.map(([px, py]) => (px - x0) * nx + (py - y0) * ny);
  const outer = project(outerLayer.polygon), inner = project(layers[0].polygon);
  if (!outer.length || !inner.length) return null;
  const mean = (values: number[]) => values.reduce((a, b) => a + b, 0) / values.length;
  const outward = mean(outer) - mean(inner);
  if (Math.abs(outward) < 1e-9) return null;
  const sign = outward > 0 ? 1 : -1;
  return { plane: sign > 0 ? Math.max(...outer) : Math.min(...outer), sign };
}

export function buildOpening(parent: THREE.Group, opening: Opening, wall: Wall, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, operation: DoorOperation | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>, isGlazed = false, isTrimless = false) {
  if (opening.kind === "rough_opening") return;
  const firstChildIndex = parent.children.length;
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return;
  const direction: [number, number] = [(x1 - x0) / length, (y1 - y0) / length];
  const position: [number, number] = [x0 + direction[0] * opening.center_along_m, y0 + direction[1] * opening.center_along_m];
  const availableHeight = Math.max(0, Math.min(opening.height_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m - opening.width_m / 2), y0 + direction[1] * (opening.center_along_m - opening.width_m / 2)) - baseRefZ(wall) - opening.sill_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m + opening.width_m / 2), y0 + direction[1] * (opening.center_along_m + opening.width_m / 2)) - baseRefZ(wall) - opening.sill_m));
  if (availableHeight <= 1e-9) return;
  const rotation = Math.atan2(direction[1], direction[0]);
  const frameWidth = Math.min(0.075, opening.width_m / 4, availableHeight / 4);
  const depth = 0.08;
  // An opening in a clad wall is an exterior product: frame/mullion/stile boxes take the
  // charcoal exterior tone, doors and windows alike, and the frame extends from its
  // interior face out to the casing's proud face so the reveal reads charcoal instead of
  // exposing the wall layers' cut foam. Mirrors resolve/geometry_openings.py.
  const exterior = exteriorFace(wall);
  const frameMaterial = standardMaterial(
    exterior ? categoryColor("window_trim") : palette.member.wood, mode);
  let frameDepth = depth, frameOffset = 0;
  if (exterior) {
    const outerEdge = exterior.plane + exterior.sign * WINDOW_TRIM_PROUD_DEPTH_M;
    const innerEdge = -exterior.sign * (depth / 2);
    frameDepth = Math.abs(outerEdge - innerEdge);
    frameOffset = (outerEdge + innerEdge) / 2;
  }
  const addBox = (width: number, height: number, thickness: number, along: number, elevation: number, material: THREE.Material, normalOffset = 0) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, thickness), material);
    mesh.position.copy(projectPointToScene([
      position[0] + direction[0] * along - direction[1] * normalOffset,
      position[1] + direction[1] * along + direction[0] * normalOffset], elevation, center));
    mesh.rotation.y = rotation;
    parent.add(mesh);
  };
  const midElevation = baseRefZ(wall) + opening.sill_m + availableHeight / 2;
  if (!isTrimless) {
    // A trimless door (drywall return jamb, no applied casing) draws no frame boxes; the
    // leaf keeps its framed size so the reveal reads the same. Mirrors emit/gltf/openings.py.
    addBox(frameWidth, availableHeight, frameDepth, -opening.width_m / 2 + frameWidth / 2, midElevation, frameMaterial, frameOffset);
    addBox(frameWidth, availableHeight, frameDepth, opening.width_m / 2 - frameWidth / 2, midElevation, frameMaterial, frameOffset);
    addBox(opening.width_m, frameWidth, frameDepth, 0, baseRefZ(wall) + opening.sill_m + availableHeight - frameWidth / 2, frameMaterial, frameOffset);
    addBox(opening.width_m, frameWidth, frameDepth, 0, baseRefZ(wall) + opening.sill_m + frameWidth / 2, frameMaterial, frameOffset);
  }
  const panelHeight = Math.max(0.01, availableHeight - 2 * frameWidth);
  const glassMaterial = standardMaterial(0x8fb7c9, mode, { transparent: true, opacity: 0.48,
    roughness: 0.2, metalness: 0.05, depthWrite: false });
  if (opening.kind === "door" && operation === "double_swing") {
    // Two leaves meeting at a center mullion, matching the 2D French-door symbol.
    const mullionWidth = Math.min(frameWidth, (opening.width_m - 2 * frameWidth) / 6);
    const leafWidth = Math.max(0.01, (opening.width_m - 2 * frameWidth - mullionWidth) / 2);
    const panelElevation = baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2;
    addBox(mullionWidth, availableHeight, depth, 0, midElevation, frameMaterial);
    const leafMaterial = isGlazed ? glassMaterial : frameMaterial;
    const leafThickness = isGlazed ? 0.015 : 0.045;
    addBox(leafWidth, panelHeight, leafThickness, -mullionWidth / 2 - leafWidth / 2, panelElevation, leafMaterial);
    addBox(leafWidth, panelHeight, leafThickness, mullionWidth / 2 + leafWidth / 2, panelElevation, leafMaterial);
  } else if (opening.kind === "door" && operation === "slide") {
    // The 3D product stays closed and coplanar; a narrow meeting stile plus bottom track
    // makes the pair read as a slider without staging one panel over the wall.
    const clearWidth = opening.width_m - 2 * frameWidth;
    const stileWidth = Math.min(frameWidth / 2, clearWidth / 12);
    const panelWidth = Math.max(0.01, (clearWidth - stileWidth) / 2);
    const panelOffset = stileWidth / 2 + panelWidth / 2;
    const trackHeight = Math.min(0.02, panelHeight);
    const panelElevation = baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2;
    const panelMaterial = isGlazed ? glassMaterial : frameMaterial;
    const panelThickness = isGlazed ? 0.015 : 0.045;
    addBox(stileWidth, panelHeight, depth, 0, panelElevation, frameMaterial);
    addBox(clearWidth, trackHeight, depth, 0,
      baseRefZ(wall) + opening.sill_m + frameWidth + trackHeight / 2, frameMaterial);
    addBox(panelWidth, panelHeight, panelThickness, -panelOffset, panelElevation, panelMaterial);
    addBox(panelWidth, panelHeight, panelThickness, panelOffset, panelElevation, panelMaterial);
  } else if (opening.kind === "door" && operation === "bifold") {
    // Four leaves are a centre-opening bifold's closed product arrangement. Small reveals
    // keep the fold joints legible while the leaves remain in the wall plane.
    const clearWidth = opening.width_m - 2 * frameWidth;
    const foldGap = Math.min(frameWidth / 8, clearWidth / 40);
    const leafWidth = Math.max(0.01, (clearWidth - 3 * foldGap) / 4);
    const firstLeafCenter = -clearWidth / 2 + leafWidth / 2;
    const panelElevation = baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2;
    for (let index = 0; index < 4; index++) {
      addBox(leafWidth, panelHeight, 0.045,
        firstLeafCenter + index * (leafWidth + foldGap), panelElevation, frameMaterial);
    }
  } else if (opening.kind === "door" && operation === "pocket") {
    // Closed and coplanar, like the slider above. The wall over a pocket is drywalled on
    // both faces and genuinely reads solid, so the leaf is drawn filling its opening
    // rather than parked in the cavity — the cavity is modelled, but as framing members.
    // A pocket has no floor track, so unlike the slider the rail sits at the head.
    const clearWidth = Math.max(0.01, opening.width_m - 2 * frameWidth);
    const trackHeight = Math.min(0.02, panelHeight);
    const leafHeight = Math.max(0.01, panelHeight - trackHeight);
    const base = baseRefZ(wall) + opening.sill_m + frameWidth;
    addBox(clearWidth, trackHeight, depth, 0, base + panelHeight - trackHeight / 2, frameMaterial);
    addBox(clearWidth, leafHeight, 0.045, 0, base + leafHeight / 2, frameMaterial);
  } else if (opening.kind === "door") {
    // A sectional overhead door's panel is a factory-finished product in its own charcoal,
    // not the wood leaf of an interior door nor the near-black trim coil its frame is drawn
    // in — at 16' wide the trim tone read as matte black across the whole elevation. The
    // colour rides the generated vocabulary ("overhead_door"), mirroring
    // resolve/geometry_openings.py::_OVERHEAD_KEY.
    const leafMaterial = isGlazed ? glassMaterial
      : operation === "overhead"
        ? standardMaterial(categoryColor("overhead_door"), mode,
          { roughness: NORDIC_ROUGHNESS.matte })
        : frameMaterial;
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, isGlazed ? 0.015 : 0.045, 0,
      baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2, leafMaterial);
  } else {
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, 0.015, 0,
      baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2, glassMaterial);
  }
  if (opening.kind === "window") {
    if (exterior) {
      // Picture-frame casing on the cladding plane: two jambs beside the RO, a head band
      // over it, an apron under the sill. Mirrors resolve/geometry_openings.py, including
      // the per-board rake clip — a head band reaches past the RO span the availableHeight
      // clip already honoured, so each board checks the raked top over its own footprint.
      const trimW = WINDOW_TRIM_FACE_WIDTH_M;
      const trimOffset = exterior.plane + exterior.sign * (WINDOW_TRIM_PROUD_DEPTH_M / 2);
      const trimMaterial = standardMaterial(categoryColor("window_trim"), mode,
        { roughness: NORDIC_ROUGHNESS.matte });
      const rakedHost = wall.top_z0_m != null || wall.top_z1_m != null;
      const sillZ = baseRefZ(wall) + opening.sill_m;
      const bands: [number, number, number, number][] = [
        [trimW, availableHeight, -opening.width_m / 2 - trimW / 2, sillZ],
        [trimW, availableHeight, opening.width_m / 2 + trimW / 2, sillZ],
        [opening.width_m + 2 * trimW, trimW, 0, sillZ + availableHeight],
        [opening.width_m + 2 * trimW, trimW, 0, sillZ - trimW],
      ];
      for (const [bandW, bandH, along, baseZ] of bands) {
        let zTop = baseZ + bandH;
        if (rakedHost) {
          for (const end of [-1, 1]) {
            zTop = Math.min(zTop, rakedTopAt(wall,
              position[0] + direction[0] * (along + end * bandW / 2),
              position[1] + direction[1] * (along + end * bandW / 2)));
          }
        }
        if (zTop - baseZ <= 1e-9) continue;
        addBox(bandW, zTop - baseZ, WINDOW_TRIM_PROUD_DEPTH_M, along,
          baseZ + (zTop - baseZ) / 2, trimMaterial, trimOffset);
      }
    }
  }
  // Frame, leaf/mullion, glazing and exterior casing are one door or window: clicking any of
  // them selects the opening record, which the Inspector already knows how to edit.
  registerSelectable(parent, firstChildIndex, opening.uid, "opening", picks, byUid);
}

// Every resolved prism that is not a wall, floor or roof: slabs, footings and pads, but also
// 6x6 posts, beams, guard rails, dowels, thermal breaks, connectors, sump pits, vent risers,
// fascia, gutters and flashings. Same outline-extrusion recipe as wall layers; the finish comes
// from the solid's authored assembly when it has one, else its category (→ three/solidMaterials.ts).
//
// Plank decking is the one case the category palette cannot express: an aluminium deck slab
// needs a UV-framed procedural board finish, not a flat colour, so it is resolved first.
