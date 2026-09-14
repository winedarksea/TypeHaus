// Trade routing in the 3D scene: an element carries a SET of trades on its meshes and draws
// iff any of them is visible. Built with the real wall builder, so a change to how bands are
// tagged fails here rather than in the browser.
import * as THREE from "three";
import type { Wall } from "../model/types";
import {
  allVisibleTrades, baseTrade, defaultVisibleTrades, DEFAULT_OFF_KEYS, onlyTrades,
  primaryTrade, solidTrades, solidVisibilityKeys,
} from "../model/tradeVisibility";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { applyTradeVisibility, tagTrades } from "./builders/registry";
import { snapshot, tagNew } from "./builders/scene";
import { buildWall } from "./builders/walls";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function groups(): Record<Trade, THREE.Group> {
  return Object.fromEntries(ALL_TRADES.map((trade) => [trade, new THREE.Group()])) as
    Record<Trade, THREE.Group>;
}

function wall(): Wall {
  const square: [number, number][] = [[0, 0], [4, 0], [4, 0.1], [0, 0.1]];
  const band = (name: string, fn: string, material: string, trades: string[]) => ({
    name, function: fn, material, thickness_m: 0.1, polygon: square, control: [], trades,
  });
  return {
    uid: "W", tag: "W-1", storey: "S-1", assembly: "A", provenance: null,
    axis: [[0, 0], [4, 0]], z0_m: 0, z1_m: 3, top_z0_m: null, top_z1_m: null,
    plate_base_z_m: null, plate_top_z_m: null, layout_axis: null, is_foundation: false,
    trades: ["siding", "insulation", "drywall", "framing"],
    layers: [
      band("cladding", "cladding", "board-batten-24", ["siding"]),
      band("foam", "insulation", "xps", ["insulation"]),
      band("ply", "sheathing", "struct-1-plywood", ["framing"]),
      band("studs", "structure", "spf", ["framing"]),
      band("board", "finish", "gwb", ["drywall"]),
    ],
    members: [],
  } as unknown as Wall;
}

export function runTradeRoutingTests() {
  const tradeGroups = groups();
  const root = new THREE.Group();
  for (const trade of ALL_TRADES) root.add(tradeGroups[trade]);
  buildWall(tradeGroups, wall(), [], [0, 0], "schematic", RESOLVED_NORDIC_PALETTE.light,
    [], new Map());
  const meshes = (trade: Trade) => tradeGroups[trade].children.filter((c) => c instanceof THREE.Mesh);
  // The body files under the wall's primary trade; every band carries its own set. A wall
  // with no lumber of its own keeps its structure band — nothing else would stand there.
  assert(meshes("siding").length === 5, "Five bands build into the siding container");
  const byTrade = (trade: string) => meshes("siding").filter((m) => (m.userData.trades as string[]).includes(trade));
  assert(byTrade("insulation").length === 1 && byTrade("drywall").length === 1,
    "Each band is tagged with its own trade");

  applyTradeVisibility(root, onlyTrades(["insulation"]));
  assert(byTrade("insulation").every((m) => m.visible), "Only insulation: the foam stays");
  assert(byTrade("siding").every((m) => !m.visible) && byTrade("drywall").every((m) => !m.visible),
    "…and the cladding and board go");
  assert(tradeGroups.siding.visible, "The container itself is never flipped");

  applyTradeVisibility(root, allVisibleTrades());
  assert(meshes("siding").every((m) => m.visible), "Everything back on");

  // Fill-in: an outer tag never overwrites a finer inner one.
  const extra = new THREE.Mesh();
  tradeGroups.siding.add(extra);
  tagTrades(tradeGroups.siding, 0, ["concrete"]);
  assert((extra.userData.trades as string[]).join() === "concrete", "Untagged children take the outer set");
  assert(byTrade("insulation").length === 1, "Tagged children keep theirs");

  // --- the framing view --------------------------------------------------------------
  // The two solid bands a framing view has to be able to drop — the structure prism standing
  // for the studs and the sheathing nailed over them — ride facets of their own, not the bare
  // `framing` token the sticks do. Before that, "just the wooden sticks" drew a solid box.
  assert(!meshes("siding").some((m) => (m.userData.trades as string[]).join() === "framing"),
    "No wall band is left on the bare framing token");
  assert(byTrade("framing:structure").length === 1 && byTrade("framing:sheathing").length === 1,
    "The structure and sheathing bands each take their own facet");

  // Just the wooden sticks: framing on, both of its facets off — which is the default.
  const sticksOnly = defaultVisibleTrades();
  for (const trade of ALL_TRADES) if (trade !== "framing") sticksOnly[trade] = false;
  applyTradeVisibility(root, sticksOnly);
  assert(meshes("siding").every((m) => !m.visible), "Not one wall band draws");
  applyTradeVisibility(root, allVisibleTrades());

  // Multi-trade sets draw while any member is on.
  const shared = new THREE.Mesh();
  shared.userData.trades = ["drainage", "earth"];
  root.add(shared);
  applyTradeVisibility(root, onlyTrades(["earth"]));
  assert(shared.visible, "A bedding tagged drainage+earth draws under Earth alone");
  applyTradeVisibility(root, onlyTrades(["concrete"]));
  assert(!shared.visible, "…and hides when neither is on");
}

