import * as THREE from "three";
import { projectScenePointToPlan, type PlanCenter } from "./planGeometry";

/**
 * World-scaled box projection on each vertex's dominant normal axis. Treads and floors read
 * plan coordinates, so clipped parts stay in phase; risers read (along-face, height).
 */
export function applyWorldBoxUv(geometry: THREE.BufferGeometry, center: PlanCenter, tileSizeM: number): void {
  if (!geometry.getAttribute("normal")) geometry.computeVertexNormals();
  const positions = geometry.getAttribute("position");
  const normals = geometry.getAttribute("normal");
  const uv = new Float32Array(positions.count * 2);
  for (let i = 0; i < positions.count; i++) {
    const sy = positions.getY(i);
    const [px, py] = projectScenePointToPlan(positions.getX(i), positions.getZ(i), center);
    const nx = Math.abs(normals.getX(i));
    const ny = Math.abs(normals.getY(i));
    const nz = Math.abs(normals.getZ(i));
    const [a, b] = ny >= nx && ny >= nz ? [px, py] : nx >= nz ? [py, sy] : [px, sy];
    uv[i * 2] = a / tileSizeM; uv[i * 2 + 1] = b / tileSizeM;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

