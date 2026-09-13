// A LEVEL is a datum, and every storey standing on it.
//
// The engine gives a storey two facts: an elevation, and the building it belongs to. Five of
// catlin's structures hold a storey at 0'-0" — the house's main floor, the garage deck, the
// porch, the north entry, the yard pads — so the flat storey list is fourteen entries long
// and names each datum up to five times. That is not a choice a reader should be offered:
// "main" and "court-main" are not alternative views of the building, they are one horizontal
// cut through two of its structures, and a plan wants BOTH. Fourteen toggles is clutter in
// the editor and, on a drawing set, a builder reading a floor plan with no porch on it.
//
// So the picker offers datums and the canvas draws every storey on the one chosen — which is
// what the storey key meant before the building axis existed. That is why this restores the
// main-floor view rather than changing it.
//
// The grouping itself comes from the engine (`model.levels`, → PlanModel.levels): picking a
// level's primary tag has a rule — the dwelling's storey wins, so the list reads basement /
// garage / main / second / attic — and a rule written twice is a rule that drifts. The
// fallback below is for an older model.json only, where there was one structure and a storey
// already was a level.
import type { Level as WireLevel, Model } from "./types";

export interface Level {
  /** The primary storey's tag: what the tab says, and what a new element is authored onto. */
  key: string;
  elevation_m: number;
  /** Every storey on this datum — the canvas's display filter. */
  storeys: string[];
}

export function levelsOf(model: Model): Level[] {
  const wire: WireLevel[] | undefined = model.levels;
  if (wire?.length) {
    return wire.map((l) => ({ key: l.key, elevation_m: l.elevation_m, storeys: l.storeys }));
  }
  return [...model.storeys]
    .sort((a, b) => a.elevation_m - b.elevation_m)
    .map((s) => ({ key: s.tag, elevation_m: s.elevation_m, storeys: [s.tag] }));
}

/** Every storey the canvas draws when `activeStorey` is picked — the whole datum.
 *
 *  `null` means "no storey filter", which the slice already reads as show-everything. A tag
 *  belonging to no level answers with itself, so a stale saved view draws one storey rather
 *  than silently drawing the entire house. */
export function storeysAtDatum(model: Model, activeStorey: string | null): Set<string> | null {
  if (!activeStorey) return null;
  for (const level of levelsOf(model)) {
    if (level.storeys.includes(activeStorey)) return new Set(level.storeys);
  }
  return new Set([activeStorey]);
}

/** The level a tag belongs to, addressed by its primary key — what the picker highlights. */
export function activeLevelKey(model: Model, activeStorey: string | null): string | null {
  if (!activeStorey) return null;
  const level = levelsOf(model).find((l) => l.storeys.includes(activeStorey));
  return level ? level.key : activeStorey;
}
