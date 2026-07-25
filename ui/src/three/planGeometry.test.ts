import * as THREE from "three";
import type { Member, Vec2 } from "../model/types";
import { buildMembers, categoryColor, disposeGroup, isRoofFramingMember, memberColor } from "./members";
import {
  createPlanPrismGeometry,
  createProjectedSurfaceGeometry,
  createRakedPlanPrismGeometry,
  geographicBearingToSceneDirection,
  geographicSoutheastSceneAzimuthRadians,
  projectPlanDirectionToScene,
  projectPlanRotationToSceneRadians,
  projectPointToScene,
  projectScenePointToPlan,
  swingArcSweepFlag,
} from "./planGeometry";
import { applyDeckBoardUv, applyStandingSeamWallUv, DECK_BOARD_WIDTH_M, SEAM_PAN_WIDTH_M } from "./materials";

function closeTo(actual: number, expected: number, message: string) {
  if (Math.abs(actual - expected) > 1e-6) {
    throw new Error(`${message}: expected ${expected}, received ${actual}`);
  }
}

function boundsFor(geometry: THREE.BufferGeometry): THREE.Box3 {
  geometry.computeBoundingBox();
  if (!geometry.boundingBox) throw new Error("Expected geometry bounds");
  return geometry.boundingBox;
}

function boundsForObject(object: THREE.Object3D): THREE.Box3 {
  object.updateMatrixWorld(true);
  return new THREE.Box3().setFromObject(object);
}


function member(overrides: Partial<Member>): Member {
  return {
    key: "test", category: "stud", profile: "2x4", p0: [12, 23], p1: [12, 23],
    z0_m: 1, z1_m: 4, z0_end_m: null, z1_end_m: null, shape: "rect",
    width_m: 0.1, depth_m: 0.2, flange_width_m: null, flange_thickness_m: null,
    web_thickness_m: null, plies: 1, orient: [1, 0], connection: null, material: null,
    ...overrides,
  };
}

// Called by scripts/run-geometry-tests.mjs. This stays framework-free because the UI does
// not otherwise need a browser-test dependency for these deterministic geometry checks.
export function runPlanGeometryTests() {
  const projectPoint = projectPointToScene([3.25, 8.5], 1.75);
  closeTo(projectPoint.x, 3.25, "Project X maps to scene X");
  closeTo(projectPoint.y, 1.75, "Project elevation maps to scene Y");
  closeTo(projectPoint.z, -8.5, "Project +Y/north maps to negative scene Z");

  const east = projectPlanDirectionToScene([1, 0]);
  const north = projectPlanDirectionToScene([0, 1]);
  const up = new THREE.Vector3().crossVectors(east, north);
  closeTo(up.x, 0, "Mapped east × north has no X component");
  closeTo(up.y, 1, "Mapped east × north equals scene up");
  closeTo(up.z, 0, "Mapped east × north has no Z component");

  const outline: [number, number][] = [[3, 7], [8, 7], [8, 11], [3, 11]];
  const geometry = createPlanPrismGeometry(outline, 1.25, 2.75);
  if (!geometry) throw new Error("Expected a prism for a valid outline");
  const bounds = boundsFor(geometry);
  closeTo(bounds.min.x, 3, "Prism preserves minimum project X");
  closeTo(bounds.max.x, 8, "Prism preserves maximum project X");
  closeTo(bounds.min.z, -11, "Prism maps maximum project Y to minimum scene Z");
  closeTo(bounds.max.z, -7, "Prism maps minimum project Y to maximum scene Z");
  closeTo(bounds.min.y, 1.25, "Prism starts at authored z0");
  closeTo(bounds.max.y, 2.75, "Prism ends at authored z1");
  geometry.dispose();

  const center: [number, number] = [10, 20];
  const centeredPoint = projectPointToScene([13.25, 28.5], 1.75, center);
  closeTo(centeredPoint.x, 3.25, "Centering only translates project X");
  closeTo(centeredPoint.z, -8.5, "Centering preserves north as negative scene Z");
  const roundTrip = projectScenePointToPlan(centeredPoint.x, centeredPoint.z, center);
  closeTo(roundTrip[0], 13.25, "Scene-to-plan inverse restores project X");
  closeTo(roundTrip[1], 28.5, "Scene-to-plan inverse restores project Y");

  const centeredPrism = createPlanPrismGeometry([[13, 27], [18, 27], [18, 31], [13, 31]], 1.25, 2.75, [], center);
  if (!centeredPrism) throw new Error("Expected centered prism");
  const centeredBounds = boundsFor(centeredPrism);
  closeTo(centeredBounds.min.x, 3, "Centered prism translates X consistently");
  closeTo(centeredBounds.min.z, -11, "Centered prism translates north consistently");
  centeredPrism.dispose();

  const raked = createRakedPlanPrismGeometry(
    [[13, 27], [18, 27], [18, 31], [13, 31]], 1,
    ([x]) => x === 13 ? 3 : 5,
    center,
  );
  if (!raked) throw new Error("Expected raked prism");
  const rakedBounds = boundsFor(raked);
  closeTo(rakedBounds.min.z, -11, "Gable wall maps north maximum to scene Z minimum");
  closeTo(rakedBounds.max.z, -7, "Gable wall maps north minimum to scene Z maximum");
  closeTo(rakedBounds.max.y, 5, "Gable wall preserves authored rake elevation");
  raked.dispose();

  const roofSurface = createProjectedSurfaceGeometry([
    [[[13, 27], 3], [[18, 27], 3], [[18, 31], 5]],
    [[[13, 27], 3], [[18, 31], 5], [[13, 31], 3]],
  ], center);
  const roofBounds = boundsFor(roofSurface);
  closeTo(roofBounds.min.z, -11, "Roof maps north maximum to scene Z minimum");
  closeTo(roofBounds.max.z, -7, "Roof maps north minimum to scene Z maximum");
  roofSurface.dispose();

  const framing = new THREE.Group();
  buildMembers(framing, [member({}), member({
    category: "raked_plate", p0: [13, 27], p1: [18, 27], z0_m: 3,
    z1_m: 3.2, z0_end_m: 5, z1_end_m: 5.2, orient: null,
  })], center, "schematic");
  const framingBounds = boundsForObject(framing);
  closeTo(framingBounds.min.z, -7.1, "Framing uses the same centered north axis");
  closeTo(framingBounds.max.z, -2.9, "Framing remains aligned with schematic north");
  closeTo(framingBounds.min.x, 1.95, "Vertical member uses the shared centered X axis");
  closeTo(framingBounds.min.y, 1, "Vertical member starts at its authored z0");
  closeTo(framingBounds.max.y, 5.2, "Raked plate preserves its authored high-end z1");
  disposeGroup(framing);

  checkMemberVerticalExtents();
  checkRakedWindingIsNormalized();
  checkAsymmetricPlanIsNotReflected();
  checkGeographicBearings();
  checkWallUvUsesProjectCoordinates();
  checkDeckBoardUvRunsNorthSouth();
  checkDoorSwingArcsPivotOnHinge();
}

