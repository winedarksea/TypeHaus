import * as THREE from "three";
import type { AssemblySpec, Roof } from "../model/types";
import type { ProjectVertex } from "./planGeometry";

// The roof surface as geometry: the sloped planes from footprint/eave_z/ridge_z (mirroring
// emit/gltf/emitter.py's _add_roof), plus what is needed to thicken them into the authored
// assembly. `Panel3D.buildRoof` turns these into meshes.

export type RoofVertex = [x: number, y: number, z: number];

export function roofPlaneTriangles(roof: Roof): RoofVertex[][] {
  const xs = roof.footprint.map((p) => p[0]);
  const ys = roof.footprint.map((p) => p[1]);
  const minx = Math.min(...xs), maxx = Math.max(...xs);
  const miny = Math.min(...ys), maxy = Math.max(...ys);
  const eave = roof.eave_z_m;
  const ridge = roof.ridge_z_m;
  const v = (x: number, y: number, z: number): RoofVertex => [x, y, z];
  const flat: RoofVertex[] = roof.form === "shed"
    ? (roof.ridge_direction === "x"
      ? [v(minx, miny, eave), v(maxx, miny, eave), v(maxx, maxy, ridge),
         v(minx, miny, eave), v(maxx, maxy, ridge), v(minx, maxy, ridge)]
      : [v(minx, miny, eave), v(maxx, miny, ridge), v(maxx, maxy, ridge),
         v(minx, miny, eave), v(maxx, maxy, ridge), v(minx, maxy, eave)])
    : roof.ridge_direction === "x"
      ? (() => {
        const mid = (miny + maxy) / 2;
        const ra = v(minx, mid, ridge), rb = v(maxx, mid, ridge);
        return [v(minx, miny, eave), v(maxx, miny, eave), rb,
          v(minx, miny, eave), rb, ra,
          ra, rb, v(maxx, maxy, eave),
          ra, v(maxx, maxy, eave), v(minx, maxy, eave)];
      })()
      : (() => {
        const mid = (minx + maxx) / 2;
        const ra = v(mid, miny, ridge), rb = v(mid, maxy, ridge);
        return [v(minx, miny, eave), ra, rb,
          v(minx, miny, eave), rb, v(minx, maxy, eave),
          ra, v(maxx, miny, eave), v(maxx, maxy, eave),
          ra, v(maxx, maxy, eave), rb];
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

