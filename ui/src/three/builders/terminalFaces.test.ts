import * as THREE from "three";
import type { CanvasObject, CanvasObjectType } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { buildCanvasObject } from "./site";

export function runTerminalFaceTests() {
  const item = {
    uid: "TERMINAL", position_m: [99, 99], domain: "mechanical", rotation: 90,
    // Delta-coded vertices: (1,2,3), (2,2,3), (1,3,3).
    body_mesh: { quantum: 1, positions: [1, 2, 3, 1, 0, 0, -1, 1, 0],
      triangles: [0, 1, 1] },
  } as CanvasObject;
  const type = { footprint_m: [5, 5], height_m: 5,
    model_parts: [{ center: [0, 0, 0], size: [5, 5, 5], color: "#ffffff" }],
  } as CanvasObjectType;
  const group = new THREE.Group();
  const picks: THREE.Mesh[] = [];
  const byUid = new Map<string, THREE.Material[]>();
  const mesh = buildCanvasObject(group, item, type, [1, 2], "schematic",
    RESOLVED_NORDIC_PALETTE.light, 99, picks, byUid) as THREE.Mesh;
  const position = mesh.geometry.getAttribute("position");
  const expected = [[0, 3, 0], [1, 3, 0], [0, 3, -1]];
  for (let i = 0; i < expected.length; i++) {
    if (position.getX(i) !== expected[i][0] || position.getY(i) !== expected[i][1]
      || position.getZ(i) !== expected[i][2]) {
      throw new Error("Terminal mesh must use resolved coordinates without a second placement");
    }
  }
  if (group.children.length !== 1 || picks[0] !== mesh
    || mesh.userData.uid !== item.uid || mesh.userData.selectionKind !== "canvas_object"
    || !byUid.has(item.uid)) {
    throw new Error("Terminal geometry must retain its canvas selection identity");
  }
  mesh.geometry.dispose();
  (mesh.material as THREE.Material).dispose();
  console.log("Terminal face tests passed.");
}
