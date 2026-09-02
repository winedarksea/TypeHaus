// Builders for the resolver's *derived* geometry: concrete solids, a footing's gravel bedding,
// framed floors, roofs and stairs.
//
// Split out of components/Panel3D.tsx. What these five share is that none of them is authored
// — each is geometry the resolver computed from something else — so all of them extrude a
// resolved outline or lay out a member list, and none carries an editing path.
import * as THREE from "three";
import type {
  Brace, Catalog, FootingBedding, Floor, LightRun, Member, Paneling, Roof, Room, Solid,
  SoffitFraming, SolarPanel, Stair, Vec2,
} from "../../model/types";
import { layerVisibilityGroupOf, type LayerVisibilityGroup } from "../../model/visibility";
import {
  authoredAppearance, finishBaseColor, floorSurface, materialColor, type MaterialAppearance,
  type ResolvedNordicPalette,
} from "../../nordic/palette";
import {
  applyDeckBoardUv, createDeckBoardMaterial, createStandingSeamMaterial,
  isAluminumDeckBoard, isStandingSeam, metalPanelProfileForFinish, SEAM_PROFILE,
} from "../materials";
import { buildMembers, isRoofFramingMember, memberColor, type SkinLine } from "../members";
import {
  applyPlankPlaneUv, applyPlankWallUv, createPlankMaterial, isWoodPlank, planLongAxis,
  plankStyleFor, plankTileSizeM,
} from "../plankMaterial";
import {
  createPlanPrismGeometry, createProjectedSurfaceGeometry, rectBetween, type PlanCenter,
  type ProjectVertex,
} from "../planGeometry";
import {
  aboveStructureLayers, applyStandingSeamRoofUv, boundaryEdges, layerInsetRect, roofOffsetter,
  roofPlaneTriangles,
} from "../roofGeometry";
import { createSolidMaterial } from "../solidMaterials";
import { createSweepGeometry } from "../tubeGeometry";
import { makeSurfaceMesh, NORDIC_ROUGHNESS, standardMaterial } from "../surfaces";
import type { SelectionKind } from "../../state/vocabulary";
import { registerSelectable, tagLayerGroup } from "./registry";

// A resolved solid: a plan prism, or — when it carries a `sweep` — the mitred tube of a run.
//
// Still ONE mesh and ONE registerSelectable either way, which is the whole point: a handrail
// that used to arrive as 292 separate solids (and 292 pick targets, and 292 Inspector rows)
// is one click, one highlight, one name. Picking, highlighting, SolidInspector and
// solidCategoryLabel are untouched below the fork.
export function buildSolid(parent: THREE.Group, solid: Solid, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, catalog: Catalog | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>,
  materials?: readonly MaterialAppearance[]) {
  const geo = solid.sweep
    ? createSweepGeometry(solid, center)
    : (solid.outline.length < 3 ? null
      : createPlanPrismGeometry(solid.outline, solid.z0_m,
        Math.max(solid.z1_m, solid.z0_m + 0.01), solid.voids ?? [], center));
  if (!geo) return;
  const deckBoards = catalog?.assemblies.find((a) => a.tag === solid.assembly)?.layers
    .some((layer) => isAluminumDeckBoard(layer.material));
  if (deckBoards) applyDeckBoardUv(geo, center);
  // A boarded ceiling: `resolve/ceilings.py` puts the ceiling stack's FINISH layer material
  // straight on the solid, so the sauna's shiplap arrives here as `material: "sauna-shiplap"` with no
  // assembly to walk. Boards run along the room's long axis — a ceiling's furring is
  // authored "horizontal", which says nothing about which horizontal.
  const plankStyle = !deckBoards && isWoodPlank(solid.material)
    ? plankStyleFor(solid.material, authoredAppearance(solid.material, materials)?.finish)
    : null;
  if (plankStyle && !solid.sweep) {
    applyPlankPlaneUv(geo, center, planLongAxis(solid.outline), plankTileSizeM(plankStyle));
  }
  const firstChildIndex = parent.children.length;
  const mesh = makeSurfaceMesh(geo,
    deckBoards ? createDeckBoardMaterial(mode)
      : plankStyle
        ? createPlankMaterial(mode, plankStyle,
          materialColor(solid.material, palette, materials))
        : createSolidMaterial(solid, catalog, mode, palette));
  parent.add(mesh);
  registerSelectable(parent, firstChildIndex, solid.uid, "solid", picks, byUid);
}

