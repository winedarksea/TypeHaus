import { hashBoard } from "./plankLayout";

export type WoodSurface = "natural-clear" | "unfinished" | "painted";
export interface WoodAppearance {
  readonly species?: string | null;
  readonly wood_surface?: WoodSurface | null;
}
export interface WoodSpeciesProfile {
  readonly key: string;
  readonly ringSpacingM: number;
  readonly ringContrast: number;
  readonly poreContrast: number;
  readonly fiberContrast: number;
  readonly interlock: number;
  readonly rayStrength: number;
  readonly variation: number;
  readonly sapwood: number;
  readonly marking: number;
}

// Physical grain dimensions, calibrated with the review scene (plans/wood-appearance.md).
// Oak's rays are wider than ash/elm/locust; red oak has rays too, at a smaller scale.
export const WOOD_SPECIES_PROFILES: Readonly<Record<string, WoodSpeciesProfile>> = {
  cherry: { key: "cherry", ringSpacingM: 0.0032, ringContrast: 0.052, poreContrast: 0.012,
    fiberContrast: 0.012, interlock: 0.04, rayStrength: 0, variation: 0.065, sapwood: 0.08, marking: 0.2 },
  ash: { key: "ash", ringSpacingM: 0.0044, ringContrast: 0.13, poreContrast: 0.055,
    fiberContrast: 0.018, interlock: 0.01, rayStrength: 0, variation: 0.055, sapwood: 0.1, marking: 0.02 },
  elm: { key: "elm", ringSpacingM: 0.0036, ringContrast: 0.11, poreContrast: 0.05,
    fiberContrast: 0.024, interlock: 0.65, rayStrength: 0, variation: 0.075, sapwood: 0.1, marking: 0.04 },
  walnut: { key: "walnut", ringSpacingM: 0.0038, ringContrast: 0.08, poreContrast: 0.03,
    fiberContrast: 0.024, interlock: 0.12, rayStrength: 0, variation: 0.09, sapwood: 0.055, marking: 0.06 },
  oak: { key: "oak", ringSpacingM: 0.0036, ringContrast: 0.115, poreContrast: 0.052,
    fiberContrast: 0.02, interlock: 0.02, rayStrength: 0.1, variation: 0.055, sapwood: 0.06, marking: 0.03 },
  locust: { key: "locust", ringSpacingM: 0.003, ringContrast: 0.11, poreContrast: 0.048,
    fiberContrast: 0.019, interlock: 0.02, rayStrength: 0, variation: 0.065, sapwood: 0.045, marking: 0.03 },
  basswood: { key: "basswood", ringSpacingM: 0.0028, ringContrast: 0.014, poreContrast: 0.004,
    fiberContrast: 0.008, interlock: 0, rayStrength: 0, variation: 0.022, sapwood: 0, marking: 0 },
  "red-oak": { key: "red-oak", ringSpacingM: 0.004, ringContrast: 0.13, poreContrast: 0.066,
    fiberContrast: 0.022, interlock: 0.02, rayStrength: 0.05, variation: 0.065, sapwood: 0.07, marking: 0.03 },
  "sugar-maple": { key: "sugar-maple", ringSpacingM: 0.003, ringContrast: 0.029, poreContrast: 0.006,
    fiberContrast: 0.012, interlock: 0.02, rayStrength: 0, variation: 0.028, sapwood: 0, marking: 0.04 },
};

export function woodSpeciesProfile(species?: string | null): WoodSpeciesProfile | null {
  return species ? WOOD_SPECIES_PROFILES[species] ?? null : null;
}

export const WOOD_RENDER_SETTINGS = {
  satinRoughness: 0.48, unfinishedRoughness: 0.88, paintedRoughness: 0.62,
  maximumTextureEdge: 2048, endGrainDarkening: 0.94,
  clearPoreDepthM: 0.000025, unfinishedPoreDepthM: 0.00008,
  solidFaceWidthM: 1.22, solidTileAlongM: 7.32, solidPixelsPerM: 240,
  continuousTileAlongM: 3.048, plainSawnFraction: 0.72,
  roughnessVariation: 0.08, sapwoodSrgb: [0.88, 0.84, 0.73],
  growthRingsPerBroadBand: 6, filterFootprintPx: 0.5,
} as const;

