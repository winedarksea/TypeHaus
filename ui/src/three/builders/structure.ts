// Builders for the resolver's *derived* geometry: concrete solids, a footing's gravel bedding,
// framed floors, roofs and stairs.
//
// Split out of components/Panel3D.tsx. What these five share is that none of them is authored
// — each is geometry the resolver computed from something else — so all of them extrude a
// resolved outline or lay out a member list, and none carries an editing path.
import * as THREE from "three";
import type {
  Brace, Catalog, FootingBedding, Floor, Member, Roof, Room, Solid, SolarPanel, Stair, Vec2,
} from "../../model/types";
import { layerVisibilityGroupOf, type LayerVisibilityGroup } from "../../model/visibility";
import {
  authoredAppearance, floorSurface, materialColor, type MaterialAppearance,
  type ResolvedNordicPalette,
} from "../../nordic/palette";
import {
  applyDeckBoardUv, createDeckBoardMaterial, createStandingSeamMaterial,
  isAluminumDeckBoard, isStandingSeam,
} from "../materials";
import { buildMembers, isRoofFramingMember } from "../members";
import {
  createPlanPrismGeometry, createProjectedSurfaceGeometry, type PlanCenter, type ProjectVertex,
} from "../planGeometry";
import {
  aboveStructureLayers, boundaryEdges, layerInsetRect, roofOffsetter, roofPlaneTriangles,
} from "../roofGeometry";
import { createSolidMaterial } from "../solidMaterials";
import { registerSelectable, tagLayerGroup } from "./registry";

export function buildSolid(parent: THREE.Group, solid: Solid, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, catalog: Catalog | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (solid.outline.length < 3) return;
  const geo = createPlanPrismGeometry(solid.outline, solid.z0_m, Math.max(solid.z1_m, solid.z0_m + 0.01), solid.voids ?? [], center);
  if (!geo) return;
  const deckBoards = catalog?.assemblies.find((a) => a.tag === solid.assembly)?.layers
    .some((layer) => isAluminumDeckBoard(layer.material));
  if (deckBoards) applyDeckBoardUv(geo, center);
  const firstChildIndex = parent.children.length;
  const mesh = new THREE.Mesh(geo,
    deckBoards ? createDeckBoardMaterial(mode) : createSolidMaterial(solid, catalog, mode, palette));
  mesh.castShadow = true;
  mesh.receiveShadow = true;
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
  const mat = new THREE.MeshStandardMaterial({
    color: SOLAR_PANEL_COLOR,
    roughness: mode === "nordic" ? 0.25 : 0.6, // glassy face under the nordic sun
    metalness: mode === "nordic" ? 0.4 : 0.1,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  registerSelectable(parent, firstChildIndex, panel.uid, "solid", picks, byUid);
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
  const mat = new THREE.MeshStandardMaterial({
    color: FOOTING_BEDDING_COLOR,
    roughness: 1,
    metalness: 0,
    flatShading: true, // faceted normals read as loose aggregate in both shading modes
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
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
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
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
    parent.add(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
      color: new THREE.Color(materialColor(floor.subfloor.material, palette)), roughness: mode === "nordic" ? 0.85 : 1,
      flatShading: mode === "schematic",
    })));
  }
  buildMembers(parent, floor.members, center, mode, palette, floor.uid);
  registerSelectable(parent, firstChildIndex, floor.uid, "floor", picks, byUid);
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
 */
export function buildRoomFloor(parent: THREE.Group, room: Room, floorTopM: number,
  openings: readonly Vec2[][], center: PlanCenter, mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette, materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (!room.floor_finish || room.clear_face.length < 3) return;
  // A coating (sealed concrete) is a sealer on the deck, not a covering over it: it has no
  // thickness of its own, so drawing a plane for it would put a second floor a hair above
  // the slab that already carries the colour. It still bills — takeoff/finishes.py.
  if (authoredAppearance(room.floor_finish, materials)?.coating) return;
  const geometry = createPlanPrismGeometry(
    room.clear_face, floorTopM, floorTopM + ROOM_FINISH_THICKNESS_M, openings, center);
  if (!geometry) return;
  const firstChildIndex = parent.children.length;
  const surface = floorSurface(room.floor_finish);
  const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
    color: new THREE.Color(materialColor(room.floor_finish, palette, materials)),
    roughness: mode === "nordic" ? surface.roughness : 1,
    metalness: mode === "nordic" ? surface.metalness : 0,
    flatShading: mode === "schematic",
  }));
  mesh.receiveShadow = true;
  parent.add(mesh);
  registerSelectable(parent, firstChildIndex, room.uid, "room", picks, byUid);
}

// Sloped quads from footprint/eave_z/ridge_z/ridge_direction — mirrors
// emit/gltf/emitter.py's _add_roof — thickened into the authored assembly, plus the
// roof's own members (rafters, ridge beam).
export function buildRoof(parent: THREE.Group, roof: Roof, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, catalog: Catalog | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>, framingGroup?: THREE.Group) {
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
    const seam = layer.function === "cladding" && isStandingSeam(layer.material);
    const mat = seam
      ? createStandingSeamMaterial(mode, [Math.sqrt(roof.surface_area_m2), Math.sqrt(roof.surface_area_m2)])
      : new THREE.MeshStandardMaterial({
        color: new THREE.Color(materialColor(layer.material, palette)),
        roughness: mode === "nordic" ? 0.9 : 1,
        flatShading: mode === "schematic",
        side: THREE.DoubleSide,
      });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.layerGroup = layerVisibilityGroupOf(layer.function);
    parent.add(mesh);
    base = top;
  }
  // Skin (closure bands, fascia/soffit, the roof-edge cladding) finishes the shell and stays
  // with it; the sticks go to the framing group so rafters, trusses and gable studs sit under
  // the framing toggle with the rest of the building's framing. Both still select as the roof.
  // The skin is merged per layer group so the assembly-layer toggles reach it too.
  const skin = roof.members.filter((m) => !isRoofFramingMember(m));
  const framing = roof.members.filter(isRoofFramingMember);
  const skinByGroup = new Map<LayerVisibilityGroup, Member[]>();
  for (const member of skin) {
    const group = layerVisibilityGroupOf(member.category);
    skinByGroup.set(group, [...(skinByGroup.get(group) ?? []), member]);
  }
  for (const [group, members] of skinByGroup) {
    const skinFirstIndex = parent.children.length;
    buildMembers(parent, members, center, mode, palette, roof.uid);
    tagLayerGroup(parent, skinFirstIndex, group);
  }
  registerSelectable(parent, firstChildIndex, roof.uid, "roof", picks, byUid);
  if (framingGroup && framing.length) {
    const framingFirstIndex = framingGroup.children.length;
    buildMembers(framingGroup, framing, center, mode, palette, roof.uid);
    registerSelectable(framingGroup, framingFirstIndex, roof.uid, "roof", picks, byUid);
  }
}

// A stair is nothing but its generated members (stringers, treads, risers), so its whole
// framing bucket is what a click has to land on.
export function buildStair(parent: THREE.Group, stair: Stair, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const firstChildIndex = parent.children.length;
  buildMembers(parent, stair.members, center, mode, palette, stair.uid);
  registerSelectable(parent, firstChildIndex, stair.uid, "stair", picks, byUid);
}

// Same shape as a stair: a brace is only its diagonal, so the member bucket is the click target.
export function buildBrace(parent: THREE.Group, brace: Brace, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const firstChildIndex = parent.children.length;
  buildMembers(parent, brace.members, center, mode, palette, brace.uid);
  registerSelectable(parent, firstChildIndex, brace.uid, "brace", picks, byUid);
}
