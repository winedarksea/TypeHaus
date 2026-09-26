// Window stools arrive with resolved geometry; the viewer only draws their oak surface.
import * as THREE from "three";
import type { WindowStool } from "../../model/types";
import { materialColor, type MaterialAppearance, type ResolvedNordicPalette } from "../../nordic/palette";
import { createPlanPrismGeometry, type PlanCenter } from "../planGeometry";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";
import { registerSelectable } from "./registry";

export function buildWindowStool(parent: THREE.Group, stool: WindowStool, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (stool.outline.length < 3 || stool.z1_m <= stool.z0_m) return;
  const geometry = createPlanPrismGeometry(stool.outline, stool.z0_m, stool.z1_m, [], center);
  if (!geometry) return;
  const firstChildIndex = parent.children.length;
  parent.add(makeSurfaceMesh(geometry, standardMaterial(
    materialColor(stool.material_ref, palette, materials), mode)));
  registerSelectable(parent, firstChildIndex, stool.opening_uid, "opening", picks, byUid);
}
