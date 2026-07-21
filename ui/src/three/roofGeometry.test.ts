import * as THREE from "three";
import type { Roof } from "../model/types";
import { boundaryEdges, roofOffsetter, roofPlaneTriangles } from "./roofGeometry";

function gableRoof(): Roof {
  return {
    uid: "R", tag: "RF-TEST", storey: "attic", form: "gable",
    footprint: [[0, 0], [12, 0], [12, 8], [0, 8]],
    eave_z_m: 6, ridge_z_m: 8, ridge_direction: "x",
    assembly: "TEST_ROOF", surface_area_m2: 100, members: [], provenance: null,
  };
}

// Called by scripts/run-geometry-tests.mjs.
export function runRoofGeometryTests() {
  const roof = gableRoof();
  const triangles = roofPlaneTriangles(roof);
  if (triangles.length !== 4) throw new Error(`Expected 4 gable triangles, got ${triangles.length}`);

  // A gable's two planes share the ridge, so only the eaves and rakes are open edges.
  const perimeter = boundaryEdges(triangles);
  if (perimeter.length !== 6) {
    throw new Error(`Expected 6 boundary edges (2 eaves + 4 rake halves), got ${perimeter.length}`);
  }

  // Every layer must sit its own thickness above the deck measured *perpendicular* to the
  // slope, or the stack reads thin at the eave and thick at the rake.
  const offsetAt = roofOffsetter(triangles);
  const thickness = 0.1;
  for (const tri of triangles) {
    const a = new THREE.Vector3(...tri[0]);
    const plane = new THREE.Plane().setFromCoplanarPoints(
      a, new THREE.Vector3(...tri[1]), new THREE.Vector3(...tri[2]),
    );
    for (const vertex of tri) {
      const [[x, y], z] = offsetAt(vertex, thickness);
      const distance = Math.abs(plane.distanceToPoint(new THREE.Vector3(x, y, z)));
      if (Math.abs(distance - thickness) > 1e-6) {
        throw new Error(`Offset vertex is ${distance} from the deck, expected ${thickness}`);
      }
    }
  }

  // The offset must go up and out, never back through the rafters.
  const [, elevation] = offsetAt(triangles[0][0], thickness);
  if (elevation <= triangles[0][0][2]) throw new Error("Roof layers stacked downward");
}
