// A cove/shadow-gap LED run (→ emit/gltf/emitter.py::_add_light_run). Split out of
// structure.ts. A raked run (`z_path_m`, one height per vertex) is a sheared box per leg,
// so it is built as triangles rather than a plan prism.
import * as THREE from "three";
import type { LightRun } from "../../model/types";
import { rectBetween, type PlanCenter } from "../planGeometry";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";
import { registerSelectable } from "./registry";

// LightRun's channel + tape — mirrors emit/gltf/palette.py `_PALETTE["cove_channel"]` /
// `["led_tape"]`, and the same distinction the Inspector draws for a solid category (a
// channel is what you'd order, tape is what lights).
export const COVE_CHANNEL_COLOR = 0xcccccc; // mill-finish aluminium extrusion
export const LED_TAPE_COLOR = 0xffeabb;     // warm-white tape, bright rather than lit

// The run's outer envelope (→ resolve/geometry.py LIGHT_STRIP_WIDTH_M/HEIGHT_M) — half an
// inch square, in metres.
const LIGHT_STRIP_WIDTH_M = 0.0127;
const LIGHT_STRIP_HEIGHT_M = 0.0127;
const CHANNEL_WALL_M = 0.0048; // 3/16" (→ resolve/trim_bands.py CHANNEL_WALL_M)
const TAPE_HEIGHT_M = 0.0023; // (→ resolve/trim_bands.py TAPE_HEIGHT_M)

// (key, offset from the back, band width, bottom drop, top drop) — one band tuple per row,
// same shape and same numbers as resolve/trim_bands.py `led_cove_bands`. Kept beside the
// colours above rather than imported: this is a small, fixed cross-section recipe, and the
// two sides of the mirror already have to move together (comment cross-reference does the
// rest, the way emit/gltf/palette.py and this file's colour constants already do).
function ledCoveBands(thicknessM: number, depthM: number):
  [key: "back" | "base" | "lip" | "tape", left: number, right: number,
   bottomDrop: number, topDrop: number][] {
  const wall = Math.min(CHANNEL_WALL_M, thicknessM / 3, depthM / 3);
  const lipDepth = depthM * 0.4;
  const tapeH = Math.min(TAPE_HEIGHT_M, depthM - wall);
  const half = thicknessM / 2;
  const span = (offset: number, width: number): [number, number] =>
    [-half + offset, -half + offset + width];
  return [
    ["back", ...span(0, wall), depthM, 0],
    ["base", ...span(wall, thicknessM - 2 * wall), depthM, depthM - wall],
    ["lip", ...span(thicknessM - wall, wall), lipDepth, 0],
    ["tape", ...span(wall, thicknessM - 2 * wall), depthM - wall, depthM - wall - tapeH],
  ];
}

// Channel (back, base, lip) with the tape in the trough. One pick target for the whole run,
// matching the single IfcLightFixture the IFC exporter emits for it.
export function buildLightRun(parent: THREE.Group, run: LightRun, center: PlanCenter,
  mode: "nordic" | "schematic", picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (run.path.length < 2) return;
  const heights = run.z_path_m?.length === run.path.length
    ? run.z_path_m : run.path.map(() => run.z_m);
  const firstChildIndex = parent.children.length;
  for (const [key, left, right, bottomDrop, topDrop] of
    ledCoveBands(LIGHT_STRIP_WIDTH_M, LIGHT_STRIP_HEIGHT_M)) {
    const positions: number[] = [];
    for (let index = 0; index < run.path.length - 1; index++) {
      const p0 = run.path[index];
      const p1 = run.path[index + 1];
      const dx = p1[0] - p0[0];
      const dy = p1[1] - p0[1];
      const run2 = dx * dx + dy * dy;
      if (run2 < 1e-12) continue;
      const za = heights[index];
      const zb = heights[index + 1];
      // Each corner takes the height of its station along the leg (resolve/geometry.py
      // light_run_band_shells), then maps to three's Y-up frame.
      const corner = (point: readonly [number, number], drop: number) => {
        const t = Math.min(Math.max(((point[0] - p0[0]) * dx + (point[1] - p0[1]) * dy) / run2, 0), 1);
        return [point[0] - center[0], za + t * (zb - za) - drop, -(point[1] - center[1])] as const;
      };
      const ring = rectBetween(p0, p1, left, right);
      const bottom = ring.map((point) => corner(point, bottomDrop));
      const top = ring.map((point) => corner(point, topDrop));
      const push = (...points: (readonly [number, number, number])[]) => {
        for (const point of points) positions.push(point[0], point[1], point[2]);
      };
      push(bottom[2], bottom[1], bottom[0], bottom[3], bottom[2], bottom[0]);
      push(top[0], top[1], top[2], top[0], top[2], top[3]);
      for (let side = 0; side < 4; side++) {
        const next = (side + 1) % 4;
        push(bottom[side], bottom[next], top[next], bottom[side], top[next], top[side]);
      }
    }
    if (!positions.length) continue;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.computeVertexNormals();
    parent.add(makeSurfaceMesh(geo, standardMaterial(key === "tape" ? LED_TAPE_COLOR : COVE_CHANNEL_COLOR, mode, {
      roughness: key === "tape" ? 0.4 : 0.5, metalness: key === "tape" ? 0 : 0.6,
      flatShading: false, // half-inch extrusion: its facets are below a pixel either way
    })));
  }
  registerSelectable(parent, firstChildIndex, run.uid, "solid", picks, byUid);
}
