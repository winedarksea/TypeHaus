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
  authoredAppearance, materialColor, type ResolvedNordicPalette,
} from "../../nordic/palette";
import {
  applyMasonryWallUv, applyStandingSeamWallUv, createMasonryMaterial,
  createStandingSeamMaterial, isMasonry, isStandingSeam, masonryStyleFor, masonryTileSizeM,
} from "../materials";
import { buildMembers, categoryColor } from "../members";
import {
  createPlanPrismGeometry, createRakedPlanPrismGeometry, projectPointToScene, type PlanCenter,
} from "../planGeometry";
import { registerMemberPicks, registerSelectable, tagLayerGroup } from "./registry";
import type { Trade } from "../../state/vocabulary";

// Arch tessellation for one continuous viewer mesh; no internal wall-piece seams are emitted.
// The segment count is derived per arch from its radius (archSoffitSegmentCount) so that a
// soffit facet never strays further than this from the true circle, whatever the arch's size.
export const ARCH_SOFFIT_CHORD_TOLERANCE_M = 0.0005;
export const ARCH_SOFFIT_MIN_SEGMENT_COUNT = 24;
export const ARCH_SOFFIT_MAX_SEGMENT_COUNT = 192;
// A vertex counts as being on the soffit circle within this distance of it. The samples are
// computed from the circle, so the only slack needed is ExtrudeGeometry's float32 storage
// (~3e-7 m at house coordinates); anything beyond was clipped away by the wall top.
const ARCH_SOFFIT_RING_TOLERANCE_M = 1e-5;
// ExtrudeGeometry gives its front/back caps normals along the sweep axis and its swept side
// walls normals in the shape plane; only the latter can belong to an arch soffit.
const ARCH_SOFFIT_SWEPT_FACE_MAX_AXIAL_NORMAL = 0.5;
// Junction resolution splits a layer ring's straight edges at every crossing wall. A vertex
// this far off the chord between its neighbours is a real corner; anything closer is padding.
export const COLLINEAR_VERTEX_TOLERANCE_M = 1e-6;

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
    const seam = ly.function === "cladding" && isStandingSeam(ly.material);
    // Masonry (brick/CMU/stone) gets coursing + recessed mortar, not a flat fill — a brick
    // veneer or CMU wythe otherwise read like painted drywall. The style (module + mortar +
    // jitter) comes from the material's authored `finish`, so CMU reads as 16"×8" grey block
    // and white brick as whitewash over grey mortar; only a material that declares nothing
    // falls back to guessing from its tag.
    const appearance = authoredAppearance(ly.material, materials);
    const masonryStyle = !seam && isMasonry(ly.material)
      ? masonryStyleFor(ly.material, appearance?.finish) : null;
    const mat = seam
      ? createStandingSeamMaterial(mode, [
        Math.hypot(w.axis[1][0] - w.axis[0][0], w.axis[1][1] - w.axis[0][1]),
        Math.max(0.1, w.z1_m - w.z0_m),
      ], 0xE8E8E2, true)
      : masonryStyle
        ? createMasonryMaterial(mode, masonryStyle,
          materialColor(ly.material, palette, materials), appearance?.color)
        : new THREE.MeshStandardMaterial({
          color: new THREE.Color(materialColor(ly.material, palette, materials)),
          roughness: mode === "nordic" ? 0.85 : 1,
          metalness: 0,
          flatShading: mode === "schematic",
        });
    mats.push(mat);
    const smoothArchGeometry = createSmoothArchedWallLayerGeometry(w, ly.polygon, openings, center);
    const geometries: (THREE.BufferGeometry | null)[] = smoothArchGeometry
      ? [smoothArchGeometry]
      : wallLayerPieces(w, ly.polygon, openings).map((piece) => piece.topIsRaked
        ? createRakedPlanPrismGeometry(piece.polygon, piece.z0_m,
          (point) => rakedTopAt(w, point[0], point[1]), center)
        : createPlanPrismGeometry(piece.polygon, piece.z0_m, piece.z1_m, [], center));
    for (const geo of geometries) {
      if (!geo) continue;
      if (seam) applyStandingSeamWallUv(geo, w.axis, center);
      else if (masonryStyle) applyMasonryWallUv(geo, w.axis, center, masonryTileSizeM(masonryStyle));
      const mesh = new THREE.Mesh(geo, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
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
    tagLayerGroup(tradeGroups.walls, layerFirstChildIndex, layerGroup);
  }
  const framingFirstIndex = tradeGroups.framing.children.length;
  buildWallSkinMembers(tradeGroups.framing, w.uid, w.members, center, mode, palette);
  // A wall's studs are pickable as themselves; the wall body remains pickable through its
  // layer meshes above, so both "this wall" and "this stud" stay one click away.
  registerMemberPicks(tradeGroups.framing, framingFirstIndex, picks);
  byUid.set(w.uid, mats);
}

