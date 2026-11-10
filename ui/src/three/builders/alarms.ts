// Smoke / CO / combo / heat / leak heads, a flat disc at the engine's point
// (server/model_json_alarms.py, the same `alarm_xy` the plan sheet and R314 use) on the face
// it names. Colour per kind comes from the theme palette. Each head has its own material, so
// selecting one highlights only that one.
import * as THREE from "three";
import type { Alarm } from "../../model/types";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { type PlanCenter } from "../planGeometry";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";

const DIAMETER_M = 0.127; // ~5"
const THICKNESS_M = 0.038; // ~1.5"

export function buildAlarms(parent: THREE.Group, alarms: readonly Alarm[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const geometry = new THREE.CylinderGeometry(DIAMETER_M / 2, DIAMETER_M / 2, THICKNESS_M, 24);
  for (const alarm of alarms) {
    if (alarm.x == null || alarm.y == null || alarm.z == null) continue;
    const color = palette.alarm[alarm.kind] ?? palette.alarm.smoke;
    const material = standardMaterial(color, mode, { roughness: 0.6 });
    const mesh = makeSurfaceMesh(geometry, material);
    // The disc's bottom rests on a floor; its top sits against a ceiling.
    const centreZ = alarm.z + (alarm.mount === "floor" ? THICKNESS_M : -THICKNESS_M) / 2;
    mesh.position.set(alarm.x - center[0], centreZ, -(alarm.y - center[1]));
    mesh.userData.uid = alarm.uid;
    mesh.userData.selectionKind = "alarm";
    picks.push(mesh);
    parent.add(mesh);
    byUid.set(alarm.uid, [material]);
  }
}
