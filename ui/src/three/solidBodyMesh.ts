import * as THREE from "three";
import type { Solid } from "../model/types";
import { decodeMesh } from "./mesh";
import type { PlanCenter } from "./planGeometry";

/** Draw the engine's dimensioned connector mesh; centring/swizzle are view transforms only. */
export function createSolidBodyMesh(solid: Solid, center: PlanCenter): THREE.BufferGeometry | null {
  if (!solid.body_mesh) return null;
  const { positions: vertices, index } = decodeMesh(solid.body_mesh, center);
  // Duplicate per triangle so folded sheet steel keeps crisp flange and punched-hole edges.
  const positions = new Float32Array(index.length * 3);
  for (let i = 0; i < index.length; i++) {
    positions.set(vertices.subarray(index[i] * 3, index[i] * 3 + 3), i * 3);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}
