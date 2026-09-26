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

// Integer frequencies keep every octave seamless across the tile. Turbulence bends the
// veins; FADE lets them thin and vanish along their length; CLOUD is the ground's shading.
const TURBULENCE: ReadonlyArray<readonly [number, number]> = [[1, 1], [2, 0.6], [4, 0.3], [8, 0.12]];
const FINE_TURBULENCE: ReadonlyArray<readonly [number, number]> = [[2, 1], [4, 0.5], [8, 0.25], [16, 0.1]];
const FADE: ReadonlyArray<readonly [number, number]> = [[2, 1], [3, 0.5]];
const CLOUD: ReadonlyArray<readonly [number, number]> = [[3, 0.04], [9, 0.02], [27, 0.01]];

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const smoothstep = (a: number, b: number, x: number) => {
  const t = clamp01((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};

/** A line where `phase` crosses zero: 1 on the vein, falling off by `sharpness`. */
function vein(phase: number, sharpness: number): number {
  return Math.pow(1 - Math.abs(Math.sin(phase)), sharpness);
}

/**
 * Luminance of the tile at `u, v` in [0, 1): ~1 on the ground, darker on a vein. Pure, so the
 * pattern can be previewed and tested without a canvas.
 */
export function marbleLuminance(u: number, v: number): number {
  const tau = Math.PI * 2;
  const turb = tiledFbm(u, v, TURBULENCE);
  // Primary: two long veins per tile on the diagonal (wave vector (1, 1)), bent by the
  // turbulence and swelling and pinching along their length — crisp edges, a faint halo.
  const primaryPhase = tau * (u + v) + 2.6 * turb;
  // Band half-width in |sin| units: pinches to a thread, swells to a finger's width.
  const width = 0.02 + 0.22 * clamp01(0.5 + 2.5 * tiledFbm(u + 0.53, v + 0.71, FADE));
  const near = 1 - Math.abs(Math.sin(primaryPhase));
  const core = smoothstep(1 - width, 1 - width * 0.35, near);
  const primaryFade = clamp01(1.1 + 2.5 * tiledFbm(u + 0.37, v + 0.11, FADE));
  const primary = (0.85 * core + 0.15 * vein(primaryPhase, 6)) * primaryFade;
  // Secondary: a web of fine veins branching off at other angles.
  const fine = tiledFbm(v, u, FINE_TURBULENCE);
  const secondary = Math.max(
    vein(tau * (2 * u - v) + 5 * fine, 45) * clamp01(0.6 + 3 * tiledFbm(v + 0.61, u, FADE)),
    vein(tau * (u + 3 * v) + 6 * fine, 60) * clamp01(0.4 + 3 * tiledFbm(u + 0.83, v + 0.29, FADE)),
  );
  return 1 + tiledFbm(u, v + 0.19, CLOUD) - 0.6 * primary - 0.3 * secondary;
}

/** True when a material's declared finish is the veined-marble print. */
export function isVeinedMarble(finish: string | null | undefined): boolean {
  return finish === "veined-marble";
}

let marbleMap: THREE.Texture | null = null;

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
  for (let y = 0; y < MARBLE_TEX_PX; y++) {
    for (let x = 0; x < MARBLE_TEX_PX; x++) {
      const level = Math.round(250 * clamp01(marbleLuminance(x / MARBLE_TEX_PX, y / MARBLE_TEX_PX)));
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
