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
 * The wire mesh (flat integers of `quantum`, each stream delta-coded per axis) as scene-frame
 * buffers: plan (x, y, z) lands at (x - cx, z, cy - y), the mapping projectPointToScene owns.
 * One tight loop per stream, keeping the running sums.
 */
export function decodeMesh(mesh: PackedMesh, center: PlanCenter = [0, 0]): DecodedMesh {
  // Dividing by the integer scale lands a round value exactly; times 1e-5 would not.
  const scale = Math.round(1 / mesh.quantum);
  const [cx, cy] = center;
  const src = mesh.positions;
  const positions = new Float32Array(src.length);
  let x = 0, y = 0, z = 0;
  for (let i = 0; i < src.length; i += 3) {
    x += src[i]; y += src[i + 1]; z += src[i + 2];
    positions[i] = x / scale - cx;
    positions[i + 1] = z / scale;
    positions[i + 2] = cy - y / scale;
  }
  let normals: Float32Array | null = null;
  if (mesh.normals?.length) {
    const n = mesh.normals;
    normals = new Float32Array(n.length);
    let nx = 0, ny = 0, nz = 0;
    for (let i = 0; i < n.length; i += 3) {
      nx += n[i]; ny += n[i + 1]; nz += n[i + 2];
      normals[i] = nx / NORMAL_SCALE;
      normals[i + 1] = nz / NORMAL_SCALE;
      normals[i + 2] = -ny / NORMAL_SCALE;
    }
  }
  const index = new Uint32Array(mesh.triangles.length);
  let at = 0;
  for (let i = 0; i < index.length; i++) index[i] = at += mesh.triangles[i];
  return { positions, normals, index };
}

/** The engine's encoding, for fixtures: nested plan-frame vectors in, a wire mesh out. */
export function packMesh(positions: Vec3[], triangles: [number, number, number][],
  normals?: Vec3[]): PackedMesh {
  const delta = (values: number[], stride: number) =>
    values.map((v, i) => (i < stride ? v : v - values[i - stride]));
  return {
    quantum: 1e-5,
    positions: delta(positions.flat().map((c) => Math.round(c * 1e5)), 3),
    triangles: delta(triangles.flat(), 1),
    ...(normals ? { normals: delta(normals.flat().map((c) => Math.round(c * NORMAL_SCALE)), 3) } : {}),
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
