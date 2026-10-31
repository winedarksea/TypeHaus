// A surface-channel or shadow-gap LED run (→ emit/gltf/emitter.py::_add_light_run). Split
// out of structure.ts. The engine serves the run's cross-section (`section`, from
// resolve/geometry.py light_run_parts); this sweeps it along each leg and keeps no copy of
// a profile. A raked run (`z_path_m`) is a sheared prism per leg, so it is built as triangles.
import * as THREE from "three";
import type { LightRun, LightRunSectionPart } from "../../model/types";
import { type PlanCenter } from "../planGeometry";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";
import { registerSelectable } from "./registry";

// Mirrors emit/gltf/palette.py `cove_channel` / `led_tape` / `cove_lens` / `cove_flange`.
export const COVE_CHANNEL_COLOR = 0xcccccc; // mill-finish aluminium extrusion
export const LED_TAPE_COLOR = 0xffeabb;     // warm-white tape, bright rather than lit
const COVE_LENS_COLOR = 0xf4f4f0;           // frosted diffuser
const COVE_FLANGE_COLOR = 0xede9e2;         // mudded wing, the ceiling's gypsum

const PART_LOOK: Record<LightRunSectionPart["key"], { color: number; metal: boolean }> = {
  back: { color: COVE_CHANNEL_COLOR, metal: true },
  base: { color: COVE_CHANNEL_COLOR, metal: true },
  lip: { color: COVE_CHANNEL_COLOR, metal: true },
  body: { color: COVE_CHANNEL_COLOR, metal: true },
  tape: { color: LED_TAPE_COLOR, metal: false },
  lens: { color: COVE_LENS_COLOR, metal: false },
  flange: { color: COVE_FLANGE_COLOR, metal: false },
};

// One mesh per section part, swept along every leg. One pick target for the whole run,
// matching the single IfcLightFixture the IFC exporter emits for it.
export function buildLightRun(parent: THREE.Group, run: LightRun, center: PlanCenter,
  mode: "nordic" | "schematic", picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (run.path.length < 2 || !run.section?.length) return;
  const heights = run.z_path_m?.length === run.path.length
    ? run.z_path_m : run.path.map(() => run.z_m);
  const sign = run.emission_side === "right" ? -1 : 1;
  const firstChildIndex = parent.children.length;
  const byKey = new Map<LightRunSectionPart["key"], number[]>();
  for (const part of run.section) {
    const positions = byKey.get(part.key) ?? [];
    byKey.set(part.key, positions);
    // (left-normal offset, rise), wound counter-clockwise seen from the leg's end.
    const ring = part.quad.map(([across, drop]) => [sign * across, -drop] as const);
    let area = 0;
    for (let i = 0; i < ring.length; i++) {
      const [a0, r0] = ring[i];
      const [a1, r1] = ring[(i + 1) % ring.length];
      area += a0 * r1 - a1 * r0;
    }
    if (area < 0) ring.reverse();
    for (let index = 0; index < run.path.length - 1; index++) {
      const p0 = run.path[index];
      const p1 = run.path[index + 1];
      const dx = p1[0] - p0[0];
      const dy = p1[1] - p0[1];
      const len = Math.hypot(dx, dy);
      if (len < 1e-6) continue;
      const nx = -dy / len;
      const ny = dx / len;
      // Plan (x, y, z) to three's Y-up frame.
      const at = (p: readonly [number, number], z: number, a: number, r: number) =>
        [p[0] + nx * a - center[0], z + r, -(p[1] + ny * a - center[1])] as const;
      const start = ring.map(([a, r]) => at(p0, heights[index], a, r));
      const end = ring.map(([a, r]) => at(p1, heights[index + 1], a, r));
      const push = (...points: (readonly [number, number, number])[]) => {
        for (const point of points) positions.push(point[0], point[1], point[2]);
      };
      const n = ring.length;
      for (let i = 1; i < n - 1; i++) {
        push(start[0], start[i + 1], start[i]);
        push(end[0], end[i], end[i + 1]);
      }
      for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        push(start[i], start[j], end[j], start[i], end[j], end[i]);
      }
    }
  }
  for (const [key, positions] of byKey) {
    if (!positions.length) continue;
    const look = PART_LOOK[key];
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.computeVertexNormals();
    parent.add(makeSurfaceMesh(geo, standardMaterial(look.color, mode, {
      roughness: look.metal ? 0.5 : 0.4, metalness: look.metal ? 0.6 : 0,
      flatShading: false, // an inch-scale extrusion: its facets are below a pixel
    })));
  }
  registerSelectable(parent, firstChildIndex, run.uid, "solid", picks, byUid);
}