// PV module glass — mirrors "solar" in emit/gltf/palette.py `_PALETTE`.
export const SOLAR_PANEL_COLOR = 0x1a2447;

// A rooftop PV module: the resolver's tilted box (two matching corner rings in metres),
// turned into 12 triangles directly — no plan-prism helper can express a sloped plate.
export function buildSolarPanel(parent: THREE.Group, panel: SolarPanel, center: PlanCenter,
  mode: "nordic" | "schematic", picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (panel.corners_bottom.length !== 4 || panel.corners_top.length !== 4) return;
  const scene = (point: number[]) =>
    [point[0] - center[0], point[2], -(point[1] - center[1])] as const;
  const bottom = panel.corners_bottom.map(scene);
  const top = panel.corners_top.map(scene);
  const positions: number[] = [];
  const push = (...points: (readonly [number, number, number])[]) => {
    for (const point of points) positions.push(point[0], point[1], point[2]);
  };
  push(bottom[2], bottom[1], bottom[0], bottom[3], bottom[2], bottom[0]);
  push(top[0], top[1], top[2], top[0], top[2], top[3]);
  for (let index = 0; index < 4; index++) {
    const next = (index + 1) % 4;
    push(bottom[index], bottom[next], top[next], bottom[index], top[next], top[index]);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.computeVertexNormals();
  const firstChildIndex = parent.children.length;
  const mat = standardMaterial(SOLAR_PANEL_COLOR, mode, {
    roughness: mode === "nordic" ? 0.25 : 0.6, // glassy face under the nordic sun
    metalness: mode === "nordic" ? 0.4 : 0.1,
    flatShading: false, // a module is a single flat plate; faceting it adds nothing in schematic
  });
  parent.add(makeSurfaceMesh(geo, mat));
  registerSelectable(parent, firstChildIndex, panel.uid, "solid", picks, byUid);
}

// LightRun's channel + tape — mirrors emit/gltf/palette.py `_PALETTE["cove_channel"]` /
// `["led_tape"]`, and the same distinction the Inspector draws for a solid category (a
// channel is what you'd order, tape is what lights).
export const COVE_CHANNEL_COLOR = 0xcccccc; // mill-finish aluminium extrusion
export const LED_TAPE_COLOR = 0xffeabb;     // warm-white tape, bright rather than lit

// The run's outer envelope (→ resolve/geometry.py LIGHT_STRIP_WIDTH_M/HEIGHT_M) — half an
// inch square, in metres.
const LIGHT_STRIP_WIDTH_M = 0.0127;
const LIGHT_STRIP_HEIGHT_M = 0.0127;
const CHANNEL_WALL_M = 0.0048; // 3/16" (→ resolve/trim_bands.py CHANNEL_WALL_M)
const TAPE_HEIGHT_M = 0.0023; // (→ resolve/trim_bands.py TAPE_HEIGHT_M)

// (key, offset from the back, band width, bottom drop, top drop) — one band tuple per row,
// same shape and same numbers as resolve/trim_bands.py `led_cove_bands`. Kept beside the
// colours above rather than imported: this is a small, fixed cross-section recipe, and the
// two sides of the mirror already have to move together (comment cross-reference does the
// rest, the way emit/gltf/palette.py and this file's colour constants already do).
function ledCoveBands(thicknessM: number, depthM: number):
  [key: "back" | "base" | "lip" | "tape", left: number, right: number,
   bottomDrop: number, topDrop: number][] {
  const wall = Math.min(CHANNEL_WALL_M, thicknessM / 3, depthM / 3);
  const lipDepth = depthM * 0.4;
  const tapeH = Math.min(TAPE_HEIGHT_M, depthM - wall);
  const half = thicknessM / 2;
  const span = (offset: number, width: number): [number, number] =>
    [-half + offset, -half + offset + width];
  return [
    ["back", ...span(0, wall), depthM, 0],
    ["base", ...span(wall, thicknessM - 2 * wall), depthM, depthM - wall],
    ["lip", ...span(thicknessM - wall, wall), lipDepth, 0],
    ["tape", ...span(wall, thicknessM - 2 * wall), depthM - wall, depthM - wall - tapeH],
  ];
}

// A cove/shadow-gap LED run: the resolver's plan polyline swept into a channel (back, base,
// lip) with the tape laid in the trough — not one undifferentiated bar. One pick target for
// the whole run, matching the single IfcLightFixture the IFC exporter emits for it.
export function buildLightRun(parent: THREE.Group, run: LightRun, center: PlanCenter,
  mode: "nordic" | "schematic", picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (run.path.length < 2) return;
  const firstChildIndex = parent.children.length;
  for (const [key, left, right, bottomDrop, topDrop] of
    ledCoveBands(LIGHT_STRIP_WIDTH_M, LIGHT_STRIP_HEIGHT_M)) {
    const color = key === "tape" ? LED_TAPE_COLOR : COVE_CHANNEL_COLOR;
    const z0 = run.z_m - bottomDrop;
    const z1 = run.z_m - topDrop;
    for (let index = 0; index < run.path.length - 1; index++) {
      const p0 = run.path[index];
      const p1 = run.path[index + 1];
      if (Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 1e-6) continue;
      const outline = rectBetween(p0, p1, left, right);
      const geo = createPlanPrismGeometry(outline, z0, z1, [], center);
      if (!geo) continue;
      parent.add(makeSurfaceMesh(geo, standardMaterial(color, mode, {
        roughness: key === "tape" ? 0.4 : 0.5, metalness: key === "tape" ? 0 : 0.6,
        flatShading: false, // half-inch extrusion: its facets are below a pixel either way
      })));
    }
  }
  registerSelectable(parent, firstChildIndex, run.uid, "solid", picks, byUid);
}

// Compacted washed-stone footing bed: a below-grade gravel prism under a strip footing.
// Rendered granular (flat-shaded, high roughness) so it reads as aggregate, not concrete.
export const FOOTING_BEDDING_COLOR = 0x8b8478;

export function buildFootingBedding(parent: THREE.Group, bedding: FootingBedding, center: PlanCenter,
  mode: "nordic" | "schematic", picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (bedding.outline.length < 3 || bedding.z1_m <= bedding.z0_m) return;
  const geo = createPlanPrismGeometry(bedding.outline, bedding.z0_m, bedding.z1_m, [], center);
  if (!geo) return;
  const firstChildIndex = parent.children.length;
  const mat = standardMaterial(FOOTING_BEDDING_COLOR, mode, {
    roughness: 1,
    flatShading: true, // faceted normals read as loose aggregate in both shading modes
  });
  parent.add(makeSurfaceMesh(geo, mat));
  if (mode === "nordic") {
    parent.add(new THREE.LineSegments(
      new THREE.EdgesGeometry(geo, 20),
      new THREE.LineBasicMaterial({ color: 0x5c574d, transparent: true, opacity: 0.4 }),
    ));
  }
  registerSelectable(parent, firstChildIndex, bedding.uid, "footing_bedding", picks, byUid);
}

export function buildFloor(parent: THREE.Group, floor: Floor, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>, framingGroup: THREE.Group,
  materials?: readonly MaterialAppearance[]) {
  const firstChildIndex = parent.children.length;
  if (floor.subfloor && floor.members.length) {
    const points = floor.members.flatMap((member) => [member.p0, member.p1]);
    const minX = Math.min(...points.map((point) => point[0]));
    const maxX = Math.max(...points.map((point) => point[0]));
    const minY = Math.min(...points.map((point) => point[1]));
    const maxY = Math.max(...points.map((point) => point[1]));
    const z = Math.max(...floor.members.map((member) => member.z1_m));
    const geometry = createPlanPrismGeometry(
      [[minX, minY], [maxX, minY], [maxX, maxY], [minX, maxY]],
      z,
      z + floor.subfloor.thickness_m,
      floor.openings,
      center,
    );
    if (!geometry) return;
    parent.add(new THREE.Mesh(geometry,
      standardMaterial(new THREE.Color(materialColor(floor.subfloor.material, palette)), mode)));
  }
  registerSelectable(parent, firstChildIndex, floor.uid, "floor", picks, byUid);
  // Joists are framing, and belong under the framing toggle with every other stick in the
  // building — not hidden behind the floors toggle. Same split roof/wall framing use.
  const framingFirstChildIndex = framingGroup.children.length;
  buildMembers(framingGroup, floor.members, center, mode, palette, floor.uid, materials);
  registerSelectable(framingGroup, framingFirstChildIndex, floor.uid, "floor", picks, byUid);
}

/** How thick a floor finish draws. Matches the room prism emit/gltf/emitter.py extrudes. */
export const ROOM_FINISH_THICKNESS_M = 0.02;

/**
 * The top of the deck a storey's rooms sit on: the subfloor's upper face where the storey has
 * a framed floor, else the storey elevation (a slab-on-grade storey — basement, garage — has
 * no `Floor` at all). Returning the storey elevation rather than 0 is what keeps an upper
 * storey's finishes off the ground plane.
 */
export function storeyFloorTopM(floors: readonly Floor[], storeyTag: string,
  storeyElevationM: number): number {
  let top = storeyElevationM;
  for (const floor of floors) {
    if (floor.storey !== storeyTag || !floor.subfloor || !floor.members.length) continue;
    const deck = Math.max(...floor.members.map((member) => member.z1_m))
      + floor.subfloor.thickness_m;
    top = Math.max(top, deck);
  }
  return top;
}

/**
 * A room's floor finish — carpet, oak, LVP, tile — as a thin slab over the deck.
 *
 * `Room.floor_finish` has been resolved and exported since M1, but nothing ever drew it:
 * `buildFloor` above renders `floor.subfloor` and stops, so every room read as bare deck no
 * matter what was authored. Colour comes from the catalog material whose tag *is* the finish
 * string, so the library is the single definition the viewer, the .glb and the takeoff all
 * key off; the surface (roughness) comes from `floorSurface`, because four flat fills of
 * similar value are hard to tell apart under one light and the sheen is what separates them.
 *
 * Openings in the storey's deck are cut out of the finish too — otherwise the finish caps
 * the stair well the subfloor correctly leaves open.
 *
 * `Room.finish_zones` are cut out the same way, and for the same reason. A zone is an *override*
 * — a hearth pad, or the band of a room sitting on a slab whose cap is itself the finished floor
 * — so the field finish stops at its edge rather than running under it. Cutting rather than
 * covering is what makes a COATING zone right: polished concrete has no plane of its own, so the
 * hole alone is the drawing, and the slab solid below shows through it, which is the real
 * condition. A covering zone draws its own slab in the hole.
 */
export function buildRoomFloor(parent: THREE.Group, room: Room, floorTopM: number,
  openings: readonly Vec2[][], center: PlanCenter, mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette, materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (room.clear_face.length < 3) return;
  const zones = (room.finish_zones ?? []).filter((zone) => zone.outline.length >= 3);
  const holes = zones.length ? [...openings, ...zones.map((zone) => zone.outline)] : openings;
  // A coating (sealed concrete) is a sealer on the deck, not a covering over it: it has no
  // thickness of its own, so drawing a plane for it would put a second floor a hair above
  // the slab that already carries the colour. It still bills — takeoff/finishes.py.
  if (room.floor_finish && !authoredAppearance(room.floor_finish, materials)?.coating) {
    addFinishPlane(parent, room, room.floor_finish, room.clear_face, holes, floorTopM,
      center, mode, palette, materials, picks, byUid);
  }
  for (const zone of zones) {
    if (authoredAppearance(zone.material_ref, materials)?.coating) continue;
    addFinishPlane(parent, room, zone.material_ref, zone.outline, openings, floorTopM,
      center, mode, palette, materials, picks, byUid);
  }
}

/** One finish plane — the room's field, or one of its zones — over the deck at `floorTopM`. */
function addFinishPlane(parent: THREE.Group, room: Room, finish: string,
  outline: readonly Vec2[], holes: readonly (readonly Vec2[])[], floorTopM: number,
  center: PlanCenter, mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const geometry = createPlanPrismGeometry(
    outline, floorTopM, floorTopM + ROOM_FINISH_THICKNESS_M, holes, center);
  if (!geometry) return;
  const firstChildIndex = parent.children.length;
  const surface = floorSurface(finish);
  // A plank floor is boards, not a sheet. Oak strip and (later) LVP take the board treatment;
  // carpet, tile and sheet vinyl stay a flat fill, which is what they are. The boards run
  // along the room's long axis — a floor is laid the long way.
  const plankStyle = isWoodPlank(finish)
    ? plankStyleFor(finish, authoredAppearance(finish, materials)?.finish) : null;
  if (plankStyle) {
    applyPlankPlaneUv(geometry, center, planLongAxis(outline), plankTileSizeM(plankStyle));
  }
  const mesh = new THREE.Mesh(geometry,
    plankStyle
      ? createPlankMaterial(mode, plankStyle,
        materialColor(finish, palette, materials), mode === "nordic" ? surface.roughness : 1)
      : standardMaterial(new THREE.Color(materialColor(finish, palette, materials)), mode, {
        roughness: mode === "nordic" ? surface.roughness : 1,
        metalness: mode === "nordic" ? surface.metalness : 0,
      }));
  // Receives but does not cast: a 20 mm finish laid on the deck has nothing to cast onto.
  mesh.receiveShadow = true;
  parent.add(mesh);
  // A zone belongs to its room: clicking the band selects RM-M-LIVING, not a nameless plane.
  registerSelectable(parent, firstChildIndex, room.uid, "room", picks, byUid);
}

/**
 * A `WallPaneling` band — the study's walnut wainscot, the sauna shower's tile splash — as a
 * thin prism on the room side of its wall.
 *
 * It resolved to quantities and nothing else until 2026-08-25: `resolve/paneling.py` computed
 * the wall, the run and the band height, billed the area and threw the geometry away, so a
 * wainscot appeared on the order and nowhere in the model. That is also why the sauna liner
 * needed this: `WP-B-SAUNA-SPLASH` REPLACES the wall finish over two 3' stretches, so without
 * a band drawn over them the basswood T&G would run straight through a tiled shower wall.
 *
 * Selecting one resolves to the paneling element itself, not to the wall it sits on — a click
 * on the walnut should say `WP-M-STUDY-WAINSCOT`.
 */
export function buildPaneling(parent: THREE.Group, band: Paneling, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  // A band with no derivable side resolves area-only (see resolve/paneling.py). Nothing to
  // draw is the honest outcome, not a degenerate prism at the wall's centreline.
  if (band.outline.length < 3 || band.z0_m === null || band.z1_m === null) return;
  const geometry = createPlanPrismGeometry(band.outline, band.z0_m, band.z1_m, [], center);
  if (!geometry) return;
  const plankStyle = isWoodPlank(band.material_ref)
    ? plankStyleFor(band.material_ref, authoredAppearance(band.material_ref, materials)?.finish)
    : null;
  if (plankStyle) {
    // A wainscot's boards stand vertical unless its wall says otherwise. The band is applied
    // OVER a finished wall rather than fastened to furring, so there is no furring layer for
    // `board_run` to derive from — and vertical is what a board wainscot is.
    applyPlankWallUv(geometry, bandAxis(band.outline), center,
      plankTileSizeM(plankStyle), band.z0_m, "vertical");
  }
  const firstChildIndex = parent.children.length;
  const mesh = makeSurfaceMesh(geometry,
    plankStyle
      ? createPlankMaterial(mode, plankStyle,
        materialColor(band.material_ref, palette, materials))
      : standardMaterial(
        new THREE.Color(materialColor(band.material_ref, palette, materials)), mode));
  parent.add(mesh);
  registerSelectable(parent, firstChildIndex, band.uid, "paneling", picks, byUid);
}

/**
 * The long axis of a band's rectangle — its run along the wall. Taken from the outline rather
 * than looked up on the wall, so the builder needs only the record it was handed.
 */
function bandAxis(outline: readonly Vec2[]): [Vec2, Vec2] {
  let best: [Vec2, Vec2] = [outline[0], outline[1]];
  let bestLen = -1;
  for (let index = 0; index < outline.length; index++) {
    const a = outline[index];
    const b = outline[(index + 1) % outline.length];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (len > bestLen) {
      bestLen = len;
      best = [a, b];
    }
  }
  return best;
}

// One owner's skin bands, merged per layer group so the assembly-layer toggles reach them.
// `skinLines` reaches only here: a closure band is a wall's own panel carried up past the top
// plate, and it takes its module phase from the facade the wall was laid out on so the ribs
// cross the joint unbroken.
function buildSkinByLayerGroup(group: THREE.Group, members: Member[], ownerUid: string,
  center: PlanCenter, mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  catalog: Catalog | undefined, skinLines?: readonly SkinLine[]) {
  const byGroup = new Map<LayerVisibilityGroup, Member[]>();
  for (const member of members) {
    const key = layerVisibilityGroupOf(member.category);
    byGroup.set(key, [...(byGroup.get(key) ?? []), member]);
  }
  for (const [key, bucket] of byGroup) {
    const firstIndex = group.children.length;
    buildMembers(group, bucket, center, mode, palette, ownerUid, catalog?.materials, skinLines);
    tagLayerGroup(group, firstIndex, key);
  }
}

// Sloped quads from footprint/eave_z/ridge_z/ridge_direction — mirrors
// emit/gltf/emitter.py's _add_roof — thickened into the authored assembly, plus the
// roof's own members (rafters, ridge beam).
export function buildRoof(parent: THREE.Group, roof: Roof, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, catalog: Catalog | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>, framingGroup?: THREE.Group,
  skinLines?: readonly SkinLine[], wallsGroup?: THREE.Group) {
  const firstChildIndex = parent.children.length;
  const triangles = roofPlaneTriangles(roof);
  const offsetAt = roofOffsetter(triangles);
  const perimeter = boundaryEdges(triangles);
  const assembly = catalog?.assemblies.find((a) => a.tag === roof.assembly);
  // eave_z_m/ridge_z_m is the rafter *top* (deck plane), so the stack starts at zero and
  // grows up. Engine-computed per-layer edge setbacks (golden eave detail clips) give
  // each layer its own inset rectangle; layers without an entry keep the footprint.
  const layers = aboveStructureLayers(assembly);
  const setbacks = new Map((roof.layer_edge_setbacks ?? []).map((e) => [e.layer, e]));
  const stack = layers.length ? layers
    : [{ name: "roofing", function: "cladding", material: "standing-seam", thickness_m: 0.05 }];

  let base = 0;
  for (const layer of stack) {
    const top = base + layer.thickness_m;
    const entry = setbacks.get(layer.name);
    let layerTriangles = triangles, layerOffsetAt = offsetAt, layerPerimeter = perimeter;
    if (entry) {
      layerTriangles = roofPlaneTriangles(roof, layerInsetRect(roof, entry, base));
      layerOffsetAt = roofOffsetter(layerTriangles);
      layerPerimeter = boundaryEdges(layerTriangles);
    }
    const faces: ProjectVertex[][] = [];
    for (const tri of layerTriangles) {
      faces.push([layerOffsetAt(tri[0], top), layerOffsetAt(tri[1], top), layerOffsetAt(tri[2], top)]);
      faces.push([layerOffsetAt(tri[0], base), layerOffsetAt(tri[2], base), layerOffsetAt(tri[1], base)]);
    }
    // Close the eave and rake so the layer stack reads as real thickness from outside.
    for (const [a, b] of layerPerimeter) {
      faces.push([layerOffsetAt(a, base), layerOffsetAt(b, base), layerOffsetAt(b, top)]);
      faces.push([layerOffsetAt(a, base), layerOffsetAt(b, top), layerOffsetAt(a, top)]);
    }
    const geo = createProjectedSurfaceGeometry(faces, center);
    // The same declared-finish-first dispatch every WALL panel goes through (→
    // builders/walls.ts): the material's authored `finish` names the profile, and only one
    // that declares nothing falls back to the `isStandingSeam` substring test. This was a
    // recorded gap until 2026-08-31 — it cost nothing while every roof was tagged
    // "standing-seam", and it would have drawn a seam recipe on a ribbed or corrugated roof.
    const roofAppearance = authoredAppearance(layer.material, catalog?.materials);
    const seamProfile = layer.function === "cladding"
      ? (metalPanelProfileForFinish(roofAppearance?.finish)
        ?? (isStandingSeam(layer.material) ? SEAM_PROFILE : null))
      : null;
    const seam = seamProfile !== null;
    const roofPaint = finishBaseColor(roofAppearance?.finish);
    // World-scaled UVs, applied to the geometry below: a roof plane carries none of its own
    // (`createProjectedSurfaceGeometry` sets position and normal only), which is why the
    // seam had nothing to sample and every roof read as flat paint.
    const mat = seam
      ? createStandingSeamMaterial(mode, [1, 1],
        roofPaint ? new THREE.Color(roofPaint).getHex() : 0xE8E8E2, true, seamProfile)
      : standardMaterial(new THREE.Color(materialColor(layer.material, palette)), mode, {
        roughness: mode === "nordic" ? NORDIC_ROUGHNESS.matte : 1,
        side: THREE.DoubleSide,
      });
    if (seam) applyStandingSeamRoofUv(geo, roof, center, seamProfile);
    const mesh = makeSurfaceMesh(geo, mat);
    mesh.userData.layerGroup = layerVisibilityGroupOf(layer.function);
    parent.add(mesh);
    base = top;
  }
  // Skin (fascia/soffit, the roof-edge cladding) finishes the shell and stays with it; the
  // sticks go to the framing group so rafters, trusses and gable studs sit under the framing
  // toggle with the rest of the building's framing. Both still select as the roof. The skin is
  // merged per layer group so the assembly-layer toggles reach it too.
  //
  // The closure bands are the exception, and they are why `owner` is asked at all: the roof
  // resolves them (only the roof planes say how high each layer climbs) but they are the
  // *wall's* own layer stack carried past the top plate, and they carry the wall's uid. They
  // build into `wallsGroup` under that uid, so the walls toggle takes them and a click lands on
  // the wall. Filing them by container instead put a gable end's whole raking face — five
  // layers, ten feet of wall, not a 12" eave strip — behind the roof toggle.
  const skin = roof.members.filter((m) => !isRoofFramingMember(m));
  const framing = roof.members.filter(isRoofFramingMember);
  const owned = skin.filter((m) => !m.parent_uid || m.parent_uid === roof.uid);
  const foreign = skin.filter((m) => m.parent_uid && m.parent_uid !== roof.uid);
  buildSkinByLayerGroup(parent, owned, roof.uid, center, mode, palette, catalog, skinLines);
  registerSelectable(parent, firstChildIndex, roof.uid, "roof", picks, byUid);
  if (wallsGroup && foreign.length) {
    for (const owner of [...new Set(foreign.map((m) => m.parent_uid as string))].sort()) {
      const ownerFirstIndex = wallsGroup.children.length;
      buildSkinByLayerGroup(wallsGroup, foreign.filter((m) => m.parent_uid === owner), owner,
        center, mode, palette, catalog, skinLines);
      registerSelectable(wallsGroup, ownerFirstIndex, owner, "wall", picks, byUid);
    }
  }
  if (framingGroup && framing.length) {
    const framingFirstIndex = framingGroup.children.length;
    buildMembers(framingGroup, framing, center, mode, palette, roof.uid, catalog?.materials);
    registerSelectable(framingGroup, framingFirstIndex, roof.uid, "roof", picks, byUid);
  }
}

// A stair is nothing but its generated members (stringers, treads, risers), so its whole
// framing bucket is what a click has to land on.
export function buildStair(parent: THREE.Group, stair: Stair, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>,
  materials?: readonly MaterialAppearance[]) {
  const firstChildIndex = parent.children.length;
  buildMembers(parent, stair.members, center, mode, palette, stair.uid, materials);
  for (const member of stair.members) {
    if (!member.plan_outline || member.plan_outline.length < 3) continue;
    const geo = createPlanPrismGeometry(member.plan_outline, member.z0_m, member.z1_m, [], center);
    if (!geo) continue;
    const mesh = makeSurfaceMesh(geo, standardMaterial(memberColor(member, palette, materials), mode));
    mesh.userData.memberKey = member.key;
    parent.add(mesh);
  }
  registerSelectable(parent, firstChildIndex, stair.uid, "stair", picks, byUid);
}

// Same shape as a stair: a brace is only its diagonal, so the member bucket is the click target.
// A host that is nothing but its own sticks: a brace, a soffit's ladder framing. Both were
// the same six lines, and this file is against AGENTS.md's 500-line limit, so they share one.
// `kind` is what differs and it is not cosmetic — a brace selects as "brace", while a
// soffit's framing selects as "solid" on the soffit's own uid, so picking a rung highlights
// the finished box with it, the way picking a stud highlights its wall.
function buildFramedHost(parent: THREE.Group, host: { uid: string; members: Member[] },
  kind: SelectionKind, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>,
  materials?: readonly MaterialAppearance[]) {
  const firstChildIndex = parent.children.length;
  buildMembers(parent, host.members, center, mode, palette, host.uid, materials);
  registerSelectable(parent, firstChildIndex, host.uid, kind, picks, byUid);
}

export function buildBrace(parent: THREE.Group, brace: Brace, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>,
  materials?: readonly MaterialAppearance[]) {
  buildFramedHost(parent, brace, "brace", center, mode, palette, picks, byUid, materials);
}

export function buildSoffitFraming(parent: THREE.Group, soffit: SoffitFraming,
  center: PlanCenter, mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>,
  materials?: readonly MaterialAppearance[]) {
  buildFramedHost(parent, soffit, "solid", center, mode, palette, picks, byUid, materials);
}