// Wall members split two ways for visibility: plain lumber answers to the Framing trade, while
// a member that names a material is a derived skin band (a gable closure, a trim run) and must
// answer to the assembly-layer control that governs the layer it continues. The split has to
// happen before the merge, since a merged mesh has one visibility flag for all of it.
function buildWallSkinMembers(
  parent: THREE.Group, wallUid: string, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
) {
  const lumber = members.filter((member) => !member.material);
  buildMembers(parent, lumber, center, mode, palette, wallUid);
  const skinByGroup = new Map<LayerVisibilityGroup, Member[]>();
  for (const member of members) {
    if (!member.material) continue;
    const group = layerVisibilityGroupOf(member.category);
    skinByGroup.set(group, [...(skinByGroup.get(group) ?? []), member]);
  }
  for (const [group, skin] of skinByGroup) {
    const firstChildIndex = parent.children.length;
    buildMembers(parent, skin, center, mode, palette, wallUid);
    tagLayerGroup(parent, firstChildIndex, group);
  }
}

export interface WallLayerPiece {
  polygon: [number, number][];
  z0_m: number;
  z1_m: number;
  topIsRaked: boolean;
}

// Drop vertices that sit on the straight line between their neighbours. Junction resolution
// splits a wall layer's long edges at every crossing wall, so an authored rectangle serializes
// as five, six or eight points (the 16" sunken-garden arch wall arrives as six). Anything that
// needs to *recognise* a rectangle has to reduce first. Mirrors `_without_collinear_vertices`
// in packages/engine/src/typehaus/emit/gltf/emitter.py — keep the two in step.
export function withoutCollinearVertices(
  polygon: readonly (readonly [number, number])[],
  toleranceM: number = COLLINEAR_VERTEX_TOLERANCE_M,
): [number, number][] {
  const ring: [number, number][] = [];
  for (const [x, y] of polygon) {
    const last = ring[ring.length - 1];
    if (!last || Math.hypot(x - last[0], y - last[1]) > toleranceM) ring.push([x, y]);
  }
  while (ring.length > 1 && Math.hypot(ring[0][0] - ring[ring.length - 1][0],
    ring[0][1] - ring[ring.length - 1][1]) <= toleranceM) ring.pop();
  if (ring.length < 3) return ring;
  const corners: [number, number][] = [];
  for (let index = 0; index < ring.length; index++) {
    const [px, py] = ring[(index - 1 + ring.length) % ring.length];
    const [cx, cy] = ring[index];
    const [nextX, nextY] = ring[(index + 1) % ring.length];
    const spanX = nextX - px, spanY = nextY - py;
    const span = Math.hypot(spanX, spanY);
    // Perpendicular distance, in metres, of this vertex from the chord between its neighbours.
    const offset = span < toleranceM
      ? Math.hypot(cx - px, cy - py)
      : Math.abs((cx - px) * spanY - (cy - py) * spanX) / span;
    if (offset > toleranceM) corners.push([cx, cy]);
  }
  return corners;
}

// Segments for a half-circle soffit sampled at even angular steps. One step's mid-chord sagitta
// is r·(1 − cos(π/2n)), so inverting it ties tessellation to the arch's actual size instead of a
// flat guess: an 8'-wide garden arch and a small niche head come out equally smooth. Mirrors
// `_arch_soffit_segment_count` in the glTF emitter.
export function archSoffitSegmentCount(radiusM: number, halfAngleRad = Math.PI / 2): number {
  if (!(radiusM > ARCH_SOFFIT_CHORD_TOLERANCE_M)) return ARCH_SOFFIT_MIN_SEGMENT_COUNT;
  const halfStep = Math.acos(Math.max(-1, 1 - ARCH_SOFFIT_CHORD_TOLERANCE_M / radiusM));
  return Math.min(ARCH_SOFFIT_MAX_SEGMENT_COUNT,
    Math.max(ARCH_SOFFIT_MIN_SEGMENT_COUNT, Math.ceil(halfAngleRad / halfStep)));
}

