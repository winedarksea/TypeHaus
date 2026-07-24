import * as THREE from "three";
import type { FootingBedding, Opening, Wall, Model } from "../model/types";
import { buildFootingBedding, canvasObjectFallbackGeometry, compassBearingScreenDirection, earthElevation, earthOutline, earthVoids, EARTH_FALLBACK_HALF_SIZE_M, FOOTING_BEDDING_COLOR, wallLayerPieces, wholeHouseGlbAssignment } from "./Panel3D";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function wall(axis: Wall["axis"], topZ0: number | null = null, topZ1: number | null = null): Wall {
  return {
    uid: "wall", tag: "W-1", storey: "S-1", assembly: "A-1", provenance: null, axis,
    z0_m: 0, z1_m: 3, top_z0_m: topZ0, top_z1_m: topZ1, is_foundation: false,
    layers: [], members: [],
  };
}

function opening(centerAlongM: number, sillM = 0.9, heightM = 1.2, archRiseM = 0): Opening {
  return {
    uid: "opening", tag: "O-1", host: "W-1", kind: "window", is_door: false,
    provenance: null, type_ref: "WIN", width_m: 1, height_m: heightM, sill_m: sillM,
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

  const arched = wallLayerPieces(wall([[0, 0], [4, 0]]), [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [opening(2, 0, 1, 0.5)]);
  const archSpandrels = arched.filter((piece) => piece.z0_m > 0);
  assert(archSpandrels.length === 32, "Strip fallback retains a smooth arch curve for complex wall layers");
  assert(Math.max(...archSpandrels.map((piece) => piece.z0_m)) > Math.min(...archSpandrels.map((piece) => piece.z0_m)),
    "Arch soffit rises from its springlines to a visible crown");

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

  // Interior spaces punch holes in the site sheet so earth no longer bleeds up through floors.
  const withRooms = {
    storeys: [
      { tag: "L1", elevation_m: 0 },
      { tag: "L2", elevation_m: 3 },
    ],
    rooms: [
      { storey: "L1", clear_face: [[0, 0], [4, 0], [4, 3], [0, 3]] },
      { storey: "L1", clear_face: [[4, 0], [7, 0], [7, 3], [4, 3]] },
      // Upper storey stacks on the same footprint — must NOT contribute a second hole.
      { storey: "L2", clear_face: [[0, 0], [7, 0], [7, 3], [0, 3]] },
      // Degenerate ring is skipped.
      { storey: "L1", clear_face: [[1, 1], [1, 1]] },
    ],
  } as unknown as Model;
  const voids = earthVoids(withRooms);
  assert(voids.length === 2, "Only ground-storey interior spaces cut the earth sheet");
  assert(voids.every((ring) => ring.length === 4), "Each cut is the room's clear-face ring");

  assert(earthVoids({} as Model).length === 0, "No rooms → no earth cuts (solid sheet)");
}

export function runFootingBeddingGeometryTests() {
  const bedding = {
    uid: "FB-1", tag: "FB-1", storey: "L1", host_footing: "F-1",
    outline: [[0, 0], [3, 0], [3, 1], [0, 1]], z0_m: -1.2, z1_m: -0.9,
    aggregate: "washed-stone", geotextile: true, drain_tile: true, provenance: null,
  } as FootingBedding;
  const group = new THREE.Group();
  buildFootingBedding(group, bedding, [0, 0], "schematic");
  const meshes = group.children.filter((child): child is THREE.Mesh => child instanceof THREE.Mesh);
  assert(meshes.length === 1, "Footing bedding renders one gravel prism (schematic omits the edge overlay)");
  const box = new THREE.Box3().setFromObject(meshes[0]);
  assert(Math.abs(box.min.y - -1.2) < 1e-6 && Math.abs(box.max.y - -0.9) < 1e-6,
    "Gravel bed spans the authored undercut below the footing underside");
  assert((meshes[0].material as THREE.MeshStandardMaterial).color.getHex() === FOOTING_BEDDING_COLOR,
    "Gravel bed uses the aggregate colour, not concrete grey");

  // Nordic mode adds a faceted edge overlay for legibility.
  const nordic = new THREE.Group();
  buildFootingBedding(nordic, bedding, [0, 0], "nordic");
  assert(nordic.children.some((child) => child instanceof THREE.LineSegments),
    "Nordic footing bedding gains an edge overlay");

  const degenerate = new THREE.Group();
  buildFootingBedding(degenerate, { ...bedding, z1_m: -1.2 } as FootingBedding, [0, 0], "schematic");
  assert(degenerate.children.length === 0, "Zero-thickness bedding produces no geometry");
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
}
