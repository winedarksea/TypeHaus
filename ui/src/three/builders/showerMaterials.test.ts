import * as THREE from "three";
import type { CanvasObject, CanvasObjectType, Paneling } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE, type MaterialAppearance } from "../../nordic/palette";
import { TILE_STYLES, tileRepeatSizeM } from "../tileMaterial";
import { buildCanvasObject } from "./site";
import { buildPaneling } from "./structure";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runShowerMaterialTests() {
  const palette = RESOLVED_NORDIC_PALETTE.light;
  const materials: MaterialAppearance[] = [
    { tag: "solid-surface-panel", color: "#f4f4f2", finish: "tile-swanstone-modern-subway" },
    { tag: "solid-surface-base", color: "#f4f4f2" },
  ];
  const parent = new THREE.Group();
  const picks: THREE.Mesh[] = [];
  const byUid = new Map<string, THREE.Material[]>();
  const band = { uid: "SURROUND", material_ref: "solid-surface-panel",
    outline: [[0, 0], [0.01, 0], [0.01, 1], [0, 1]], z0_m: 0, z1_m: 2.6924 } as Paneling;
  buildPaneling(parent, band, [0, 0], "nordic", palette, materials, picks, byUid);
  const wall = parent.children[0] as THREE.Mesh;
  const uv = wall.geometry.getAttribute("uv");
  assert(uv && Math.max(...Array.from(uv.array)) > 0.5,
    "Subway walls receive world-scaled UVs, not a flat fill or a floor projection");
  const [, courseRepeat] = tileRepeatSizeM(TILE_STYLES["tile-swanstone-modern-subway"]);
  const position = wall.geometry.getAttribute("position");
  const topIndices = Array.from({ length: position.count }, (_, i) => i)
    .filter(i => position.getY(i) > 2);
  assert(topIndices.every(i => Math.abs(uv.getY(i) - position.getY(i) / courseRepeat) < 1e-6),
    "Courses stack up the wall from the band base at the panel's 6-inch module");
  assert((wall.material as THREE.MeshStandardMaterial).roughness === 0.35,
    "The subway panel takes its gloss solid-surface roughness");

  const item = { uid: "SHOWER", position_m: [0, 0], rotation: -90 } as CanvasObject;
  const type = { tag: "SHOWER-TYPE", footprint_m: [0.9144, 0.9144], height_m: 2.6543,
    model_parts: [
      { center: [0, 0, 0.01], size: [0.9144, 0.9144, 0.02], color: "#ecebe8",
        material_ref: "solid-surface-base" },
      { center: [0, 0, 1], size: [0.7, 0.006, 1.8], color: "#8fb7c9", opacity: 0.48 },
      { center: [0, 0, 1], size: [0.02, 0.02, 1.8], color: "#c7ccd1",
        metalness: 1, roughness: 0.12 },
    ] } as CanvasObjectType;
  const group = buildCanvasObject(parent, item, type, [0, 0], "nordic", palette,
    0.0381, picks, byUid, materials) as THREE.Group;
  const [pan, glass, chrome] = group.children as THREE.Mesh[];
  assert(!(pan.material as THREE.MeshStandardMaterial).map,
    "The pan stays smooth: its base material carries no subway relief");
  assert((glass.material as THREE.MeshStandardMaterial).transparent,
    "Glass remains transparent beside the pan");
  assert((chrome.material as THREE.MeshStandardMaterial).metalness === 1,
    "Chrome remains metal beside the pan");
  assert(byUid.has("SURROUND") && byUid.has("SHOWER"), "Both remain independently selectable");
  console.log("Shower material tests passed.");
}
