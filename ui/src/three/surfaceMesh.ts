import type * as THREE from "three";
import type { SurfaceMesh } from "../model/types";
import { packedMeshGeometry } from "./mesh";
import type { PlanCenter } from "./planGeometry";

/** Swizzle only: folds and clipping are the engine's answer in both 3D paths. */
export function createSurfaceMeshGeometry(mesh: SurfaceMesh, center: PlanCenter): THREE.BufferGeometry {
  return packedMeshGeometry(mesh, center);
}
