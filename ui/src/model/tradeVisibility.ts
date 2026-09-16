// Trade visibility: the groups the Views panel toggles, the chips inside them, and the one
// rule both viewers apply — an element is drawn iff ANY trade in its set is visible.
//
// Isolation is the dominant gesture ("only concrete"), and a wall body is several trades at
// once (its studs are framing, its foam insulation, its cladding siding, its board drywall),
// so a per-element boolean was never going to be honest. The tables here are generated from
// the engine (emit/trades.py → generated/vocabulary.json); the functions are the UI's.
import vocabulary from "../generated/vocabulary.json";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import type { CanvasObject, Layer, Roof, Solid, Wall } from "./types";

// --- framing facets -------------------------------------------------------------------
// `framing` is the one trade that owns both the sticks and the planes nailed to them, and
// that is right for a bid: one framer buys the studs, the sheathing and the furring. It is
// wrong for looking. A viewer asking for "just the wooden sticks" got a solid plywood skin
// over every stud bay, because the sheathing band rides the same token the studs do.
//
// So `framing` alone splits into viewer-only FACETS, keyed `framing:<layer function>`.
// Nothing below the UI knows them: the engine still stamps `framing`, the BOM and the
// schedule still bid one trade, and `layerTrades`/`memberTrades` swap the facet in from the
// layer function (or member category) that is already on the record. `primaryTrade` maps one
// back to `framing`, so a facet never needs a container of its own.
//
// The line is BAND vs STICK, not one material against another. A `structure` band is a
// full-height prism of the wall's own lumber drawn straight over the studs it stands for; a
// `furring` band is the same stand-in for the girts; `sheathing` is the sheet nailed across
// both. All three are solid planes, and all three were riding the token the sticks ride — so
// "just the wooden sticks" drew a closed box with the framing sealed inside it.
//
// A furring *stick* is not affected: an outrigger or a girt is lumber a carpenter cuts, and
// `builders/wallSkin.ts::memberTradeSet` puts it on the bare `framing` token by category,
// never through this table. Only the layer band comes here.
//
// All three default OFF (`DEFAULT_OFF_KEYS`): they are interior sandwich layers, buried
// behind the cladding outside and the board inside, so the only view they ever reached was
// the cutaway that wanted them gone.

/** Layer function -> the facet it takes when its trade is framing. */
const FRAMING_FACET_OF: Record<string, FramingFacet> = {
  structure: "framing:structure",
  furring: "framing:furring",
  sheathing: "framing:sheathing",
};

// The connector facets are a different kind of split from the three bands above, and worth
// saying why they are facets rather than trades. A trade is a BID (emit/trades.py), and
// nobody bids connectors separately from framing — the framer buys the studs and the ties
// together. But "show me the hardware" and "show me the concrete sub's cast-in hardware" are
// two things a person wants to look at, and looking is exactly what a facet is for.
//
// Both default ON, unlike the three bands: a band is an interior sandwich layer buried behind
// the cladding, while a connector marker is the thing somebody asked to be able to see.
export const FRAMING_FACETS =
  ["framing:structure", "framing:furring", "framing:sheathing",
   "framing:connector", "framing:connector-embedded"] as const;
export type FramingFacet = (typeof FRAMING_FACETS)[number];

/** Keys a fresh session starts with OFF. Kept to the three framing BANDS: every trade is a
 *  scope somebody bids and starts visible, and these are interior sandwich layers inside one
 *  of them. The connector facets are not here — they are what was asked for. */
export const DEFAULT_OFF_KEYS: readonly FramingFacet[] =
  ["framing:structure", "framing:furring", "framing:sheathing"];

/** What the Views panel can switch on and off: every trade, plus the framing facets. */
export type VisibilityKey = Trade | FramingFacet;

export const ALL_VISIBILITY_KEYS: VisibilityKey[] = [...ALL_TRADES, ...FRAMING_FACETS];

/** The keys a trade covers — `framing` covers its facets as well as the bare sticks. */
export function visibilityKeysOf(trade: Trade): VisibilityKey[] {
  return trade === "framing" ? [trade, ...FRAMING_FACETS] : [trade];
}

/** The trade a visibility key answers to: a facet's own trade, else the key itself. */
export function baseTrade(key: VisibilityKey): Trade {
  return (key.split(":", 1)[0]) as Trade;
}

