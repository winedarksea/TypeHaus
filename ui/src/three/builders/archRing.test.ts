import * as THREE from "three";
import type { Opening, Wall } from "../../model/types";
import { masonryStyleFor } from "../materials";
import {
  ARCH_RING_DEPTH_M, ARCH_RING_MIN_BRICKS, ARCH_RING_PROUD_M, archRingBrickCount,
  createArchRingGeometry,
} from "./archRing";
import { archSoffitCircle } from "./wallFrame";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const IN = 0.0254;

function wall(topZ0: number | null = null, topZ1: number | null = null): Wall {
  return {
    uid: "wall", tag: "W-B-BRICK", storey: "S-B", assembly: "A-1", provenance: null,
    axis: [[0, 0], [5.842, 0]], z0_m: 0, z1_m: 101 * IN,
    top_z0_m: topZ0, top_z1_m: topZ1, plate_base_z_m: null, layout_axis: null, is_foundation: false, layers: [], members: [],
  };
}

// The 3⅝" wythe as a rectangle in plan, padded with the edge-splitting vertices junction
// resolution leaves behind — the shape the Ishtar wall actually arrives in.
const WYTHE: [number, number][] = [
  [0, 0], [0, 3.625 * IN], [3, 3.625 * IN], [5.842, 3.625 * IN], [5.842, 0], [3, 0],
];

function opening(widthIn: number, heightIn: number, riseIn: number, sillIn: number): Opening {
  return {
    uid: "opening", tag: "AO-B-BRICK-DOOR", host: "W-B-BRICK", kind: "rough_opening", is_door: false,
    provenance: null, type_ref: null, width_m: widthIn * IN, height_m: heightIn * IN,
    sill_m: sillIn * IN, center_along_m: 3.2, arch_rise_m: riseIn * IN,
    flip_hinge: false, flip_swing: false,
  };
}

// The reference house's two arched reveals, at their authored sizes.
const DOOR = opening(60, 78, 8, 0);
const WINDOW = opening(14, 20, 2, 29);

