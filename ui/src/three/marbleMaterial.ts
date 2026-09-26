// ── Veined marble (printed sheet flooring) ──────────────────────────────────────────────
// A continuous Calacatta-look print on 12' sheet vinyl: near-white ground, soft cloud, a few
// bold turbulent grey veins and a finer secondary set. No tile or grout lines — the product
// is one sheet. Like the plank maps, the tile is neutral luminance and `material.color`
// tints it, so the authored colour still answers "what colour is this floor".
import * as THREE from "three";
import { tiledFbm } from "./valueNoise";

const MARBLE_TEX_PX = 1024;
/** One repeat = the 12' roll width, so the print repeats at the scale the product does. */
export const MARBLE_TILE_M = 3.6576;

// Octaves for the turbulence that bends the veins, and for the fade that makes them come
// and go along their length. Integer frequencies keep both seamless.
const TURBULENCE: ReadonlyArray<readonly [number, number]> = [[2, 1], [4, 0.5], [8, 0.25], [16, 0.12]];
const FADE: ReadonlyArray<readonly [number, number]> = [[2, 1], [5, 0.5]];
const CLOUD: ReadonlyArray<readonly [number, number]> = [[3, 0.05], [9, 0.025], [27, 0.012]];

/** True when a material's declared finish is the veined-marble print. */
export function isVeinedMarble(finish: string | null | undefined): boolean {
  return finish === "veined-marble";
}

let marbleMap: THREE.Texture | null = null;

/** A thin line where `phase` crosses zero: 1 on the vein, falling off by `sharpness`. */
function vein(phase: number, sharpness: number): number {
  return Math.pow(1 - Math.abs(Math.sin(phase)), sharpness);
}

/**
 * The shared marble tile, or null where there is no 2D canvas (SSR, the headless geometry
 * tests) — the caller then draws a flat fill, never a throw.
 */
export function buildMarbleMap(): THREE.Texture | null {
  if (marbleMap) return marbleMap;
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = MARBLE_TEX_PX;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const image = ctx.createImageData(MARBLE_TEX_PX, MARBLE_TEX_PX);
  const tau = Math.PI * 2;
  for (let y = 0; y < MARBLE_TEX_PX; y++) {
    const v = y / MARBLE_TEX_PX;
    for (let x = 0; x < MARBLE_TEX_PX; x++) {
      const u = x / MARBLE_TEX_PX;
      const turb = tiledFbm(u, v, TURBULENCE);
      // Primary: bold veins on a shallow diagonal (integer wave vector (1, 2) wraps the tile).
      const primary = vein(tau * (u + 2 * v) + 5 * turb, 10)
        * Math.max(0, Math.min(1, 0.55 + 2.2 * tiledFbm(u + 0.37, v, FADE)));
      // Secondary: finer, fainter, crossing at another angle.
      const secondary = vein(tau * (3 * u - 2 * v) + 7 * tiledFbm(v, u, TURBULENCE), 40)
        * Math.max(0, Math.min(1, 0.4 + 2 * tiledFbm(v + 0.61, u, FADE)));
      const lum = 1 + tiledFbm(u, v + 0.19, CLOUD) - 0.42 * primary - 0.16 * secondary;
      const level = Math.max(0, Math.min(255, Math.round(250 * lum)));
      const index = (y * MARBLE_TEX_PX + x) * 4;
      image.data[index] = image.data[index + 1] = image.data[index + 2] = level;
      image.data[index + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  marbleMap = texture;
  return marbleMap;
}

/**
 * The veined-marble floor. `schematic` keeps a flat fill — a diagram, not a surface — and so
 * does a missing canvas. `roughness` is the finish's own (`floorSurface`).
 */
export function createMarbleMaterial(
  mode: "nordic" | "schematic", color: THREE.ColorRepresentation, roughness: number,
): THREE.Material {
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true });
  }
  const map = buildMarbleMap();
  if (!map) return new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });
  return new THREE.MeshStandardMaterial({ color, map, roughness, metalness: 0 });
}

/** Drop the shared marble tile — only for teardown in tests/hot reload. */
export function disposeMarbleTextures(): void {
  marbleMap?.dispose();
  marbleMap = null;
}
