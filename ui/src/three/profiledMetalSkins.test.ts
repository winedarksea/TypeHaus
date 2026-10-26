import * as THREE from "three";
import type { Member, SurfaceMesh, Wall } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { buildWall } from "./builders/walls";
import { buildMembers } from "./members";

/** Physical gable closures must use the same finish as the wall sheet they continue. */
export function runProfiledMetalSkinTests(): void {
  const surface: SurfaceMesh = {
    positions: [[0, -.1, 0], [1, -.1, 0], [0, -.1, 1]],
    normals: [[0, -1, 0], [0, -1, 0], [0, -1, 0]], triangles: [[0, 1, 2]],
  };
  for (const finish of ["board-and-batten", "ribbed-panel", "corrugated"]) {
    const materials = [{ tag: "panel", name: "Painted panel", color: "#6b7076", finish,
      r_per_inch: null, perm_rating: null, density: null }];
    const wall = {
      uid: "wall", tag: "W", kind: "Wall", axis: [[0, 0], [1, 0]],
      z0_m: 0, z1_m: 1, members: [],
      layers: [{ name: "skin", material: "panel", function: "cladding", thickness_m: .022225,
        polygon: [[0, -.122225], [1, -.122225], [1, -.1], [0, -.1]], surface_mesh: surface }],
    } as unknown as Wall;
    const closure = { key: "W-closure-0-skin", material: "panel", category: "cladding",
      surface_mesh: surface } as unknown as Member;
    for (const mode of ["nordic", "schematic"] as const) {
      const groups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as
        Record<Trade, THREE.Group>;
      const closureGroup = new THREE.Group();
      buildWall(groups, wall, [], [0, 0], mode, RESOLVED_NORDIC_PALETTE.light,
        [], new Map(), materials);
      buildMembers(closureGroup, [closure], [0, 0], mode, RESOLVED_NORDIC_PALETTE.light,
        wall.uid, materials);
      const body = groups.siding.children[0] as THREE.Mesh;
      const gable = closureGroup.children[0] as THREE.Mesh;
      const bodyMaterial = body.material as THREE.MeshStandardMaterial;
      const gableMaterial = gable.material as THREE.MeshStandardMaterial;
      if (bodyMaterial.color.getHex() !== 0xe8e8e2
        || !gableMaterial.color.equals(bodyMaterial.color)) {
        throw new Error(`${mode} ${finish}: gable closure uses hatch color instead of wall paint`);
      }
      for (const mesh of [body, gable]) {
        mesh.geometry.dispose(); (mesh.material as THREE.Material).dispose();
      }
    }
  }
}
