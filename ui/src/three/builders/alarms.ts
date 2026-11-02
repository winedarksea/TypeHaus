// Smoke / CO / combo / heat heads, a flat disc on the ceiling face at the engine's point
// (server/model_json_alarms.py, the same `alarm_xy` the plan sheet and R314 use). Colour per
// kind comes from the theme palette. A head carries its uid (highlight, probe) but no
// selectionKind, so a click on it is inert.
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
  const materials = new Map<string, THREE.MeshStandardMaterial>();
  for (const alarm of alarms) {
    if (alarm.x == null || alarm.y == null || alarm.z == null) continue;
    const color = palette.alarm[alarm.kind] ?? palette.alarm.smoke;
    let material = materials.get(color);
    if (!material) {
      material = standardMaterial(color, mode, { roughness: 0.6 });
      materials.set(color, material);
    }
    const mesh = makeSurfaceMesh(geometry, material);
    // Disc hangs from the ceiling face: its top sits on z.
    mesh.position.set(alarm.x - center[0], alarm.z - THICKNESS_M / 2, -(alarm.y - center[1]));
    mesh.userData.uid = alarm.uid;
    picks.push(mesh);
    parent.add(mesh);
    byUid.set(alarm.uid, [material]);
  }
}