export function woodSurfaceRoughness(surface?: WoodSurface | null): number {
  return surface === "unfinished" ? WOOD_RENDER_SETTINGS.unfinishedRoughness
    : surface === "painted" ? WOOD_RENDER_SETTINGS.paintedRoughness
    : WOOD_RENDER_SETTINGS.satinRoughness;
}

/** Face/end grain share a seed and ring spacing. All coordinates are physical metres. */
export function woodFigureSampler(seed: number, profile: WoodSpeciesProfile, endGrain = false,
  pixelsPerM = Infinity) {
  const values = Array.from({ length: 11 }, (_, n) => hashBoard(seed + 11, n));
  const random = (n: number) => values[n];
  const phase = random(1) * Math.PI * 2;
  const plain = hashBoard(seed, 42) < WOOD_RENDER_SETTINGS.plainSawnFraction;
  const ringCenterM = 0.025 + random(3) * 0.085;
  const cutDepthRangeM = 0.025 + random(4) * 0.03;
  const cutFrequency = 2 + random(5) * 2;
  const hasMarking = profile.marking > 0 && random(8) < profile.marking;
  const markingX = random(9) * 0.25, markingY = random(10) * 1.8;
  const filter = (radiansPerM: number) => Math.exp(-0.5
    * (radiansPerM / pixelsPerM * WOOD_RENDER_SETTINGS.filterFootprintPx) ** 2);
  const ringFrequency = Math.PI * 2 / profile.ringSpacingM;
  const fineWeight = filter(ringFrequency);
  const broadWeight = filter(ringFrequency / WOOD_RENDER_SETTINGS.growthRingsPerBroadBand);
  const fiberWeight = filter(3700);
  return (x: number, y: number) => {
    const sway = 0.0015 * Math.sin(y * 5 + phase)
      + profile.interlock * 0.002 * Math.sin(y * 42 + x * 61 + phase);
    const across = x + sway;
    const depth = 0.012 + cutDepthRangeM * (0.5 + 0.5 * Math.cos(y * cutFrequency + phase));
    const radius = endGrain ? Math.hypot(x - ringCenterM, y + 0.025)
      : plain ? Math.hypot(across - ringCenterM, depth) : across * 0.65 + 0.001 * Math.sin(y * 8 + phase);
    const growth = radius / profile.ringSpacingM;
    const ring = Math.cos(growth * Math.PI * 2);
    // Band-limited grooves: pores belong to the earlywood bands, not random dark scratches.
    const groupedRings = Math.cos(growth * Math.PI * 2 / WOOD_RENDER_SETTINGS.growthRingsPerBroadBand + phase);
    const early = Math.pow(0.5 + 0.5 * ring, 6);
    const fibers = Math.sin(across * 3700 + Math.sin(y * 18 + phase) * 1.6 + phase)
      * Math.sin(across * 1800 + y * 3);
    const broad = Math.sin(across * 75 + Math.sin(y * 2 + phase) * 0.7 + phase);
    const pore = early * (0.65 + 0.35 * Math.sin(across * 2100 + y * 430));
    let ray = 0;
    if (!plain && !endGrain && profile.rayStrength > 0) {
      const cellX = Math.floor(x / 0.036), cellY = Math.floor(y / 0.027);
      const scatter = hashBoard(cellX + seed * 13, cellY + 9);
      const dx = (x / 0.036 - cellX - 0.5) / (profile.key === "oak" ? 0.5 : 0.26);
      const dy = (y / 0.027 - cellY - 0.5) / 0.08;
      ray = scatter > 0.55 ? Math.max(0, 1 - dx * dx - dy * dy) * profile.rayStrength : 0;
    }
    const marking = hasMarking
      ? Math.exp(-Math.pow((x - markingX) / 0.0015, 2)
        - Math.pow((y - markingY) / 0.014, 2)) * 0.12 : 0;
    return {
      tone: profile.ringContrast * ((0.35 * ring - 0.45 * (early - 0.23)) * fineWeight
        + 0.3 * groupedRings * broadWeight)
        + profile.fiberContrast * fibers * fiberWeight + profile.variation * 0.32 * broad + ray - marking,
      pore: pore * profile.poreContrast * fineWeight,
    };
  };
}

export function sampleWoodFigure(x: number, y: number, seed: number,
  profile: WoodSpeciesProfile, endGrain = false) {
  return woodFigureSampler(seed, profile, endGrain)(x, y);
}
