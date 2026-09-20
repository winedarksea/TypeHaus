// Trade visibility: the groups the Views panel toggles, the chips inside them, and the one
// two rules the viewers apply — `anyTradeVisible` (drawn iff ANY trade in the set is on) and
// `primaryTradeVisible` (drawn iff the FIRST is), which is what lets a multi-trade body be
// isolated away.
//
// Isolation is the dominant gesture ("only concrete"), and a wall body is several trades at
// once (its studs are framing, its foam insulation, its cladding siding, its board drywall),
// so a per-element boolean was never going to be honest. The tables here are generated from
// the engine (emit/trades.py → generated/vocabulary.json); the functions are the UI's.
import vocabulary from "../generated/vocabulary.json";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import type { CanvasObject, Layer, Roof, Solid, Wall } from "./types";
import {
  FACET_KEYS, FACET_LABEL, FACETS, type FacetKey, facetsOf, facetTrade, withFacets,
} from "./visibilityFacets";

// --- facets ---------------------------------------------------------------------------
// Viewer-only splits of one trade (`framing:sheathing`, `concrete:rebar`): the table and the
// reasons for each live in visibilityFacets.ts. Everything below reads the table.
export {
  FACETS, FACET_KEYS, FRAMING_FACETS, type FacetKey, type FramingFacet,
} from "./visibilityFacets";

/** Keys a fresh session starts with OFF: the facets the table marks so. Every trade is a
 *  scope somebody bids and starts visible. */
export const DEFAULT_OFF_KEYS: readonly FacetKey[] =
  FACETS.filter((facet) => facet.defaultOff).map((facet) => facet.key);

/** What the Views panel can switch on and off: every trade, plus the facets. */
export type VisibilityKey = Trade | FacetKey;

export const ALL_VISIBILITY_KEYS: VisibilityKey[] = [...ALL_TRADES, ...FACET_KEYS];

/** The keys a trade covers — the bare trade, then its facets. */
export function visibilityKeysOf(trade: Trade): VisibilityKey[] {
  return [trade, ...facetsOf(trade)];
}

/** The trade a visibility key answers to: a facet's own trade, else the key itself. */
export function baseTrade(key: VisibilityKey): Trade {
  return facetTrade(key);
}

export interface TradeGroup {
  id: string;
  label: string;
  trades: Trade[];
}

/** The viewer's toggles, in engine order. Partition of ALL_TRADES. */
export const TRADE_GROUPS: TradeGroup[] = (vocabulary.tradeGroups as TradeGroup[]);

/** trade -> group id. */
export const TRADE_GROUP_OF: Record<Trade, string> = Object.fromEntries(
  TRADE_GROUPS.flatMap((group) => group.trades.map((trade) => [trade, group.id])),
) as Record<Trade, string>;

/** What a chip prints. */
export const TRADE_LABEL: Record<Trade, string> = vocabulary.tradeLabels as Record<Trade, string>;

/** What a Views-panel chip prints for one visibility key. */
export function visibilityKeyLabel(key: VisibilityKey): string {
  // `framing` shows as chips beside its facets, so "Framing" beside a "Framing" group header
  // would read as the whole group — hence the facet's own label.
  return FACET_LABEL[key as FacetKey] ?? TRADE_LABEL[key as Trade];
}

export type VisibleTrades = Record<VisibilityKey, boolean>;
export type GroupState = "on" | "off" | "mixed";

const KNOWN = new Set<string>(ALL_VISIBILITY_KEYS);

/** Draw iff any of `trades` is visible. An element that names no trade is always drawn:
 *  hiding what nobody classified would make a missing tag look like a toggle. An unknown
 *  token is skipped rather than trusted. */
export function anyTradeVisible(
  trades: readonly string[] | null | undefined, visible: VisibleTrades,
): boolean {
  const known = (trades ?? []).filter((trade) => KNOWN.has(trade)) as VisibilityKey[];
  if (known.length === 0) return true;
  return known.some((trade) => visible[trade] !== false);
}

export function groupState(groupId: string, visible: VisibleTrades): GroupState {
  const group = TRADE_GROUPS.find((g) => g.id === groupId);
  if (!group) return "off";
  const keys = group.trades.flatMap(visibilityKeysOf);
  const on = keys.filter((key) => visible[key] !== false).length;
  return on === 0 ? "off" : on === keys.length ? "on" : "mixed";
}

/** Literally everything on — what the "All" button restores. */
export function allVisibleTrades(): VisibleTrades {
  return Object.fromEntries(ALL_VISIBILITY_KEYS.map((key) => [key, true])) as VisibleTrades;
}

/** What a fresh session opens with: everything except `DEFAULT_OFF_KEYS`. */
export function defaultVisibleTrades(): VisibleTrades {
  const out = allVisibleTrades();
  for (const key of DEFAULT_OFF_KEYS) out[key] = false;
  return out;
}

