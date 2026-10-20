import * as THREE from "three";
import type { Catalog, Solid } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { buildSolid } from "./structure";

export function runWindowReturnTests() {
  const catalog = { assemblies: [], materials: [
    { tag: "return-accent", color: "#23453a", coating: true },
  ] } as unknown as Catalog;
  const solid = { uid: "return-head", tag: "return-head", category: "window_return",
    storey: "main", provenance: null,
    material: "return-accent", assembly: null, outline: [[0, 0], [1, 0], [1, 0.3], [0, 0.3]],
    voids: [], z0_m: 2, z1_m: 2.000254 } as Solid;
  const group = new THREE.Group();
  buildSolid(group, solid, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light,
    catalog, [], new Map());
  const mesh = group.children[0] as THREE.Mesh;
  mesh.geometry.computeBoundingBox();
  const thickness = mesh.geometry.boundingBox!.max.y - mesh.geometry.boundingBox!.min.y;
  if (Math.abs(thickness - 0.000254) > 1e-6) {
    throw new Error("A return's paint film must retain the engine's thickness in the live viewer");
  }
  const material = mesh.material as THREE.MeshStandardMaterial;
  if (material.color.getHexString() !== "23453a") {
    throw new Error("Return paint must use its inherited catalog color");
  }
  console.log("Window return tests passed.");
}
