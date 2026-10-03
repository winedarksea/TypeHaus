import * as THREE from "three";
import type { CanvasObject, ModelPart } from "../../model/types";
import { buildCanvasObjectParts } from "./site";

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

export function runCurvedPlaceableTests(): void {
  // A ribbon surface with a crest in elevation: engine geometry includes its local offset.
  const part: ModelPart = {
    center: [0, 0.2, 0.15], size: [1, 0.04, 0.1], color: "#c7994c", shape: "mesh",
    mesh: {
      positions: [[-0.5, 0.18, 0.1], [-0.5, 0.22, 0.1], [0, 0.18, 0.2],
        [0, 0.22, 0.2], [0.5, 0.18, 0.1], [0.5, 0.22, 0.1]],
      triangles: [[0, 2, 3], [0, 3, 1], [2, 4, 5], [2, 5, 3]],
      normals: [[-0.6, 0, 0.8], [-0.6, 0, 0.8], [0, 0, 1], [0, 0, 1],
        [0.6, 0, 0.8], [0.6, 0, 0.8]],
    },
  };
  const item = { uid: "ED-M-DINING-PEND", position_m: [4, 6], rotation: 90 } as CanvasObject;
  const picks: THREE.Mesh[] = [];
  const byUid = new Map<string, THREE.Material[]>();
  const group = buildCanvasObjectParts(new THREE.Group(), item, [part], [1, 2],
    "nordic", 1.7, picks, byUid);
  const mesh = group.children[0] as THREE.Mesh;
  const geometry = mesh.geometry;
  const positions = geometry.getAttribute("position"), normals = geometry.getAttribute("normal");
  const near = (actual: number, expected: number) => Math.abs(actual - expected) < 1e-6;
  assert(positions.count === part.mesh!.positions.length && geometry.index!.count === 12,
    "Curved parts retain shared vertices and triangulation instead of becoming bounding boxes");
  for (let index = 0; index < positions.count; index++) {
    const [x, y, z] = part.mesh!.positions[index];
    const [nx, ny, nz] = part.mesh!.normals[index];
    assert(near(positions.getX(index), x) && near(positions.getY(index), z)
      && near(positions.getZ(index), -y), "Ribbon positions use the shared scene axis mapping");
    assert(near(normals.getX(index), nx) && near(normals.getY(index), nz)
      && near(normals.getZ(index), -ny), "Analytic normals survive without faceted recomputation");
  }
  assert(mesh.position.length() === 0, "The engine's local offset is applied exactly once");
  group.updateMatrixWorld(true);
  const world = new THREE.Vector3().fromBufferAttribute(positions, 0).applyMatrix4(mesh.matrixWorld);
  assert(near(world.x, 2.82) && near(world.y, 1.8) && near(world.z, -3.5),
    "The ribbon follows the pendant's translation, mounting elevation and plan rotation");
  assert(picks[0] === mesh && mesh.userData.uid === item.uid
    && byUid.get(item.uid)?.[0] === mesh.material,
    "Continuous ribbons retain picking and selection highlighting");
  assert(!(mesh.material as THREE.MeshStandardMaterial).flatShading,
    "Curved strips use the supplied smooth shading in the viewer");
}
