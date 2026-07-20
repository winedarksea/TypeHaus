import * as THREE from "three";
import type { Vec2 } from "../model/types";

// TypeHaus geometry is authored in the project-north plan frame: (x, y) in plan and z
// in elevation. Three.js uses Y for elevation, so every 3D builder maps project
// (x, y, z) to scene (x, z, y). Keep that conversion here rather than letting each
// presentation builder choose its own extrusion rotation.
export function projectPointToScene([x, y]: Vec2, elevationM: number): THREE.Vector3 {
  return new THREE.Vector3(x, elevationM, y);
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
): THREE.ExtrudeGeometry | null {
  if (outline.length < 3 || z1M <= z0M) return null;

  const toPath = (points: readonly Vec2[]) => {
    const path = new THREE.Path();
    points.forEach(([x, y], index) => {
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
  geometry.rotateX(Math.PI / 2);
  geometry.translate(0, z1M, 0);
  return geometry;
}
