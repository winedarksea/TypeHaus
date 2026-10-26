// Sprayed skin relief affects lighting only; the resolved insulation keeps its geometry.
import * as THREE from "three";
import type { PlanCenter } from "./planGeometry";
import { standardMaterial, type ShadingMode } from "./surfaces";
import { latticeHash, tiledFbm } from "./valueNoise";
import { applyWorldBoxUv } from "./worldBoxUv";

export const SPRAY_FOAM_SURFACE = {
  textureSizePx: 512,
  tileSizeM: 0.6,
  cellsPerTile: 32,
  cellHeightM: 0.0018,
  cellRadius: 0.48,
  cellRadiusVariation: 0.22,
  centerJitter: 0.7,
  roughness: 0.96,
  anisotropy: 4,
} as const;
const UNDULATION: ReadonlyArray<readonly [number, number]> = [[3, 0.004], [7, 0.0015]];

export function isSprayFoamFinish(finish: string | null | undefined): boolean {
  return finish === "spray-foam";
}

/** Periodic, overlapping rounded lobes avoid a visible square noise lattice. */
export function sprayFoamSample(u: number, v: number): { height: number; luminance: number } {
  const config = SPRAY_FOAM_SURFACE;
  const x = u * config.cellsPerTile, y = v * config.cellsPerTile;
  const wrap = (value: number) => ((value % config.cellsPerTile) + config.cellsPerTile) % config.cellsPerTile;
  let relief = 0;
  for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
    const cellX = Math.floor(x) + dx, cellY = Math.floor(y) + dy;
    const seedX = wrap(cellX), seedY = wrap(cellY);
    const seed = latticeHash(seedX, seedY);
    const centerX = cellX + 0.5 + config.centerJitter * (latticeHash(seedX + 0.37, seedY) - 0.5);
    const centerY = cellY + 0.5 + config.centerJitter * (latticeHash(seedX, seedY + 0.71) - 0.5);
    const radius = config.cellRadius + config.cellRadiusVariation * seed;
    const distance = Math.hypot(x - centerX, y - centerY) / radius;
    // Compact smooth support keeps both height and slope continuous at each lobe's edge.
    const dome = Math.max(0, 1 - distance * distance);
    relief += dome * dome * (0.65 + 0.35 * seed);
  }
  const undulation = tiledFbm(u, v, UNDULATION);
  return {
    height: config.cellHeightM * relief + undulation,
    luminance: 0.97 + 0.02 * (relief - 0.5) + undulation * 4,
  };
}

interface SprayFoamMaps { color: THREE.DataTexture; normal: THREE.DataTexture }
let sharedMaps: SprayFoamMaps | null = null;

/** Typed pixel buffers also work in headless previews; no canvas dependency. */
export function buildSprayFoamMaps(): SprayFoamMaps {
  if (sharedMaps) return sharedMaps;
  const { textureSizePx: size, tileSizeM, anisotropy } = SPRAY_FOAM_SURFACE;
  const heights = new Float32Array(size * size);
  const colorPixels = new Uint8Array(size * size * 4);
  const normalPixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const sample = sprayFoamSample(x / size, y / size);
    const index = y * size + x, offset = index * 4;
    heights[index] = sample.height;
    const level = Math.round(255 * Math.max(0, Math.min(1, sample.luminance)));
    colorPixels.set([level, level, level, 255], offset);
  }
  const height = (x: number, y: number) => heights[((y + size) % size) * size + (x + size) % size];
  const derivativeScale = size / (2 * tileSizeM);
  const normal = new THREE.Vector3();
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    normal.set(
      -(height(x + 1, y) - height(x - 1, y)) * derivativeScale,
      -(height(x, y + 1) - height(x, y - 1)) * derivativeScale, 1,
    ).normalize();
    const offset = (y * size + x) * 4;
    normalPixels.set([normal.x, normal.y, normal.z].map(value => Math.round((value * 0.5 + 0.5) * 255)), offset);
    normalPixels[offset + 3] = 255;
  }
  const texture = (pixels: Uint8Array<ArrayBuffer>, colorSpace: THREE.ColorSpace) => {
    const map = new THREE.DataTexture(pixels, size, size);
    map.wrapS = map.wrapT = THREE.RepeatWrapping;
    map.magFilter = THREE.LinearFilter;
    map.minFilter = THREE.LinearMipmapLinearFilter;
    map.generateMipmaps = true;
    map.colorSpace = colorSpace;
    map.anisotropy = anisotropy;
    map.needsUpdate = true;
    return map;
  };
  sharedMaps = { color: texture(colorPixels, THREE.SRGBColorSpace), normal: texture(normalPixels, THREE.NoColorSpace) };
  return sharedMaps;
}

export function createSprayFoamMaterial(mode: ShadingMode, color: THREE.ColorRepresentation): THREE.MeshStandardMaterial {
  if (mode === "schematic") return standardMaterial(color, mode);
  const maps = buildSprayFoamMaps();
  return standardMaterial(color, mode, {
    map: maps.color, normalMap: maps.normal, roughness: SPRAY_FOAM_SURFACE.roughness, metalness: 0,
  });
}

export function applySprayFoamUv(geometry: THREE.BufferGeometry, center: PlanCenter): void {
  applyWorldBoxUv(geometry, center, SPRAY_FOAM_SURFACE.tileSizeM);
}

export function disposeSprayFoamTextures(): void {
  if (sharedMaps) Object.values(sharedMaps).forEach(map => map.dispose());
  sharedMaps = null;
}
