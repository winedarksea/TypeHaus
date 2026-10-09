import * as THREE from "three";
import type { Opening, Wall } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { buildOpening } from "./openings";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runTrimlessGlazedDoorTests() {
  const wall: Wall = {
    uid: "wall", tag: "W-1", storey: "S-1", assembly: "A-1", provenance: null,
    axis: [[0, 0], [4, 0]], z0_m: 0, z1_m: 3, top_z0_m: null, top_z1_m: null,
    plate_base_z_m: null, plate_top_z_m: null, layout_axis: null, is_foundation: false,
    layers: [{ name: "stud", material: "spf", function: "structure", thickness_m: 0.18, control: [],
      polygon: [[0, -0.09], [4, -0.09], [4, 0.09], [0, 0.09]] }], members: [],
  };
  const opening: Opening = {
    uid: "study", tag: "D-STUDY", host: wall.tag, kind: "door", is_door: true,
    provenance: null, type_ref: "DT-STUDY", width_m: 0.762, height_m: 2.032, sill_m: 0,
    center_along_m: 2, arch_rise_m: 0, flip_hinge: true, flip_swing: true,
  };
  for (const leafSet of ["pull", "push"] as const) {
    for (const flipSwing of [false, true]) {
      const group = new THREE.Group();
      const picks: THREE.Mesh[] = [];
      const byUid = new Map<string, THREE.Material[]>();
      buildOpening(group, { ...opening, flip_swing: flipSwing }, wall, [0, 0], "nordic",
        RESOLVED_NORDIC_PALETTE.light, "swing", picks, byUid, true, true,
        undefined, undefined, leafSet);
      const meshes = group.children as THREE.Mesh<THREE.BoxGeometry, THREE.MeshStandardMaterial>[];
      const panes = meshes.filter((mesh) => mesh.material.transparent);
      assert(panes.length === 1 && panes[0].material.opacity === 0.48,
        "The trimless door retains a transparent pane in the viewer");
      const wood = meshes.filter((mesh) => !mesh.material.transparent
        && Math.abs(mesh.geometry.parameters.depth - 0.045) < 1e-9);
      assert(wood.length === 4, "Glass sits between wood stiles and rails, without a solid slab");
      const bounds = (mesh: THREE.Mesh) => new THREE.Box3().setFromObject(mesh);
      const leafBounds = wood.reduce((box, mesh) => box.union(bounds(mesh)), new THREE.Box3());
      const pullFace = flipSwing ? 0.09 : -0.09;
      const pushFace = flipSwing ? -0.09 : 0.09;
      const near = (actual: number, expected: number) => Math.abs(actual - expected) < 1e-6;
      assert(leafSet === "pull"
        ? near(flipSwing ? leafBounds.max.z : leafBounds.min.z, pullFace)
        : near(flipSwing ? leafBounds.min.z : leafBounds.max.z,
          pushFace + (flipSwing ? 0.016 : -0.016)),
      "Glazed doors honor pull-flush and push-rebated placement on either swing side");
      const paneBounds = bounds(panes[0]);
      assert(paneBounds.min.x > leafBounds.min.x && paneBounds.max.x < leafBounds.max.x
        && paneBounds.min.y > leafBounds.min.y && paneBounds.max.y < leafBounds.max.y,
      "The pane stays inside the wood perimeter");
      assert(near(leafBounds.min.y, 0.019), "The leaf retains its open ventilation undercut");
      assert(!meshes.some((mesh) => bounds(mesh).min.y < 0.018
        && bounds(mesh).min.x < 2 && bounds(mesh).max.x > 2),
      "No jamb sill or bottom seal closes the relief path");
      assert(picks.length === meshes.length && byUid.has(opening.uid),
        "Glass and joinery remain selectable as the door");
      meshes.forEach((mesh) => mesh.geometry.dispose());
      new Set(meshes.map((mesh) => mesh.material)).forEach((material) => material.dispose());
    }
  }
}
