// Resolved stair coverings are separate from the stock members they protect.
import * as THREE from "three";
import type { StairFinishPart } from "../../model/types";
import {
  authoredAppearance, floorSurface, materialColor, type MaterialAppearance,
  type ResolvedNordicPalette,
} from "../../nordic/palette";
import { createPlanPrismGeometry, type PlanCenter } from "../planGeometry";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";

export function addStairFinishParts(parent: THREE.Group,
  parts: readonly StairFinishPart[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials?: readonly MaterialAppearance[]) {
  const appearances = new Map<string, THREE.Material>();
  for (const part of parts) {
    const geometry = createPlanPrismGeometry(part.outline, part.z0_m, part.z1_m, [], center);
    if (!geometry) continue;
    let material = appearances.get(part.material_ref);
    if (!material) {
      const recipe = authoredAppearance(part.material_ref, materials)?.finish;
      material = standardMaterial(materialColor(part.material_ref, palette, materials), mode, {
        roughness: mode === "nordic" ? floorSurface(part.material_ref, recipe).roughness : 1,
      });
      appearances.set(part.material_ref, material);
    }
    const mesh = makeSurfaceMesh(geometry, material);
    mesh.userData.memberKey = part.key;
    parent.add(mesh);
  }
}
