// The one visibility vocabulary both viewers read. The store owns the *state* (which trades
// are on); model/tradeVisibility.ts owns the classification and the any-visible rule; this
// module keeps the two viewer-facing questions that are not about a single record: whether a
// layer band draws, and which viewer can draw a trade at all.
import type { Trade } from "../state/vocabulary";
import type { CanvasObject, Layer } from "./types";
import {
  anyTradeVisible, baseTrade, canvasObjectTrades, layerTrades, type VisibleTrades,
} from "./tradeVisibility";

export {
  anyTradeVisible, canvasObjectTrades, layerTrades, memberTrades, solidTrades,
  type VisibleTrades,
} from "./tradeVisibility";

/**
 * Whether a resolved wall/roof layer should draw **in the plan**. Cavity fill is judged by its
 * *own* trade (insulation), not its structure host: hiding Framing to look at the sheathing
 * must not take the batts with it, and hiding Insulation is exactly how the garage gable-end
 * question — is that outermost band the weather skin or cavity fill? — gets settled.
 *
 * The framing FACETS are collapsed to their trade here, and only here. They exist because the
 * 3D viewer draws a wall's structure/furring/sheathing bands as solid prisms *over* the very
 * sticks a framing view wants to see, and they default off for that reason. The plan has no
 * such problem — it is a horizontal cut, every band is a stripe beside its neighbours — and
 * honouring the default there would open a hole through the middle of every wall at the
 * representations that draw no members.
 */
export function isLayerVisible(
  layer: Pick<Layer, "function" | "trades">, visibleTrades: VisibleTrades,
): boolean {
  return anyTradeVisible(layerTrades(layer).map(baseTrade), visibleTrades);
}

/** The primary trade of a placeable, for consumers that file under one. */
export function canvasObjectTrade(item: Pick<CanvasObject, "domain" | "trades">): Trade {
  return canvasObjectTrades(item)[0];
}

// Which viewer can actually draw a trade. The 2D plan is a horizontal cut: it has no roof
// surface, no site sheet, no finish floor plane and no tile, so those toggles are honestly
// 3D-only rather than silently inert. `general` (permits, dumpsters) draws nowhere and is not
// rendered as a chip at all. Concrete *is* drawn in the plan — the per-storey slab outline
// pass (components/plan/PlanMarkers.tsx::SlabOutlines) — so its toggle works in both.
export interface TradeSurfaces {
  plan: boolean;
  model: boolean;
}

export const TRADE_SURFACES: Record<Trade, TradeSurfaces> = {
  general: { plan: false, model: false },
  earth: { plan: false, model: true },
  // Most of the stormwater run is gutters overhead and buried tile below; the sump pit is
  // cast at the storey's own elevation and gets a plan glyph (PlanMarkers.tsx::SumpOutlines).
  drainage: { plan: true, model: true },
  landscaping: { plan: false, model: true },
  concrete: { plan: true, model: true },
  masonry: { plan: true, model: true },
  framing: { plan: true, model: true },
  stairs: { plan: true, model: true },
  roofing: { plan: false, model: true },
  siding: { plan: true, model: true },
  insulation: { plan: true, model: true },
  drywall: { plan: true, model: true },
  paint: { plan: true, model: true },
  openings: { plan: true, model: true },
  tile: { plan: false, model: true },
  flooring: { plan: false, model: true },
  millwork: { plan: true, model: true },
  plumbing: { plan: true, model: true },
  electrical: { plan: true, model: true },
  mechanical: { plan: true, model: true },
  furniture: { plan: true, model: true },
};
