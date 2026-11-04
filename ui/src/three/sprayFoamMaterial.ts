// Sprayed skin relief affects lighting only; the resolved insulation keeps its geometry.
import * as THREE from "three";
import { textureTimer } from "./buildTimings";
import { writeHeightNormals } from "./heightNormals";
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

// Each cell's seed and centre jitter, hashed once rather than 27 sins per pixel.
let cellTable: Float64Array | null = null;
function cells(): Float64Array {
  if (cellTable) return cellTable;
  const { cellsPerTile: n, centerJitter } = SPRAY_FOAM_SURFACE;
  cellTable = new Float64Array(n * n * 3);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const i = (y * n + x) * 3;
    cellTable[i] = latticeHash(x, y);
    cellTable[i + 1] = 0.5 + centerJitter * (latticeHash(x + 0.37, y) - 0.5);
    cellTable[i + 2] = 0.5 + centerJitter * (latticeHash(x, y + 0.71) - 0.5);
  }
  return cellTable;
}

/** Periodic, overlapping rounded lobes avoid a visible square noise lattice. */
export function sprayFoamSample(u: number, v: number): { height: number; luminance: number } {
  const config = SPRAY_FOAM_SURFACE;
  const x = u * config.cellsPerTile, y = v * config.cellsPerTile;
  const wrap = (value: number) => ((value % config.cellsPerTile) + config.cellsPerTile) % config.cellsPerTile;
  const table = cells();
  let relief = 0;
  for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
    const cellX = Math.floor(x) + dx, cellY = Math.floor(y) + dy;
    const i = (wrap(cellY) * config.cellsPerTile + wrap(cellX)) * 3;
    const seed = table[i];
    const centerX = cellX + table[i + 1];
    const centerY = cellY + table[i + 2];
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
  const timed = textureTimer("sprayFoam");
  const { textureSizePx: size, tileSizeM, anisotropy } = SPRAY_FOAM_SURFACE;
  const heights = new Float32Array(size * size);
  const colorPixels = new Uint8Array(size * size * 4);
  const normalPixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const sample = sprayFoamSample(x / size, y / size);
    const index = y * size + x, offset = index * 4;
    heights[index] = sample.height;
    const level = Math.round(255 * Math.max(0, Math.min(1, sample.luminance)));
    colorPixels[offset] = colorPixels[offset + 1] = colorPixels[offset + 2] = level;
    colorPixels[offset + 3] = normalPixels[offset + 3] = 255;
  }
  const derivativeScale = size / (2 * tileSizeM);
  writeHeightNormals(heights, size, size, derivativeScale, derivativeScale, normalPixels);
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
  timed();
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
