// Curved placeable surfaces retain the engine's normals, just as the arch soffits do.
import type * as THREE from "three";
import type { PackedMesh } from "../model/types";
import { packedMeshGeometry } from "./mesh";

export function createModelPartMeshGeometry(mesh: PackedMesh): THREE.BufferGeometry {
  return packedMeshGeometry(mesh);
}
