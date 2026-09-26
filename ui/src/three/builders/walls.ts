// Wall and opening builders: the layer stack of every wall, the smooth arched soffits some of
// them carry, and the door/window fills cut into them.
//
// Split out of components/Panel3D.tsx — by far the largest builder family, and the one with
// real geometry of its own (arch tessellation, the piece decomposition around openings, the
// raked top of a gable or ToRoof wall) rather than a straight extrusion of a resolved polygon.
import * as THREE from "three";
import { layerTrades, primaryTrade, wallTrades } from "../../model/tradeVisibility";
import type { Layer, MaterialSpec, Opening, Wall } from "../../model/types";
import {
  authoredAppearance, finishBaseColor, materialColor, type ResolvedNordicPalette,
} from "../../nordic/palette";
import {
  applyMasonryWallUv, applyMineralWashUv, applyStandingSeamWallUv, createMasonryMaterial,
  createMineralWashMaterial, createStandingSeamMaterial, isMasonry, isMineralWashFinish,
  isStandingSeam, masonryStyleFor, masonryTileSizeM,
  metalPanelProfileForFinish, type MetalPanelProfile, SEAM_PROFILE,
} from "../materials";
import {
  applyPlankWallUv, createPlankMaterial, isWoodPlank, plankStyleFor, plankTileSizeM,
} from "../plankMaterial";
import {
  createPlanPrismGeometry, createRakedPlanPrismGeometry, type PlanCenter,
} from "../planGeometry";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";
import { registerMemberPicks, tagTrades } from "./registry";
import { buildWallSkinMembers } from "./wallSkin";
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

/** Whether a resolved layer gets an extruded prism of its own in the 3-D viewer.
 *
 * Cavity fill shares its host structure layer's polygon — a solid there would only z-fight
 * with the studs it lives between.
 *
 * A FRAMED FURRING band is not a plane. Furring is sticks at a spacing — catlin's girts, a
 * sauna's 1x4 strapping, a resilient channel — and the solver has already emitted every one of
 * them into the wall's own `members`, which this builder draws beside the bands. Extruding the
 * band as well drew a solid prism over the sticks it stands for AND, on EXT_2X6, closed the
 * 1/2" vent gap the girts stand off the foam on, so a vented rainscreen read as sheet furring.
 * Only the FRAMED ones: a furring layer with no FramingSpec is a genuine continuous sheet and
 * still has a solid to draw.
 *
 * Structure and sheathing bands deliberately stay. A wall body has to be opaque from outside,
 * and their double-draw is answered by the `framing:*` facets (model/tradeVisibility.ts) —
 * which a furring band on a wall no longer reaches.
 *
 * Depth accounting must NOT use this: the girts are 1 1/2" of real wall (→ `exteriorFace`).
 */