/** Swap the bare `framing` token for the facet `layerFunction` names, if it names one. */
function withFramingFacet(trades: readonly string[], layerFunction: string): VisibilityKey[] {
  const facet = FRAMING_FACET_OF[layerFunction];
  if (!facet) return trades as VisibilityKey[];
  return trades.map((trade) => (trade === "framing" ? facet : trade)) as VisibilityKey[];
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

// What a chip prints when the trade's own label would not do. `framing` is split into chips,
// so the bare one has to say which half it is — "Framing" beside a "Framing" group header
// reads as the whole group, which is exactly the thing it is not.
const VISIBILITY_KEY_LABEL: Partial<Record<VisibilityKey, string>> = {
  "framing:structure": "Structure band",
  "framing:furring": "Furring band",
  "framing:sheathing": "Sheathing",
  "framing:connector": "Connectors",
  "framing:connector-embedded": "Cast-in connectors",
};

/** What a Views-panel chip prints for one visibility key. */
export function visibilityKeyLabel(key: VisibilityKey): string {
  return VISIBILITY_KEY_LABEL[key] ?? TRADE_LABEL[key as Trade];
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
}

export function expandRolePreset(preset: RolePreset): VisibilityKey[] {
  const out = new Set<Trade>(preset.trades ?? []);
  for (const id of preset.groups ?? []) {
    for (const trade of TRADE_GROUPS.find((g) => g.id === id)?.trades ?? []) out.add(trade);
  }
  // A preset names TRADES, so a named `framing` means the sheathing it bids as well.
  return ALL_TRADES.filter((trade) => out.has(trade)).flatMap(visibilityKeysOf);
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
  Site: { groups: ["site", "concrete_masonry"] },
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
  // From the default, not from everything: a recipe saved before the framing facets existed
  // has no opinion about the structure band, and the default is the one to inherit.
  const out = defaultVisibleTrades();
  for (const [name, on] of Object.entries(saved ?? {})) {
    // A recipe saved before the facets existed named `framing` and meant all of it — but
    // only downward: `framing: false` takes the bands with it, `framing: true` leaves them at
    // the default, since that recipe was never asked about them.
    const targets: VisibilityKey[] = KNOWN.has(name)
      ? (name === "framing" && on === false ? visibilityKeysOf("framing") : [name as VisibilityKey])
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

/** Solid category -> the framing facet it takes. Cast-in hardware separates from the rest
 *  because it is the concrete sub's scope on site, not the framer's. */
const FRAMING_FACET_OF_CATEGORY: Record<string, FramingFacet> = {
  connector: "framing:connector",
  connector_hanger: "framing:connector",
  connector_embedded: "framing:connector-embedded",
};

/** The visibility keys a solid answers to — `solidTrades` with the framing token swapped for
 *  the facet its category names.
 *
 *  Deliberately a second function rather than a wider return type on `solidTrades`: that one
 *  is what `primaryTrade` and every non-viewer caller reads, and a facet leaking into those
 *  would put a connector in a container of its own. Mirrors `layerTrades`, which does the same
 *  thing for a layer band. */
export function solidVisibilityKeys(
  solid: Pick<Solid, "category" | "trades">,
): VisibilityKey[] {
  const facet = FRAMING_FACET_OF_CATEGORY[solid.category?.toLowerCase() ?? ""];
  const trades = solidTrades(solid);
  if (!facet) return trades as VisibilityKey[];
  return trades.map((trade) => (trade === "framing" ? facet : trade)) as VisibilityKey[];
}

export function layerTrades(layer: Pick<Layer, "function" | "trades">): VisibilityKey[] {
  const key = (layer.function ?? "").trim().toLowerCase();
  const stamped = layer.trades?.length
    ? (layer.trades as Trade[])
    : [(LAYER_FUNCTION_TRADES[key] ?? "framing") as Trade];
  return withFramingFacet(stamped, key);
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
    ? withFramingFacet([byCategory], key)
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

/** The container an element files under: the first (primary) trade of its set. A framing
 *  facet files under `framing` — the facets are a filter, not containers of their own. */
export function primaryTrade(trades: readonly string[]): Trade {
  const first = trades.find((trade) => KNOWN.has(trade));
  return first ? baseTrade(first as VisibilityKey) : (SOLID_FALLBACK as Trade);
}
