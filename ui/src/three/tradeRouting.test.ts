// Trade routing in the 3D scene: an element carries a SET of trades on its meshes and draws
// iff any of them is visible. Built with the real wall builder, so a change to how bands are
// tagged fails here rather than in the browser.
import * as THREE from "three";
import type { Wall } from "../model/types";
import { allVisibleTrades, onlyTrades } from "../model/tradeVisibility";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { applyTradeVisibility, tagTrades } from "./builders/registry";
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
  // The body files under the wall's primary trade; every band carries its own set.
  assert(meshes("siding").length === 4, "Four bands build into the siding container");
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

  // Multi-trade sets draw while any member is on.
  const shared = new THREE.Mesh();
  shared.userData.trades = ["drainage", "earth"];
  root.add(shared);
  applyTradeVisibility(root, onlyTrades(["earth"]));
  assert(shared.visible, "A bedding tagged drainage+earth draws under Earth alone");
  applyTradeVisibility(root, onlyTrades(["concrete"]));
  assert(!shared.visible, "…and hides when neither is on");
}
