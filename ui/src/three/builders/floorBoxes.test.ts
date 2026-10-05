import * as THREE from "three";
import type { CanvasObject, CanvasObjectType } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { buildCanvasObject } from "./site";

export function runFloorBoxTests() {
  const floorElevation = 0.025;
  const height = 6.55 * 0.0254;
  const type = {
    tag: "FLOOR-BOX", footprint_m: [0.168, 0.168], height_m: height,
  } as CanvasObjectType;
  for (const recessed of [true, false]) {
    const item = {
      uid: "FLOOR-BOX-1", position_m: [0, 0], domain: "electrical", rotation: 0,
      mount: { kind: "floor", elevation_m: 0, drop_m: null,
        recessed_into_host_surface: recessed },
    } as CanvasObject;
    const group = new THREE.Group();
    buildCanvasObject(group, item, type, [0, 0], "nordic",
      RESOLVED_NORDIC_PALETTE.light, floorElevation, [], new Map());
    group.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(group);
    const expectedBottom = floorElevation - (recessed ? height : 0);
    const expectedTop = floorElevation + (recessed ? 0 : height);
    if (Math.abs(bounds.min.y - expectedBottom) > 1e-6
      || Math.abs(bounds.max.y - expectedTop) > 1e-6) {
      throw new Error("Floor-box geometry must honor its recessed mount");
    }
  }
  console.log("Floor box tests passed.");
}
