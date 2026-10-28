// Real-canvas checks, run by scripts/wood-review.mjs rather than a DOM mock.
import * as THREE from "three";
import { createPlankMaterial, WOOD_PLANK_STYLES } from "./plankMaterial";
import { boardBoxGeometry, woodMaterialsForGeometry } from "./woodPiece";
import { buildBaseRun } from "./builders/millwork";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import type { BaseRun } from "../model/types";
import { woodMapsSettled } from "./woodMaps";

function pixels(map: THREE.Texture) {
  const canvas = map.image as HTMLCanvasElement;
  return canvas.getContext("2d")!.getImageData(0, 0, canvas.width, canvas.height).data;
}
function digest(map: THREE.Texture) {
  const data = pixels(map);
  let hash = 2166136261;
  for (let i = 0; i < data.length; i += 97) hash = Math.imul(hash ^ data[i], 16777619);
  return hash >>> 0;
}

export async function runWoodBrowserChecks(samples: readonly { species: string; color: string }[]) {
  const failures: string[] = [];
  const check = (condition: unknown, message: string) => { if (!condition) failures.push(message); };
  const style = WOOD_PLANK_STYLES["solid-board"];
  const materials = samples.map(sample => createPlankMaterial("nordic", style, sample.color, undefined, sample));
  const ash = createPlankMaterial("nordic", style, "#c4b18c", undefined, { species: "ash" });
  const oak = createPlankMaterial("nordic", style, "#c4b18c", undefined, { species: "oak" });
  const raw = createPlankMaterial("nordic", style, "#c4b18c", undefined,
    { species: "oak", wood_surface: "unfinished" });
  const painted = createPlankMaterial("nordic", style, "#f4f2ee", undefined,
    { species: "oak", wood_surface: "painted" });
  // Maps are flat placeholders until the worker returns (→ woodMaps.ts); digest the real figure.
  await woodMapsSettled();
  const reports = samples.map((sample, index) => {
    const material = materials[index];
    check(material.map && material.normalMap && material.roughnessMap, `${sample.species}: three maps`);
    check(material.color.getHex() === 0xffffff, `${sample.species}: full-colour map uses neutral tint`);
    check(material.map?.colorSpace === THREE.SRGBColorSpace, `${sample.species}: sRGB albedo`);
    check(material.normalMap?.colorSpace === THREE.NoColorSpace, `${sample.species}: linear normal data`);
    const repeated = createPlankMaterial("nordic", style, sample.color, undefined, sample);
    check(repeated.map === material.map, `${sample.species}: shared cached maps`);
    const end = material.userData.endGrainMaterial as THREE.MeshStandardMaterial;
    check(end?.map && digest(end.map) !== digest(material.map!), `${sample.species}: distinct crosscut figure`);
    check(digest(material.roughnessMap!) !== digest(material.map!), `${sample.species}: separate roughness`);
    const geometry = boardBoxGeometry(new THREE.Matrix4().makeScale(0.15, 0.9, 0.04), style, 7);
    check(Array.isArray(woodMaterialsForGeometry(material, geometry)), `${sample.species}: end material bound`);
    geometry.dispose(); repeated.dispose();
    return { species: sample.species, color: sample.color, albedo: digest(material.map!),
      endGrain: digest(end.map!), roughness: material.roughness,
      dimensions: [material.map!.image.width, material.map!.image.height] };
  });
  check(new Set(reports.map(r => r.albedo)).size === samples.length, "Species maps must differ");
  // Equal base colours must not accidentally share another species' grain.
  check(ash.map !== oak.map && digest(ash.map!) !== digest(oak.map!), "Cache isolates species, not just colour");
  check(raw.map !== oak.map && raw.roughness > oak.roughness, "Unfinished wood keeps its own matte treatment");
  const data = pixels(painted.map!);
  let paintedMinimum = 255, paintedMaximum = 0;
  for (let i = 0; i < data.length; i += 4) {
    paintedMinimum = Math.min(paintedMinimum, data[i]); paintedMaximum = Math.max(paintedMaximum, data[i]);
  }
  check(paintedMaximum === paintedMinimum, "Opaque paint suppresses underlying wood colour variation");
  const group = new THREE.Group(), picks: THREE.Mesh[] = [], byUid = new Map<string, THREE.Material[]>();
  const run = { uid: "wood-review-base", room_uid: "room-1", material_ref: "cherry-base",
    outline: [[0, 0], [1.4, 0], [1.4, 0.02], [0, 0.02]], z0_m: 0, z1_m: 0.09 } as BaseRun;
  buildBaseRun(group, run, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light,
    [{ tag: "cherry-base", species: "cherry", finish: "solid-board", color: "#b77d60" }], picks, byUid);
  check(picks.length === 1 && byUid.get("room-1")?.length === 2,
    "Selecting trim registers both face and end materials on its room");
  return { failures, reports };
}
