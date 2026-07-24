import * as THREE from "three";
import type { Member, Vec2 } from "../model/types";
import { buildMembers } from "./members";
import {
  createPlanPrismGeometry,
  createProjectedSurfaceGeometry,
  createRakedPlanPrismGeometry,
  projectPointToScene,
  swingArcSweepFlag,
} from "./planGeometry";

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
    web_thickness_m: null, plies: 1, orient: [1, 0], connection: null,
    ...overrides,
  };
}

// Called by scripts/run-geometry-tests.mjs. This stays framework-free because the UI does
// not otherwise need a browser-test dependency for these deterministic geometry checks.
export function runPlanGeometryTests() {
  const projectPoint = projectPointToScene([3.25, 8.5], 1.75);
  closeTo(projectPoint.x, 3.25, "Project X maps to scene X");
  closeTo(projectPoint.y, 1.75, "Project elevation maps to scene Y");
  closeTo(projectPoint.z, 8.5, "Project +Y maps to positive scene Z");

  const outline: [number, number][] = [[3, 7], [8, 7], [8, 11], [3, 11]];
  const geometry = createPlanPrismGeometry(outline, 1.25, 2.75);
  if (!geometry) throw new Error("Expected a prism for a valid outline");
  const bounds = boundsFor(geometry);
  closeTo(bounds.min.x, 3, "Prism preserves minimum project X");
  closeTo(bounds.max.x, 8, "Prism preserves maximum project X");
  closeTo(bounds.min.z, 7, "Prism preserves minimum project Y as scene Z");
  closeTo(bounds.max.z, 11, "Prism preserves maximum project Y as scene Z");
  closeTo(bounds.min.y, 1.25, "Prism starts at authored z0");
  closeTo(bounds.max.y, 2.75, "Prism ends at authored z1");
  geometry.dispose();

  const center: [number, number] = [10, 20];
  const centeredPoint = projectPointToScene([13.25, 28.5], 1.75, center);
  closeTo(centeredPoint.x, 3.25, "Centering only translates project X");
  closeTo(centeredPoint.z, 8.5, "Centering preserves positive project Y/north");

  const centeredPrism = createPlanPrismGeometry([[13, 27], [18, 27], [18, 31], [13, 31]], 1.25, 2.75, [], center);
  if (!centeredPrism) throw new Error("Expected centered prism");
  const centeredBounds = boundsFor(centeredPrism);
  closeTo(centeredBounds.min.x, 3, "Centered prism translates X consistently");
  closeTo(centeredBounds.min.z, 7, "Centered prism translates north consistently");
  centeredPrism.dispose();

  const raked = createRakedPlanPrismGeometry(
    [[13, 27], [18, 27], [18, 31], [13, 31]], 1,
    ([x]) => x === 13 ? 3 : 5,
    center,
  );
  if (!raked) throw new Error("Expected raked prism");
  const rakedBounds = boundsFor(raked);
  closeTo(rakedBounds.min.z, 7, "Gable wall preserves north minimum");
  closeTo(rakedBounds.max.z, 11, "Gable wall preserves north maximum");
  closeTo(rakedBounds.max.y, 5, "Gable wall preserves authored rake elevation");
  raked.dispose();

  const roofSurface = createProjectedSurfaceGeometry([
    [[[13, 27], 3], [[18, 27], 3], [[18, 31], 5]],
    [[[13, 27], 3], [[18, 31], 5], [[13, 31], 3]],
  ], center);
  const roofBounds = boundsFor(roofSurface);
  closeTo(roofBounds.min.z, 7, "Roof preserves north minimum");
  closeTo(roofBounds.max.z, 11, "Roof preserves north maximum");
  roofSurface.dispose();

  const framing = new THREE.Group();
  buildMembers(framing, [member({}), member({
    category: "raked_plate", p0: [13, 27], p1: [18, 27], z0_m: 3,
    z1_m: 3.2, z0_end_m: 5, z1_end_m: 5.2, orient: null,
  })], center, "schematic");
  const framingBounds = boundsForObject(framing);
  closeTo(framingBounds.min.z, 2.9, "Framing uses the same centered north axis");
  closeTo(framingBounds.max.z, 7.1, "Framing remains aligned with schematic north");
  closeTo(framingBounds.min.x, 1.95, "Vertical member uses the shared centered X axis");
  framing.traverse((object) => {
    const mesh = object as THREE.Mesh;
    mesh.geometry?.dispose();
    const material = mesh.material;
    if (Array.isArray(material)) material.forEach((entry) => entry.dispose());
    else material?.dispose();
  });

  checkRakedWindingIsNormalized();
  checkDoorSwingArcsPivotOnHinge();
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
