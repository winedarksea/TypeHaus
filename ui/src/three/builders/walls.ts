// Wall and opening builders: the layer stack of every wall, the smooth arched soffits some of
// them carry, and the door/window fills cut into them.
//
// Split out of components/Panel3D.tsx — by far the largest builder family, and the one with
// real geometry of its own (arch tessellation, the piece decomposition around openings, the
// raked top of a gable or ToRoof wall) rather than a straight extrusion of a resolved polygon.
import * as THREE from "three";
import type { LayerVisibilityGroup } from "../../model/visibility";
import { layerVisibilityGroupOf } from "../../model/visibility";
import type { MaterialSpec, Member, Opening, Wall } from "../../model/types";
import {
  authoredAppearance, materialColor, type ResolvedNordicPalette,
} from "../../nordic/palette";
import {
  applyMasonryWallUv, applyStandingSeamWallUv, createMasonryMaterial,
  createStandingSeamMaterial, isMasonry, isStandingSeam, masonryStyleFor, masonryTileSizeM,
} from "../materials";
import { buildMembers } from "../members";
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

      if (mode === "nordic") {
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
export function archSoffitSegmentCount(radiusM: number): number {
  if (!(radiusM > ARCH_SOFFIT_CHORD_TOLERANCE_M)) return ARCH_SOFFIT_MIN_SEGMENT_COUNT;
  const halfStep = Math.acos(Math.max(-1, 1 - ARCH_SOFFIT_CHORD_TOLERANCE_M / radiusM));
  return Math.min(ARCH_SOFFIT_MAX_SEGMENT_COUNT,
    Math.max(ARCH_SOFFIT_MIN_SEGMENT_COUNT, Math.ceil(Math.PI / (2 * halfStep))));
}

// One soffit sample as (offset from the arch centreline, height above the springline). The arc
// is walked by *angle*: stepping evenly in x collapses near the springlines, where a semicircle
// turns vertical, so the last step alone dropped ~40 cm on the catlin arches — the striping.
// Mirrors `_arch_soffit_sample` in the glTF emitter.
export function archSoffitSample(
  segment: number, segmentCount: number, radiusM: number,
): { offsetM: number; heightM: number } {
  const angle = Math.PI * segment / segmentCount;
  return { offsetM: -radiusM * Math.cos(angle), heightM: radiusM * Math.sin(angle) };
}

interface ArchSoffitCylinder { centerAlongM: number; springlineM: number; radiusM: number }

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
    for (const { centerAlongM, springlineM, radiusM } of soffits) {
      const dx = along - centerAlongM, dy = elevation - springlineM;
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
    const bottom = Math.max(wall.z0_m, wall.z0_m + opening.sill_m);
    if (end - start <= 1e-9 || bottom >= wall.z1_m - 1e-9) continue;
    const hole = new THREE.Path();
    const archRise = opening.arch_rise_m ?? 0;
    if (archRise <= 1e-9) {
      const top = Math.min(wall.z1_m, bottom + opening.height_m);
      hole.moveTo(start, bottom); hole.lineTo(start, top); hole.lineTo(end, top); hole.lineTo(end, bottom);
    } else {
      const radiusM = opening.width_m / 2;
      const springlineM = bottom + Math.max(0, opening.height_m - archRise);
      const segmentCount = archSoffitSegmentCount(radiusM);
      hole.moveTo(start, bottom);
      hole.lineTo(start, Math.min(wall.z1_m, springlineM));
      for (let segment = 0; segment <= segmentCount; segment++) {
        const { offsetM, heightM } = archSoffitSample(segment, segmentCount, radiusM);
        hole.lineTo(opening.center_along_m + offsetM, Math.min(wall.z1_m, springlineM + heightM));
      }
      hole.lineTo(end, bottom);
      soffits.push({ centerAlongM: opening.center_along_m, springlineM, radiusM });
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
      const radius = active.width_m / 2;
      // Angular steps here too: even-x strips leave a ~40 cm riser at each springline.
      const segmentCount = archSoffitSegmentCount(radius);
      for (let segment = 0; segment < segmentCount; segment++) {
        const segmentStart = active.center_along_m + archSoffitSample(segment, segmentCount, radius).offsetM;
        const segmentEnd = active.center_along_m + archSoffitSample(segment + 1, segmentCount, radius).offsetM;
        const clippedStart = Math.max(start, segmentStart);
        const clippedEnd = Math.min(end, segmentEnd);
        if (clippedEnd - clippedStart <= 1e-9) continue;
        const midpoint = (clippedStart + clippedEnd) / 2;
        const offset = midpoint - active.center_along_m;
        const curve = radius * radius - offset * offset;
        const soffit = springline + Math.sqrt(Math.max(0, curve));
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

export function buildOpening(parent: THREE.Group, opening: Opening, wall: Wall, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, isDoubleSwing: boolean,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>, isGlazed = false) {
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
  const frameMaterial = new THREE.MeshStandardMaterial({ color: palette.member.wood, roughness: mode === "nordic" ? 0.85 : 1, flatShading: mode === "schematic" });
  const addBox = (width: number, height: number, thickness: number, along: number, elevation: number, material: THREE.Material) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, thickness), material);
    mesh.position.copy(projectPointToScene([position[0] + direction[0] * along, position[1] + direction[1] * along], elevation, center));
    mesh.rotation.y = rotation;
    parent.add(mesh);
  };
  const midElevation = wall.z0_m + opening.sill_m + availableHeight / 2;
  addBox(frameWidth, availableHeight, depth, -opening.width_m / 2 + frameWidth / 2, midElevation, frameMaterial);
  addBox(frameWidth, availableHeight, depth, opening.width_m / 2 - frameWidth / 2, midElevation, frameMaterial);
  addBox(opening.width_m, frameWidth, depth, 0, wall.z0_m + opening.sill_m + availableHeight - frameWidth / 2, frameMaterial);
  addBox(opening.width_m, frameWidth, depth, 0, wall.z0_m + opening.sill_m + frameWidth / 2, frameMaterial);
  const panelHeight = Math.max(0.01, availableHeight - 2 * frameWidth);
  const glassMaterial = new THREE.MeshStandardMaterial({ color: 0x8fb7c9, transparent: true, opacity: 0.48,
    roughness: 0.2, metalness: 0.05, flatShading: mode === "schematic", depthWrite: false });
  if (opening.kind === "door" && isDoubleSwing) {
    // Two leaves meeting at a center mullion, matching the 2D French-door symbol.
    const mullionWidth = Math.min(frameWidth, (opening.width_m - 2 * frameWidth) / 6);
    const leafWidth = Math.max(0.01, (opening.width_m - 2 * frameWidth - mullionWidth) / 2);
    const panelElevation = wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2;
    addBox(mullionWidth, availableHeight, depth, 0, midElevation, frameMaterial);
    const leafMaterial = isGlazed ? glassMaterial : frameMaterial;
    const leafThickness = isGlazed ? 0.015 : 0.045;
    addBox(leafWidth, panelHeight, leafThickness, -mullionWidth / 2 - leafWidth / 2, panelElevation, leafMaterial);
    addBox(leafWidth, panelHeight, leafThickness, mullionWidth / 2 + leafWidth / 2, panelElevation, leafMaterial);
  } else if (opening.kind === "door") {
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, isGlazed ? 0.015 : 0.045, 0,
      wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2, isGlazed ? glassMaterial : frameMaterial);
  } else {
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, 0.015, 0,
      wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2, glassMaterial);
  }
  // Frame, leaf/mullion and glazing are one door or window: clicking any of them selects the
  // opening record, which the Inspector already knows how to edit.
  registerSelectable(parent, firstChildIndex, opening.uid, "opening", picks, byUid);
}

// Every resolved prism that is not a wall, floor or roof: slabs, footings and pads, but also
// 6x6 posts, beams, guard rails, dowels, thermal breaks, connectors, sump pits, vent risers,
// fascia, gutters and flashings. Same outline-extrusion recipe as wall layers; the finish comes
// from the solid's authored assembly when it has one, else its category (→ three/solidMaterials.ts).
//
// Plank decking is the one case the category palette cannot express: an aluminium deck slab
// needs a UV-framed procedural board finish, not a flat colour, so it is resolved first.
