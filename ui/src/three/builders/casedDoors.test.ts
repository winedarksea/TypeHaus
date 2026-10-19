import * as THREE from "three";
import fixtures from "./casedDoorFixtures.json";
import type { DoorOperation, Opening, Wall } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { categoryColor } from "../members";
import { buildOpening } from "./openings";

export function runCasedDoorTests() {
  const near = (a: number, b: number) => Math.abs(a - b) < 0.000001;
  for (const fixture of fixtures) {
    const opening = fixture.opening as unknown as Opening;
    const group = new THREE.Group(), picks: THREE.Mesh[] = [], byUid = new Map<string, THREE.Material[]>();
    buildOpening(group, opening, fixture.wall as unknown as Wall, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light,
      { operation: fixture.operation as DoorOperation }, picks, byUid);
    // Python groups each named part; the viewer's construction order is liner, leaf, stop,
    // hardware. Both fixtures pin every box, including levers and the pocket's open slot.
    const meshes = group.children as THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>[];
    if (meshes.length !== fixture.boxes.length) throw new Error(`${fixture.name}: part count`);
    const remaining = [...meshes];
    for (const expected of fixture.boxes) {
      const index = remaining.findIndex(mesh => {
        const b = new THREE.Box3().setFromObject(mesh);
        return [...b.min.toArray(), ...b.max.toArray()].every((n, i) => near(n, expected.bounds[i]));
      });
      if (index < 0) throw new Error(`${fixture.name}: missing ${expected.part} bounds`);
      const mesh = remaining.splice(index, 1)[0];
      const color = new THREE.Color(categoryColor(expected.finish));
      if (["door_frame", "door_leaf"].includes(expected.finish)
        && !mesh.material.color.toArray().every((n, i) => near(n, expected.color[i]))) {
        throw new Error(`${fixture.name}: GLB/viewer linear color mismatch`);
      }
      if (!mesh.material.color.equals(color)) throw new Error(`${fixture.name}: ${expected.part} finish`);
      if (!near(mesh.material.roughness, expected.surface[0]) || !near(mesh.material.metalness, expected.surface[1])) {
        throw new Error(`${fixture.name}: ${expected.part} sheen`);
      }
    }
    if (picks.length !== meshes.length || !byUid.has(opening.uid)) throw new Error("Door selection lost");
    for (const mesh of meshes) { mesh.geometry.dispose(); mesh.material.dispose(); }
  }
  const fixture = fixtures[0], opening = fixture.opening as unknown as Opening;
  const group = new THREE.Group();
  buildOpening(group, { ...opening, effective_frame_material_ref: "paint-gray", effective_leaf_material_ref: "paint-red" },
    fixture.wall as unknown as Wall, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light, {
      operation: "swing", materials: [{ tag: "paint-gray", color: "#808080" }, { tag: "paint-red", color: "#ff0000" }],
    }, [], new Map());
  const materials = group.children.map(c => (c as THREE.Mesh).material) as THREE.MeshStandardMaterial[];
  if (!near(materials[0].color.r, 0.2158605) || materials[3].color.getHexString() !== "ff0000") {
    throw new Error("Independent catalog frame/leaf colors must reach the viewer in linear light");
  }
  const wood = new THREE.Group();
  buildOpening(wood, { ...opening, effective_frame_material_ref: "oak-test", effective_leaf_material_ref: "oak-test" },
    fixture.wall as unknown as Wall, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light, {
      operation: "swing", materials: [{ tag: "oak-test", color: "#bda77c", species: "oak", finish: "solid-board" }],
    }, [], new Map());
  const plain = new THREE.Group();
  buildOpening(plain, opening, fixture.wall as unknown as Wall, [0, 0], "nordic",
    RESOLVED_NORDIC_PALETTE.light, { operation: "swing" }, [], new Map());
  for (const [index, mesh] of wood.children.entries()) {
    const actual = new THREE.Box3().setFromObject(mesh), expected = new THREE.Box3().setFromObject(plain.children[index]);
    if (![...actual.min.toArray(), ...actual.max.toArray()].every((n, i) =>
      near(n, [...expected.min.toArray(), ...expected.max.toArray()][i]))) {
      throw new Error("Wood appearance must preserve every product part's physical bounds");
    }
  }
  console.log("Cased door Python/viewer parity tests passed.");
}
