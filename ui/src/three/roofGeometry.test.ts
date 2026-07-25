import * as THREE from "three";
import type { Roof } from "../model/types";
import { boundaryEdges, layerInsetRect, roofOffsetter, roofPlaneTriangles, roofPlaneZ } from "./roofGeometry";

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

  // --- per-layer edge setbacks (golden eave detail) -------------------------------

  // A roof without setbacks keeps the uniform footprint (optional fields tolerated).
  if (roof.layer_edge_setbacks !== undefined && roof.layer_edge_setbacks.length) {
    throw new Error("Test roof must start with no setbacks");
  }

  // Inset-rect vertices must stay z-continuous with the base plane: every vertex of the
  // inset triangles lies exactly on the plane of the corresponding full-footprint plane.
  const entry = { layer: "deck", west: 0.12, east: 0.12, south: 0.12, north: 0.12 };
  const insetTriangles = roofPlaneTriangles(roof, layerInsetRect(roof, entry, 0));
  if (insetTriangles.length !== 4) {
    throw new Error(`Expected 4 inset gable triangles, got ${insetTriangles.length}`);
  }
  const basePlanes = triangles.map((tri) => new THREE.Plane().setFromCoplanarPoints(
    new THREE.Vector3(...tri[0]), new THREE.Vector3(...tri[1]), new THREE.Vector3(...tri[2]),
  ));
  for (const tri of insetTriangles) {
    for (const vertex of tri) {
      const point = new THREE.Vector3(...vertex);
      const onBase = basePlanes.some((plane) => Math.abs(plane.distanceToPoint(point)) < 1e-9);
      if (!onBase) throw new Error(`Inset vertex ${vertex} left the base roof plane`);
      if (Math.abs(roofPlaneZ(roof, vertex[0], vertex[1]) - vertex[2]) > 1e-9) {
        throw new Error("Inset vertex z disagrees with roofPlaneZ");
      }
    }
  }

  // Eave-drift compensation: a layer based `d` above the deck insets its eave edges an
  // extra d*sin(theta) so the mitered offsetter lands the edge back at the serialized
  // plan position. Ridge runs "x" here, so south/north are the eaves; the rakes don't move.
  const baseOffset = 0.2;
  const pitch = (roof.ridge_z_m - roof.eave_z_m) / ((8 - 0) / 2); // rise over half span
  const drift = (baseOffset * pitch) / Math.sqrt(1 + pitch * pitch);
  const [minx, maxx, miny, maxy] = layerInsetRect(roof, entry, baseOffset);
  if (Math.abs(miny - (0.12 + drift)) > 1e-9 || Math.abs(8 - maxy - (0.12 + drift)) > 1e-9) {
    throw new Error("Eave insets missing the offset-drift compensation");
  }
  if (Math.abs(minx - 0.12) > 1e-9 || Math.abs(12 - maxx - 0.12) > 1e-9) {
    throw new Error("Rake insets must not drift");
  }

  // After the mitered offset, the drift-compensated eave edge lands back at the
  // serialized plan setback (this is the parity contract with emit/gltf/emitter.py).
  const driftTriangles = roofPlaneTriangles(roof, layerInsetRect(roof, entry, baseOffset));
  const driftOffset = roofOffsetter(driftTriangles);
  const eaveVertex = driftTriangles
    .flat()
    .find((v) => Math.abs(v[1] - miny) < 1e-9);
  if (!eaveVertex) throw new Error("No eave vertex found on the inset rect");
  const planY = driftOffset(eaveVertex, baseOffset)[0][1];
  if (Math.abs(planY - 0.12) > 1e-6) {
    throw new Error(`Offset eave edge landed at y=${planY}, expected the 0.12 clip face`);
  }
}
