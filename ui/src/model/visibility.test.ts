import { ALL_TRADES } from "../state/vocabulary";
import vocabulary from "../generated/vocabulary.json";
import {
  canvasObjectTrade, canvasObjectTrades, isLayerVisible, layerTrades, memberTrades,
  solidTrades, TRADE_SURFACES,
} from "./visibility";
import {
  ALL_VISIBILITY_KEYS, allVisibleTrades, anyTradeVisible, baseTrade, defaultVisibleTrades,
  expandRolePreset, FRAMING_FACETS, groupState, migrateSavedVisibility, onlyTrades, primaryTrade,
  TRADE_GROUP_OF, TRADE_GROUPS, TRADE_LABEL, visibilityKeyLabel, visibilityKeysOf, wallTrades,
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
  assert(layerTrades({ function: "sheathing" }).join() === "framing:sheathing",
    "Sheathing goes up with the framing, on its own facet");
  assert(layerTrades({ function: "sheathing", trades: ["framing"] }).join() === "framing:sheathing",
    "The engine's `framing` verdict is refined, not overridden");
  assert(layerTrades({ function: "sheathing", trades: ["siding"] }).join() === "siding",
    "A 303 MDO sheathing layer the engine filed as siding keeps siding");
  assert(layerTrades({ function: "structure", trades: ["framing"] }).join() === "framing:structure",
    "The structure band is a facet of its own — that solid prism over the studs");
  assert(layerTrades({ function: "structure", trades: ["concrete"] }).join() === "concrete",
    "A foundation wall's structure layer is concrete and never a framing facet");
  assert(layerTrades({ function: "furring", trades: ["framing"] }).join() === "framing:furring",
    "A furring BAND is a solid plane and takes a facet");
  assert(layerTrades({ function: "furring" }).join() === "siding",
    "An unstamped furring band is the rainscreen's, and never a framing facet");
  assert(layerTrades({ function: "finish" }).join() === "drywall",
    "An unstamped finish is the drywaller's");
  assert(memberTrades({ category: "cladding" }).join() === "siding",
    "A skin member answers to the layer it continues");
  assert(memberTrades({ category: "sheathing" }).join() === "framing:sheathing",
    "A sheathing closure band goes with the sheathing it continues");
  // Categories that are NOT layer functions: the engine's member map, not the fallback.
  assert(memberTrades({ category: "soffit" }).join() === "siding",
    "An eave soffit panel is the siding contractor's, not a stick of framing");
  assert(memberTrades({ category: "fascia" }).join() === "siding", "So is the fascia");
  assert(memberTrades({ category: "gutter" }).join() === "drainage",
    "A gutter is the head of the stormwater run");
  assert(memberTrades({ category: "ridge_cap" }).join() === "roofing", "A ridge cap is roofing");
  assert(memberTrades({ category: "stringer" }).join() === "stairs",
    "A stringer is the stair builder's");
  assert(memberTrades({ category: "stud" }).join() === "framing",
    "…and a stick nobody named is still the framer's");

  // Cavity fill is judged by its own trade, so hiding Framing keeps the batts drawn —
  // that separation is the whole point of per-band visibility.
  const visible = allVisibleTrades();
  // `isLayerVisible` is the PLAN's question and collapses the facets: the plan is a cut, so a
  // band hidden there is a hole in the wall, not a stud field revealed.
  const planFacetsOff = defaultVisibleTrades();
  assert(isLayerVisible({ function: "sheathing", trades: ["framing"] }, planFacetsOff),
    "The plan draws the sheathing stripe although the 3D facet is off");
  assert(isLayerVisible({ function: "structure", trades: ["framing"] }, planFacetsOff),
    "…and the structure stripe, or the wall would have a hole through it");
  planFacetsOff.framing = false;
  assert(!isLayerVisible({ function: "structure", trades: ["framing"] }, planFacetsOff),
    "Hiding the framing trade itself still takes the stripe down");
  visible.framing = false;
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
    "framing,framing:structure,framing:furring,framing:sheathing,siding,insulation,drywall,paint",
    "A preset expands its groups and trades, in order, framing to its facets");

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
  assert(primaryTrade(["framing:sheathing"]) === "framing",
    "A facet files under its trade's container");

  // --- framing facets -----------------------------------------------------------------
  for (const facet of FRAMING_FACETS) {
    assert(baseTrade(facet) === "framing", `${facet} answers to the framing trade`);
    assert(ALL_VISIBILITY_KEYS.includes(facet), `${facet} is a key the panel can switch`);
    assert(visibilityKeyLabel(facet) !== visibilityKeyLabel("framing"),
      `${facet} prints a label of its own`);
  }
  assert(visibilityKeysOf("framing").join() === ["framing", ...FRAMING_FACETS].join(),
    "The framing trade covers the sticks and every facet");
  assert(visibilityKeysOf("insulation").join() === "insulation",
    "Every other trade is one key");
  assert(groupState("structure", allVisibleTrades()) === "on",
    "All framing keys on → the group is on");
  const sticksOnly = allVisibleTrades();
  sticksOnly["framing:sheathing"] = false;
  assert(groupState("structure", sticksOnly) === "mixed",
    "Sheathing off, sticks on → the Framing group reads mixed");
  assert(anyTradeVisible(["framing:sheathing"], sticksOnly) === false,
    "The sheathing band is hidden while the studs stay");
  assert(anyTradeVisible(["framing"], sticksOnly), "The studs stay");
  // A saved view keeps a facet OFF: onlyTrades takes its keys literally, or restoring a
  // "just the sticks" view would hand the sheathing back.
  const restored = onlyTrades(["framing"]);
  assert(restored.framing && !restored["framing:sheathing"],
    "onlyTrades is literal — a facet left out stays out");
  // Defaults: the two solid bands start off, so the framing view opens on the sticks.
  const fresh = defaultVisibleTrades();
  assert(fresh.framing && fresh.siding && fresh.concrete, "Every trade starts visible");
  for (const facet of FRAMING_FACETS) assert(!fresh[facet], `${facet} starts hidden`);
  assert(groupState("structure", fresh) === "mixed",
    "The Framing group opens mixed: sticks on, the bands off");
  assert(ALL_VISIBILITY_KEYS.every((key) => allVisibleTrades()[key]),
    "…and the All button still means all of it");
  const migratedOff = migrateSavedVisibility({ framing: false });
  assert(!migratedOff.framing && !migratedOff["framing:structure"],
    "A legacy `framing: false` takes the bands down with the sticks");
  const migratedOn = migrateSavedVisibility({ framing: true, siding: false });
  assert(migratedOn.framing && !migratedOn["framing:structure"] && !migratedOn.siding,
    "…and a legacy `framing: true` leaves the bands at the default it never knew about");

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
