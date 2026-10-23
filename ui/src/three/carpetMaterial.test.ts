import * as THREE from "three";
import {
  applyCarpetUv, buildCarpetMaps, CARPET_TILE_M, carpetSample, createCarpetMaterial, isCarpetPile,
} from "./carpetMaterial";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// Pure (no-canvas) assertions; the maps themselves need a 2D canvas.
export function runCarpetMaterialTests() {
  assert(isCarpetPile("carpet-pile"), "the declared finish selects the carpet recipe");
  assert(!isCarpetPile("carpet") && !isCarpetPile(null) && !isCarpetPile("veined-marble"),
    "only the declared FINISH selects it, never a material tag");

  assert(buildCarpetMaps() === null, "no 2D canvas: no maps, and no throw");
  const flat = createCarpetMaterial("nordic", "#9c8f80", 1) as THREE.MeshStandardMaterial;
  assert(flat.map === null && flat.roughness === 1 && flat.color.getHexString() === "9c8f80",
    "without a canvas the carpet is a flat fill in its own colour and roughness");
  const schematic = createCarpetMaterial("schematic", "#9c8f80", 1) as THREE.MeshStandardMaterial;
  assert(schematic.map === null && schematic.flatShading, "schematic mode is a flat diagram fill");

  for (const t of [0, 0.131, 0.5, 0.873]) {
    const [a, b, c, d] = [carpetSample(0, t), carpetSample(1, t), carpetSample(t, 0), carpetSample(t, 1)];
    assert(Math.abs(a.luminance - b.luminance) < 1e-9 && Math.abs(a.height - b.height) < 1e-12
      && Math.abs(c.luminance - d.luminance) < 1e-9 && Math.abs(c.height - d.height) < 1e-12,
      "the tile is seamless across both edges");
  }
  for (let i = 0; i < 400; i++) {
    const s = carpetSample((i * 0.6180339) % 1, (i * 0.4142136) % 1);
    assert(s.luminance > 0.75 && s.luminance < 1.1, `luminance stays near 1 (${s.luminance})`);
    assert(s.roughness >= 0.85 && s.roughness <= 1, "pile roughness stays high");
  }

  const box = new THREE.BoxGeometry(0.6, 0.18, 0.3);
  applyCarpetUv(box, [0, 0]);
  const uv = box.getAttribute("uv");
  const normal = box.getAttribute("normal");
  for (const axis of ["x", "y", "z"] as const) {
    const us: number[] = [], vs: number[] = [];
    for (let i = 0; i < uv.count; i++) {
      const n = { x: normal.getX(i), y: normal.getY(i), z: normal.getZ(i) };
      if (Math.abs(n[axis]) < 0.9) continue;
      us.push(uv.getX(i)); vs.push(uv.getY(i));
    }
    const span = (xs: number[]) => Math.max(...xs) - Math.min(...xs);
    assert(span(us) > 1e-6 && span(vs) > 1e-6, `faces normal to ${axis} have no zero-span UV axis`);
  }
  const topSpan = (() => {
    const xs: number[] = [];
    for (let i = 0; i < uv.count; i++) if (normal.getY(i) > 0.9) xs.push(uv.getX(i));
    return Math.max(...xs) - Math.min(...xs);
  })();
  assert(Math.abs(topSpan - 0.6 / CARPET_TILE_M) < 1e-6, "the top projects at world scale");
}
