import * as THREE from "three";
import type { SurfaceMesh } from "../model/types";
import type { PlanCenter } from "./planGeometry";

/** Swizzle only: folds and clipping are the engine's answer in both 3D paths. */
export function createSurfaceMeshGeometry(mesh: SurfaceMesh, center: PlanCenter): THREE.BufferGeometry {
  if (mesh.positions.length !== mesh.normals.length) throw new Error("Invalid surface mesh normals");
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(
    mesh.positions.flatMap(([x, y, z]) => [x - center[0], z, center[1] - y]), 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(
    mesh.normals.flatMap(([x, y, z]) => [x, z, -y]), 3));
  geometry.setIndex(mesh.triangles.flat());
  return geometry;
}
