import * as THREE from "three";
import type { CanvasObject, Catalog, Floor, FootingBedding, Member, ModelPart, Opening, Roof, Solid, Stair, Vec2, Wall, Model } from "../model/types";
import { compassBearingScreenDirection } from "./Panel3D";
import {
  frameRadiusForBounds, normalizedWheelDeltaPx, VIEW_FIT_MIN_RADIUS_M, VIEW_FIT_POLAR_ANGLE,
  WHEEL_MAX_STEP_PX,
} from "../three/cameraFraming";
import { wholeHouseGlbAssignment } from "../three/wholeHouseGlb";
import { isRenderedInScene } from "../three/builders/registry";
import {
  buildCanvasObjectParts, canvasObjectFallbackGeometry, earthElevation, earthOutline, earthVoids,
  EARTH_FALLBACK_HALF_SIZE_M,
} from "../three/builders/site";
import {
  archSoffitSegmentCount, buildOpening, createSmoothArchedWallLayerGeometry, wallLayerPieces,
  withoutCollinearVertices,
} from "../three/builders/walls";
import {
  buildFloor, buildFootingBedding, buildRoof, buildSolid, buildStair, FOOTING_BEDDING_COLOR,
} from "../three/builders/structure";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { SOLID_CATEGORY_COLOR, createSolidMaterial, solidColor } from "../three/solidMaterials";
import { carriesMemberIdentity, resolveMemberPickUid } from "../three/memberPicking";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const PALETTE = RESOLVED_NORDIC_PALETTE.light;

// A fresh, empty selection registry — the two structures createScene threads through every
// builder (the raycast target list and the uid → materials index the highlight pass drives).
function registry() {
  return { picks: [] as THREE.Mesh[], byUid: new Map<string, THREE.Material[]>() };
}

function wall(axis: Wall["axis"], topZ0: number | null = null, topZ1: number | null = null): Wall {
  return {
    uid: "wall", tag: "W-1", storey: "S-1", assembly: "A-1", provenance: null, axis,
    z0_m: 0, z1_m: 3, top_z0_m: topZ0, top_z1_m: topZ1, is_foundation: false,
    layers: [], members: [],
  };
}

function opening(centerAlongM: number, sillM = 0.9, heightM = 1.2, archRiseM = 0, widthM = 1): Opening {
  return {
    uid: "opening", tag: "O-1", host: "W-1", kind: "window", is_door: false,
    provenance: null, type_ref: "WIN", width_m: widthM, height_m: heightM, sill_m: sillM,
    center_along_m: centerAlongM, arch_rise_m: archRiseM, flip_hinge: false, flip_swing: false,
  };
}

