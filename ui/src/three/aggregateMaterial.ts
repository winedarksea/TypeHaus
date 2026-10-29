// ── Loose aggregate (washed stone, crushed base, drain-column #57, sands) ────────────────
// A cached luminance map of angular speckle, tinted by `material.color` so one tile serves
// every stone. World-scaled via `worldBoxUv`: one stone reads about 1 inch. No 2D canvas
// (Node geometry tests) -> a plain flat fill, never a throw.
import * as THREE from "three";
import type { PlanCenter } from "./planGeometry";
import { standardMaterial, type ShadingMode } from "./surfaces";
import { applyWorldBoxUv } from "./worldBoxUv";

export type AggregateKind = "stone" | "sand";

interface Recipe { tileM: number; px: number; count: number; minPx: number; maxPx: number; lo: number; hi: number }
// stone: ~1" pieces (25 mm = 21 px at 0.3 m / 256 px); sand: ~1 mm grains, tighter tonal range.
const RECIPES: Readonly<Record<AggregateKind, Recipe>> = {
  stone: { tileM: 0.3, px: 256, count: 190, minPx: 10, maxPx: 22, lo: 0.62, hi: 1 },
  sand: { tileM: 0.1, px: 256, count: 2600, minPx: 1.5, maxPx: 3.5, lo: 0.8, hi: 1 },
};

const STONE_REFS: ReadonlySet<string> = new Set([
  "capillary-break-stone", "footing-crushed-stone", "mndot-class-5-base",
]);
const STONE_CATEGORIES: ReadonlySet<string> = new Set(["drain_column"]);

/** Stone aggregate by material ref (or category). Sands are separate (`isSand`). */
export function isAggregate(materialRef?: string | null, category?: string | null): boolean {
  return STONE_REFS.has((materialRef ?? "").toLowerCase())
    || STONE_CATEGORIES.has((category ?? "").toLowerCase());
}

/** `usga-*` sands and the rootzone mix. */
export function isSand(materialRef?: string | null): boolean {
  const ref = (materialRef ?? "").toLowerCase();
  return ref.startsWith("usga-") || ref === "rootzone-sand";
}

/** Which speckle recipe a solid takes, or null for a plain fill. */
export function aggregateKind(
  materialRef?: string | null, category?: string | null,
): AggregateKind | null {
  if (isSand(materialRef)) return "sand";
  return isAggregate(materialRef, category) ? "stone" : null;
}

// Small seeded PRNG: the tile is identical across reloads.
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const textures: Partial<Record<AggregateKind, THREE.Texture>> = {};

/** The shared speckle tile, or null where there is no 2D canvas (SSR, headless tests). */
export function buildAggregateTexture(kind: AggregateKind): THREE.Texture | null {
  const cached = textures[kind];
  if (cached) return cached;
  if (typeof document === "undefined") return null;
  const recipe = RECIPES[kind];
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = recipe.px;
  const context = canvas.getContext("2d");
  if (!context) return null;
  const gray = (level: number) => {
    const v = Math.round(255 * level);
    return `rgb(${v},${v},${v})`;
  };
  context.fillStyle = gray((recipe.lo + recipe.hi) / 2 * 0.8);
  context.fillRect(0, 0, recipe.px, recipe.px);
  const random = mulberry32(kind === "stone" ? 0x57 : 0x5a);
  for (let i = 0; i < recipe.count; i++) {
    const cx = random() * recipe.px, cy = random() * recipe.px;
    const radius = recipe.minPx / 2 + random() * (recipe.maxPx - recipe.minPx) / 2;
    const sides = 5 + Math.floor(random() * 3);
    const phase = random() * Math.PI * 2;
    const points = Array.from({ length: sides }, (_, k) => {
      const angle = phase + (k / sides) * Math.PI * 2;
      const r = radius * (0.65 + 0.35 * random());
      return [Math.cos(angle) * r, Math.sin(angle) * r] as const;
    });
    context.fillStyle = gray(recipe.lo + random() * (recipe.hi - recipe.lo));
    // Wrapped copies at the tile edges keep the repeat seamless.
    for (const ox of [-recipe.px, 0, recipe.px]) for (const oy of [-recipe.px, 0, recipe.px]) {
      const x = cx + ox, y = cy + oy;
      if (x < -radius || y < -radius || x > recipe.px + radius || y > recipe.px + radius) continue;
      context.beginPath();
      points.forEach(([dx, dy], k) => (k ? context.lineTo(x + dx, y + dy) : context.moveTo(x + dx, y + dy)));
      context.closePath();
      context.fill();
    }
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  textures[kind] = texture;
  return texture;
}

/**
 * Aggregate surface tinted `color`. Schematic mode and a missing canvas keep a flat-shaded
 * fill; faceted normals read as loose aggregate in both modes.
 */
export function createAggregateMaterial(
  mode: ShadingMode, color: THREE.ColorRepresentation, kind: AggregateKind = "stone",
  overrides: THREE.MeshStandardMaterialParameters = {},
): THREE.MeshStandardMaterial {
  const map = mode === "nordic" ? buildAggregateTexture(kind) : null;
  return standardMaterial(color, mode, {
    roughness: 1, flatShading: kind === "stone", ...(map ? { map } : {}), ...overrides,
  });
}

export function applyAggregateUv(
  geometry: THREE.BufferGeometry, center: PlanCenter, kind: AggregateKind = "stone",
): void {
  applyWorldBoxUv(geometry, center, RECIPES[kind].tileM);
}

export function disposeAggregateTextures(): void {
  for (const kind of Object.keys(textures) as AggregateKind[]) {
    textures[kind]?.dispose();
    delete textures[kind];
  }
}
