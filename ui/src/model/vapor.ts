// Water-vapour permeance for the vapour lens (→ TODO: the lens should show the actual
// permeance, not just the control flag).
//
// Mirrors `Material.vapor_permeance_at` (packages/engine/src/typehaus/model/materials.py) —
// keep the two in step. The rule is not a formatting detail: `vapor_permeance_perms` is the
// finished product's ASTM E96 permeance and wins outright, while `perm_rating` is perm-*inch*
// and must be divided by the layer's own thickness. Applying the second rule to the first
// invents a number nobody measured, which is exactly what the engine refuses to do.
//
// `null` means "not authored" and must be reported as UNKNOWN naming the material (→ 32); a
// resolved `0` is a sourced vapour barrier and is a real answer.

import type { Layer, MaterialSpec } from "./types";

export const INCHES_PER_METER = 1 / 0.0254;

/** Permeance in US perms for `thicknessInches` of `material`, or null when unauthored. */
export function vaporPermeanceAt(
  material: Pick<MaterialSpec, "perm_rating" | "vapor_permeance_perms"> | undefined,
  thicknessInches: number,
): number | null {
  if (!material) return null;
  if (material.vapor_permeance_perms != null) return material.vapor_permeance_perms;
  const permeability = material.perm_rating;
  if (permeability == null || permeability <= 0 || thicknessInches <= 0) return null;
  return permeability / thicknessInches;
}

// IRC R702.7 / ASHRAE 160 vapour-retarder classes. Naming the class is what turns a bare
// number into something a reviewer can act on ("Class II — needs to be on the warm side").
export type VaporRetarderClass = "I" | "II" | "III" | "permeable" | "unknown";

export const VAPOR_CLASS_LABEL: Record<VaporRetarderClass, string> = {
  I: "Class I · impermeable",
  II: "Class II · semi-impermeable",
  III: "Class III · semi-permeable",
  permeable: "Permeable",
  unknown: "Not authored",
};

export const VAPOR_CLASS_I_MAX_PERMS = 0.1;
export const VAPOR_CLASS_II_MAX_PERMS = 1.0;
export const VAPOR_CLASS_III_MAX_PERMS = 10.0;

export function vaporRetarderClass(perms: number | null): VaporRetarderClass {
  if (perms == null) return "unknown";
  if (perms <= VAPOR_CLASS_I_MAX_PERMS) return "I";
  if (perms <= VAPOR_CLASS_II_MAX_PERMS) return "II";
  if (perms <= VAPOR_CLASS_III_MAX_PERMS) return "III";
  return "permeable";
}

export interface VaporLayerReading {
  material: string;
  layerName: string;
  thicknessM: number;
  perms: number | null;
  retarderClass: VaporRetarderClass;
  source: string | null;
}

/**
 * One reading per distinct (material, layer) in `layers`, resolved against the catalog.
 * Deduped: a wall stack repeats across dozens of walls, and the lens is describing the
 * *assembly*, not counting instances.
 */
export function vaporReadings(
  layers: readonly Pick<Layer, "name" | "material" | "thickness_m">[],
  materials: readonly MaterialSpec[] | undefined,
): VaporLayerReading[] {
  const catalog = new Map((materials ?? []).map((material) => [material.tag, material]));
  const readings = new Map<string, VaporLayerReading>();
  for (const layer of layers) {
    const key = `${layer.material}|${layer.name}|${layer.thickness_m.toFixed(6)}`;
    if (readings.has(key)) continue;
    const material = catalog.get(layer.material);
    const perms = vaporPermeanceAt(material, layer.thickness_m * INCHES_PER_METER);
    readings.set(key, {
      material: layer.material,
      layerName: layer.name,
      thicknessM: layer.thickness_m,
      perms,
      retarderClass: vaporRetarderClass(perms),
      source: material?.source ?? null,
    });
  }
  // Tightest first: the vapour retarder is the layer the reviewer is looking for, and an
  // unauthored layer sorts last because it is a question, not a measurement.
  return [...readings.values()].sort((a, b) => {
    if (a.perms == null) return b.perms == null ? a.material.localeCompare(b.material) : 1;
    if (b.perms == null) return -1;
    return a.perms - b.perms;
  });
}

/** Format a permeance for display; `0` is a barrier, small values need more precision. */
export function formatPerms(perms: number | null): string {
  if (perms == null) return "—";
  if (perms === 0) return "0 perms (barrier)";
  if (perms < 0.1) return `${perms.toFixed(3)} perms`;
  if (perms < 10) return `${perms.toFixed(2)} perms`;
  return `${Math.round(perms)} perms`;
}