// Horizontal members (rims, joists, plates, headers, the U-stair well partition) used to be
// drawn centred on z0 instead of spanning z0→z1, so each one hung half its own depth too low
// — an 11⅞" rim band read ~6" below the subfloor and a 9'-tall stair partition dropped
// 4'6" through the basement slab. The original framing assertions only covered plan (x/z)
// bounds, which is exactly why it shipped; every case below asserts the vertical extent.
function checkMemberVerticalExtents() {
  const center: [number, number] = [10, 20];
  const bandDepth = 0.3016; // 11⅞" floor band
  const bandWidth = 0.03175; // 1¼" rim stock
  const datum = 2.6; // storey datum = top of floor structure

  const rim = new THREE.Group();
  buildMembers(rim, [member({
    key: "rim", category: "rim", profile: "1.25x11.875 rim", p0: [13, 27], p1: [18, 27],
    z0_m: datum - bandDepth, z1_m: datum, width_m: bandWidth, depth_m: 0.038, orient: null,
  })], center, "schematic");
  const rimBounds = boundsForObject(rim);
  closeTo(rimBounds.min.y, datum - bandDepth, "Rim band hangs its full depth below the datum");
  closeTo(rimBounds.max.y, datum, "Rim band tops out flush at the datum, not half a depth low");
  closeTo(rimBounds.min.x, 3, "Rim band spans from its authored p0");
  closeTo(rimBounds.max.x, 8, "Rim band spans to its authored p1");
  closeTo(rimBounds.min.z, -7 - bandWidth / 2, "Rim band stays centred across its own width");
  closeTo(rimBounds.max.z, -7 + bandWidth / 2, "Rim band stays centred across its own width");
  disposeGroup(rim);

  // The catlin basement→main U-stair: a 9' well partition springing from the basement
  // subfloor. Centred on z0 it drew from −13.5' to −4.5', i.e. a wall under the foundation.
  const stairBase = -2.7432; // −9'
  const partition = new THREE.Group();
  buildMembers(partition, [member({
    key: "well-partition", category: "partition", profile: "2x4", p0: [13, 27], p1: [16, 27],
    z0_m: stairBase, z1_m: 0, width_m: 0.0381, depth_m: 0.0889, orient: null,
  })], center, "schematic");
  const partitionBounds = boundsForObject(partition);
  closeTo(partitionBounds.min.y, stairBase, "Stair well partition bears on the storey it springs from");
  closeTo(partitionBounds.max.y, 0, "Stair well partition rises to the arrival deck");
  disposeGroup(partition);
  if (categoryColor("partition") === categoryColor("no-such-category")) {
    throw new Error("Stair well partition must have a framing colour, not the grey fallback");
  }

  // I-joist plies: bottom flange, web, top flange must tile the section soffit-to-top with
  // no gaps. Each was previously centred on its own offset, delaminating the section.
  const flangeThickness = 0.0349;
  const webDepth = bandDepth - 2 * flangeThickness;
  const ijoist = new THREE.Group();
  buildMembers(ijoist, [member({
    key: "joist", category: "joist", profile: "11.875 I-joist", shape: "i_joist",
    p0: [13, 27], p1: [18, 27], z0_m: datum - bandDepth, z1_m: datum,
    width_m: 0.0635, depth_m: bandDepth, flange_width_m: 0.0635,
    flange_thickness_m: flangeThickness, web_thickness_m: 0.0095, orient: null,
  })], center, "schematic");
  const soffit = datum - bandDepth;
  const expectedPlies: [number, number, string][] = [
    [soffit, soffit + flangeThickness, "bottom flange"],
    [soffit + flangeThickness, soffit + flangeThickness + webDepth, "web"],
    [datum - flangeThickness, datum, "top flange"],
  ];
  const plies = ijoist.children
    .map((child) => boundsForObject(child))
    .sort((a, b) => a.min.y - b.min.y);
  if (plies.length !== expectedPlies.length) {
    throw new Error(`Expected ${expectedPlies.length} i-joist plies, received ${plies.length}`);
  }
  expectedPlies.forEach(([low, high, label], index) => {
    closeTo(plies[index].min.y, low, `I-joist ${label} starts at its section offset`);
    closeTo(plies[index].max.y, high, `I-joist ${label} ends at its section offset`);
  });
  disposeGroup(ijoist);

  // Roof members split two ways: sticks under the framing toggle, skin with the shell.
  // Mirrors ROOF_SKIN_CATEGORIES in emit/gltf/emitter.py.
  for (const category of ["rafter", "top_chord", "truss_web", "stud", "outlooker"]) {
    if (!isRoofFramingMember(member({ category }))) {
      throw new Error(`${category} is a stick and belongs in the framing trade`);
    }
  }
  for (const category of ["sheathing", "cladding", "insulation", "fascia", "soffit"]) {
    if (isRoofFramingMember(member({ category }))) {
      throw new Error(`${category} is envelope skin and belongs with the roof shell`);
    }
  }

  // A member that names a material is skin, and is coloured by that material — a
  // standing-seam closure band read as the grey category fallback before, which is what made
  // the garage gable look like unwanted fill instead of white metal.
  const seamBand = member({
    key: "rake-lo-0-edge-cladding", category: "cladding", material: "standing-seam",
    p0: [0, 0], p1: [4, 0], z0_m: 3, z1_m: 3.2, z0_end_m: 4, z1_end_m: 4.2,
    width_m: 0.0127, depth_m: 0.0127, orient: null,
  });
  if (memberColor(seamBand) === categoryColor("cladding")) {
    throw new Error("A standing-seam band must take its material's colour, not the category's");
  }
  if (memberColor(member({ category: "stud" })) !== categoryColor("stud")) {
    throw new Error("Lumber keeps its category colour");
  }

  // The seam band renders raked (its far end is 1 m higher) and carries UVs, without which
  // the shared seam normal map has no coordinate frame and the pans collapse.
  const seam = new THREE.Group();
  buildMembers(seam, [seamBand], center, "schematic");
  const seamBounds = boundsForObject(seam);
  closeTo(seamBounds.min.y, 3, "Seam band starts on the roof plane at its low end");
  closeTo(seamBounds.max.y, 4.2, "Seam band climbs the rake with the roof plane");
  const seamMesh = seam.children[0] as THREE.Mesh;
  if (!seamMesh?.geometry?.getAttribute("uv")) {
    throw new Error("Seam band needs UVs for the standing-seam normal map");
  }
  disposeGroup(seam);
}

