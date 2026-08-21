import * as THREE from "three";
import type { Opening, Wall } from "../../model/types";
import { createSmoothArchedWallLayerGeometry } from "./walls";
import { wallBandShapes } from "./wallBandShape";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const IN = 0.0254;

// W-B-BRICK, the Ishtar wythe, and its two arched reveals — the case the band clamp broke.
const WALL: Wall = {
  uid: "wall", tag: "W-B-BRICK", storey: "S-B", assembly: "A-1", provenance: null,
  axis: [[0, 0], [5.842, 0]], z0_m: 0, z1_m: 105 * IN,
  top_z0_m: null, top_z1_m: null, is_foundation: false, layers: [], members: [],
};
const WYTHE: [number, number][] = [
  [0, 0], [0, 3.625 * IN], [5.842, 3.625 * IN], [5.842, 0],
];
const DOOR: Opening = {
  uid: "door", tag: "AO-B-BRICK-DOOR", host: "W-B-BRICK", kind: "rough_opening", is_door: false,
  provenance: null, type_ref: null, width_m: 60 * IN, height_m: 78 * IN, sill_m: 0,
  center_along_m: 3.2, arch_rise_m: 8 * IN, flip_hinge: false, flip_swing: false,
};
// The 14" reveal sits 29" up, so in the 24"–29⅓" gold register it reaches the top edge only.
const WINDOW: Opening = {
  ...DOOR, uid: "window", tag: "AO-B-BRICK-WIN", width_m: 14 * IN, height_m: 20 * IN,
  sill_m: 29 * IN, center_along_m: 1.2, arch_rise_m: 2 * IN,
};

const BANDS: { name: string; z0: number; z1: number }[] = [
  { name: "brown-brick", z0: 0, z1: 24 },
  { name: "glazed-gold-brick", z0: 24, z1: 29 + 1 / 3 },
  { name: "glazed-lapis-brick", z0: 29 + 1 / 3, z1: 88 },
];

/**
 * Nothing may be drawn across an opening at a band's own edge.
 *
 * This is the whole point of builders/wallBandShape.ts. Building a band as a rectangle with a
 * *hole* clamped into it lays the hole's head (or sill) exactly on the band edge whenever the
 * opening runs past it, and ExtrudeGeometry sweeps that clamped edge as a lit strip hanging in
 * the void — the thin bright band that used to cross both reveals at every colour change.
 * A triangle lying flat at a band edge, inside an opening's width, is that strip.
 */
function assertNoStripHangsInAnOpening(): void {
  for (const band of BANDS) {
    const geometry = createSmoothArchedWallLayerGeometry(
      WALL, WYTHE, [DOOR, WINDOW], [0, 0],
      { z0_m: band.z0 * IN, z1_m: band.z1 * IN },
    );
    assert(geometry, `${band.name} builds`);
    const position = geometry.getAttribute("position");
    for (const opening of [DOOR, WINDOW]) {
      // Only the edges this opening actually runs out to: elsewhere the band is solid brick
      // over the opening, and a cap spanning it there is the wall, not an artifact.
      // An opening that misses the band entirely cuts nothing from it.
      if (opening.sill_m >= band.z1 * IN - 1e-9 ||
          opening.sill_m + opening.height_m <= band.z0 * IN + 1e-9) continue;
      const edges: number[] = [];
      if (opening.sill_m <= band.z0 * IN + 1e-9) edges.push(band.z0 * IN);
      if (opening.sill_m + opening.height_m >= band.z1 * IN - 1e-9) edges.push(band.z1 * IN);
      if (edges.length === 0) continue;
      // The middle half of the width, so a band top that cut across an arch's shoulders would
      // not read the spandrels either side of it as a strip.
      const start = opening.center_along_m - opening.width_m / 4;
      const end = opening.center_along_m + opening.width_m / 4;
      // The wall runs along +x from the origin, so scene x is distance along it.
      for (let triangle = 0; triangle < position.count; triangle += 3) {
        const ys = [0, 1, 2].map((k) => position.getY(triangle + k));
        if (Math.max(...ys) - Math.min(...ys) > 1e-9) continue;
        if (!edges.some((edge) => Math.abs(ys[0] - edge) < 1e-6)) continue;
        const xs = [0, 1, 2].map((k) => position.getX(triangle + k));
        assert(Math.max(...xs) <= start + 1e-6 || Math.min(...xs) >= end - 1e-6,
          `${band.name} draws nothing across ${opening.tag} at its band edge`);
      }
    }
  }
}

// Called by scripts/run-geometry-tests.mjs.
export function runWallBandShapeTests(): void {
  // The door runs the full height of the 24"-tall plinth, so the plinth is two pieces of
  // brickwork, not one with a hole — which is what it is in the wall as well.
  const plinth = wallBandShapes(
    { minAlong: 0, maxAlong: 5.842, bandBottom: 0, bandTop: 24 * IN }, WALL, [DOOR]);
  assert(plinth.shapes.length === 2, "An opening that spans a band parts it into two shapes");
  assert(plinth.soffits.length === 1, "The arch still reports its soffit cylinder");

  // A reveal wholly inside its band is still a hole, and the band is still one shape.
  const field = wallBandShapes(
    { minAlong: 0, maxAlong: 5.842, bandBottom: 24 * IN, bandTop: 88 * IN }, WALL, [WINDOW]);
  assert(field.shapes.length === 1 && field.shapes[0].holes.length === 1,
    "An opening inside the band stays a hole in one shape");

  assertNoStripHangsInAnOpening();

  // The band is still a solid rectangle where no opening reaches it.
  const above = wallBandShapes(
    { minAlong: 0, maxAlong: 5.842, bandBottom: 88 * IN, bandTop: 93 * IN }, WALL, [DOOR, WINDOW]);
  assert(above.shapes.length === 1 && above.shapes[0].holes.length === 0,
    "A band clear of every opening is one unbroken shape");
  const box = new THREE.Box2().setFromPoints(above.shapes[0].getPoints(1));
  assert(Math.abs(box.min.x) < 1e-9 && Math.abs(box.max.x - 5.842) < 1e-9 &&
    Math.abs(box.min.y - 88 * IN) < 1e-9 && Math.abs(box.max.y - 93 * IN) < 1e-9,
    "and it fills its band exactly");
}
