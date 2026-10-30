import * as THREE from "three";
import type { LightRun } from "../../model/types";
import { buildLightRun } from "./lightRun";

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

// The served section sweeps to a closed, outward-wound prism on the emission side.
export function runLightRunBuilderTests(): void {
  const run = {
    uid: "lr", tag: "LR", storey: "main", path: [[0, 0], [0, 2]], z_m: 3,
    length_m: 2, type: "T", room: null, circuit: null, psu_ref: null, controlled_by: [],
    provenance: null, emission_side: "left",
    section: [{ key: "body", quad: [[0.01, -0.03], [0.03, -0.03], [0.03, 0], [0.01, 0]] }],
  } as LightRun;
  for (const side of ["left", "right"] as const) {
    const group = new THREE.Group();
    buildLightRun(group, { ...run, emission_side: side }, [0, 0], "nordic", [], new Map());
    const geometry = (group.children[0] as THREE.Mesh).geometry;
    geometry.computeBoundingBox();
    const box = geometry.boundingBox!;
    // A north-going leg's left is west (three x < 0); drop -0.03 rises above z.
    const west = side === "left";
    assert(west ? box.max.x <= -0.01 + 1e-9 : box.min.x >= 0.01 - 1e-9,
      `the ${side} section stands on its emission side`);
    assert(Math.abs(box.max.y - 3.03) < 1e-6 && Math.abs(box.min.y - 3) < 1e-6,
      "drop is measured down from the run's height");
    const p = geometry.getAttribute("position");
    let volume = 0;
    for (let i = 0; i < p.count; i += 3) {
      const a = new THREE.Vector3().fromBufferAttribute(p, i);
      const b = new THREE.Vector3().fromBufferAttribute(p, i + 1);
      const c = new THREE.Vector3().fromBufferAttribute(p, i + 2);
      volume += a.dot(b.cross(c)) / 6;
    }
    assert(Math.abs(volume - 0.02 * 0.03 * 2) < 1e-8, `the ${side} sweep is closed and outward`);
  }
}
