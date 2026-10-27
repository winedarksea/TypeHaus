// Cast concrete: a tinted, matte colour map only (no normal map, no extra lights). Bugholes,
// sand-fine grain and form-pour cloud carry the read; the authored colour supplies the tone.
import * as THREE from "three";
import type { PlanCenter } from "./planGeometry";
import { standardMaterial, type ShadingMode } from "./surfaces";
import { latticeHash, tiledFbm, tiledValueNoise } from "./valueNoise";
import { applyWorldBoxUv } from "./worldBoxUv";

export const CONCRETE_SURFACE = {
  textureSizePx: 256,
  tileSizeM: 1.2192,
  pitCells: 40,
  pitChance: 0.16,
  pitDarkness: 0.2,
  grainFrequency: 128,
  grainContrast: 0.05,
  roughness: 0.92,
} as const;
const CLOUD: ReadonlyArray<readonly [number, number]> = [[3, 0.07], [9, 0.04]];

export function isCastConcreteFinish(finish: string | null | undefined): boolean {
  return finish === "cast-concrete";
}

/** Tile-periodic luminance around 0.95; ~1 so the authored colour keeps its tone. */
export function concreteLuminance(u: number, v: number): number {
  const config = CONCRETE_SURFACE;
  const cells = config.pitCells;
  const x = u * cells, y = v * cells;
  const wrap = (n: number) => ((n % cells) + cells) % cells;
  let pit = 0;
  for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
    const cx = Math.floor(x) + dx, cy = Math.floor(y) + dy;
    const sx = wrap(cx), sy = wrap(cy);
    if (latticeHash(sx, sy) > config.pitChance) continue;
    const px = cx + 0.2 + 0.6 * latticeHash(sx + 0.37, sy);
    const py = cy + 0.2 + 0.6 * latticeHash(sx, sy + 0.71);
    const radius = 0.16 + 0.22 * latticeHash(sx + 0.13, sy + 0.29);
    const d = Math.hypot(x - px, y - py) / radius;
    pit = Math.max(pit, Math.max(0, 1 - d * d));
  }
  const grain = tiledValueNoise(u, v, config.grainFrequency) - 0.5;
  return 0.95 + tiledFbm(u, v, CLOUD) + config.grainContrast * grain - config.pitDarkness * pit;
}

let sharedMap: THREE.DataTexture | null = null;
export function buildConcreteMap(): THREE.DataTexture {
  if (sharedMap) return sharedMap;
  const size = CONCRETE_SURFACE.textureSizePx;
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const level = Math.round(255 * Math.max(0, Math.min(1, concreteLuminance(x / size, y / size))));
    pixels.set([level, level, level, 255], (y * size + x) * 4);
  }
  const map = new THREE.DataTexture(pixels, size, size);
  map.wrapS = map.wrapT = THREE.RepeatWrapping;
  map.magFilter = THREE.LinearFilter;
  map.minFilter = THREE.LinearMipmapLinearFilter;
  map.generateMipmaps = true;
  map.colorSpace = THREE.SRGBColorSpace;
  map.anisotropy = 4;
  map.needsUpdate = true;
  sharedMap = map;
  return map;
}

export function createConcreteMaterial(mode: ShadingMode, color: THREE.ColorRepresentation,
  extra: THREE.MeshStandardMaterialParameters = {}): THREE.MeshStandardMaterial {
  if (mode === "schematic") return standardMaterial(color, mode, extra);
  return standardMaterial(color, mode, {
    ...extra, map: buildConcreteMap(), roughness: CONCRETE_SURFACE.roughness, metalness: 0,
  });
}

export function applyConcreteUv(geometry: THREE.BufferGeometry, center: PlanCenter): void {
  applyWorldBoxUv(geometry, center, CONCRETE_SURFACE.tileSizeM);
}

export function disposeConcreteTexture(): void {
  sharedMap?.dispose();
  sharedMap = null;
}
