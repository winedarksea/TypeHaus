import * as THREE from "three";
import type { Floor, Member } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { buildFloor } from "./structure";

export function runFloorCoverTests() {
  const member = { key: "joist", category: "joist", profile: "2x8",
    p0: [0, 0], p1: [4, 3], z0_m: -0.2, z1_m: 0, length_m: 5,
    shape: "rect", width_m: 0.04, depth_m: 0.2, plies: 1 } as Member;
  const floor: Floor = { uid: "floor", tag: "F", storey: "main", direction: "x",
    subfloor: { material: "osb", thickness_m: 0.019 }, provenance: null,
    openings: [], members: [member],
    deck_outline: [[0, 0], [4, 0], [4, 3], [3, 3], [3, 2], [1, 2], [1, 3], [0, 3]],
    deck_voids: [[[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]],
  };
  const group = new THREE.Group();
  buildFloor(group, floor, [0, 0], "schematic", RESOLVED_NORDIC_PALETTE.light,
    [], new Map(), new THREE.Group());
  group.updateMatrixWorld(true);
  const hits = (x: number, y: number) => new THREE.Raycaster(
    new THREE.Vector3(x, 5, -y), new THREE.Vector3(0, -1, 0)).intersectObject(group, true);
  if (hits(2, 2.5).length) throw new Error("Decking fills resolved doorway approach cutback");
  if (hits(0.5, 0.5).length) throw new Error("Decking fills resolved deck void");
  if (!hits(3.5, 0.5).length) throw new Error("Resolved decking loses its walking surface");
  console.log("Resolved floor cover and approach cutback tests passed.");
}
