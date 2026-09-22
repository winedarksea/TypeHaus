import * as THREE from "three";
import type { PlantInstance, PlantModel } from "../../model/types";
import {
  buildPlants, composePlantMatrix, instancedPlantUids, plantPartGeometry, resolvePlantPickUid,
  SHADE_BASE,
} from "./plants";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// A one-leaf "prototype": a unit-height triangle, two-sided, plus a closed-ish bloom part.
const MODEL: PlantModel = {
  ref: "PT-X#0", type_ref: "PT-X", form: "perennial", height: 1, quantum: 0.001,
  colors: { foliage: "#6f8c4a", bloom: "#efe08a", stem: "#3d4d29", fruit: "#6f8c4a" },
  parts: [
    { role: "foliage", two_sided: true, positions: [0, 0, 0, 500, 0, 0, 0, 0, 1000],
      indices: [0, 1, 2] },
    { role: "bloom", two_sided: false, positions: [0, 0, 900, 100, 0, 900, 0, 100, 1000],
      indices: [0, 1, 2] },
  ],
};

function plant(uid: string, x: number, storey = "S"): PlantInstance {
  return {
    uid, tag: uid, storey, type_ref: "PT-X", model: "PT-X#0", x, y: 2, z: -0.5,
    rotation: Math.PI / 2, scale: [0.4, 0.4, 0.6], source: "PB", accent: false,
  };
}

export function runPlantBuilderTests() {
  // Geometry: plan (x, y, z) → scene (x, z, -y), quantised, shaded root to tip.
  const geometry = plantPartGeometry(MODEL, MODEL.parts[0], true);
  const position = geometry.getAttribute("position");
  assert(Math.abs(position.getX(1) - 0.5) < 1e-9, "x keeps its sign and scale");
  assert(Math.abs(position.getY(2) - 1) < 1e-9, "plan z is scene y");
  const color = geometry.getAttribute("color");
  assert(Math.abs(color.getX(0) - SHADE_BASE) < 1e-6 && Math.abs(color.getX(2) - 1) < 1e-6,
    "root is SHADE_BASE, tip is 1");
  assert(geometry.getIndex()?.count === 3 && geometry.getAttribute("normal"), "indexed, normals");

  // Placement: a quarter turn about plan z carries plan +x to plan +y (scene -z).
  const m = composePlantMatrix(new THREE.Matrix4(), plant("a", 3), [1, 1]);
  const tip = new THREE.Vector3(1, 0, 0).applyMatrix4(m);
  assert(Math.abs(tip.x - 2) < 1e-9 && Math.abs(tip.y + 0.5) < 1e-9, "origin at (x-cx, z)");
  assert(Math.abs(tip.z - (-(2 - 1) - 0.4)) < 1e-9, "plan +x turned to plan +y, scaled by spread");
  const top = new THREE.Vector3(0, 1, 0).applyMatrix4(m);
  assert(Math.abs(top.y - (-0.5 + 0.6)) < 1e-9, "unit height scales to the plant's height");

  // Instancing: one InstancedMesh per part, one instance per plant, picks resolve to uids.
  const plants = [plant("a", 0), plant("b", 1), plant("c", 2)];
  const parent = new THREE.Group();
  const picks: THREE.Mesh[] = [];
  const meshes = buildPlants(parent, plants, [MODEL], [0, 0], "nordic", picks);
  assert(meshes.length === 2 && parent.children.length === 2, "one mesh per prototype part");
  assert(meshes.every((mesh) => mesh.count === 3), "one instance per plant");
  assert(picks.length === 2, "every part is pickable");
  assert(resolvePlantPickUid(meshes[0], 1) === "b", "instance 1 is plant b");
  assert(resolvePlantPickUid(meshes[1], 2) === "c", "every part carries the uids");
  assert(resolvePlantPickUid(new THREE.Mesh(), 0) === null, "a plain mesh is not a plant");
  const leaf = meshes[0].material as THREE.MeshStandardMaterial;
  assert(leaf.side === THREE.DoubleSide && leaf.vertexColors, "a leaf reads from behind");
  assert((meshes[1].material as THREE.MeshStandardMaterial).side === THREE.FrontSide,
    "a closed part is single-sided");
  assert(meshes.every((mesh) => mesh.castShadow && !mesh.receiveShadow), "cast, not receive");

  // Schematic: flat colour, no gradient.
  const flat = buildPlants(new THREE.Group(), plants, [MODEL], [0, 0], "schematic", []);
  assert(!flat[0].geometry.getAttribute("color"), "no shade attribute in schematic");

  // Only plants whose prototype arrived are instanced; the rest keep their prisms.
  const orphan = { ...plant("d", 0), model: "PT-Y#0" };
  const uids = instancedPlantUids([...plants, orphan], [MODEL]);
  assert(uids.has("a") && !uids.has("d"), "an unknown prototype is not instanced");
  assert(instancedPlantUids(undefined, undefined).size === 0, "an older model.json draws prisms");
  console.log("Plant builder tests passed.");
}