/** Exactly `keys` on, everything else off. Keys are taken literally — a saved view that had
 *  the sheathing facet off must come back with it off — so a caller that means a whole trade
 *  (a role preset) expands it first with `visibilityKeysOf`. */
export function onlyTrades(keys: readonly VisibilityKey[]): VisibleTrades {
  const wanted = new Set<string>(keys);
  return Object.fromEntries(
    ALL_VISIBILITY_KEYS.map((key) => [key, wanted.has(key)])) as VisibleTrades;
}

/** A role preset names groups and/or individual trades; both expand to trades. */
export interface RolePreset {
  groups?: string[];
  trades?: Trade[];
  /** Facets the named trades would bring along that this role does not want. */
  exclude?: FacetKey[];
}

export function expandRolePreset(preset: RolePreset): VisibilityKey[] {
  const out = new Set<Trade>(preset.trades ?? []);
  for (const id of preset.groups ?? []) {
    for (const trade of TRADE_GROUPS.find((g) => g.id === id)?.trades ?? []) out.add(trade);
  }
  // A preset names TRADES, so a named `framing` means the sheathing it bids as well.
  const excluded = new Set<string>(preset.exclude ?? []);
  return ALL_TRADES.filter((trade) => out.has(trade)).flatMap(visibilityKeysOf)
    .filter((key) => !excluded.has(key));
}

// Role presets: the trades each discipline reviews. Selecting one shows exactly those and
// hides the rest, so Structure can read stair continuity with the finish floors dropped.
export const ROLE_PRESETS: Record<string, RolePreset> = {
  Architecture: { groups: ["walls", "openings", "finishes", "roof", "furniture"],
    trades: ["stairs"] },
  Structure: { groups: ["structure", "concrete_masonry"], trades: ["roofing"] },
  // Drainage sits in both MEP and Site: it is a service run an MEP reviewer sizes, and the
  // half of it that matters on site is read against the grade sheet.
  MEP: { groups: ["plumbing", "electrical", "mechanical"], trades: ["drainage"] },
  // Site reads the pour, not the cage inside it (and never pays for the lazy bar fetch).
  Site: { groups: ["site", "concrete_masonry"], exclude: ["concrete:rebar"] },
};

// The 13-name vocabulary a saved view may have been captured with, and the assembly-layer
// groups that sat beside it. Each old name maps to the trades it covered; a legacy layer group
// hidden in the recipe hides the trade that band now belongs to.
const LEGACY_TRADES: Record<string, Trade[]> = {
  walls: ["siding", "insulation", "drywall", "paint"],
  floors: ["flooring"],
  roof: ["roofing"],
};
const LEGACY_LAYER_GROUPS: Record<string, Trade[]> = {
  insulation: ["insulation"],
  cladding: ["siding"],
  furring: ["siding"],
  airgap: ["siding"],
  membrane: ["siding"],
  finish: ["drywall", "paint"],
};

/** Fold a saved recipe's visibility onto the current vocabulary. Unknown names are ignored;
 *  a trade the recipe never mentions stays on. */
export function migrateSavedVisibility(
  saved: Record<string, boolean> | undefined,
  layerGroups?: Record<string, boolean>,
): VisibleTrades {
  // From the default, not from everything: a recipe saved before a facet existed has no
  // opinion about it, and the default is the one to inherit.
  const out = defaultVisibleTrades();
  const entries = Object.entries(saved ?? {});
  const named = new Set(entries.map(([name]) => name));
  for (const [name, on] of entries) {
    // A bare trade saved OFF meant all of it — but only downward, and only for the facets the
    // recipe does not name itself: `framing: false` takes the bands with it, `framing: true`
    // leaves them at the default, since that recipe was never asked about them.
    const targets: VisibilityKey[] = KNOWN.has(name)
      ? [name as VisibilityKey, ...(on === false && !name.includes(":")
        ? facetsOf(name as Trade).filter((facet) => !named.has(facet)) : [])]
      : (LEGACY_TRADES[name] ?? []);
    for (const key of targets) out[key] = on !== false;
  }
  for (const [name, on] of Object.entries(layerGroups ?? {})) {
    if (on !== false) continue;
    for (const trade of LEGACY_LAYER_GROUPS[name] ?? []) out[trade] = false;
  }
  return out;
}

// --- per-record classification --------------------------------------------------------
// Each prefers the record's own `trades` (stamped by server/model_json*) and falls back to the
// generated maps for an older payload.

const SOLID_TRADE_SETS: Record<string, string[]> = vocabulary.solidTradeSets;
const SOLID_FALLBACK: string = vocabulary.solidTradeFallback;
const LAYER_FUNCTION_TRADES: Record<string, string> = vocabulary.layerFunctionTrades;
const MEMBER_CATEGORY_TRADES: Record<string, string> = vocabulary.memberCategoryTrades;
const CANVAS_DOMAIN_TRADES: Record<string, string> = vocabulary.canvasDomainTrades;
export const RECORD_FAMILY_TRADES: Record<string, Trade[]> =
  vocabulary.recordFamilyTrades as Record<string, Trade[]>;

