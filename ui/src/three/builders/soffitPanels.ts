import type * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import type { Solid } from "../../model/types";
import { createPlanPrismGeometry, type PlanCenter } from "../planGeometry";

// Merge the resolver's boards into one pick target, preserving the soffit's stable UID.
export function soffitPanelGeometry(panels: NonNullable<Solid["finish_panels"]>,
  center: PlanCenter): THREE.BufferGeometry | null {
  const geometries = panels.map((panel) => createPlanPrismGeometry(
    panel.outline, panel.z0_m, panel.z1_m, panel.voids, center));
  const valid = geometries.filter((geometry): geometry is THREE.ExtrudeGeometry => geometry !== null);
  if (!valid.length) return null;
  const merged = mergeGeometries(valid);
  for (const geometry of valid) geometry.dispose();
  return merged;
}
