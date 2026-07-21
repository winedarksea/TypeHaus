import * as THREE from "three";
import type { Vec2 } from "../model/types";

export type PlanCenter = readonly [number, number];
export type ProjectVertex = readonly [point: Vec2, elevationM: number];

// This is the only project-to-Three.js boundary. TypeHaus is authored as
// (project X, project Y/north, elevation); Three.js is (X, elevation, Z). Do not
// use rotateX() as a coordinate conversion in individual builders: it is too easy
// for one path to reflect north while another follows the canonical framing axis.
export function projectPointToScene([x, y]: Vec2, elevationM: number, center: PlanCenter = [0, 0]): THREE.Vector3 {
  return new THREE.Vector3(x - center[0], elevationM, y - center[1]);
}

export function projectPlanDirectionToScene([x, y]: Vec2): THREE.Vector3 {
  return new THREE.Vector3(x, 0, y);
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
 * `ExtrudeGeometry` grows along local +Z. Rotating it +90 degrees about X makes plan
 * +Y become scene +Z and local extrusion depth become scene -Y; translating to z1M
 * therefore places the prism exactly between z0M and z1M without reflecting north.
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
  // ExtrudeGeometry grows along local +Z. This rotation maps authored plan +Y to
  // scene +Z; translating to z1 puts the reversed extrusion depth at its elevation.
  geometry.rotateX(Math.PI / 2);
  geometry.translate(0, z1M, 0);
  return geometry;
}

export function createRakedPlanPrismGeometry(
  outline: readonly Vec2[],
  z0M: number,
  topElevationAt: (point: Vec2) => number,
  center: PlanCenter = [0, 0],
): THREE.BufferGeometry | null {
  if (outline.length < 3) return null;
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
