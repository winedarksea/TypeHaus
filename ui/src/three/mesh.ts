import * as THREE from "three";
import type { PackedMesh, Vec3 } from "../model/types";
import type { PlanCenter } from "./planGeometry";

// Mirrors server/model_json_mesh.py NORMAL_SCALE.
const NORMAL_SCALE = 1e4;

export interface DecodedMesh {
  positions: Float32Array;
  normals: Float32Array | null;
  index: Uint32Array;
}

/**
 * The wire mesh (flat integers of `quantum`) as scene-frame buffers: plan (x, y, z) lands at
 * (x - cx, z, cy - y), the mapping projectPointToScene owns. One tight loop, no nesting.
 */
export function decodeMesh(mesh: PackedMesh, center: PlanCenter = [0, 0]): DecodedMesh {
  // Dividing by the integer scale lands a round value exactly; times 1e-5 would not.
  const scale = Math.round(1 / mesh.quantum);
  const [cx, cy] = center;
  const src = mesh.positions;
  const positions = new Float32Array(src.length);
  for (let i = 0; i < src.length; i += 3) {
    positions[i] = src[i] / scale - cx;
    positions[i + 1] = src[i + 2] / scale;
    positions[i + 2] = cy - src[i + 1] / scale;
  }
  let normals: Float32Array | null = null;
  if (mesh.normals?.length) {
    const n = mesh.normals;
    normals = new Float32Array(n.length);
    for (let i = 0; i < n.length; i += 3) {
      normals[i] = n[i] / NORMAL_SCALE;
      normals[i + 1] = n[i + 2] / NORMAL_SCALE;
      normals[i + 2] = -n[i + 1] / NORMAL_SCALE;
    }
  }
  return { positions, normals, index: Uint32Array.from(mesh.triangles) };
}

/** The engine's encoding, for fixtures: nested plan-frame vectors in, a wire mesh out. */
export function packMesh(positions: Vec3[], triangles: [number, number, number][],
  normals?: Vec3[]): PackedMesh {
  return {
    quantum: 1e-5,
    positions: positions.flat().map((c) => Math.round(c * 1e5)),
    triangles: triangles.flat(),
    ...(normals ? { normals: normals.flat().map((c) => Math.round(c * NORMAL_SCALE)) } : {}),
  };
}

export function meshTriangleCount(mesh: PackedMesh): number {
  return mesh.triangles.length / 3;
}

/** Indexed geometry carrying the engine's own normals (surface skins, curved product parts). */
export function packedMeshGeometry(mesh: PackedMesh, center: PlanCenter = [0, 0]): THREE.BufferGeometry {
  const { positions, normals, index } = decodeMesh(mesh, center);
  if (!normals || normals.length !== positions.length) throw new Error("Invalid packed mesh normals");
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
  geometry.setIndex(new THREE.BufferAttribute(index, 1));
  return geometry;
}
