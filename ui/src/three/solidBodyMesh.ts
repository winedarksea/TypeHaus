import * as THREE from "three";
import type { Solid } from "../model/types";
import { projectPointToScene, type PlanCenter } from "./planGeometry";

/** Draw the engine's dimensioned connector mesh; centring/swizzle are view transforms only. */
export function createSolidBodyMesh(solid: Solid, center: PlanCenter): THREE.BufferGeometry | null {
  if (!solid.body_mesh) return null;
  const positions: number[] = [];
  // Duplicate per triangle so folded sheet steel keeps crisp flange and punched-hole edges.
  for (const triangle of solid.body_mesh.triangles) {
    for (const index of triangle) {
      const [x, y, z] = solid.body_mesh.positions[index];
      const point = projectPointToScene([x, y], z, center);
      positions.push(point.x, point.y, point.z);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}
