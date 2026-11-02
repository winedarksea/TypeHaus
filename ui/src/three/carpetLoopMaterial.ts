// ── Multi-level loop pattern carpet ("Structural") ──────────────────────────────────────
// One 36 x 18 in repeat: a web of thin high-pile lines over a lower field, traced from the
// swatch, with ~2.5 mm loop rows running along the 18 in direction. Same cheap recipe as the
// cut pile, but the colour map carries the product's own colours (material.color is white).
import * as THREE from "three";
import type { PlanCenter } from "./planGeometry";
import { applyWorldBoxUv } from "./worldBoxUv";
import { latticeHash, tiledFbm, tiledValueNoise } from "./valueNoise";

const W = 512 * 2;
const H = 512;
export const CARPET_LOOP_TILE_M: readonly [number, number] = [0.9144, 0.4572];
const TILE_IN: readonly [number, number] = [36, 18];
/** Loop rows across the width: 36 in / 2.54 mm. */
const ROWS = 360;
const LINE_HALF_IN = 0.17;
// Baked product colours (the swatch's field and web); material.color is white.
const FIELD_RGB = [0x3c, 0x4c, 0x56] as const;
const LINE_RGB = [0x8b, 0x89, 0x87] as const;
const FIELD_H_M = 0.0008;
const LINE_H_M = 0.0016;
const ROW_H_M = 0.0005;
const MOTTLE: ReadonlyArray<readonly [number, number]> = [[4, 0.04], [11, 0.025]];
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

// Segments traced on the 500 x 250 swatch preview (x along 36 in, y along 18 in). Edge ends
// pair across the repeat (top/bottom by x, left/right by y), so it tiles.
const PX: ReadonlyArray<readonly [number, number, number, number]> = [
  [110, 85, 128, 0],
  [110, 85, 40, 0],
  [300, 45, 282, 0],
  [300, 45, 345, 0],
  [420, 70, 395, 0],
  [420, 70, 485, 0],
  [70, 145, 40, 250],
  [70, 145, 128, 250],
  [230, 135, 282, 250],
  [335, 125, 345, 250],
  [375, 150, 395, 250],
  [375, 150, 485, 250],
  [70, 145, 0, 95],
  [70, 145, 0, 150],
  [420, 70, 500, 95],
  [375, 150, 500, 150],
  [110, 85, 0, 40],
  [420, 70, 500, 40],
  [110, 85, 70, 145],
  [110, 85, 300, 45],
  [300, 45, 230, 135],
  [300, 45, 335, 125],
  [335, 125, 420, 70],
  [335, 125, 230, 135],
  [230, 135, 70, 145],
  [230, 135, 128, 250],
  [375, 150, 335, 125],
  [420, 70, 375, 150],
  [110, 85, 230, 135],
  [230, 135, 375, 150],
];
const SEGMENTS = PX.map(([a, b, c, d]) => [a / 500, b / 250, c / 500, d / 250] as const);

export interface CarpetLoopSample { rgb: readonly [number, number, number]; luminance: number; height: number; roughness: number; line: number }

function lineCoverage(u: number, v: number): number {
  let best = Infinity;
  for (const [ax, ay, bx, by] of SEGMENTS) for (let ox = -1; ox <= 1; ox++) for (let oy = -1; oy <= 1; oy++) {
    const px = (u - ox - ax) * TILE_IN[0], py = (v - oy - ay) * TILE_IN[1];
    const sx = (bx - ax) * TILE_IN[0], sy = (by - ay) * TILE_IN[1];
    const t = clamp01((px * sx + py * sy) / (sx * sx + sy * sy));
    best = Math.min(best, Math.hypot(px - t * sx, py - t * sy));
  }
  // Slightly broken: a coarse noise gap shrinks the line to nothing.
  const gap = tiledValueNoise(u, v, 40) < 0.18 ? 0.35 : 1;
  const half = LINE_HALF_IN * gap;
  return clamp01((half + 0.06 - best) / 0.12);
}