// The circle through both springlines and the crown of an arch of half-span `halfSpanM` rising
// `riseM` above them: [radius, half-angle, how far the centre sits below the springline].
//
// This is what makes a *segmental* arch possible. The soffit used to be hard-wired to a
// half-circle of width/2, so `arch_rise_m` only chose where the springline sat and every head
// came out semicircular however shallow the rise said it was. A rise at or above the half-span
// is the semicircle and is clamped to it. Mirrors `arch_soffit_circle` in the engine
// (resolve/geometry_prims.py) — keep the two in step.
export function archSoffitCircle(
  halfSpanM: number, riseM: number,
): { radiusM: number; halfAngleRad: number; depthM: number } {
  const span = Math.max(halfSpanM, 1e-9);
  const rise = Math.min(Math.max(riseM, 1e-9), span);
  const radiusM = (span * span + rise * rise) / (2 * rise);
  return {
    radiusM,
    halfAngleRad: Math.asin(Math.max(-1, Math.min(1, span / radiusM))),
    depthM: radiusM - rise,
  };
}

// One soffit sample as (offset from the arch centreline, height above the springline). The arc
// is walked by *angle*: stepping evenly in x collapses near the springlines, where a semicircle
// turns vertical, so the last step alone dropped ~40 cm on the catlin arches — the striping.
// Mirrors `_arch_soffit_sample` in the glTF emitter.
// Sweeping −halfAngle..+halfAngle and subtracting the circle's depth below the springline
// generalises this to a segmental arch; at the default π/2 the depth is zero and this is the
// same half-circle it always was, merely parameterised from the centre out.
export function archSoffitSample(
  segment: number, segmentCount: number, radiusM: number, halfAngleRad = Math.PI / 2,
): { offsetM: number; heightM: number } {
  const angle = -halfAngleRad + 2 * halfAngleRad * segment / segmentCount;
  return {
    offsetM: radiusM * Math.sin(angle),
    heightM: radiusM * Math.cos(angle) - radiusM * Math.cos(halfAngleRad),
  };
}

// `circleCenterM` is the soffit circle's centre elevation — the springline for a semicircle,
// and `depthM` below it for a segmental arch.
interface ArchSoffitCylinder { centerAlongM: number; circleCenterM: number; radiusM: number }

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

