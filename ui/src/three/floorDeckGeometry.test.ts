import type { Floor } from "../model/types";
import { createFloorDeckGeometry } from "./floorDeckGeometry";

export function runFloorDeckGeometryTests() {
  const assert = (condition: boolean, message: string) => { if (!condition) throw new Error(message); };
  const floor = { uid: "F", tag: "F", storey: "second", direction: "x", provenance: null,
    deck_outline: [[10, 20], [12, 20], [12, 24], [10, 24]], deck_voids: [], openings: [],
    subfloor: { material: "aluminum-deck", thickness_m: 0.04 },
    members: [{ p0: [10, 20], p1: [12, 20], z1_m: 3 }], deck_z0_m: 3,
    deck_plane: { origin: [10, 20], lift_at_origin_m: 0, gradient: [0, 1/48] },
  } as unknown as Floor;
  const geometry = createFloorDeckGeometry(floor, [10, 20])!;
  const positions = geometry.getAttribute("position");
  for (let i = 0; i < positions.count; i++) {
    const rise = -positions.getZ(i)/48;
    const height = positions.getY(i) - rise;
    assert(Math.min(Math.abs(height - 3), Math.abs(height - 3.04)) < 1e-6,
      "Deck vertices must follow the engine plane while keeping their sheet thickness");
  }
  const legacy = createFloorDeckGeometry({ ...floor, deck_plane: undefined, deck_z0_m: undefined }, [10, 20])!;
  legacy.computeBoundingBox();
  assert(Math.abs(legacy.boundingBox!.min.y - 3) < 1e-6, "Legacy floors keep their member-top datum");
  assert(Math.abs(legacy.boundingBox!.max.y - 3.04) < 1e-6, "Legacy floors keep their thickness");
  assert(createFloorDeckGeometry({ ...floor, subfloor: null }, [10, 20]) === null,
    "A framing-only floor has no walking sheet");
  geometry.dispose(); legacy.dispose();
}