/** The tile at `u, v` in [0, 1): pure; `line` is 1 on the high level. */
export function carpetLoopSample(u: number, v: number): CarpetLoopSample {
  const line = lineCoverage(u, v);
  const row = Math.floor(u * ROWS);
  const along = Math.floor(v * ROWS * 0.5 * (TILE_IN[1] / TILE_IN[0]) * 2);
  const seed = latticeHash(row % ROWS, along % 180);
  const phase = u * ROWS - row;
  const ridge = Math.sin(Math.PI * phase) ** 2;
  const flicker = 0.93 + 0.07 * ridge + 0.05 * (seed - 0.5) + tiledFbm(u, v, MOTTLE);
  const mix = (i: number) => (FIELD_RGB[i] + (LINE_RGB[i] - FIELD_RGB[i]) * line) / 255 * flicker;
  const rgb = [mix(0), mix(1), mix(2)] as const;
  const luminance = (rgb[0] + rgb[1] + rgb[2]) / 3;
  const base = FIELD_H_M + (LINE_H_M - FIELD_H_M) * line;
  return { rgb, luminance, height: base + ROW_H_M * ridge * (0.8 + 0.2 * seed), roughness: 1 - 0.08 * ridge, line };
}

/** True when a material's declared finish is the loop-pattern recipe (never the tag, #57). */
export function isCarpetRefineStructural(finish: string | null | undefined): boolean {
  return finish === "carpet-refine-structural";
}

interface LoopMaps { color: THREE.Texture; normal: THREE.Texture; roughness: THREE.Texture }
let loopMaps: LoopMaps | null = null;

function buildLoopMaps(): LoopMaps | null {
  if (loopMaps) return loopMaps;
  if (typeof document === "undefined") return null;
  const canvases = Array.from({ length: 3 }, () => {
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    return canvas;
  });
  const contexts = canvases.map(canvas => canvas.getContext("2d"));
  if (contexts.some(context => !context)) return null;
  const images = contexts.map(context => context!.createImageData(W, H));
  const heights = new Float32Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const s = carpetLoopSample(x / W, y / H);
    const offset = (y * W + x) * 4;
    const rough = Math.round(255 * clamp01(s.roughness));
    for (let c = 0; c < 3; c++) {
      images[0].data[offset + c] = Math.round(255 * clamp01(s.rgb[c]));
      images[2].data[offset + c] = rough;
    }
    heights[y * W + x] = s.height;
    for (const image of images) image.data[offset + 3] = 255;
  }
  const height = (x: number, y: number) => heights[((y % H) + H) % H * W + ((x % W) + W) % W];
  const scale = W / (2 * CARPET_LOOP_TILE_M[0]);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const n = new THREE.Vector3(-(height(x + 1, y) - height(x - 1, y)) * scale,
      -(height(x, y + 1) - height(x, y - 1)) * scale, 1).normalize();
    const offset = (y * W + x) * 4;
    [n.x, n.y, n.z].forEach((value, i) => { images[1].data[offset + i] = (value * 0.5 + 0.5) * 255; });
  }
  const textures = canvases.map((canvas, index) => {
    contexts[index]!.putImageData(images[index], 0, 0);
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.colorSpace = index === 0 ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    texture.anisotropy = 4;
    return texture;
  });
  loopMaps = { color: textures[0], normal: textures[1], roughness: textures[2] };
  return loopMaps;
}

/** The loop-pattern surface; `schematic` and a missing canvas keep the flat fill. */
export function createCarpetLoopMaterial(
  mode: "nordic" | "schematic", color: THREE.ColorRepresentation, roughness: number,
): THREE.Material {
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true });
  }
  const maps = buildLoopMaps();
  if (!maps) return new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });
  return new THREE.MeshPhysicalMaterial({
    color: 0xffffff, metalness: 0, roughness,
    map: maps.color, normalMap: maps.normal, roughnessMap: maps.roughness,
    normalScale: new THREE.Vector2(0.6, 0.6),
  });
}

/** World-scaled 36 x 18 in repeat on floors, treads and risers. */
export function applyCarpetLoopUv(geometry: THREE.BufferGeometry, center: PlanCenter): void {
  applyWorldBoxUv(geometry, center, CARPET_LOOP_TILE_M);
}

export function disposeCarpetLoopTextures(): void {
  if (loopMaps) Object.values(loopMaps).forEach(map => map.dispose());
  loopMaps = null;
}
