// Curved placeable surfaces retain the engine's normals, just as the arch soffits do.
import * as THREE from "three";
import type { ModelPart } from "../model/types";

export function createModelPartMeshGeometry(mesh: NonNullable<ModelPart["mesh"]>):
  THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  const toScene = (vectors: [number, number, number][]) =>
    vectors.flatMap(([x, y, z]) => [x, z, -y]);
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(toScene(mesh.positions), 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(toScene(mesh.normals), 3));
  geometry.setIndex(mesh.triangles.flat());
  return geometry;
}
