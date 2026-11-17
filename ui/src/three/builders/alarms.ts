// Smoke / CO / combo / heat / leak / freeze heads: the engine's resolved body
// (resolve/alarm_heads.py, served by server/model_json_alarms.py), the same prism the GLB and
// IFC exports carry. Colour per kind comes from the theme palette. Each head has its own
// material, so selecting one highlights only that one.
import * as THREE from "three";
import type { Alarm } from "../../model/types";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { createPlanPrismGeometry, type PlanCenter } from "../planGeometry";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";

export function buildAlarms(parent: THREE.Group, alarms: readonly Alarm[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  for (const alarm of alarms) {
    const solid = alarm.solid;
    if (!solid) continue;
    const geometry = createPlanPrismGeometry(solid.ring, solid.z0_m, solid.z1_m, [], center);
    if (!geometry) continue;
    const color = palette.alarm[alarm.kind] ?? palette.alarm.smoke;
    const material = standardMaterial(color, mode, { roughness: 0.6 });
    const mesh = makeSurfaceMesh(geometry, material);
    mesh.userData.uid = alarm.uid;
    mesh.userData.selectionKind = "alarm";
    picks.push(mesh);
    parent.add(mesh);
    byUid.set(alarm.uid, [material]);
  }
}