export function layerDrawsBandSolid(layer: Pick<Layer, "function" | "is_cavity" | "framed">) {
  if (layer.is_cavity) return false;
  return !(layer.framed && layer.function.trim().toLowerCase() === "furring");
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
  // The body files under the wall's PRIMARY trade (siding for an exterior wall, drywall for
  // a partition, concrete for a foundation) and every band carries its own trade set, so
  // "only insulation" keeps the foam and drops the cladding around it.
  const body = tradeGroups[primaryTrade(wallTrades(w))];
  for (const ly of w.layers) {
    const bandTrades = layerTrades(ly);
    const layerFirstChildIndex = body.children.length;
    if (ly.polygon.length < 3) continue;
    if (!layerDrawsBandSolid(ly)) continue;
    const appearance = authoredAppearance(ly.material, materials);
    // A metal panel finish is DECLARED first and guessed second. `metalPanelProfileForFinish`
    // reads the material's authored `finish` — "ribbed-panel" for the house's exposed-fastener
    // PBR, "standing-seam" for anything that says so — and only a material that declares
    // nothing falls back to `isStandingSeam`, which is a substring test on the ref and cannot
    // tell a rib from a fold. `pbr-panel-24` has no "seam" in its tag on purpose, so without
    // this branch it would render as flat grey.
    const seamProfile = metalPanelProfileFor(ly.function, ly.material, appearance?.finish);
    const seam = seamProfile !== null;
    // Masonry (brick/CMU/stone) gets coursing + recessed mortar, not a flat fill — a brick
    // veneer or CMU wythe otherwise read like painted drywall. The style (module + mortar +
    // jitter) comes from the material's authored `finish`, so CMU reads as 16"×8" grey block
    // and white brick as whitewash over grey mortar; only a material that declares nothing
    // falls back to guessing from its tag.
    // The court's mineral silicate wash on cast concrete. Declared by `Material.finish` rather
    // than guessed from the ref, for the reason `metalPanelProfileFor` above is: a substring test
    // cannot tell a coating from what it coats. Checked BEFORE the masonry branch. The washes on
    // SRW block and on the fireplace brick DO follow a module, declare `silicate-wash-block` /
    // `silicate-wash-brick`, and so go down the masonry path instead.
    const wash = !seam && isMineralWashFinish(appearance?.finish);
    const masonryStyle = !seam && !wash && isMasonry(ly.material)
      ? masonryStyleFor(ly.material, appearance?.finish) : null;
    // Wood boards get the same treatment for the same reason: the sauna's basswood T&G liner
    // and the study's walnut wainscot are boards, and a flat fill made a lined room read as
    // tan drywall. `ly.board_run` is derived by the engine from the furring behind the layer
    // (resolve/topology.py `_board_run`), so the boards land the way they are fastened.
    const plankStyle = !seam && !wash && !masonryStyle && isWoodPlank(ly.material)
      ? plankStyleFor(ly.material, appearance?.finish) : null;
    // The coil white is the DEFAULT, not the only option. A metal panel that
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
      : wash
        ? createMineralWashMaterial(mode, materialColor(ly.material, palette, materials))
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
    // a full-height solid per region — N coincident wythes z-fighting for the same face. The
    // case was the sunken garden's five-region Ishtar wall, whose arched door and window put
    // it on the swept path in the first place; that wall is one flat field since 2026-09-04,
    // so the clamp has no live subject and the rule stays because `Layer.slot` does.
    // A blind recess cuts only the layers the engine says its depth reaches.
    const layerOpenings = openings.filter((op) => !op.cut_layers || op.cut_layers.includes(ly.name));
    const smoothArchGeometry = createSmoothArchedWallLayerGeometry(w, ly.polygon, layerOpenings, center, ly);
    const geometries: (THREE.BufferGeometry | null)[] = smoothArchGeometry
      ? [smoothArchGeometry]
      : clampPiecesToBand(wallLayerPieces(w, ly.polygon, layerOpenings), ly).map((piece) => piece.topIsRaked
        ? createRakedPlanPrismGeometry(piece.polygon, piece.z0_m,
          (point) => rakedTopAt(w, point[0], point[1]), center)
        : createPlanPrismGeometry(piece.polygon, piece.z0_m, piece.z1_m, [], center));
    for (const geo of geometries) {
      if (!geo) continue;
      // The line, not the wall: the pan module belongs to the facade, and the outriggers it
      // clips to are laid out on that same line (resolve/framing/furring.py).
      if (seam) applyStandingSeamWallUv(geo, w.layout_axis ?? w.axis, center, seamProfile ?? SEAM_PROFILE);
      else if (wash) {
        // The mottle belongs to the WALL, not to the triangle: without world-scaled UVs a tall
        // court wall and a 20 SF fireplace panel would show the same cloud at two scales.
        applyMineralWashUv(geo, w.axis, center, w.z0_m);
      } else if (masonryStyle) {
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
      body.add(mesh);
      picks.push(mesh);

      // Nordic outlines, except on the cladding. `wallLayerPieces` splits a layer at every
      // opening jamb, so outlining each piece drew a full-height line down the facade at every
      // window and a full-width one at every storey break — grid lines across a finish that has
      // no joints there. The finish carries its own definition (seam module, coursing) and the
      // building's corners come from the shading, so the outermost layer goes without; the
      // layers behind it keep theirs, where the piece boundary is a real edge.
      if (mode === "nordic" && ly.function !== "cladding") {
        body.add(new THREE.LineSegments(
          new THREE.EdgesGeometry(geo, 25),
          new THREE.LineBasicMaterial({ color: palette.edge, transparent: true, opacity: 0.35 }),
        ));
      }
    }
    // Voussoirs. A masonry layer's arched openings each get a ring of radiating bricks, so the
    // head reads as an arch instead of as a curve sliced out of running bond. Built once per
    // arch, in the layer band that holds the arch's SPRINGLINE — the Ishtar wall's split
    // brick row was five layers deep, and without that rule the same ring would have been
    // built five times, once per band. The springline is where the arch is born, so its band
    // is the one whose brick the arch would actually be turned in; it decided the ring's
    // COLOUR there, which is how the rule got written. W-B-BRICK is one flat unglazed field
    // since 2026-09-04 so there is one band to pick, and the rule still governs any banded
    // wythe. The layer's own material does the rest —
    // the ring carries polar UVs into the very same tile, so `mat` is reused as it stands.
    if (masonryStyle) {
      for (const opening of layerOpenings) {
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
        body.add(mesh);
        picks.push(mesh);
        // No Nordic outline: the ring's own joints are its definition, and an edge line per
        // facet would scribble over the coursing the ring exists to show.
      }
    }
    tagTrades(body, layerFirstChildIndex, bandTrades);
  }
  const framingFirstIndex = tradeGroups.framing.children.length;
  const skinFirstIndex = body.children.length;
  buildWallSkinMembers(tradeGroups, body, w.uid, w.members, center, mode, palette, materials,
    [{ axis: w.axis, datum: w.layout_axis ?? w.axis }]);
  // A wall's studs are pickable as themselves; the wall body remains pickable through its
  // layer meshes above, so both "this wall" and "this stud" stay one click away.
  registerMemberPicks(tradeGroups.framing, framingFirstIndex, picks);
  registerMemberPicks(body, skinFirstIndex, picks);
  byUid.set(w.uid, mats);
}

/** The metal-panel profile a wall layer renders with, or null for an untextured one.
 *
 * A metal panel finish is DECLARED first and guessed second. `metalPanelProfileForFinish`
 * reads the material's authored `finish` — "ribbed-panel" for the house's exposed-fastener
 * PBR, "corrugated" for the garage's, "standing-seam" for anything that says so.
 *
 * **The DECLARED half is not gated on the layer function; the GUESS is.** A material that
 * authors `finish="corrugated"` has said what it is, and it is the same sheet whether an
 * assembly files it as cladding or as its one structural layer. `ENTRY_SCREEN_SKIRT` is the
 * second kind — a self-supporting skin whose single layer IS the element, the shape
 * `integrity.assembly_layers` forces on it — and under a blanket cladding gate it rendered
 * as a flat grey slab beside the corrugated wall it continues. The masonry and plank
 * branches in `buildWall` never carried that gate, for the same reason.
 *
 * `isStandingSeam` keeps it: a substring test on the ref cannot tell a rib from a fold, so
 * letting it fire on a structure layer would corrugate things nobody declared. Mirrors
 * `emit/gltf/palette.py::_material_finish_color` — keep the two in step.
 */
export function metalPanelProfileFor(
  layerFunction: string,
  materialRef: string,
  declaredFinish: string | null | undefined,
): MetalPanelProfile | null {
  const declared = metalPanelProfileForFinish(declaredFinish);
  if (declared !== null) return declared;
  return layerFunction === "cladding" && isStandingSeam(materialRef) ? SEAM_PROFILE : null;
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

// Every resolved prism that is not a wall, floor or roof: slabs, footings and pads, but also
// 6x6 posts, beams, guard rails, dowels, thermal breaks, connectors, sump pits, vent risers,
// fascia, gutters and flashings. Same outline-extrusion recipe as wall layers; the finish comes
// from the solid's authored assembly when it has one, else its category (→ three/solidMaterials.ts).
//
// Plank decking is the one case the category palette cannot express: an aluminium deck slab
// needs a UV-framed procedural board finish, not a flat colour, so it is resolved first.
