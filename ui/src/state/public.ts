/**
 * What the published site does not show.
 *
 * type-haus.com/app is the same bundle as the local editor, built with `VITE_PUBLIC_SITE=1`
 * (landing/build-site.mjs). The house it ships is a real one, and its prices are the owner's
 * business — so the Estimate reader and the BOM's cost columns are gated here rather than
 * being deleted from a build nobody else runs.
 *
 * The gate is layered, not single: `ui/scripts/build-house-asset.mjs` also refuses to bundle
 * `prices.toml` / `costs.toml` / `tasks.toml` under `HAUS_PUBLIC=1`, so the numbers are not
 * merely hidden — they are not in the download. This module is the *interface* half: it stops
 * the app offering a page that would come back empty.
 *
 * DOM-free and dependency-free so a test can read it (`public.test.ts`).
 */

export const IS_PUBLIC_SITE = import.meta.env.VITE_PUBLIC_SITE === "1";

/** Report ids the public build does not offer, in the hub, the palette, or anywhere else. */
export const HIDDEN_REPORTS: ReadonlySet<string> = new Set(
  IS_PUBLIC_SITE ? ["estimate"] : [],
);

/**
 * BOM columns the public build drops.
 *
 * These are the columns `model/engineCosts.ts` *appends* to a priced table, not columns the
 * engine's BOM carries — the BOM is quantities, always. Listing them is belt and braces: the
 * public build never fetches costs, so nothing appends them in the first place.
 */
export const HIDDEN_BOM_COLUMNS: ReadonlySet<string> = new Set(
  IS_PUBLIC_SITE ? ["unit_price", "cost", "actual_cost", "paid"] : [],
);

/** Whether a report is offered on this build. */
export function reportVisible(id: string): boolean {
  return !HIDDEN_REPORTS.has(id);
}
