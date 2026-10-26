// ── Cut-pile carpet ─────────────────────────────────────────────────────────────────────
// A cheap PBR read of pile: hashed ~3 mm tufts drive a normal map and a faint luminance
// flicker, low-frequency fbm mottles the pile, and a sheen lobe gives the grazing-angle glow
// that tells textile from matte paint. No fibres, shells or displacement. The colour map is
// luminance only and `material.color` tints it, so one tile serves every carpet colour.
import * as THREE from "three";
import type { PlanCenter } from "./planGeometry";
import { applyWorldBoxUv } from "./worldBoxUv";
import { latticeHash, tiledFbm } from "./valueNoise";

const CARPET_TEX_PX = 512;
/** One repeat, in metres. */
export const CARPET_TILE_M = 0.3;
/** Tufts per tile edge (~3 mm pitch). An integer, so the lattice wraps. */
const TUFTS = 100;
const TUFT_HEIGHT_M = 0.0015;
/** The sheen lobe is the only extra shader cost; switch it off here if it shows. */
export const CARPET_SHEEN = true;

const MOTTLE: ReadonlyArray<readonly [number, number]> = [[3, 0.05], [7, 0.03], [17, 0.015]];
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

export interface CarpetSample { luminance: number; height: number; roughness: number }

/** The tile at `u, v` in [0, 1): pure, so it can be tested without a canvas. */
export function carpetSample(u: number, v: number): CarpetSample {
  const fx = u * TUFTS;
  const fy = v * TUFTS;
  const cx = Math.floor(fx);
  const cy = Math.floor(fy);
  const wrap = (n: number) => ((n % TUFTS) + TUFTS) % TUFTS;
  const seed = latticeHash(wrap(cx), wrap(cy));
  // A jittered tuft centre per cell, with a soft rounded top.
  const ox = 0.3 + 0.4 * latticeHash(wrap(cx) + 0.37, wrap(cy) + 0.91);
  const oy = 0.3 + 0.4 * latticeHash(wrap(cx) + 0.71, wrap(cy) + 0.13);
  const d = Math.hypot(fx - cx - ox, fy - cy - oy) / 0.55;
  const dome = clamp01(1 - d * d);
  const tuft = dome * (0.7 + 0.3 * seed);
  const luminance = 0.92 + 0.12 * (seed - 0.5) * dome + 0.06 * dome + tiledFbm(u, v, MOTTLE);
  return { luminance, height: tuft * TUFT_HEIGHT_M, roughness: 1 - 0.1 * dome };
}

/** True when a material's declared finish is the cut-pile recipe (never the tag, #57). */
export function isCarpetPile(finish: string | null | undefined): boolean {
  return finish === "carpet-pile";
}

interface CarpetMaps { color: THREE.Texture; normal: THREE.Texture; roughness: THREE.Texture }
let carpetMaps: CarpetMaps | null = null;

/** The shared carpet maps, or null where there is no 2D canvas (SSR, headless tests). */
export function buildCarpetMaps(): CarpetMaps | null {
  if (carpetMaps) return carpetMaps;
  if (typeof document === "undefined") return null;
  const size = CARPET_TEX_PX;
  const canvases = Array.from({ length: 3 }, () => {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    return canvas;
  });
  const contexts = canvases.map(canvas => canvas.getContext("2d"));
  if (contexts.some(context => !context)) return null;
  const images = contexts.map(context => context!.createImageData(size, size));
  const heights = new Float32Array(size * size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const sample = carpetSample(x / size, y / size);
    const offset = (y * size + x) * 4;
    const level = Math.round(250 * clamp01(sample.luminance));
    const rough = Math.round(255 * clamp01(sample.roughness));
    for (let c = 0; c < 3; c++) {
      images[0].data[offset + c] = level;
      images[2].data[offset + c] = rough;
    }
    heights[y * size + x] = sample.height;
    for (const image of images) image.data[offset + 3] = 255;
  }
  const wrap = (n: number) => ((n % size) + size) % size;
  const height = (x: number, y: number) => heights[wrap(y) * size + wrap(x)];
  const scale = size / (2 * CARPET_TILE_M);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const dx = (height(x + 1, y) - height(x - 1, y)) * scale;
    const dy = (height(x, y + 1) - height(x, y - 1)) * scale;
    const n = new THREE.Vector3(-dx, -dy, 1).normalize();
    const offset = (y * size + x) * 4;
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
  carpetMaps = { color: textures[0], normal: textures[1], roughness: textures[2] };
  return carpetMaps;
}

/**
 * The carpet surface. `schematic` and a missing canvas keep the flat fill. `roughness` is
 * the finish's own (`floorSurface`).
 */
export function createCarpetMaterial(
  mode: "nordic" | "schematic", color: THREE.ColorRepresentation, roughness: number,
): THREE.Material {
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true });
  }
  const maps = buildCarpetMaps();
  if (!maps) return new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });
  const material = new THREE.MeshPhysicalMaterial({
    color, metalness: 0, roughness,
    map: maps.color, normalMap: maps.normal, roughnessMap: maps.roughness,
    normalScale: new THREE.Vector2(0.5, 0.5),
  });
  if (CARPET_SHEEN) {
    material.sheen = 0.5;
    material.sheenRoughness = 0.8;
    material.sheenColor = new THREE.Color(color).lerp(new THREE.Color(0xffffff), 0.3);
  }
  return material;
}

/** World-scaled pile on floors, treads and risers. */
export function applyCarpetUv(geometry: THREE.BufferGeometry, center: PlanCenter): void {
  applyWorldBoxUv(geometry, center, CARPET_TILE_M);
}

/** Drop the shared carpet maps — only for teardown in tests/hot reload. */
export function disposeCarpetTextures(): void {
  if (carpetMaps) Object.values(carpetMaps).forEach(map => map.dispose());
  carpetMaps = null;
}
