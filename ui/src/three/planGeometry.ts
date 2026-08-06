import * as THREE from "three";
import type { Vec2 } from "../model/types";

export type PlanCenter = readonly [number, number];
export type ProjectVertex = readonly [point: Vec2, elevationM: number];

// This is the only project-to-Three.js boundary. TypeHaus is authored in the
// right-handed frame (project X/east, project Y/north, elevation). Three.js is
// Y-up, so project north maps to scene -Z: east × north must still equal up.
export function projectPointToScene([x, y]: Vec2, elevationM: number, center: PlanCenter = [0, 0]): THREE.Vector3 {
  return new THREE.Vector3(x - center[0], elevationM, -(y - center[1]));
}

export function projectPlanDirectionToScene([x, y]: Vec2): THREE.Vector3 {
  return new THREE.Vector3(x, 0, -y);
}

export function projectScenePointToPlan(sceneX: number, sceneZ: number, center: PlanCenter = [0, 0]): Vec2 {
  return [sceneX + center[0], center[1] - sceneZ];
}

export function projectPlanRotationToSceneRadians(rotationDegrees: number): number {
  return THREE.MathUtils.degToRad(rotationDegrees);
}

/** Geographic bearing (clockwise from true north) expressed in the shared scene frame. */
export function geographicBearingToSceneDirection(
  bearingDegrees: number,
  trueNorthDegrees: number,
): THREE.Vector3 {
  const projectBearingRadians = THREE.MathUtils.degToRad(bearingDegrees + trueNorthDegrees);
  return new THREE.Vector3(
    Math.sin(projectBearingRadians),
    0,
    -Math.cos(projectBearingRadians),
  );
}

/** Scene-orbit azimuth for a camera geographically southeast of the model. */
export function geographicSoutheastSceneAzimuthRadians(trueNorthDegrees: number): number {
  const southeastDirection = geographicBearingToSceneDirection(135, trueNorthDegrees);
  return Math.atan2(southeastDirection.z, southeastDirection.x);
}

export function projectTriangleVerticesToScene(vertices: readonly ProjectVertex[], center: PlanCenter = [0, 0]): THREE.Vector3[] {
  return vertices.map(([point, elevationM]) => projectPointToScene(point, elevationM, center));
}

export function createProjectedSurfaceGeometry(
  triangles: readonly ProjectVertex[][],
  center: PlanCenter = [0, 0],
): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  geometry.setFromPoints(triangles.flatMap((triangle) => projectTriangleVerticesToScene(triangle, center)));
  geometry.computeVertexNormals();
  return geometry;
}

/**
 * Extrude an authored plan ring from `z0M` to `z1M` in the shared scene frame.
 *
 * `ExtrudeGeometry` grows along local +Z. Rotating it -90 degrees about X maps
 * plan +Y to scene -Z and extrusion depth to scene +Y.
 */
export function createPlanPrismGeometry(
  outline: readonly Vec2[],
  z0M: number,
  z1M: number,
  holes: readonly (readonly Vec2[])[] = [],
  center: PlanCenter = [0, 0],
): THREE.ExtrudeGeometry | null {
  if (outline.length < 3 || z1M <= z0M) return null;

  const toPath = (points: readonly Vec2[]) => {
    const path = new THREE.Path();
    points.forEach(([x, y], index) => {
      x -= center[0];
      y -= center[1];
      if (index === 0) path.moveTo(x, y);
      else path.lineTo(x, y);
    });
    return path;
  };

  const shape = new THREE.Shape(toPath(outline).getPoints());
  for (const hole of holes) {
    if (hole.length >= 3) shape.holes.push(toPath(hole));
  }

  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: z1M - z0M,
    bevelEnabled: false,
  });
  geometry.rotateX(-Math.PI / 2);
  geometry.translate(0, z0M, 0);
  return geometry;
}