function checkAsymmetricPlanIsNotReflected() {
  // An L-plan plus independent north/east landmarks catches a reflection that symmetric
  // bounds cannot. Every scene point must invert to its exact authored plan location.
  const asymmetricPlan: Vec2[] = [[0, 0], [5, 0], [5, 2], [2, 2], [2, 6], [0, 6]];
  const center: [number, number] = [2.5, 3];
  for (const point of asymmetricPlan) {
    const scenePoint = projectPointToScene(point, 0, center);
    const restored = projectScenePointToPlan(scenePoint.x, scenePoint.z, center);
    closeTo(restored[0], point[0], "Asymmetric plan round-trip preserves east/west");
    closeTo(restored[1], point[1], "Asymmetric plan round-trip preserves north/south");
  }
  const northLandmark = projectPointToScene([1, 5], 0, center);
  const southLandmark = projectPointToScene([1, 1], 0, center);
  if (northLandmark.z >= southLandmark.z) {
    throw new Error("The asymmetric plan's north landmark must remain north at negative scene Z");
  }
  const rotatedEast = new THREE.Vector3(1, 0, 0).applyAxisAngle(
    new THREE.Vector3(0, 1, 0),
    projectPlanRotationToSceneRadians(90),
  );
  closeTo(rotatedEast.z, -1, "Positive plan rotation turns east toward north in 3D");
}

