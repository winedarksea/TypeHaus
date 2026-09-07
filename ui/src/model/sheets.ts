// Arrangement for the printed sheet index — which series a sheet belongs to, in what order,
// and what "next sheet" means. DOM-free so it is testable without a browser, the same split
// model/engineBom.ts makes for the BOM.
//
// The engine numbers sheets to the National CAD Standard's discipline series (emit/draw/
// sheets.py): G general, S structural, A architectural, P plumbing, M mechanical, E
// electrical. That order is a convention a contractor already knows — it is the order the
// sheets are bound in — so the list follows it rather than sorting alphabetically, which
// would put the architectural plans in front of the cover.

import type { SheetEntry } from "../engine/EngineClient";

/** NCS discipline order. `C` (civil) is here for a house that grows a site set. */
export const SERIES_ORDER = ["G", "C", "S", "A", "P", "M", "E"] as const;
export type Series = (typeof SERIES_ORDER)[number] | "?";

export const SERIES_LABEL: Record<Series, string> = {
  G: "General",
  C: "Civil",
  S: "Structural",
  A: "Architectural",
  P: "Plumbing",
  M: "Mechanical",
  E: "Electrical",
  "?": "Other",
};

/** `"A-101"` → `"A"`. A number the engine numbered some other way falls to `"?"`. */
export function seriesOf(number: string): Series {
  const letter = number.trim().charAt(0).toUpperCase();
  return (SERIES_ORDER as readonly string[]).includes(letter) ? (letter as Series) : "?";
}

export interface SheetGroup {
  readonly series: Series;
  readonly label: string;
  readonly sheets: readonly SheetEntry[];
}

/**
 * Sheets grouped by series, in NCS order, each group in page order.
 *
 * Page order rather than number order within a group: the page is where the sheet actually
 * is in the set, and the two agree except when the engine composes a series out of numeric
 * sequence. When they disagree the set itself is the authority.
 */
export function groupSheets(sheets: readonly SheetEntry[]): SheetGroup[] {
  const buckets = new Map<Series, SheetEntry[]>();
  for (const sheet of sheets) {
    const series = seriesOf(sheet.number);
    const bucket = buckets.get(series);
    if (bucket) bucket.push(sheet);
    else buckets.set(series, [sheet]);
  }
  const groups: SheetGroup[] = [];
  for (const series of [...SERIES_ORDER, "?"] as Series[]) {
    const bucket = buckets.get(series);
    if (!bucket) continue;
    groups.push({
      series,
      label: SERIES_LABEL[series],
      sheets: [...bucket].sort((a, b) => a.page - b.page),
    });
  }
  return groups;
}

/** The sheet `number` names, or null. Exact match — sheet numbers are not prefixes. */
export function findSheet(sheets: readonly SheetEntry[], number: string | null): SheetEntry | null {
  if (!number) return null;
  return sheets.find((sheet) => sheet.number === number) ?? null;
}

/** Step through the set in page order. Returns null at the ends rather than wrapping: a
 *  wrap would make "next" past the last sheet look like nothing happened. */
export function stepSheet(sheets: readonly SheetEntry[], current: string | null,
                          delta: 1 | -1): SheetEntry | null {
  const ordered = [...sheets].sort((a, b) => a.page - b.page);
  if (!ordered.length) return null;
  const index = ordered.findIndex((sheet) => sheet.number === current);
  if (index < 0) return delta === 1 ? ordered[0] : ordered[ordered.length - 1];
  const next = ordered[index + delta];
  return next ?? null;
}

export const nextSheet = (sheets: readonly SheetEntry[], current: string | null) =>
  stepSheet(sheets, current, 1);
export const prevSheet = (sheets: readonly SheetEntry[], current: string | null) =>
  stepSheet(sheets, current, -1);