// A concrete arch should read as one continuous cast surface. Extruding a Shape with opening
// holes gives the soffit a single smooth mesh; the strip fallback below is retained for raked
// and junction-mitered wall layers whose non-rectangular plan footprint cannot be swept safely.
export function createSmoothArchedWallLayerGeometry(
  wall: Wall, polygon: readonly [number, number][], openings: Opening[], center: PlanCenter,
): THREE.BufferGeometry | null {
  if (!openings.some((opening) => (opening.arch_rise_m ?? 0) > 1e-9) ||
      wall.top_z0_m != null || wall.top_z1_m != null) return null;
  const [[sx, sy], [ex, ey]] = wall.axis;
  const length = Math.hypot(ex - sx, ey - sy);
  if (length < 1e-9) return null;
  const ux = (ex - sx) / length, uy = (ey - sy) / length;
  const nx = -uy, ny = ux;
  // A padded ring is still a rectangle; only its *corners* decide whether it can be swept.
  const footprint = withoutCollinearVertices(polygon);
  if (footprint.length !== 4) return null;
  const local = footprint.map(([x, y]) => [
    (x - sx) * ux + (y - sy) * uy,
    (x - sx) * nx + (y - sy) * ny,
  ] as const);
  const alongs = local.map(([along]) => along), acrosses = local.map(([, across]) => across);
  const minAlong = Math.min(...alongs), maxAlong = Math.max(...alongs);
  const minAcross = Math.min(...acrosses), maxAcross = Math.max(...acrosses);
  const corners = new Set(local.map(([along, across]) => `${along.toFixed(8)},${across.toFixed(8)}`));
  if (corners.size !== 4 || ![
    [minAlong, minAcross], [minAlong, maxAcross], [maxAlong, minAcross], [maxAlong, maxAcross],
  ].every(([along, across]) => corners.has(`${along.toFixed(8)},${across.toFixed(8)}`))) return null;

  const shape = new THREE.Shape();
  shape.moveTo(minAlong, wall.z0_m);
  shape.lineTo(maxAlong, wall.z0_m);
  shape.lineTo(maxAlong, wall.z1_m);
  shape.lineTo(minAlong, wall.z1_m);
  shape.closePath();
  const soffits: ArchSoffitCylinder[] = [];
  for (const opening of openings) {
    const start = Math.max(minAlong, opening.center_along_m - opening.width_m / 2);
    const end = Math.min(maxAlong, opening.center_along_m + opening.width_m / 2);
    // The threshold is where the opening's height is measured *from*, and it can sit below
    // the wall that hosts it — the garage overhead door lands on the slab, one stem reveal
    // under W-G-E's base. Only the cut is clamped to the wall body; measuring the head off
    // the clamped value instead would make the hole as much too tall as the sill is
    // negative, and disagree with the wall solids (resolve/geometry_walls.py, and
    // wallLayerPieces below, which both measure from the threshold).
    const threshold = wall.z0_m + opening.sill_m;
    const bottom = Math.max(wall.z0_m, threshold);
    if (end - start <= 1e-9 || bottom >= wall.z1_m - 1e-9) continue;
    const hole = new THREE.Path();
    const archRise = opening.arch_rise_m ?? 0;
    if (archRise <= 1e-9) {
      const top = Math.min(wall.z1_m, threshold + opening.height_m);
      hole.moveTo(start, bottom); hole.lineTo(start, top); hole.lineTo(end, top); hole.lineTo(end, bottom);
    } else {
      const { radiusM, halfAngleRad, depthM } = archSoffitCircle(opening.width_m / 2, archRise);
      const springlineM = threshold + Math.max(0, opening.height_m - archRise);
      const segmentCount = archSoffitSegmentCount(radiusM, halfAngleRad);
      hole.moveTo(start, bottom);
      hole.lineTo(start, Math.min(wall.z1_m, springlineM));
      for (let segment = 0; segment <= segmentCount; segment++) {
        const { offsetM, heightM } = archSoffitSample(segment, segmentCount, radiusM, halfAngleRad);
        hole.lineTo(opening.center_along_m + offsetM, Math.min(wall.z1_m, springlineM + heightM));
      }
      hole.lineTo(end, bottom);
      soffits.push({
        centerAlongM: opening.center_along_m, circleCenterM: springlineM - depthM, radiusM,
      });
    }
    hole.closePath();
    shape.holes.push(hole);
  }
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: maxAcross - minAcross, bevelEnabled: false, curveSegments: 1,
  });
  applySmoothArchSoffitNormals(geometry, soffits);
  // Extrude from the maximum-across face toward the minimum-across face. This keeps
  // the local-to-scene matrix right-handed while mapping project north to scene -Z.
  geometry.applyMatrix4(new THREE.Matrix4().set(
    ux, 0, -nx, sx + nx * maxAcross - center[0],
    0, 1, 0, 0,
    -uy, 0, ny, center[1] - sy - ny * maxAcross,
    0, 0, 0, 1,
  ));
  return geometry;
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
    const openingBottom = wall.z0_m + active.sill_m;
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
// 1 1/4" face: the visible width of standard J-channel/flat trim. Was 0.064 (2 1/2")
// until 2026-07-30 — too heavy in 3D, since casing and window frame are both charcoal
// here and read as one band.
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
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m - opening.width_m / 2), y0 + direction[1] * (opening.center_along_m - opening.width_m / 2)) - wall.z0_m - opening.sill_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m + opening.width_m / 2), y0 + direction[1] * (opening.center_along_m + opening.width_m / 2)) - wall.z0_m - opening.sill_m));
  if (availableHeight <= 1e-9) return;
  const rotation = Math.atan2(direction[1], direction[0]);
  const frameWidth = Math.min(0.075, opening.width_m / 4, availableHeight / 4);
  const depth = 0.08;
  // An opening in a clad wall is an exterior product: frame/mullion/stile boxes take the
  // charcoal exterior tone, doors and windows alike, and the frame extends from its
  // interior face out to the casing's proud face so the reveal reads charcoal instead of
  // exposing the wall layers' cut foam. Mirrors resolve/geometry_openings.py.
  const exterior = exteriorFace(wall);
  const frameMaterial = new THREE.MeshStandardMaterial({
    color: exterior ? categoryColor("window_trim") : palette.member.wood,
    roughness: mode === "nordic" ? 0.85 : 1, flatShading: mode === "schematic" });
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
  const midElevation = wall.z0_m + opening.sill_m + availableHeight / 2;
  if (!isTrimless) {
    // A trimless door (drywall return jamb, no applied casing) draws no frame boxes; the
    // leaf keeps its framed size so the reveal reads the same. Mirrors emit/gltf/openings.py.
    addBox(frameWidth, availableHeight, frameDepth, -opening.width_m / 2 + frameWidth / 2, midElevation, frameMaterial, frameOffset);
    addBox(frameWidth, availableHeight, frameDepth, opening.width_m / 2 - frameWidth / 2, midElevation, frameMaterial, frameOffset);
    addBox(opening.width_m, frameWidth, frameDepth, 0, wall.z0_m + opening.sill_m + availableHeight - frameWidth / 2, frameMaterial, frameOffset);
    addBox(opening.width_m, frameWidth, frameDepth, 0, wall.z0_m + opening.sill_m + frameWidth / 2, frameMaterial, frameOffset);
  }
  const panelHeight = Math.max(0.01, availableHeight - 2 * frameWidth);
  const glassMaterial = new THREE.MeshStandardMaterial({ color: 0x8fb7c9, transparent: true, opacity: 0.48,
    roughness: 0.2, metalness: 0.05, flatShading: mode === "schematic", depthWrite: false });
  if (opening.kind === "door" && operation === "double_swing") {
    // Two leaves meeting at a center mullion, matching the 2D French-door symbol.
    const mullionWidth = Math.min(frameWidth, (opening.width_m - 2 * frameWidth) / 6);
    const leafWidth = Math.max(0.01, (opening.width_m - 2 * frameWidth - mullionWidth) / 2);
    const panelElevation = wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2;
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
    const panelElevation = wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2;
    const panelMaterial = isGlazed ? glassMaterial : frameMaterial;
    const panelThickness = isGlazed ? 0.015 : 0.045;
    addBox(stileWidth, panelHeight, depth, 0, panelElevation, frameMaterial);
    addBox(clearWidth, trackHeight, depth, 0,
      wall.z0_m + opening.sill_m + frameWidth + trackHeight / 2, frameMaterial);
    addBox(panelWidth, panelHeight, panelThickness, -panelOffset, panelElevation, panelMaterial);
    addBox(panelWidth, panelHeight, panelThickness, panelOffset, panelElevation, panelMaterial);
  } else if (opening.kind === "door" && operation === "bifold") {
    // Four leaves are a centre-opening bifold's closed product arrangement. Small reveals
    // keep the fold joints legible while the leaves remain in the wall plane.
    const clearWidth = opening.width_m - 2 * frameWidth;
    const foldGap = Math.min(frameWidth / 8, clearWidth / 40);
    const leafWidth = Math.max(0.01, (clearWidth - 3 * foldGap) / 4);
    const firstLeafCenter = -clearWidth / 2 + leafWidth / 2;
    const panelElevation = wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2;
    for (let index = 0; index < 4; index++) {
      addBox(leafWidth, panelHeight, 0.045,
        firstLeafCenter + index * (leafWidth + foldGap), panelElevation, frameMaterial);
    }
  } else if (opening.kind === "door") {
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, isGlazed ? 0.015 : 0.045, 0,
      wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2, isGlazed ? glassMaterial : frameMaterial);
  } else {
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, 0.015, 0,
      wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2, glassMaterial);
  }
  if (opening.kind === "window") {
    if (exterior) {
      // Picture-frame casing on the cladding plane: two jambs beside the RO, a head band
      // over it, an apron under the sill. Mirrors resolve/geometry_openings.py, including
      // the per-board rake clip — a head band reaches past the RO span the availableHeight
      // clip already honoured, so each board checks the raked top over its own footprint.
      const trimW = WINDOW_TRIM_FACE_WIDTH_M;
      const trimOffset = exterior.plane + exterior.sign * (WINDOW_TRIM_PROUD_DEPTH_M / 2);
      const trimMaterial = new THREE.MeshStandardMaterial({ color: categoryColor("window_trim"),
        roughness: 0.9, flatShading: mode === "schematic" });
      const rakedHost = wall.top_z0_m != null || wall.top_z1_m != null;
      const sillZ = wall.z0_m + opening.sill_m;
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
