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

export type VisibleTrades = Record<Trade, boolean>;
export type GroupState = "on" | "off" | "mixed";

const KNOWN = new Set<string>(ALL_TRADES);

/** Draw iff any of `trades` is visible. An element that names no trade is always drawn:
 *  hiding what nobody classified would make a missing tag look like a toggle. An unknown
 *  token is skipped rather than trusted. */
export function anyTradeVisible(
  trades: readonly string[] | null | undefined, visible: VisibleTrades,
): boolean {
  const known = (trades ?? []).filter((trade) => KNOWN.has(trade)) as Trade[];
  if (known.length === 0) return true;
  return known.some((trade) => visible[trade] !== false);
}

export function groupState(groupId: string, visible: VisibleTrades): GroupState {
  const group = TRADE_GROUPS.find((g) => g.id === groupId);
  if (!group) return "off";
  const on = group.trades.filter((trade) => visible[trade] !== false).length;
  return on === 0 ? "off" : on === group.trades.length ? "on" : "mixed";
}

export function allVisibleTrades(): VisibleTrades {
  return Object.fromEntries(ALL_TRADES.map((trade) => [trade, true])) as VisibleTrades;
}

/** Exactly `trades` on, everything else off. */
export function onlyTrades(trades: readonly Trade[]): VisibleTrades {
  const wanted = new Set(trades);
  return Object.fromEntries(ALL_TRADES.map((trade) => [trade, wanted.has(trade)])) as VisibleTrades;
}

/** A role preset names groups and/or individual trades; both expand to trades. */
export interface RolePreset {
  groups?: string[];
  trades?: Trade[];
}

export function expandRolePreset(preset: RolePreset): Trade[] {
  const out = new Set<Trade>(preset.trades ?? []);
  for (const id of preset.groups ?? []) {
    for (const trade of TRADE_GROUPS.find((g) => g.id === id)?.trades ?? []) out.add(trade);
  }
  return ALL_TRADES.filter((trade) => out.has(trade));
}

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
  const out = allVisibleTrades();
  for (const [name, on] of Object.entries(saved ?? {})) {
    const targets = KNOWN.has(name) ? [name as Trade] : LEGACY_TRADES[name] ?? [];
    for (const trade of targets) out[trade] = on !== false;
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
const CANVAS_DOMAIN_TRADES: Record<string, string> = vocabulary.canvasDomainTrades;
export const RECORD_FAMILY_TRADES: Record<string, Trade[]> =
  vocabulary.recordFamilyTrades as Record<string, Trade[]>;

export function solidTrades(solid: Pick<Solid, "category" | "trades">): Trade[] {
  if (solid.trades?.length) return solid.trades as Trade[];
  const category = solid.category?.toLowerCase() ?? "";
  return (SOLID_TRADE_SETS[category] ?? [SOLID_FALLBACK]) as Trade[];
}

export function layerTrades(layer: Pick<Layer, "function" | "trades">): Trade[] {
  if (layer.trades?.length) return layer.trades as Trade[];
  const key = (layer.function ?? "").trim().toLowerCase();
  return [(LAYER_FUNCTION_TRADES[key] ?? "framing") as Trade];
}

/** A skin member (a derived closure band) continues the layer whose function is its category. */
export function memberTrades(member: { category: string }): Trade[] {
  return layerTrades({ function: member.category });
}

/** A wall body's set: stamped by the engine, else the union of its layers'. */
export function wallTrades(wall: Pick<Wall, "trades" | "layers">): Trade[] {
  if (wall.trades?.length) return wall.trades as Trade[];
  const found = new Set<Trade>();
  for (const layer of wall.layers ?? []) for (const trade of layerTrades(layer)) found.add(trade);
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

/** The container an element files under: the first (primary) trade of its set. */
export function primaryTrade(trades: readonly string[]): Trade {
  const first = trades.find((trade) => KNOWN.has(trade));
  return (first ?? SOLID_FALLBACK) as Trade;
}
