// Add-floor form defaults and validation (→ server/storeys_api.py). Pure.
import type { Storey } from "./types";

// Mirrors storey_modules.TAG_RE: the tag names the module file and its placeables list.
export const STOREY_TAG_RE = /^[a-z][a-z0-9_]*$/;
const DEFAULT_CEILING_M = 2.7432; // 9'

export interface NewFloorDefaults {
  tag: string;
  elevation_m: number;
  ceiling_m: number;
}

// Stack on the top storey: its elevation plus its ceiling. Never moves an existing floor.
export function newFloorDefaults(storeys: Storey[]): NewFloorDefaults {
  const top = storeys.reduce<Storey | null>(
    (best, s) => (best === null || s.elevation_m > best.elevation_m ? s : best), null);
  const used = new Set(storeys.map((s) => s.tag));
  let n = storeys.length + 1;
  while (used.has(`level_${n}`)) n += 1;
  return {
    tag: `level_${n}`,
    elevation_m: top ? top.elevation_m + top.ceiling_m : 0,
    ceiling_m: top?.ceiling_m ?? DEFAULT_CEILING_M,
  };
}

// Null when the tag is usable; otherwise the reason to show under the field.
export function storeyTagError(tag: string, storeys: Storey[]): string | null {
  if (!STOREY_TAG_RE.test(tag)) return "Lowercase letters, digits and _; start with a letter";
  if (storeys.some((s) => s.tag === tag)) return `A floor named ${tag} already exists`;
  return null;
}
