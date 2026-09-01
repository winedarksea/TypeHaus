import * as THREE from "three";
import type { AssemblySpec, Roof, RoofLayerSetback } from "../model/types";
import { panelTileSizeM, SEAM_PROFILE, type MetalPanelProfile } from "./materials";
import { projectScenePointToPlan, type PlanCenter, type ProjectVertex } from "./planGeometry";

// The roof surface as geometry: the sloped planes from footprint/eave_z/ridge_z (mirroring
// emit/gltf/emitter.py's _add_roof), plus what is needed to thicken them into the authored
// assembly. `Panel3D.buildRoof` turns these into meshes.

export type RoofVertex = [x: number, y: number, z: number];

/**
 * Base roof-plane elevation at a plan point (emitter.py `_roof_plane_z`): unclamped, so a
 * slightly-outset layer edge (negative setback) lands just below the eave plane.
 */
export function roofPlaneZ(roof: Roof, x: number, y: number): number {
  const xs = roof.footprint.map((p) => p[0]);
  const ys = roof.footprint.map((p) => p[1]);
  const coordinate = roof.ridge_direction === "x" ? y : x;
  const low = roof.ridge_direction === "x" ? Math.min(...ys) : Math.min(...xs);
  const high = roof.ridge_direction === "x" ? Math.max(...ys) : Math.max(...xs);
  const span = high - low;
  if (span <= 1e-9) return roof.eave_z_m;
  if (roof.form === "shed") {
    return roof.eave_z_m + ((coordinate - low) / span) * (roof.ridge_z_m - roof.eave_z_m);
  }
  const midpoint = (low + high) / 2;
  const ratio = 1 - Math.abs(coordinate - midpoint) / (span / 2);
  return roof.eave_z_m + ratio * (roof.ridge_z_m - roof.eave_z_m);
}

export type RoofRect = [minx: number, maxx: number, miny: number, maxy: number];

/**
 * Per-layer inset rectangle from serialized edge setbacks + eave drift compensation
 * (emitter.py `_layer_inset_rect`). Serialized setbacks are final *plan* positions;
 * offsetting a layer perpendicular to the slope drifts its eave edge down-slope (outward)
 * by `baseOffset * sin(theta)`, so that drift is added to the eave-edge insets here.
 * Rake edges run parallel to the fall line and have no drift.
 */
export function layerInsetRect(roof: Roof, entry: RoofLayerSetback, baseOffset: number): RoofRect {
  const xs = roof.footprint.map((p) => p[0]);
  const ys = roof.footprint.map((p) => p[1]);
  const minx = Math.min(...xs), maxx = Math.max(...xs);
  const miny = Math.min(...ys), maxy = Math.max(...ys);
  let west = entry.west ?? 0, east = entry.east ?? 0;
  let south = entry.south ?? 0, north = entry.north ?? 0;
  const span = roof.ridge_direction === "x" ? maxy - miny : maxx - minx;
  const run = roof.form === "shed" ? span : span / 2;
  const rise = roof.ridge_z_m - roof.eave_z_m;
  if (run > 1e-9 && rise > 1e-9 && baseOffset !== 0) {
    const pitch = rise / run;
    const drift = (baseOffset * pitch) / Math.sqrt(1 + pitch * pitch);
    if (roof.form === "shed") {
      // One plane: the low (eave) edge drifts outward, the high edge inward.
      if (roof.ridge_direction === "x") { south += drift; north -= drift; }
      else { west += drift; east -= drift; }
    } else if (roof.ridge_direction === "x") { south += drift; north += drift; }
    else { west += drift; east += drift; }
  }
  return [minx + west, maxx - east, miny + south, maxy - north];
}

/**
 * The sloped gable/shed planes as plan-space triangles. `rect` builds them over a
 * per-layer inset rectangle instead of the footprint; vertex z is always evaluated from
 * the *base* plane (`roofPlaneZ`), so inset edges land at the right height and the ridge
 * line stays at the footprint's midline.
 */
export function roofPlaneTriangles(roof: Roof, rect?: RoofRect): RoofVertex[][] {
  const xs = roof.footprint.map((p) => p[0]);
  const ys = roof.footprint.map((p) => p[1]);
  const fminx = Math.min(...xs), fmaxx = Math.max(...xs);
  const fminy = Math.min(...ys), fmaxy = Math.max(...ys);
  const [minx, maxx, miny, maxy] = rect ?? [fminx, fmaxx, fminy, fmaxy];
  const v = (x: number, y: number): RoofVertex => [x, y, roofPlaneZ(roof, x, y)];
  const flat: RoofVertex[] = roof.form === "shed"
    ? [v(minx, miny), v(maxx, miny), v(maxx, maxy),
       v(minx, miny), v(maxx, maxy), v(minx, maxy)]
    : roof.ridge_direction === "x"
      ? (() => {
        const mid = (fminy + fmaxy) / 2;
        const ra = v(minx, mid), rb = v(maxx, mid);
        return [v(minx, miny), v(maxx, miny), rb,
          v(minx, miny), rb, ra,
          ra, rb, v(maxx, maxy),
          ra, v(maxx, maxy), v(minx, maxy)];
      })()
      : (() => {
        const mid = (fminx + fmaxx) / 2;
        const ra = v(mid, miny), rb = v(mid, maxy);
        return [v(minx, miny), ra, rb,
          v(minx, miny), rb, v(minx, maxy),
          ra, v(maxx, miny), v(maxx, maxy),
          ra, v(maxx, maxy), rb];
      })();
  const triangles: RoofVertex[][] = [];
  for (let i = 0; i < flat.length; i += 3) triangles.push([flat[i], flat[i + 1], flat[i + 2]]);
  return triangles;
}

