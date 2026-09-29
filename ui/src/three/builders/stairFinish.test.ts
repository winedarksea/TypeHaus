import * as THREE from "three";
import type { Stair } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE, materialColor, type MaterialAppearance } from "../../nordic/palette";
import { buildStair } from "./structure";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runStairFinishTests() {
  const materials: MaterialAppearance[] = [
    { tag: "carpet", color: "#9c8f80", finish: "carpet-pile", finish_thickness_in: 0.5 },
  ];
  const stair = {
    uid: "ST-UID", tag: "ST-B2M", members: [],
    finish_parts: [
      { key: "tread-000:top", role: "walking", material_ref: "carpet",
        outline: [[0, 0], [1, 0], [1, 1], [0, 1]], z0_m: 1, z1_m: 1.0127 },
      { key: "riser-000:face", role: "riser", material_ref: "carpet",
        outline: [[0, 0], [1, 0], [1, 0.0127], [0, 0.0127]], z0_m: 0, z1_m: 1.0127 },
    ],
  } as unknown as Stair;
  const group = new THREE.Group();
  const picks: THREE.Mesh[] = [];
  const byUid = new Map<string, THREE.Material[]>();
  const palette = RESOLVED_NORDIC_PALETTE.light;
  buildStair(group, stair, [0, 0], "nordic", palette, picks, byUid, materials);
  assert(group.children.length === 2, "The viewer draws the tread and riser coverings");
  assert(picks.length === 2, "The coverings select their parent stair");
  for (const child of group.children) {
    assert(child instanceof THREE.Mesh, "A stair finish part is a mesh");
    const material = child.material as THREE.MeshStandardMaterial;
    assert(material.color.getHexString() === new THREE.Color(
      materialColor("carpet", palette, materials)).getHexString(),
    "The carpet gets its catalog color");
    assert(material.roughness === 1, "The carpet has the catalog pile roughness");
  }
  console.log("Stair finish tests passed.");
}
