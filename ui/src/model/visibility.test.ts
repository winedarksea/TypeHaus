import {
  ALL_LAYER_VISIBILITY_GROUPS,
  canvasObjectTrade,
  isLayerVisible,
  layerVisibilityGroupOf,
  memberLayerVisibilityGroup,
  TRADE_SURFACES,
  type LayerVisibilityGroup,
} from "./visibility";

// Spelled out rather than imported from the store: importing the store instantiates an engine
// client at module scope, which has no business running inside a geometry test.
const EXPECTED_TRADES = ["walls", "openings", "framing", "floors", "concrete", "roof", "stairs",
  "furniture", "plumbing", "electrical", "mechanical", "earth"];

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function allVisible(): Record<LayerVisibilityGroup, boolean> {
  return Object.fromEntries(ALL_LAYER_VISIBILITY_GROUPS.map((group) => [group, true])) as
    Record<LayerVisibilityGroup, boolean>;
}

export function runVisibilityTests() {
  // The engine's own layer-function vocabulary must survive the round trip unchanged, or a
  // toggle silently governs nothing. These are the eight functions catlin's model.json emits.
  for (const layerFunction of ["structure", "sheathing", "membrane", "insulation", "airgap",
    "furring", "cladding", "finish"]) {
    assert(layerVisibilityGroupOf(layerFunction) === layerFunction,
      `Engine layer function ${layerFunction} must map to its own visibility group`);
  }
  assert(layerVisibilityGroupOf("AIR_GAP") === "airgap", "Aliases fold in, case-insensitively");
  assert(layerVisibilityGroupOf("lining") === "finish", "Interior lining is a finish layer");
  assert(layerVisibilityGroupOf("soffit") === "cladding", "Derived eave trim continues the cladding");
  assert(layerVisibilityGroupOf("") === "other", "An unnamed function is togglable as 'other'");
  assert(layerVisibilityGroupOf("something-new") === "other",
    "An unrecognised function must stay hideable rather than becoming permanently visible");

  // Cavity fill is judged by its own function, so hiding Structure keeps the batts drawn —
  // that separation is the whole point of the per-layer control.
  const groups = allVisible();
  groups.structure = false;
  assert(!isLayerVisible({ function: "structure" }, groups), "Hiding structure hides the structure layer");
  assert(isLayerVisible({ function: "insulation" }, groups),
    "Cavity insulation is not taken down with its structure host");

  assert(memberLayerVisibilityGroup({ category: "cladding" }) === "cladding",
    "A skin member answers to the layer group it continues");
  assert(memberLayerVisibilityGroup({ category: "stud" }) === "other",
    "Plain lumber has no layer group of its own");

  assert(canvasObjectTrade({ domain: "plumbing" }) === "plumbing", "Service domains map to their trade");
  assert(canvasObjectTrade({ domain: "appliance" }) === "furniture",
    "Anything that is not a service run falls under furniture, as it does in 3D");

  // Every trade must declare where it can be drawn, or the Views panel would show a toggle
  // with no honest answer for one of the two viewers.
  assert(Object.keys(TRADE_SURFACES).sort().join() === [...EXPECTED_TRADES].sort().join(),
    "TRADE_SURFACES must cover exactly the store's trade vocabulary");
  for (const surfaces of Object.values(TRADE_SURFACES)) {
    assert(surfaces.model, "Every trade must be drawable in 3D");
  }
  assert(!TRADE_SURFACES.roof.plan && !TRADE_SURFACES.earth.plan,
    "The plan has no roof surface or site sheet to hide");
  assert(TRADE_SURFACES.walls.plan && TRADE_SURFACES.framing.plan && TRADE_SURFACES.stairs.plan,
    "Walls, framing and stairs are drawn in the plan and must be hideable there");
}
