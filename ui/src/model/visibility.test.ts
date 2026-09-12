import { ALL_TRADES } from "../state/vocabulary";
import vocabulary from "../generated/vocabulary.json";
import {
  canvasObjectTrade, canvasObjectTrades, isLayerVisible, layerTrades, memberTrades,
  solidTrades, TRADE_SURFACES,
} from "./visibility";
import {
  allVisibleTrades, anyTradeVisible, expandRolePreset, groupState, migrateSavedVisibility,
  onlyTrades, primaryTrade, TRADE_GROUP_OF, TRADE_GROUPS, TRADE_LABEL, wallTrades,
} from "./tradeVisibility";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runVisibilityTests() {
  // The literal union in state/vocabulary.ts and the engine's generated list must be the
  // same set, or a trade the engine files rows under has no chip.
  assert([...ALL_TRADES].sort().join() === [...(vocabulary.trades as string[])].sort().join(),
    "ALL_TRADES must equal the generated trade list");
  assert(TRADE_GROUPS.flatMap((g) => g.trades).sort().join() === [...ALL_TRADES].sort().join(),
    "The groups partition the trades");
  for (const trade of ALL_TRADES) {
    assert(TRADE_GROUP_OF[trade], `${trade} belongs to a group`);
    assert(TRADE_LABEL[trade], `${trade} has a label`);
    assert(TRADE_SURFACES[trade], `${trade} declares where it can be drawn`);
  }

  // Layer bands take their trade from the record, else from the function map.
  assert(layerTrades({ function: "cladding", trades: ["roofing"] }).join() === "roofing",
    "A stamped layer keeps the engine's verdict");
  assert(layerTrades({ function: "insulation" }).join() === "insulation",
    "Insulation is the insulation trade");
  assert(layerTrades({ function: "cladding" }).join() === "siding",
    "An unstamped cladding band falls back to siding");
  assert(layerTrades({ function: "sheathing" }).join() === "framing",
    "Sheathing goes up with the framing");
  assert(layerTrades({ function: "finish" }).join() === "drywall",
    "An unstamped finish is the drywaller's");
  assert(memberTrades({ category: "cladding" }).join() === "siding",
    "A skin member answers to the layer it continues");

  // Cavity fill is judged by its own trade, so hiding Framing keeps the batts drawn —
  // that separation is the whole point of per-band visibility.
  const visible = allVisibleTrades();
  visible.framing = false;
  assert(!isLayerVisible({ function: "sheathing" }, visible), "Hiding framing hides the sheathing");
  assert(isLayerVisible({ function: "insulation" }, visible),
    "Cavity insulation is not taken down with its structure host");
  assert(isLayerVisible({ function: "finish", trades: ["drywall", "paint"] }, visible),
    "A band with several trades draws while any of them is on");

  // The any-visible rule.
  const onlyConcrete = onlyTrades(["concrete"]);
  assert(anyTradeVisible(["concrete", "plumbing"], onlyConcrete), "Any visible trade draws it");
  assert(!anyTradeVisible(["siding", "paint"], onlyConcrete), "None visible hides it");
  assert(anyTradeVisible([], onlyConcrete), "An unclassified element is never hidden");
  assert(anyTradeVisible(["no-such-trade"], onlyConcrete), "An unknown token is not a toggle");

  assert(groupState("walls", allVisibleTrades()) === "on", "All chips on → group on");
  assert(groupState("walls", onlyConcrete) === "off", "All chips off → group off");
  const mixed = allVisibleTrades();
  mixed.paint = false;
  assert(groupState("walls", mixed) === "mixed", "Some chips off → mixed");

  assert(expandRolePreset({ groups: ["walls"], trades: ["framing"] }).join() ===
    "framing,siding,insulation,drywall,paint", "A preset expands its groups and trades, in order");

  // Saved recipes from the 13-name vocabulary still apply.
  const legacy = migrateSavedVisibility({ walls: false, roof: false, concrete: true });
  assert(!legacy.siding && !legacy.insulation && !legacy.drywall && !legacy.paint,
    "walls off → every wall trade off");
  assert(!legacy.roofing && legacy.concrete && legacy.framing, "roof → roofing; the rest stays on");
  const layered = migrateSavedVisibility({}, { cladding: false });
  assert(!layered.siding && layered.insulation, "A hidden legacy cladding group hides the siding");

  assert(solidTrades({ category: "column", trades: ["concrete"] }).join() === "concrete",
    "A stamped cast column is concrete");
  assert(solidTrades({ category: "column" }).join() === "framing",
    "An unstamped column is framing by category");
  assert(solidTrades({ category: "eave_soffit" }).join() === "siding",
    "The vented eave panel is the siding contractor's");
  assert(solidTrades({ category: "soffit" }).join() === "drywall",
    "A dropped soffit box is the drywaller's");
  assert(primaryTrade(["siding", "insulation"]) === "siding", "Primary is the first known");

  assert(canvasObjectTrade({ domain: "plumbing" }) === "plumbing", "Service domains map to their trade");
  assert(canvasObjectTrades({ domain: "appliance" }).join() === "furniture",
    "An appliance is furniture in the viewer");
  assert(canvasObjectTrades({ domain: "furniture", trades: ["millwork"] }).join() === "millwork",
    "A stamped set wins over the domain");

  const wall = { trades: undefined, layers: [
    { function: "cladding", trades: ["siding"] }, { function: "insulation" },
    { function: "structure", trades: ["framing"] },
  ] } as unknown as Parameters<typeof wallTrades>[0];
  assert(wallTrades(wall).join() === "framing,siding,insulation",
    "An unstamped wall unions its layers, in sequence order");

  // Every trade must declare where it can be drawn, or the Views panel would show a toggle
  // with no honest answer for one of the two viewers.
  assert(!TRADE_SURFACES.roofing.plan && !TRADE_SURFACES.earth.plan,
    "The plan has no roof surface or site sheet to hide");
  assert(TRADE_SURFACES.siding.plan && TRADE_SURFACES.framing.plan && TRADE_SURFACES.stairs.plan,
    "Siding, framing and stairs are drawn in the plan and must be hideable there");
  assert(TRADE_SURFACES.concrete.plan,
    "The plan draws slab outlines (Canvas2D slab pass), so the concrete toggle works there");
  assert(!TRADE_SURFACES.general.plan && !TRADE_SURFACES.general.model,
    "General conditions draw nowhere and get no chip");
}
