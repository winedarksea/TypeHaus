import * as THREE from "three";
import { authoredAppearance, type MaterialAppearance } from "../nordic/palette";
import { tiledValueNoise } from "./valueNoise";

// Visual approximation of MSI's Frost White close-up: fine translucent aggregate in a
// cool white ground. Scale is an estimate; confirm against the ordered physical sample.
export const FROST_WHITE_SURFACE = {
  tileSizeM: 0.24,
  textureSizePx: 512,
  ground: 0xf5f5f4,
  roughness: 0.19,
  clearcoat: 0.35,
  clearcoatRoughness: 0.13,
  grainFrequency: 160,
  cloudFrequency: 19,
  grainContrast: 0.12,
  cloudContrast: 0.025,
} as const;

/** Keep this selection on kitchen pieces even if a vanity later shares the slab ref. */
export function isKitchenFrostWhite(piece: { tag: string; material_ref: string },
  materials: readonly MaterialAppearance[] | undefined): boolean {
  return authoredAppearance(piece.material_ref, materials)?.finish === "polished"
    && /^(CT-M-KIT(?:-|$)|STOOL-WIN-M-KIT(?:CH)?(?:-|$))/.test(piece.tag);
}

export function frostWhiteLuminance(u: number, v: number): number {
  const config = FROST_WHITE_SURFACE;
  const grain = tiledValueNoise(u, v, config.grainFrequency);
  const cloud = tiledValueNoise(u, v, config.cloudFrequency);
  return 1 - config.grainContrast * Math.pow(grain, 4) - config.cloudContrast * cloud;
}

let aggregateMap: THREE.DataTexture | undefined;
function frostWhiteMap(): THREE.DataTexture {
  if (aggregateMap) return aggregateMap;
  const size = FROST_WHITE_SURFACE.textureSizePx;
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const index = (y * size + x) * 4;
      const value = Math.round(255 * frostWhiteLuminance(x / size, y / size));
      pixels[index] = pixels[index + 1] = pixels[index + 2] = value;
      pixels[index + 3] = 255;
    }
  }
  aggregateMap = new THREE.DataTexture(pixels, size, size);
  aggregateMap.colorSpace = THREE.SRGBColorSpace;
  aggregateMap.wrapS = aggregateMap.wrapT = THREE.RepeatWrapping;
  aggregateMap.magFilter = THREE.LinearFilter;
  aggregateMap.minFilter = THREE.LinearMipmapLinearFilter;
  aggregateMap.generateMipmaps = true;
  aggregateMap.anisotropy = 4;
  aggregateMap.needsUpdate = true;
  return aggregateMap;
}

export function createFrostWhiteMaterial(): THREE.MeshPhysicalMaterial {
  const config = FROST_WHITE_SURFACE;
  // A polished slab is smooth: aggregate changes colour, not the surface's relief.
  return new THREE.MeshPhysicalMaterial({
    color: config.ground, map: frostWhiteMap(), metalness: 0,
    roughness: config.roughness, clearcoat: config.clearcoat,
    clearcoatRoughness: config.clearcoatRoughness,
  });
}