// Called by scripts/run-geometry-tests.mjs. This verifies the CSG-free split used for
// partial-height openings: no generated wall piece may occupy the sill-to-head interval.
export function runOpeningGeometryTests() {
  const horizontal = wallLayerPieces(wall([[0, 0], [4, 0]]), [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [opening(2)]);
  assert(horizontal.length === 4, "Window splits a rectangular wall layer into side, sill, and header pieces");
  assert(!horizontal.some((piece) => piece.z0_m < 2.1 && piece.z1_m > 0.9 && piece.polygon.some(([x]) => x > 1.5 && x < 2.5)),
    "No horizontal-wall piece fills the window void");

  // A raked wall cannot be swept as one Shape, so its arch still falls back to stepped strips —
  // but they are stepped by angle, so no single strip carries a springline-sized riser.
  const rakedArch = wallLayerPieces(wall([[0, 0], [4, 0]], 3, 2.4),
    [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [opening(2, 0, 1, 0.5)]);
  const archSpandrels = rakedArch.filter((piece) => piece.z0_m > 0);
  assert(archSpandrels.length === archSoffitSegmentCount(0.5),
    "Strip fallback tessellates the arch to its radius-derived segment count");
  assert(Math.max(...archSpandrels.map((piece) => piece.z0_m)) > Math.min(...archSpandrels.map((piece) => piece.z0_m)),
    "Arch soffit rises from its springlines to a visible crown");
  const risers = archSpandrels.slice(1).map((piece, index) => Math.abs(piece.z0_m - archSpandrels[index].z0_m));
  assert(Math.max(...risers) < 0.5 / 2,
    "Angular sampling keeps every soffit step well under the radius — even-x steps dropped ~85% of it at the springline");

  const vertical = wallLayerPieces(wall([[0, 0], [0, 4]]), [[-0.1, 0], [0.1, 0], [0.1, 4], [-0.1, 4]], [opening(2)]);
  assert(vertical.length === 4, "Vertical wall uses the same axis-relative opening split");

  const raked = wallLayerPieces(wall([[0, 0], [4, 0]], 3, 2.4), [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [opening(2, 0.9, 1)]);
  assert(raked.some((piece) => piece.topIsRaked), "Header pieces preserve a raked wall top");

  const mitered = wallLayerPieces(
    wall([[0, 0], [4, 0]]),
    [[-0.25, 0], [0, -0.25], [4, -0.25], [4, 0.25], [0, 0.25]],
    [opening(2)],
  );
  assert(mitered.some((piece) => piece.polygon.some(([x, y]) => x === -0.25 && y === 0)),
    "Opening splitting preserves a junction-solved miter vertex");
}

// Arches must read as true half circles, not a stack of stripes. That needs the swept-Shape
// path — and the guard that admits a layer to it has to see past the collinear vertices
// junction resolution leaves on the ring, or every real arched wall falls back to strips.
export function runArchGeometryTests() {
  assert(withoutCollinearVertices([[0, 0], [2, 0], [4, 0], [4, 1], [0, 1]]).length === 4,
    "A rectangle padded with an edge-splitting vertex reduces to its four corners");
  assert(withoutCollinearVertices([[-0.25, 0], [0, -0.25], [4, -0.25], [4, 0.25], [0, 0.25]]).length === 5,
    "A junction-solved miter vertex is a real corner and survives reduction");
  assert(withoutCollinearVertices([[0, 0], [4, 0], [4, 1], [4, 1], [0, 1]]).length === 4,
    "Duplicate vertices collapse without inventing a corner");

  assert(archSoffitSegmentCount(1.2192) > archSoffitSegmentCount(0.3),
    "Tessellation follows the arch radius rather than a flat constant");

  // W-SG-ARCH's serialized 16" concrete layer: one rectangle, six points.
  const archWall = wall([[0, 0], [6, 0]]);
  const paddedThinRect: [number, number][] = [[0.5, -0.2], [0.5, 0], [0.5, 0.2], [5.5, 0.2], [5.5, 0], [5.5, -0.2]];
  const arch = opening(3, 0.1, 2.4, 1.2, 2.4);
  const smooth = createSmoothArchedWallLayerGeometry(archWall, paddedThinRect, [arch], [0, 0]);
  assert(smooth !== null, "A collinear-padded rectangle still takes the smooth swept-arch path");
  const box = new THREE.Box3().setFromBufferAttribute(smooth.getAttribute("position") as THREE.BufferAttribute);
  assert(Math.abs((box.max.z - box.min.z) - 0.4) < 1e-6,
    "The swept layer keeps its full authored thickness");

  // Every soffit vertex carries the analytic cylinder normal, so adjacent facets shade as one
  // curve instead of ARCH segment-count flats. Wall axis is +x, so scene x/y are the shape plane.
  const position = smooth.getAttribute("position");
  const normal = smooth.getAttribute("normal");
  const springline = archWall.z0_m + arch.sill_m + (arch.height_m - (arch.arch_rise_m ?? 0));
  let soffitVertices = 0;
  for (let index = 0; index < position.count; index++) {
    // The front/back caps also have vertices on the arc; they must keep their axial normals.
    if (Math.abs(normal.getZ(index)) > 0.5) continue;
    const dx = position.getX(index) - arch.center_along_m;
    const dy = position.getY(index) - springline;
    const distance = Math.hypot(dx, dy);
    // Positions are float32, so allow a hair of slack around the circle and the springline.
    if (dy < 1e-4 || Math.abs(distance - 1.2) > 1e-4) continue;
    soffitVertices++;
    const aligned = Math.abs(normal.getX(index) * dx / distance + normal.getY(index) * dy / distance);
    assert(aligned > 1 - 1e-5 && Math.abs(normal.getZ(index)) < 1e-5,
      "Soffit normals are radial to the arch circle, not per-facet");
  }
  assert(soffitVertices > archSoffitSegmentCount(1.2),
    "The soffit ring was actually found and smoothed");

  assert(createSmoothArchedWallLayerGeometry(archWall, paddedThinRect, [opening(3)], [0, 0]) === null,
    "A wall with no arched opening keeps the ordinary extrusion path");
  assert(createSmoothArchedWallLayerGeometry(
    wall([[0, 0], [6, 0]], 3, 2.4), paddedThinRect, [arch], [0, 0]) === null,
    "A raked wall cannot be swept as one Shape and falls back to strips");
  assert(createSmoothArchedWallLayerGeometry(archWall,
    [[-0.25, 0], [0, -0.2], [6, -0.2], [6, 0.2], [0, 0.2]], [arch], [0, 0]) === null,
    "A genuinely non-rectangular (mitered) footprint still falls back to strips");
}

export function runEarthGeometryTests() {
  const model = { site: { lat: 0, lon: 0, true_north_deg: 0,
    parcel: [[-2, -1], [4, -1], [4, 3], [-2, 3]] } } as Model;
  const parcel = earthOutline(model, [0, 0]);
  assert(parcel.length === 4 && parcel[0][0] === -2 && parcel[2][1] === 3,
    "Earth uses the authored parcel outline");

  const fallback = earthOutline({} as Model, [3, 5]);
  assert(fallback[0][0] === 3 - EARTH_FALLBACK_HALF_SIZE_M &&
    fallback[2][1] === 5 + EARTH_FALLBACK_HALF_SIZE_M,
    "Earth falls back to a large centered sheet without a parcel");

  assert(earthElevation({ site: { lat: 0, lon: 0, true_north_deg: 0, grade_m: 1.5 } } as Model) === 1.5,
    "Earth uses the serialized site grade");
  assert(earthElevation({} as Model) === 0, "Earth defaults to the main-floor datum");

  // Excavations punch holes in the site sheet so the earth no longer bleeds up through the
  // spaces that were dug for it. The rings are resolved server-side from slabs at or below
  // grade (resolve/site_earth.py) and arrive already unioned into disjoint outer boundaries —
  // one per structure, which is why the viewer must not re-derive them. The old room-derived
  // version could only ever see one storey of one structure, so a detached garage and an
  // open-air sunken garden (no shared storey, room set or wall loop) stayed uncut.
  const withVoids = {
    site: {
      lat: 0, lon: 0, true_north_deg: 0,
      earth_voids: [
        [[0, 0], [7, 0], [7, 3], [0, 3]], // house
        [[10, 0], [16, 0], [16, 6], [10, 6]], // detached garage — its own structure
        [[0, 8], [4, 8], [4, 12], [0, 12]], // open-air sunken garden — no rooms at all
        [[1, 1], [1, 1]], // degenerate ring is skipped
      ],
    },
    // Rooms are deliberately present and disagree with the voids: nothing here may fall back
    // to them, or the multi-structure fix silently regresses.
    storeys: [{ tag: "L1", elevation_m: 0 }],
    rooms: [{ storey: "L1", clear_face: [[0, 0], [4, 0], [4, 3], [0, 3]] }],
  } as unknown as Model;
  const voids = earthVoids(withVoids);
  assert(voids.length === 3, "Every excavated structure cuts the sheet, not just the house");
  assert(voids.every((ring) => ring.length === 4), "Each cut is the resolved outer ring");
  assert(voids.some(([first]) => first[0] === 10) && voids.some(([first]) => first[1] === 8),
    "The detached garage and the sunken garden both cut, though neither shares a storey with the house");

  assert(earthVoids({} as Model).length === 0,
    "No serialized voids → a solid sheet (older model.json), never a room-derived guess");
  assert(earthVoids({ rooms: [{ storey: "L1", clear_face: [[0, 0], [4, 0], [4, 3]] }],
    storeys: [{ tag: "L1", elevation_m: 0 }] } as unknown as Model).length === 0,
    "Rooms alone never cut the sheet — the engine owns this derivation now");
}

export function runFootingBeddingGeometryTests() {
  const bedding = {
    uid: "FB-1", tag: "FB-1", storey: "L1", host_footing: "F-1",
    outline: [[0, 0], [3, 0], [3, 1], [0, 1]], z0_m: -1.2, z1_m: -0.9,
    aggregate: "washed-stone", geotextile: true, drain_tile: true, provenance: null,
  } as FootingBedding;
  const group = new THREE.Group();
  const schematic = registry();
  buildFootingBedding(group, bedding, [0, 0], "schematic", schematic.picks, schematic.byUid);
  const meshes = group.children.filter((child): child is THREE.Mesh => child instanceof THREE.Mesh);
  assert(meshes.length === 1, "Footing bedding renders one gravel prism (schematic omits the edge overlay)");
  const box = new THREE.Box3().setFromObject(meshes[0]);
  assert(Math.abs(box.min.y - -1.2) < 1e-6 && Math.abs(box.max.y - -0.9) < 1e-6,
    "Gravel bed spans the authored undercut below the footing underside");
  assert((meshes[0].material as THREE.MeshStandardMaterial).color.getHex() === FOOTING_BEDDING_COLOR,
    "Gravel bed uses the aggregate colour, not concrete grey");

  // Nordic mode adds a faceted edge overlay for legibility.
  const nordic = new THREE.Group();
  const nordicRegistry = registry();
  buildFootingBedding(nordic, bedding, [0, 0], "nordic", nordicRegistry.picks, nordicRegistry.byUid);
  assert(nordic.children.some((child) => child instanceof THREE.LineSegments),
    "Nordic footing bedding gains an edge overlay");
  assert(nordicRegistry.picks.length === 1,
    "The edge overlay stays out of the raycast set — only the gravel prism is pickable");

  const degenerate = new THREE.Group();
  const skipped = registry();
  buildFootingBedding(degenerate, { ...bedding, z1_m: -1.2 } as FootingBedding, [0, 0], "schematic",
    skipped.picks, skipped.byUid);
  assert(degenerate.children.length === 0, "Zero-thickness bedding produces no geometry");
  assert(skipped.picks.length === 0, "Geometry-free bedding registers nothing to pick");
}

// --- B7: solid finishes ------------------------------------------------------
// Every non-wall prism used to render as one concrete grey. Category + assembly now drive the
// finish, mirroring emit/gltf/emitter.py::_solid_color / _PALETTE.

const POST_PAINT_CATALOG = {
  window_types: [], door_types: [], occupancies: [], materials: [],
  assemblies: [{
    tag: "POST_WHITE_PAINT", editable: false, provenance: null, stc: null, variant_of: null,
    layers: [{ name: "post-paint-white", material: "post-paint-white", function: "structure", thickness_m: 0.1397 }],
  }],
} as Catalog;

function solid(category: string, assembly: string | null = null, uid = "S-1"): Solid {
  return {
    uid, tag: uid, storey: "L1", category, assembly, provenance: null,
    outline: [[0, 0], [1, 0], [1, 0.2], [0, 0.2]], voids: [], z0_m: 0, z1_m: 2.4,
  };
}

export function runSolidMaterialTests() {
  assert(solidColor(solid("beam"), undefined, PALETTE) === SOLID_CATEGORY_COLOR.beam,
    "An unfinished beam reads as wood from the category palette");
  assert(SOLID_CATEGORY_COLOR.beam !== PALETTE.member.concrete,
    "The beam colour is wood, not the concrete fallback the old buildSolid used");

  // The TODO's headline case: six 6x6 posts carry assembly=POST_WHITE_PAINT.
  const painted = solidColor(solid("column", "POST_WHITE_PAINT"), POST_PAINT_CATALOG, PALETTE);
  assert(painted === 0xf4f2ee, `A painted post reads as its paint colour, got ${painted.toString(16)}`);
  assert(painted !== SOLID_CATEGORY_COLOR.column,
    "The authored assembly overrides the bare column palette entry");

  // Gutters, fascia and flashings were invisible grey slivers before B7.
  for (const category of ["gutter", "fascia", "flashing"]) {
    const color = solidColor(solid(category), undefined, PALETTE);
    assert(color === SOLID_CATEGORY_COLOR[category], `${category} uses its own palette entry`);
    assert(color !== PALETTE.member.concrete, `${category} no longer renders as concrete grey`);
  }

  // An unmapped category falls back to the theme's neutral rather than inventing a colour.
  // (Construction returns used to arrive here as "return:*" solids; the engine emits none
  // now — they are records on Model.construction_returns, drawn by nothing.)
  assert(solidColor(solid("no-such-category"), undefined, PALETTE) === PALETTE.member.concrete,
    "An unmapped category falls back to the theme's neutral, matching the emitter's _FALLBACK");

  const metal = createSolidMaterial(solid("gutter"), undefined, "nordic", PALETTE);
  assert(metal.metalness > 0, "Shop-finished metal accessories render metallic");
  const concrete = createSolidMaterial(solid("slab"), undefined, "nordic", PALETTE);
  assert(concrete.metalness === 0, "Cast concrete stays fully dielectric");
}

// --- B7: pick registration ---------------------------------------------------
// picks[] is the only raycast target and byUid drives the emissive highlight, so a builder that
// forgets either leaves its element unselectable. One assertion per builder that opts in.

function member(key: string): Member {
  return {
    key, category: "joist", profile: "2x10", p0: [0, 0], p1: [3, 0], z0_m: 2.4, z1_m: 2.65,
    length_m: 3, z0_end_m: null, z1_end_m: null, shape: "rect", width_m: 0.038, depth_m: 0.235,
    flange_width_m: null, flange_thickness_m: null, web_thickness_m: null, plies: 1,
    orient: null,
  } as Member;
}

function registered(group: THREE.Group, uid: string, kind: string, picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>, label: string) {
  const mine = picks.filter((mesh) => mesh.userData.uid === uid);
  assert(mine.length > 0, `${label} pushes at least one mesh into the raycast set`);
  assert(mine.every((mesh) => mesh.userData.selectionKind === kind),
    `${label} tags every pickable mesh with selectionKind "${kind}"`);
  assert((byUid.get(uid) ?? []).length > 0, `${label} indexes its materials for the highlight pass`);
  assert(group.children.length > 0, `${label} actually built geometry`);
}

export function runSelectionRegistrationTests() {
  const solidGroup = new THREE.Group();
  const solids = registry();
  buildSolid(solidGroup, solid("column", null, "SO-1"), [0, 0], "schematic", PALETTE, undefined,
    solids.picks, solids.byUid);
  registered(solidGroup, "SO-1", "solid", solids.picks, solids.byUid, "buildSolid");

  const beddingGroup = new THREE.Group();
  const beddings = registry();
  buildFootingBedding(beddingGroup, {
    uid: "FB-9", tag: "FB-9", storey: "L1", host_footing: "F-1",
    outline: [[0, 0], [3, 0], [3, 1], [0, 1]], z0_m: -1.2, z1_m: -0.9,
    aggregate: "washed-stone", geotextile: true, drain_tile: true, provenance: null,
  } as FootingBedding, [0, 0], "schematic", beddings.picks, beddings.byUid);
  registered(beddingGroup, "FB-9", "footing_bedding", beddings.picks, beddings.byUid, "buildFootingBedding");

  // A floor's joists are merged into shared draw calls, but each bucket carries its own
  // per-member identity — so the deck selects as the floor while a joist selects as a joist.
  const floorGroup = new THREE.Group();
  const floors = registry();
  buildFloor(floorGroup, {
    uid: "FL-1", tag: "FL-1", storey: "L1", direction: "x", provenance: null, openings: [],
    subfloor: { material: "osb", thickness_m: 0.019 }, members: [member("J-1"), member("J-2")],
  } as Floor, [0, 0], "schematic", PALETTE, floors.picks, floors.byUid);
  registered(floorGroup, "FL-1", "floor", floors.picks, floors.byUid, "buildFloor");
  assert(floors.picks.length > 1, "The subfloor deck and the joist bucket are both raycast targets");
  const joistBucket = floors.picks.find(carriesMemberIdentity);
  assert(joistBucket !== undefined, "buildFloor makes its joist bucket pickable");
  assert(resolveMemberPickUid(joistBucket!, 1, null) === "FL-1::J-2",
    "Instance 1 of the floor's joist bucket resolves to the second joist, not to the floor");
  assert((floors.byUid.get("FL-1") ?? []).includes(joistBucket!.material as THREE.Material),
    "Selecting the floor still lights its joists — the bucket stays in the owner's highlight set");

  const roofGroup = new THREE.Group();
  const roofs = registry();
  buildRoof(roofGroup, {
    uid: "R-1", tag: "R-1", storey: "L1", form: "gable",
    footprint: [[0, 0], [6, 0], [6, 4], [0, 4]], eave_z_m: 3, ridge_z_m: 4.5,
    ridge_direction: "x", assembly: "ROOF-1", surface_area_m2: 26, members: [], provenance: null,
  } as Roof, [0, 0], "schematic", PALETTE, undefined, roofs.picks, roofs.byUid);
  registered(roofGroup, "R-1", "roof", roofs.picks, roofs.byUid, "buildRoof");

  // A stair is nothing *but* members, so every one of its picks now resolves to a tread or a
  // stringer rather than to the stair. The stair is still reachable — from the 2D plan, and
  // from the member inspector's parent link — and still highlights, because its member bucket
  // stays in byUid.
  const stairGroup = new THREE.Group();
  const stairs = registry();
  buildStair(stairGroup, { uid: "ST-1", members: [member("T-1"), member("T-2")] } as Stair,
    [0, 0], "schematic", PALETTE, stairs.picks, stairs.byUid);
  assert(stairs.picks.length > 0 && stairs.picks.every(carriesMemberIdentity),
    "buildStair's picks are all member buckets");
  assert(resolveMemberPickUid(stairs.picks[0], 0, null) === "ST-1::T-1",
    "Clicking the first tread selects that tread");
  assert((stairs.byUid.get("ST-1") ?? []).length > 0,
    "buildStair still indexes its materials so selecting the stair highlights it");

  const openingGroup = new THREE.Group();
  const openings = registry();
  buildOpening(openingGroup, opening(2), wall([[0, 0], [4, 0]]), [0, 0], "schematic", PALETTE,
    false, openings.picks, openings.byUid);
  registered(openingGroup, "opening", "opening", openings.picks, openings.byUid, "buildOpening");

  // A rough opening has no filling to click on, so it must register nothing at all.
  const roughGroup = new THREE.Group();
  const rough = registry();
  buildOpening(roughGroup, { ...opening(2), kind: "rough_opening" } as Opening,
    wall([[0, 0], [4, 0]]), [0, 0], "schematic", PALETTE, false, rough.picks, rough.byUid);
  assert(rough.picks.length === 0 && roughGroup.children.length === 0,
    "An unfilled rough opening builds nothing and registers nothing");
}

export function runCanvasObjectGeometryTests() {
  assert(canvasObjectFallbackGeometry("cylinder", 0.4, 1, 0.6).type === "CylinderGeometry",
    "Configured cylinder primitives are rendered before their GLB is ready");
  assert(canvasObjectFallbackGeometry("unsupported", 0.4, 1, 0.6).type === "BoxGeometry",
    "Unknown primitives retain the footprint-box fallback");

  const target = new THREE.Vector3(0, 0, 0);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
  camera.position.set(5, 5, 5);
  camera.lookAt(target);
  const northFromSoutheast = compassBearingScreenDirection(camera, target, 0, 0);
  camera.position.set(-5, 5, 5);
  camera.lookAt(target);
  const northFromSouthwest = compassBearingScreenDirection(camera, target, 0, 0);
  assert(Math.abs(northFromSoutheast[0] - northFromSouthwest[0]) > 0.5,
    "Compass north responds to camera orbit");

  camera.position.set(5, 5, 5);
  camera.lookAt(target);
  const rotatedTrueNorth = compassBearingScreenDirection(camera, target, 0, 90);
  assert(Math.hypot(
    northFromSoutheast[0] - rotatedTrueNorth[0],
    northFromSoutheast[1] - rotatedTrueNorth[1],
  ) > 0.5, "Compass north responds to site true-north rotation");
}

// A generated massing is one group of boxes, not one mesh — but it is still one *object*:
// every part has to answer to the same uid, or clicking an arm would select an arm.
export function runCanvasObjectPartsTests() {
  const group = new THREE.Group();
  const { picks, byUid } = registry();
  const item = {
    uid: "CO-1", tag: "F-1", storey: "L1", kind: "Furniture", type: "FURN-SOFA-84",
    domain: "furniture", room: null, position_m: [2, 3] as Vec2, rotation: 90,
    host: null, attachment: null,
  } as CanvasObject;
  const parts: ModelPart[] = [
    { center: [0, 0.3, 0.4], size: [2, 0.2, 0.8], color: "#8c8f95" },
    { center: [-0.8, 0, 0.3], size: [0.14, 0.9, 0.6], color: "#8c8f95" },
    { center: [0, -0.1, 0.45], size: [1.6, 0.6, 0.12], color: "#adb0b3" },
  ];
  const built = buildCanvasObjectParts(group, item, parts, [0, 0], "schematic", 1.5, picks, byUid);

  assert(built instanceof THREE.Group, "A multi-part massing builds a group, not a single mesh");
  assert(built.children.length === parts.length, "Every part becomes its own box mesh");
  registered(group, "CO-1", "canvas_object", picks, byUid, "buildCanvasObjectParts");
  assert(picks.filter((mesh) => mesh.userData.uid === "CO-1").length === parts.length,
    "Clicking any part selects the whole object: all of them are raycast targets for one uid");
  // Two roles, three parts — the highlight pass must reach both materials and no duplicates.
  assert((byUid.get("CO-1") ?? []).length === 2,
    "One material per distinct colour, shared across the parts that use it");

  // Placement lives on the group; a part only carries its local offset, mapped plan → scene
  // as (x, z, -y). Nothing may be baked into the meshes themselves.
  assert(Math.abs(built.position.y - 1.5) < 1e-9, "The group sits at the object's base elevation");
  assert(Math.abs(built.position.x - 2) < 1e-9 && Math.abs(built.position.z + 3) < 1e-9,
    "The group carries the plan position");
  assert(Math.abs(built.rotation.y - Math.PI / 2) < 1e-9, "The group carries the plan rotation");
  const back = built.children[0] as THREE.Mesh;
  assert(Math.abs(back.position.x) < 1e-9 && Math.abs(back.position.y - 0.4) < 1e-9
    && Math.abs(back.position.z + 0.3) < 1e-9, "A part offset maps (x, y, z) -> (x, z, -y)");
  assert(back.rotation.y === 0, "Rotation is the group's job, never the part's");
}

// The whole-house glb only becomes the primary scene when its nodes map back to trades (and,
// for selectable elements, model uids). A single untagged "building" node — today's emitter
// output — must classify as unstructured so the model.json baseline stands with no regression.
export function runWholeHouseGlbTests() {
  assert(wholeHouseGlbAssignment("building", undefined) === null,
    "The monolithic color-bucketed node is unstructured → glb is not promoted");
  assert(wholeHouseGlbAssignment(undefined, {}) === null, "A node with no trade is unassigned");
  assert(wholeHouseGlbAssignment("not-a-trade|wall|W-1", undefined) === null,
    "An unknown trade token does not classify");

  const fromExtras = wholeHouseGlbAssignment(undefined, { trade: "walls", uid: "W-1", kind: "wall" });
  assert(fromExtras !== null && fromExtras.trade === "walls" && fromExtras.uid === "W-1"
    && fromExtras.kind === "wall", "glTF extras assign trade + uid + selection kind");

  const fromName = wholeHouseGlbAssignment("furniture|canvas_object|CO-9", undefined);
  assert(fromName !== null && fromName.trade === "furniture" && fromName.uid === "CO-9"
    && fromName.kind === "canvas_object", "The <trade>|<kind>|<uid> name convention is the fallback");

  const envelopeOnly = wholeHouseGlbAssignment("roof", undefined);
  assert(envelopeOnly !== null && envelopeOnly.trade === "roof" && envelopeOnly.uid === null
    && envelopeOnly.kind === null, "Non-selectable envelope geometry only needs its trade");

  const extrasWinName = wholeHouseGlbAssignment("walls|wall|FROM-NAME", { trade: "concrete", uid: "FROM-EXTRAS", kind: "wall" });
  assert(extrasWinName !== null && extrasWinName.trade === "concrete" && extrasWinName.uid === "FROM-EXTRAS",
    "Explicit extras take precedence over the name convention");

  // B7 widened the kind vocabulary on both sides of the export
  // (emit/gltf/emitter.py::_SELECTION_KINDS ↔ state/store.ts SelectionKind).
  for (const kind of ["opening", "room", "solid", "footing_bedding", "floor", "roof", "stair"]) {
    const widened = wholeHouseGlbAssignment(undefined, { trade: "concrete", uid: "X-1", kind });
    assert(widened !== null && widened.kind === kind, `glb nodes may declare kind "${kind}"`);
  }
  const bogus = wholeHouseGlbAssignment(undefined, { trade: "concrete", uid: "X-1", kind: "gutter" });
  assert(bogus !== null && bogus.kind === null,
    "A kind outside the shared vocabulary is dropped rather than trusted");
}

// Default / reset framing (→ TODO: "the 'default zoom' for reset is poorly calculated").
export function runViewFramingTests() {
  const verticalFov = THREE.MathUtils.degToRad(50);
  const aspect = 16 / 9;
  // A house-shaped box: long in plan, comparatively low. The old bounding-sphere fit dollied
  // back far enough to contain the plan diagonal, which is why the model landed small.
  const house = new THREE.Box3(new THREE.Vector3(-10, 0, -6), new THREE.Vector3(10, 8, 6));
  const target = house.getCenter(new THREE.Vector3());
  const theta = Math.PI * 0.25;
  const phi = VIEW_FIT_POLAR_ANGLE;
  const radius = frameRadiusForBounds(house, target, theta, phi, verticalFov, aspect);

  const sphereRadius = house.getBoundingSphere(new THREE.Sphere()).radius;
  const limitingHalfFov = Math.min(verticalFov / 2, Math.atan(Math.tan(verticalFov / 2) * aspect));
  const oldFit = sphereRadius / Math.sin(limitingHalfFov) * 1.15;
  assert(radius < oldFit, "The exact corner fit must frame a house tighter than a bounding-sphere fit");

  // Every corner has to land inside the frustum, or "frame the whole model" does not.
  const camera = new THREE.PerspectiveCamera(50, aspect, 0.05, 5000);
  camera.position.set(
    target.x + radius * Math.sin(phi) * Math.cos(theta),
    target.y + radius * Math.cos(phi),
    target.z + radius * Math.sin(phi) * Math.sin(theta));
  camera.lookAt(target);
  camera.updateMatrixWorld(true);
  for (const x of [house.min.x, house.max.x]) {
    for (const y of [house.min.y, house.max.y]) {
      for (const z of [house.min.z, house.max.z]) {
        const ndc = new THREE.Vector3(x, y, z).project(camera);
        assert(Math.abs(ndc.x) <= 1 && Math.abs(ndc.y) <= 1,
          `Corner (${x}, ${y}, ${z}) must sit inside the framed view`);
      }
    }
  }

  // A narrow split pane needs to pull further back than a wide one for the same building —
  // which is why reset recomputes the fit instead of replaying a stored snapshot.
  const narrow = frameRadiusForBounds(house, target, theta, phi, verticalFov, 0.6);
  assert(narrow > radius, "A narrower pane must dolly further out");

  assert(frameRadiusForBounds(new THREE.Box3(new THREE.Vector3(), new THREE.Vector3()),
    new THREE.Vector3(), theta, phi, verticalFov, aspect) === VIEW_FIT_MIN_RADIUS_M,
    "A degenerate box still yields a usable dolly distance");

  // Wheel normalization: a line-mode notch and a pixel-mode flick must land in the same range.
  assert(normalizedWheelDeltaPx(3, 1) === 48, "Line-mode deltas are converted to pixels");
  assert(normalizedWheelDeltaPx(4000, 0) === WHEEL_MAX_STEP_PX,
    "A trackpad flick is clamped so one gesture cannot cross the whole zoom range");
  assert(normalizedWheelDeltaPx(-4000, 0) === -WHEEL_MAX_STEP_PX, "Clamping is symmetric");

  // Picking has to honour the same visibility the renderer does, or a hidden trade keeps
  // intercepting clicks aimed at whatever it was hiding.
  const tradeGroup = new THREE.Group();
  const layerMesh = new THREE.Mesh();
  tradeGroup.add(layerMesh);
  assert(isRenderedInScene(layerMesh), "A visible mesh under a visible group is pickable");
  tradeGroup.visible = false;
  assert(!isRenderedInScene(layerMesh), "Hiding the trade group takes its meshes out of the raycast");
  tradeGroup.visible = true;
  layerMesh.visible = false;
  assert(!isRenderedInScene(layerMesh), "Hiding one assembly layer takes just that mesh out");
}