// The gap the Connectors toggle falls through without the `tagNew` narrowing in `scene.ts`.
//
// Facets were built for layer bands and were only ever derived from a layer FUNCTION. A solid
// has no layer function, and `tagNew` force-tags everything landing in the framing container
// with the bare `framing` token — so a connector marker arrived correctly routed and was
// immediately relabelled, and the toggle silently did nothing.
//
// Three properties have to hold together, and the middle one is the one that was broken: the
// marker is IN the framing container (so it needs no container of its own), it is TAGGED with
// its own facet (so its own toggle reaches it), and hiding the whole framing trade still hides
// it (so a facet is a refinement, never an escape hatch).
export function runConnectorFacetTests() {
  const solid = (category: string) => ({ category, trades: undefined });

  // In the framing container. `primaryTrade` maps a framing facet back to `framing`, so the
  // three connector categories need no container of their own.
  for (const category of ["connector", "connector_hanger", "connector_embedded"]) {
    assert(primaryTrade(solidTrades(solid(category))) === "framing",
      `${category} belongs in the framing container`);
  }

  // Tagged with the facet, not the bare token. Cast-in hardware separates from the rest
  // because on site it is the concrete sub's scope, not the framer's.
  assert(solidVisibilityKeys(solid("connector")).join() === "framing:connector",
    "A connector marker carries its own facet");
  assert(solidVisibilityKeys(solid("connector_hanger")).join() === "framing:connector",
    "A hanger is a connector to a viewer — one toggle, not two");
  assert(solidVisibilityKeys(solid("connector_embedded")).join() === "framing:connector-embedded",
    "Cast-in hardware separates: it is the concrete sub's scope");

  // …and `solidTrades` itself is untouched, so no non-viewer caller sees a facet.
  assert(solidTrades(solid("connector_embedded")).join() === "framing",
    "solidTrades still answers the bare trade for every caller that is not the viewer");

  // A facet is a refinement of framing, never an escape from it.
  for (const category of ["connector", "connector_hanger", "connector_embedded"]) {
    for (const key of solidVisibilityKeys(solid(category))) {
      assert(baseTrade(key) === "framing", `${key} still answers to the framing trade`);
    }
  }

  // Both start ON — unlike the three bands, which are interior sandwich layers. These are
  // what somebody asked to be able to see.
  assert(!(DEFAULT_OFF_KEYS as readonly string[]).includes("framing:connector")
    && !(DEFAULT_OFF_KEYS as readonly string[]).includes("framing:connector-embedded"),
    "The connector facets default visible");

  // Hiding framing hides it; hiding a sibling facet does not.
  const container = new THREE.Group();
  container.add(new THREE.Object3D());
  tagTrades(container, 0, solidVisibilityKeys(solid("connector")));
  const marker = container.children[0];

  applyTradeVisibility(container, allVisibleTrades());
  assert(marker.visible, "Everything on: the marker draws");
  applyTradeVisibility(container, { ...allVisibleTrades(), "framing:structure": false });
  assert(marker.visible, "Dropping the structure band leaves the connectors alone");
  applyTradeVisibility(container, { ...allVisibleTrades(), "framing:connector": false });
  assert(!marker.visible, "Its own toggle reaches it");
  applyTradeVisibility(container, onlyTrades(["concrete"]));
  assert(!marker.visible, "Hiding framing outright hides it too");
}

// `tagNew` is where the toggle was actually lost. Every assertion above passes with the bug
// still in place, because they never route through the scene builder — this is the one that
// fails without the fix.
export function runTagNewFacetTests() {
  const tradeGroups = groups();

  const tagOne = (keys: readonly string[]) => {
    const before = snapshot(tradeGroups);
    tradeGroups.framing.add(new THREE.Object3D());
    tagNew(tradeGroups, before, keys as never);
    const child = tradeGroups.framing.children[tradeGroups.framing.children.length - 1];
    return (child.userData.trades as string[]).join();
  };

  assert(tagOne(["framing:connector"]) === "framing:connector",
    "tagNew keeps a framing facet the caller already named");
  assert(tagOne(["framing:connector-embedded"]) === "framing:connector-embedded",
    "…including the cast-in one");
  // The case the force-tag is actually for: a wall or roof whose incidental framing landed in
  // the container with no framing key of its own.
  assert(tagOne(["concrete"]) === "framing",
    "A caller that named no framing facet is still force-tagged framing");
}