export function solidTrades(solid: Pick<Solid, "category" | "trades">): Trade[] {
  if (solid.trades?.length) return solid.trades as Trade[];
  const category = solid.category?.toLowerCase() ?? "";
  return (SOLID_TRADE_SETS[category] ?? [SOLID_FALLBACK]) as Trade[];
}

/** The visibility keys a solid answers to — `solidTrades` with the facet its category names
 *  swapped in (a connector's framing token becomes `framing:connector`).
 *
 *  Deliberately a second function rather than a wider return type on `solidTrades`: that one
 *  is what `primaryTrade` and every non-viewer caller reads, and a facet leaking into those
 *  would put a connector in a container of its own. Mirrors `layerTrades`. */
export function solidVisibilityKeys(
  solid: Pick<Solid, "category" | "trades">,
): VisibilityKey[] {
  return withFacets(solidTrades(solid), solid.category?.toLowerCase() ?? "",
    ["solidCategories"]) as VisibilityKey[];
}

export function layerTrades(layer: Pick<Layer, "function" | "trades">): VisibilityKey[] {
  const key = (layer.function ?? "").trim().toLowerCase();
  const stamped = layer.trades?.length
    ? (layer.trades as Trade[])
    : [(LAYER_FUNCTION_TRADES[key] ?? "framing") as Trade];
  return withFacets(stamped, key, ["layerFunctions"]) as VisibilityKey[];
}

/** A skin member (a derived closure band) continues the layer whose function is its category.
 *
 *  Not every category IS a layer function, though: the derived eave trim (fascia, soffit,
 *  corner trim), the gutter, the ridge cap and the stair builder's pieces are members with no
 *  band behind them, and the engine grades those in `MEMBER_CATEGORY_TRADE`. Reading only the
 *  layer-function map dropped every one of them into the "framing" fallback — the garage's
 *  eave soffit panel hid with the studs instead of standing with the siding it continues. */
export function memberTrades(member: { category: string }): VisibilityKey[] {
  const key = (member.category ?? "").trim().toLowerCase();
  const byCategory = MEMBER_CATEGORY_TRADES[key];
  return byCategory !== undefined
    ? withFacets([byCategory], key, ["memberCategories", "layerFunctions"]) as VisibilityKey[]
    : layerTrades({ function: member.category });
}

/** A wall body's set: stamped by the engine, else the union of its layers'. Facets collapse
 *  back to their trade here — this is the whole wall, not one band of it. */
export function wallTrades(wall: Pick<Wall, "trades" | "layers">): Trade[] {
  if (wall.trades?.length) return wall.trades as Trade[];
  const found = new Set<Trade>();
  for (const layer of wall.layers ?? []) {
    for (const key of layerTrades(layer)) found.add(baseTrade(key));
  }
  return found.size ? ALL_TRADES.filter((trade) => found.has(trade)) : ["framing"];
}

/** A roof shell's set. The roof record carries no layers, so an older payload is roofing. */
export function roofTrades(roof: Pick<Roof, "trades">): Trade[] {
  return roof.trades?.length ? (roof.trades as Trade[]) : ["roofing"];
}

export function canvasObjectTrades(item: Pick<CanvasObject, "domain" | "trades">): Trade[] {
  if (item.trades?.length) return item.trades as Trade[];
  return [(CANVAS_DOMAIN_TRADES[item.domain] ?? "furniture") as Trade];
}

/** The container an element files under: the first (primary) trade of its set. A facet
 *  files under its trade — the facets are a filter, not containers of their own. */
export function primaryTrade(trades: readonly string[]): Trade {
  const first = trades.find((trade) => KNOWN.has(trade));
  return first ? baseTrade(first as VisibilityKey) : (SOLID_FALLBACK as Trade);
}

/** Draw iff the element's PRIMARY trade — the first known token in its set — is visible.
 *
 *  The isolation gesture ("only concrete") needs this: a foundation wall's set is
 *  `("concrete","insulation")`, and `anyTradeVisible` leaves it on screen under Insulation
 *  with Concrete off, so the wall can never be isolated away. The engine stamps the set
 *  primary-first (`emit/trade_rules.py:166` — sequence order, framing last), which is what
 *  makes "first" mean something.
 *
 *  A facet key is read literally, the way `anyTradeVisible` reads it: a band stamped
 *  `framing:sheathing` answers to its own chip. An element that names no known trade is
 *  always drawn — hiding what nobody classified would make a missing tag look like a toggle. */
export function primaryTradeVisible(
  trades: readonly string[] | null | undefined, visible: VisibleTrades,
): boolean {
  const first = (trades ?? []).find((trade) => KNOWN.has(trade)) as VisibilityKey | undefined;
  return first === undefined || visible[first] !== false;
}