const vertexKey = (v: RoofVertex) => v.map((n) => n.toFixed(4)).join(",");

function faceNormal(tri: RoofVertex[]): THREE.Vector3 {
  const a = new THREE.Vector3(...tri[0]);
  const ab = new THREE.Vector3(...tri[1]).sub(a);
  const ac = new THREE.Vector3(...tri[2]).sub(a);
  const n = ab.cross(ac).normalize();
  return n.z < 0 ? n.negate() : n; // always the up-slope side
}

/**
 * Offset the whole roof surface perpendicular to its slope. Vertices on the ridge belong
 * to two planes, so they move along the averaged normal, lengthened by 1/cos of the half
 * angle — the standard miter — which keeps every layer at its true thickness measured
 * perpendicular to the deck instead of opening a wedge at the ridge.
 */
export function roofOffsetter(triangles: RoofVertex[][]) {
  const normals = triangles.map(faceNormal);
  // Average over distinct *planes*, not triangles: a ridge vertex shared by two triangles
  // of one plane and one of the other would otherwise miter off-centre.
  const planes = new Map<string, Map<string, THREE.Vector3>>();
  triangles.forEach((tri, i) => {
    for (const v of tri) {
      const key = vertexKey(v);
      const perVertex = planes.get(key) ?? new Map<string, THREE.Vector3>();
      perVertex.set(normals[i].toArray().map((n) => n.toFixed(5)).join(","), normals[i]);
      planes.set(key, perVertex);
    }
  });
  const miters = new Map<string, THREE.Vector3>();
  for (const [key, perVertex] of planes) {
    const faces = [...perVertex.values()];
    const dir = faces.reduce((sum, n) => sum.add(n), new THREE.Vector3()).normalize();
    miters.set(key, dir.multiplyScalar(1 / Math.max(0.2, dir.dot(faces[0]))));
  }
  return (v: RoofVertex, distance: number): ProjectVertex => {
    const m = miters.get(vertexKey(v))!;
    return [[v[0] + m.x * distance, v[1] + m.y * distance], v[2] + m.z * distance];
  };
}

/** Edges used by exactly one triangle — the eave and rake perimeter to close. */
export function boundaryEdges(triangles: RoofVertex[][]): [RoofVertex, RoofVertex][] {
  const counts = new Map<string, { edge: [RoofVertex, RoofVertex]; count: number }>();
  for (const tri of triangles) {
    for (let i = 0; i < 3; i++) {
      const a = tri[i], b = tri[(i + 1) % 3];
      const key = [vertexKey(a), vertexKey(b)].sort().join("|");
      const entry = counts.get(key);
      if (entry) entry.count++;
      else counts.set(key, { edge: [a, b], count: 1 });
    }
  }
  return [...counts.values()].filter((e) => e.count === 1).map((e) => e.edge);
}

/** The layers that sit above the rafters — everything the sky actually sees. */
export function aboveStructureLayers(assembly: AssemblySpec | undefined) {
  if (!assembly) return [];
  let last = -1;
  assembly.layers.forEach((ly, i) => { if (ly.function === "structure") last = i; });
  return assembly.layers.slice(last + 1);
}


/**
 * Give a roof plane's metal-panel map an architectural coordinate frame, the way
 * `applyStandingSeamWallUv` gives a wall one.
 *
 * A roof plane is built by `createProjectedSurfaceGeometry`, which sets position and normal
 * and NOTHING ELSE — no `uv` attribute at all. A normal map on a geometry with no UVs samples
 * one texel forever, so every roof in the model rendered as flat paint: the seam was there in
 * the material and had nothing to sample against. (`createStandingSeamMaterial`'s
 * `worldSizeM` repeat could not save it either — a repeat multiplies a UV that does not
 * exist.) Fixed 2026-08-31.
 *
 * The frame is the one a roofer works in, not the one the footprint is authored in:
 *  - `u` runs ALONG THE RIDGE, because that is the axis the pans are counted across. Pans run
 *    up the slope, eave to ridge, so the seams have to be constant in the fall line and step
 *    every 16" sideways.
 *  - `v` is TRUE SLOPE DISTANCE from the ridge, not the plan run. A 6:12 plane is 11.8%
 *    longer than its footprint, and measuring `v` in plan would shorten the pan by exactly
 *    that much — visible where a rake band drawn at true length meets it.
 * Both are divided by the profile's tile size, so the module lands at true scale and matches
 * the wall panel and the closure bands that continue it.
 */
export function applyStandingSeamRoofUv(
  geometry: THREE.BufferGeometry,
  roof: Roof,
  center: PlanCenter,
  profile: MetalPanelProfile = SEAM_PROFILE,
): void {
  const tileM = panelTileSizeM(profile);
  const xs = roof.footprint.map((p) => p[0]);
  const ys = roof.footprint.map((p) => p[1]);
  const alongRidgeIsX = roof.ridge_direction === "x";
  const low = alongRidgeIsX ? Math.min(...ys) : Math.min(...xs);
  const high = alongRidgeIsX ? Math.max(...ys) : Math.max(...xs);
  // A shed's high edge is its "ridge"; a gable's is the midline. Either way `v` is measured
  // from there, so the two planes of a gable mirror each other and their pans meet at the
  // ridge instead of running past it out of phase.
  const ridgeCoordinate = roof.form === "shed" ? high : (low + high) / 2;
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  for (let index = 0; index < positions.count; index++) {
    const [planX, planY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    const elevation = positions.getY(index);
    const alongRidge = alongRidgeIsX ? planX : planY;
    const downSlope = (alongRidgeIsX ? planY : planX) - ridgeCoordinate;
    uv[index * 2] = alongRidge / tileM;
    uv[index * 2 + 1] = Math.hypot(downSlope, elevation - roof.ridge_z_m) / tileM;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}
