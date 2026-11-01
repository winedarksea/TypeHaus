// The viewer draws an opening's served parts as served: same bounds, the GLB's finishes.
import * as THREE from "three";
import fixtures from "./casedDoorFixtures.json";
import type { Opening, OpeningPart, Wall } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { categoryColor } from "../members";
import { buildOpening } from "./openings";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const near = (a: number, b: number) => Math.abs(a - b) < 1e-6;
const boundsOf = (object: THREE.Object3D) => {
  const box = new THREE.Box3().setFromObject(object);
  return [...box.min.toArray(), ...box.max.toArray()];
};

/** A fixture box, pinned by test_cased_door_products.py in scene (x, z, -y), as a served part. */
function servedPart(part: string, finish: string, bounds: number[]): OpeningPart {
  const [x0, z0, sy0, x1, z1, sy1] = bounds, y0 = -sy1, y1 = -sy0;
  return { key: part, material_key: finish,
    solids: [{ ring: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], z0_m: z0, z1_m: z1 }] };
}

// Called by scripts/run-geometry-tests.mjs.
export function runOpeningPartTests() {
  for (const fixture of fixtures) {
    const opening = { ...fixture.opening, opening_parts: fixture.boxes.map(box =>
      servedPart(box.part, box.finish, box.bounds)) } as unknown as Opening;
    const group = new THREE.Group(), picks: THREE.Mesh[] = [];
    const byUid = new Map<string, THREE.Material[]>();
    buildOpening(group, opening, fixture.wall as unknown as Wall, [0, 0], "nordic",
      RESOLVED_NORDIC_PALETTE.light, {}, picks, byUid);
    const meshes = group.children as THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>[];
    assert(meshes.length === fixture.boxes.length, `${fixture.name}: part count`);
    for (const [index, expected] of fixture.boxes.entries()) {
      const mesh = meshes[index];
      assert(boundsOf(mesh).every((n, i) => near(n, expected.bounds[i])),
        `${fixture.name}: ${expected.part} bounds`);
      assert(mesh.material.color.equals(new THREE.Color(categoryColor(expected.finish))),
        `${fixture.name}: ${expected.part} finish`);
      if (["door_frame", "door_leaf"].includes(expected.finish)) {
        assert(mesh.material.color.toArray().every((n, i) => near(n, expected.color[i])),
          `${fixture.name}: GLB/viewer linear color mismatch`);
      }
      assert(near(mesh.material.roughness, expected.surface[0])
        && near(mesh.material.metalness, expected.surface[1]), `${fixture.name}: ${expected.part} sheen`);
    }
    assert(picks.length === meshes.length && byUid.has(opening.uid), "Door selection lost");
  }

  // Catalog refs: independent frame and leaf colours, in linear light; wood keeps the bounds.
  const fixture = fixtures[0];
  const withRefs = (frame: string, leaf: string) => ({ ...fixture.opening,
    opening_parts: fixture.boxes.map(box => ({ ...servedPart(box.part, box.finish, box.bounds),
      material_ref: box.part === "leaf" ? leaf : box.part === "hardware" ? null : frame })),
  }) as unknown as Opening;
  const painted = new THREE.Group();
  buildOpening(painted, withRefs("paint-gray", "paint-red"), fixture.wall as unknown as Wall,
    [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light, { materials: [
      { tag: "paint-gray", color: "#808080" }, { tag: "paint-red", color: "#ff0000" }] },
    [], new Map());
  const colorOf = (part: string) => ((painted.children[fixture.boxes.findIndex(box =>
    box.part === part)] as THREE.Mesh).material as THREE.MeshStandardMaterial).color;
  assert(near(colorOf("jamb_liner").r, 0.2158605) && colorOf("leaf").getHexString() === "ff0000",
    "Independent catalog frame/leaf colors must reach the viewer in linear light");
  const wood = new THREE.Group();
  buildOpening(wood, withRefs("oak-test", "oak-test"), fixture.wall as unknown as Wall, [0, 0],
    "nordic", RESOLVED_NORDIC_PALETTE.light, { materials: [
      { tag: "oak-test", color: "#bda77c", species: "oak", finish: "solid-board" }] },
    [], new Map());
  for (const [index, mesh] of wood.children.entries()) {
    assert(boundsOf(mesh).every((n, i) => near(n, fixture.boxes[index].bounds[i])),
      "Wood appearance must preserve every product part's physical bounds");
  }

  // The entry door's two painted faces and its viewer, placed by the engine on the leaf.
  const wall = { uid: "wall", tag: "W-1", axis: [[0, 0], [4, 0]], layers: [] } as unknown as Wall;
  const door = { uid: "entry", tag: "D-1", host: "W-1", kind: "door", is_door: true,
    width_m: 0.9, height_m: 2.1, sill_m: 0, center_along_m: 2, arch_rise_m: 0,
    opening_parts: [
      { key: "leaf:exterior", material_key: "door_leaf", material_ref: "door-black",
        solids: [{ ring: [[1.6, 0], [2.4, 0], [2.4, 0.022], [1.6, 0.022]], z0_m: 0.02, z1_m: 2 }] },
      { key: "leaf:interior", material_key: "door_leaf", material_ref: "door-white",
        solids: [{ ring: [[1.6, -0.022], [2.4, -0.022], [2.4, 0], [1.6, 0]], z0_m: 0.02, z1_m: 2 }] },
      { key: "hardware:viewer", material_key: "door_hardware",
        solids: [{ ring: [[1.97, 0.022], [2.03, 0.022], [2.03, 0.035], [1.97, 0.035]],
          z0_m: 1.514, z1_m: 1.574 }] },
      { key: "glass", material_key: "glass", material_ref: "door-black",
        solids: [{ ring: [[1.7, -0.005], [2.3, -0.005], [2.3, 0.005], [1.7, 0.005]],
          z0_m: 1.2, z1_m: 1.8 }] },
    ] } as unknown as Opening;
  const entry = new THREE.Group(), entryPicks: THREE.Mesh[] = [];
  buildOpening(entry, door, wall, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light,
    { materials: [{ tag: "door-black", color: "#181818" }, { tag: "door-white", color: "#f4f3ee" }] },
    entryPicks, new Map());
  const meshes = entry.children as THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>[];
  assert(meshes.length === 4 && entryPicks.length === 4, "Every served part is drawn and selectable");
  assert(meshes[0].material.color.getHexString() === "181818"
    && meshes[1].material.color.getHexString() === "f4f3ee",
  "The entry keeps independent black and white faces");
  const viewer = new THREE.Box3().setFromObject(meshes[2]);
  assert(near(viewer.getCenter(new THREE.Vector3()).y, 1.544), "The viewer stays where it was served");
  assert(meshes[2].material.metalness === 0.8, "Served hardware keeps its metal finish");
  assert(meshes[3].material.transparent && meshes[3].material.opacity === 0.48,
    "A glazed leaf stays glass whatever finish its catalog names");
  assert(["hardware:viewer", "glass:0"].every((piece, i) => meshes[i + 2].userData.piece === piece),
    "Pieces name the served part");
  console.log("Opening served-part tests passed.");
}