// Called by scripts/run-geometry-tests.mjs. The voussoir ring is viewer-only geometry, so
// these are the only assertions standing between it and a silent regression.
export function runArchRingTests() {
  const lapis = masonryStyleFor("glazed-lapis-brick", "glazed-lapis-brick");
  const doorCircle = archSoffitCircle(DOOR.width_m / 2, DOOR.arch_rise_m ?? 0);
  const windowCircle = archSoffitCircle(WINDOW.width_m / 2, WINDOW.arch_rise_m ?? 0);

  // An odd count puts one brick — the keystone — on the crown, which is what the eye reads the
  // centre of an arch from. An even one splits the crown down a joint.
  const doorBricks = archRingBrickCount(doorCircle.radiusM, doorCircle.halfAngleRad, lapis);
  const windowBricks = archRingBrickCount(windowCircle.radiusM, windowCircle.halfAngleRad, lapis);
  assert(doorBricks % 2 === 1 && windowBricks % 2 === 1,
    "A voussoir count is odd, so a keystone lands on the crown");
  assert(doorBricks >= ARCH_RING_MIN_BRICKS && windowBricks >= ARCH_RING_MIN_BRICKS,
    "Even a small arch turns enough bricks to read as an arch rather than a polygon");
  assert(doorBricks > windowBricks * 2,
    "The count follows the arc: the 5'-0\" door turns far more bricks than the 14\" window");

  const geometry = createArchRingGeometry(DOOR, wall(), WYTHE, [0, 0], lapis);
  assert(geometry !== null, "The door reveal carries a voussoir ring");
  const position = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  assert(position.count > 0 && position.count % 3 === 0, "The ring is built of whole triangles");

  // Wall axis is +x from the origin, so scene x/y are the arch's own plane and the soffit
  // circle's centre sits at (center_along, springline - depth).
  const springline = DOOR.sill_m + DOOR.height_m - (DOOR.arch_rise_m ?? 0);
  const centerY = springline - doorCircle.depthM;
  const inner = doorCircle.radiusM - ARCH_RING_PROUD_M;
  const outer = doorCircle.radiusM + ARCH_RING_DEPTH_M;
  let radialVertices = 0;
  for (let index = 0; index < position.count; index++) {
    const dx = position.getX(index) - DOOR.center_along_m;
    const dy = position.getY(index) - centerY;
    const distance = Math.hypot(dx, dy);
    assert(distance > inner - 1e-4 && distance < outer + 1e-4,
      "Every ring vertex lies in the band between the intrados and the extrados");
    assert(position.getY(index) > springline - ARCH_RING_PROUD_M - 1e-4,
      "The ring dies at the springline; it does not run down the jamb");
    // Intrados and extrados carry analytic radial normals *at each vertex's own angle*, so the
    // ring shades as one curve instead of as N flats. The only other in-plane normals belong to
    // the two skewback caps, which are tangential — nothing in between is correct.
    if (Math.abs(normal.getZ(index)) > 0.5) continue;
    const aligned = Math.abs(
      normal.getX(index) * dx / distance + normal.getY(index) * dy / distance);
    assert(aligned > 1 - 1e-4 || aligned < 1e-4,
      "An in-plane ring normal is either radial (soffit, extrados) or tangential (skewback)");
    if (aligned > 1 - 1e-4) radialVertices++;
  }
  assert(radialVertices > 4 * doorBricks,
    "The radial surfaces were found, and there are more of them than there are voussoirs");

  // The constraint that pins ARCH_RING_DEPTH_M: the ring may not grow into the gold register
  // `brick-band-hi`, whose bottom edge is 88". AO-B-BRICK-DOOR crowns at 78", so a 3 5/8"
  // ring extradoses at 81 5/8". The margin is comfortable at this head height and was not at
  // the 84" the door passed through, which is the reason to keep asserting it.
  const bounds = new THREE.Box3().setFromBufferAttribute(position as THREE.BufferAttribute);
  const extrados = centerY + outer;
  // An ODD voussoir count means the crown falls mid-brick rather than on a joint — the whole
  // point of the keystone — so the highest vertex sits half a facet to either side of it and
  // misses the analytic extrados by that facet's sagitta, well under a millimetre here.
  assert(bounds.max.y <= extrados + 1e-6 && extrados - bounds.max.y < 1e-3,
    "The ring's high point is its extrados crown, straddled by the keystone");
  assert(Math.abs(extrados - 81.625 * IN) < 1e-4,
    "The extrados crowns at 81⅝\" — the door's 78\" head plus one 3⅝\" header ring");
  assert(extrados < 88 * IN, "The ring stays clear of the 88\" gold register");

  // Proud on every side, so no ring surface is coincident with the wall's own and nothing
  // z-fights. The wythe is 3⅝"; the ring is that plus a ⅜" projection each way.
  assert(Math.abs((bounds.max.z - bounds.min.z) - (3.625 * IN + 2 * ARCH_RING_PROUD_M)) < 1e-4,
    "The ring stands proud of both faces of the wythe");

  // The gate matches the swept-arch path exactly, so the two never disagree about what an arch
  // is or which walls can be built against.
  assert(createArchRingGeometry(opening(60, 84, 0, 0), wall(), WYTHE, [0, 0], lapis) === null,
    "A square-headed opening has no arch to ring");
  assert(createArchRingGeometry(DOOR, wall(2.4, 1.8), WYTHE, [0, 0], lapis) === null,
    "A raked wall declines, exactly as the swept-arch path does");
  assert(createArchRingGeometry(DOOR, wall(),
    [[-0.25, 0], [0, -0.2], [5.842, -0.2], [5.842, 0.2], [0, 0.2]], [0, 0], lapis) === null,
    "A junction-mitered footprint has no frame to build the ring in");
}