/**
 * A rectangular band around the p0→p1 plan axis, from `left` to `right` offsets off it —
 * mirrors resolve/geometry.py `rect_between` (sans the miter-closing `extend0`/`extend1`,
 * unused on this side). Used to sweep a cross-section band along a run's path leg by leg.
 */
export function rectBetween(p0: Vec2, p1: Vec2, left: number, right: number): Vec2[] {
  const dx = p1[0] - p0[0];
  const dy = p1[1] - p0[1];
  const len = Math.hypot(dx, dy);
  if (len < 1e-9) return [p0, p1, p1, p0];
  const ux = dx / len;
  const uy = dy / len;
  const nx = -uy;
  const ny = ux;
  return [
    [p0[0] + nx * left, p0[1] + ny * left],
    [p1[0] + nx * left, p1[1] + ny * left],
    [p1[0] + nx * right, p1[1] + ny * right],
    [p0[0] + nx * right, p0[1] + ny * right],
  ];
}

/**
 * SVG arc sweep-flag for a quarter-circle swing arc that must be centred on `center`
 * (screen pixel space, y pointing down). An `A r r 0 0 <flag> …` command from `from`
 * to `to` — both a radius away from `center` — has two candidate centres; the flag
 * selects the one that keeps the pivot at `center`, so the arc stays correctly concave
 * toward the hinge. A double door's two leaves hinge at opposite jambs and are mirror
 * images, so they resolve to opposite flags — the reason a single shared flag rendered
 * one convex + one concave leaf.
 *
 * SVG sweep-flag 1 draws clockwise on screen; for a y-down frame a visually clockwise
 * turn from (from-center) to (to-center) has a positive 2D cross product.
 */
export function swingArcSweepFlag(center: Vec2, from: Vec2, to: Vec2): 0 | 1 {
  const cross = (from[0] - center[0]) * (to[1] - center[1]) - (from[1] - center[1]) * (to[0] - center[0]);
  return cross > 0 ? 1 : 0;
}

/** Shoelace area of a plan ring; positive is counter-clockwise in plan coordinates. */
export function planRingSignedArea(ring: readonly Vec2[]): number {
  let sum = 0;
  for (let i = 0; i < ring.length; i++) {
    const [x0, y0] = ring[i];
    const [x1, y1] = ring[(i + 1) % ring.length];
    sum += x0 * y1 - x1 * y0;
  }
  return sum / 2;
}

export function createRakedPlanPrismGeometry(
  outline: readonly Vec2[],
  z0M: number,
  topElevationAt: (point: Vec2) => number,
  center: PlanCenter = [0, 0],
): THREE.BufferGeometry | null {
  if (outline.length < 3) return null;
  // Unlike `createPlanPrismGeometry`, nothing downstream normalizes winding for us:
  // the fixed vertex order below only faces outward for one input orientation, so a
  // ring authored the other way renders inside-out and vanishes to backface culling.
  // The shared transform preserves handedness, so counter-clockwise plan rings give
  // outward side normals and upward top-cap normals.
  outline = planRingSignedArea(outline) < 0 ? [...outline].reverse() : outline;
  const triangles: ProjectVertex[][] = [];
  for (let index = 0; index < outline.length; index++) {
    const next = (index + 1) % outline.length;
    triangles.push(
      [[outline[index], z0M], [outline[next], z0M], [outline[next], topElevationAt(outline[next])]],
      [[outline[index], z0M], [outline[next], topElevationAt(outline[next])], [outline[index], topElevationAt(outline[index])]],
    );
  }
  for (let index = 1; index < outline.length - 1; index++) {
    triangles.push(
      [[outline[0], z0M], [outline[index + 1], z0M], [outline[index], z0M]],
      [[outline[0], topElevationAt(outline[0])], [outline[index], topElevationAt(outline[index])], [outline[index + 1], topElevationAt(outline[index + 1])]],
    );
  }
  return createProjectedSurfaceGeometry(triangles, center);
}
