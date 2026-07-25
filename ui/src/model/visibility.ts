// The one visibility vocabulary both viewers read (→ TODO "turn parts on/off in the 2d and 3d
// views, either by trade ... or by role"). The store owns the *state* (which trades and which
// layer groups are on); this module owns the *classification* — which trade a record belongs
// to, which layer group a layer/skin-member belongs to, and which of the two viewers can draw
// a given trade at all. Keeping the rules here means a trade hidden in the plan and the same
// trade hidden in the model are answering the same question, and both are unit-testable
// without a DOM.

import type { Trade } from "../state/vocabulary";
import type { CanvasObject, Layer, Member } from "./types";

// Layer *function* buckets, i.e. the engine's `Layer.function` vocabulary (model_json.py
// `_layer_json`) collapsed to the set a person would toggle. Roof/wall skin members reuse the
// same words as their `category` (members.ts ROOF_SKIN_CATEGORIES), so one control covers
// both the extruded layer bands and the derived closure bands that continue them.
export type LayerVisibilityGroup =
  | "structure" | "sheathing" | "membrane" | "insulation"
  | "airgap" | "furring" | "cladding" | "finish" | "other";

export const ALL_LAYER_VISIBILITY_GROUPS: LayerVisibilityGroup[] = [
  "structure", "sheathing", "membrane", "insulation",
  "airgap", "furring", "cladding", "finish", "other",
];

export const LAYER_VISIBILITY_GROUP_LABEL: Record<LayerVisibilityGroup, string> = {
  structure: "Structure", sheathing: "Sheathing", membrane: "Membrane",
  insulation: "Insulation", airgap: "Air gap", furring: "Furring",
  cladding: "Cladding", finish: "Finish", other: "Other",
};

// Synonyms the engine emits for the same bucket. `lining` is an interior finish stack, and
// `fascia`/`soffit` are the derived eave trim that continues the cladding plane.
const LAYER_FUNCTION_ALIASES: Record<string, LayerVisibilityGroup> = {
  air_gap: "airgap",
  lining: "finish",
  fascia: "cladding",
  soffit: "cladding",
  roofing: "cladding",
};

/** Bucket a `Layer.function` (or a skin `Member.category`) into a togglable group. */
export function layerVisibilityGroupOf(layerFunction: string | null | undefined): LayerVisibilityGroup {
  const key = (layerFunction ?? "").trim().toLowerCase();
  if (!key) return "other";
  if ((ALL_LAYER_VISIBILITY_GROUPS as string[]).includes(key)) return key as LayerVisibilityGroup;
  return LAYER_FUNCTION_ALIASES[key] ?? "other";
}

/**
 * Whether a resolved wall/roof layer should draw.
 *
 * Cavity fill is deliberately judged by its *own* function (insulation), not its structure
 * host: hiding "Structure" to look at the framing must not take the batts with it, and hiding
 * "Insulation" is exactly how the garage gable-end question — is that outermost band the
 * weather skin or cavity fill? — gets settled (→ TODO "a per-layer visibility control would
 * settle it").
 */
export function isLayerVisible(
  layer: Pick<Layer, "function">,
  visibleLayerGroups: Record<LayerVisibilityGroup, boolean>,
): boolean {
  return visibleLayerGroups[layerVisibilityGroupOf(layer.function)] !== false;
}

/** A skin member (a derived closure/trim band) belongs to the layer group it continues. */
export function memberLayerVisibilityGroup(member: Pick<Member, "category">): LayerVisibilityGroup {
  return layerVisibilityGroupOf(member.category);
}

// Placeables carry a `domain` that is already the discipline name; furniture is the catch-all
// for anything that is not a service run. Mirrors the group routing in Panel3D::setModel so a
// chair hidden in the plan is the same chair hidden in the model.
const CANVAS_OBJECT_DOMAIN_TRADES: Record<string, Trade> = {
  plumbing: "plumbing",
  electrical: "electrical",
  mechanical: "mechanical",
};

export function canvasObjectTrade(item: Pick<CanvasObject, "domain">): Trade {
  return CANVAS_OBJECT_DOMAIN_TRADES[item.domain] ?? "furniture";
}

// Which viewer can actually draw a trade. The 2D plan is a horizontal cut: it has no roof
// surface and no site sheet, so those toggles are honestly 3D-only rather than silently
// inert. Concrete *is* drawn in the plan — the per-storey slab outline pass
// (components/plan/PlanMarkers.tsx::SlabOutlines) — so its toggle works in both viewers.
// Surfacing this in the Views panel is what keeps one shared visibility model from reading
// as half-broken in the plan.
export interface TradeSurfaces {
  plan: boolean;
  model: boolean;
}

export const TRADE_SURFACES: Record<Trade, TradeSurfaces> = {
  walls: { plan: true, model: true },
  openings: { plan: true, model: true },
  framing: { plan: true, model: true },
  floors: { plan: false, model: true },
  concrete: { plan: true, model: true },
  roof: { plan: false, model: true },
  stairs: { plan: true, model: true },
  furniture: { plan: true, model: true },
  plumbing: { plan: true, model: true },
  electrical: { plan: true, model: true },
  mechanical: { plan: true, model: true },
  earth: { plan: false, model: true },
};
