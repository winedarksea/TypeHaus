import type { Opening, Wall, Model } from "../model/types";
import { canvasObjectFallbackGeometry, earthElevation, earthOutline, EARTH_FALLBACK_HALF_SIZE_M, wallLayerPieces } from "./Panel3D";

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
  assert(archSpandrels.length === 12, "Arch head is approximated by twelve spandrel strips");
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
}

export function runCanvasObjectGeometryTests() {
  assert(canvasObjectFallbackGeometry("cylinder", 0.4, 1, 0.6).type === "CylinderGeometry",
    "Configured cylinder primitives are rendered before their GLB is ready");
  assert(canvasObjectFallbackGeometry("unsupported", 0.4, 1, 0.6).type === "BoxGeometry",
    "Unknown primitives retain the footprint-box fallback");
}