function checkGeographicBearings() {
  const northAtZero = geographicBearingToSceneDirection(0, 0);
  closeTo(northAtZero.x, 0, "True north at 0° has no east component");
  closeTo(northAtZero.z, -1, "True north at 0° follows project north");
  const northAtNinety = geographicBearingToSceneDirection(0, 90);
  closeTo(northAtNinety.x, 1, "True north at 90° follows project east");
  closeTo(northAtNinety.z, 0, "True north at 90° has no project-north component");
  const southeastAtThirty = geographicBearingToSceneDirection(135, 30);
  const resetAzimuth = geographicSoutheastSceneAzimuthRadians(30);
  closeTo(Math.cos(resetAzimuth), southeastAtThirty.x,
    "Reset camera X follows geographic southeast at a non-cardinal angle");
  closeTo(Math.sin(resetAzimuth), southeastAtThirty.z,
    "Reset camera Z follows geographic southeast at a non-cardinal angle");
}

function checkWallUvUsesProjectCoordinates() {
  const center: [number, number] = [10, 20];
  const geometry = createPlanPrismGeometry(
    [[10, 20], [10, 24], [10.1, 24], [10.1, 20]], 0, 3, [], center,
  );
  if (!geometry) throw new Error("Expected wall prism for UV orientation test");
  applyStandingSeamWallUv(geometry, [[10, 20], [10, 24]], center);
  const positions = geometry.getAttribute("position");
  const uv = geometry.getAttribute("uv");
  for (let index = 0; index < positions.count; index++) {
    const [, projectY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    closeTo(uv.getX(index), (projectY - 20) / (SEAM_PAN_WIDTH_M * 4),
      "Wall UV distance follows authored project Y after scene reflection is removed");
  }
  geometry.dispose();
}

// The deck-board normal map's x-axis runs across the 5½" planks, so tying u to project X is
// what makes the boards run north–south (perpendicular to the house and to the balcony's
// east–west joists). A u that varied with project Y would lay them the wrong way.
function checkDeckBoardUvRunsNorthSouth() {
  const center: [number, number] = [10, 20];
  const tile = DECK_BOARD_WIDTH_M * 4;
  const geometry = createPlanPrismGeometry(
    [[10, 20], [14, 20], [14, 26], [10, 26]], 3.048, 3.086, [], center,
  );
  if (!geometry) throw new Error("Expected deck prism for board-UV orientation test");
  applyDeckBoardUv(geometry, center);
  const positions = geometry.getAttribute("position");
  const uv = geometry.getAttribute("uv");
  const uByProjectX = new Map<number, number>();
  for (let index = 0; index < positions.count; index++) {
    const [projectX, projectY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    closeTo(uv.getX(index), projectX / tile, "Deck board U counts planks across project X");
    closeTo(uv.getY(index), projectY / tile, "Deck board V runs along the plank in project Y");
    const key = Math.round(projectX * 1e6);
    const seen = uByProjectX.get(key);
    if (seen !== undefined) {
      closeTo(uv.getX(index), seen, "Deck boards stay constant along project north");
    }
    uByProjectX.set(key, uv.getX(index));
  }
  if (uByProjectX.size < 2) {
    throw new Error("Deck board UV test needs at least two distinct project-X columns");
  }
  geometry.dispose();
}

// Reconstruct an SVG elliptical-arc centre (F.6.5, rx=ry=r, rotation 0, large-arc 0) from
// its endpoints and sweep flag, so we can assert the drawn swing arc really pivots on the
// hinge rather than bowing convex off the wrong centre.
function svgArcCenter(from: Vec2, to: Vec2, r: number, sweep: 0 | 1): Vec2 {
  const x1p = (from[0] - to[0]) / 2;
  const y1p = (from[1] - to[1]) / 2;
  const num = r * r * r * r - r * r * y1p * y1p - r * r * x1p * x1p;
  const denom = r * r * y1p * y1p + r * r * x1p * x1p;
  const sign = sweep === 1 ? 1 : -1; // (large-arc 0) !== sweep → +1, else −1
  const coef = sign * Math.sqrt(Math.max(0, num / denom));
  const cxp = coef * y1p;
  const cyp = coef * -x1p;
  return [cxp + (from[0] + to[0]) / 2, cyp + (from[1] + to[1]) / 2];
}

function checkDoorSwingArcsPivotOnHinge() {
  const near = (a: Vec2, b: Vec2, message: string) => {
    if (Math.hypot(a[0] - b[0], a[1] - b[1]) > 1e-6) {
      throw new Error(`${message}: expected (${b}), received (${a})`);
    }
  };
  // Single leaf: hinge at one jamb, closed leaf along the wall at the far jamb, open leaf
  // perpendicular. The arc must pivot on the hinge for every hinge/swing handing.
  const r = 1;
  for (const hingeDir of [1, -1]) {
    for (const swingSign of [1, -1]) {
      const hinge: Vec2 = [hingeDir * 0.5, 0];
      const closed: Vec2 = [-hingeDir * 0.5, 0];
      const open: Vec2 = [hinge[0] + swingSign * 0, hinge[1] - swingSign * r];
      const flag = swingArcSweepFlag(hinge, closed, open);
      near(svgArcCenter(closed, open, r, flag), hinge,
        `Single door swing arc pivots on hinge (hinge ${hingeDir}, swing ${swingSign})`);
    }
  }
  // Double door: leaves hinge at opposite jambs and mirror across the mullion. Each must
  // pivot on its own jamb, which forces the two sweep flags to differ.
  const rh = 0.5;
  const leftJamb: Vec2 = [-0.5, 0];
  const rightJamb: Vec2 = [0.5, 0];
  const mullion: Vec2 = [0, 0];
  const leftOpen: Vec2 = [leftJamb[0], leftJamb[1] - rh];
  const rightOpen: Vec2 = [rightJamb[0], rightJamb[1] - rh];
  const leftFlag = swingArcSweepFlag(leftJamb, mullion, leftOpen);
  const rightFlag = swingArcSweepFlag(rightJamb, mullion, rightOpen);
  near(svgArcCenter(mullion, leftOpen, rh, leftFlag), leftJamb, "Double door left leaf pivots on its jamb");
  near(svgArcCenter(mullion, rightOpen, rh, rightFlag), rightJamb, "Double door right leaf pivots on its jamb");
  if (leftFlag === rightFlag) {
    throw new Error("Double door leaves must use opposite sweep flags, else one renders convex");
  }
}

/**
 * Raked walls are the one prism path that does not go through THREE.Shape, so nothing
 * fixes their winding for us. Both author orders must produce outward-facing triangles,
 * or gable ends turn invisible and you see straight through to the studs.
 */
function checkRakedWindingIsNormalized() {
  const ccw: Vec2[] = [[0, 0], [4, 0], [4, 1], [0, 1]];
  const cw: Vec2[] = [...ccw].reverse();
  for (const [label, ring] of [["CCW", ccw], ["CW", cw]] as const) {
    const geometry = createRakedPlanPrismGeometry(ring, 0, ([x]) => 2 + x * 0.25, [2, 0.5]);
    if (!geometry) throw new Error(`Expected raked prism for ${label} ring`);
    const position = geometry.getAttribute("position");
    const normal = geometry.getAttribute("normal");
    const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
    // The shape is convex, so every face normal must point away from its centroid.
    const center = boundsFor(geometry).getCenter(new THREE.Vector3());
    for (let i = 0; i < position.count; i += 3) {
      a.fromBufferAttribute(position, i);
      b.fromBufferAttribute(position, i + 1);
      c.fromBufferAttribute(position, i + 2);
      const centroid = a.clone().add(b).add(c).divideScalar(3);
      const face = new THREE.Vector3().fromBufferAttribute(normal, i);
      const alignment = face.dot(centroid.sub(center).normalize());
      if (alignment < -1e-6) {
        throw new Error(`${label} raked prism face ${i / 3} points inward (${alignment})`);
      }
    }
    geometry.dispose();
  }
}
