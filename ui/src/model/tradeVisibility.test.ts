// The generic facet table, pinned on its newest row: `concrete:rebar`. What must hold: it
// starts off, it is independent of the `concrete` chip (the x-ray view), links and saved
// views address it, and a view saved before it existed comes back with it off.
import * as THREE from "three";
import {
  ALL_VISIBILITY_KEYS, anyTradeVisible, baseTrade, DEFAULT_OFF_KEYS, defaultVisibleTrades,
  expandRolePreset, groupState, memberTrades, migrateSavedVisibility, onlyTrades, primaryTrade,
  ROLE_PRESETS, visibilityKeyLabel, visibilityKeysOf,
} from "./tradeVisibility";
import { FACETS } from "./visibilityFacets";
import type { Model, RebarSet } from "./types";
import { parseViewParams, viewParamsFor } from "../state/viewUrl";
import { applyVisibility } from "../three/builders/registry";
import { buildRebarGroups } from "../three/builders/rebar";
import { wholeHouseGlbAssignment } from "../three/wholeHouseGlb";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const REBAR = "concrete:rebar" as const;

function checkTable() {
  for (const facet of FACETS) {
    assert(ALL_VISIBILITY_KEYS.includes(facet.key), `${facet.key} is switchable`);
    assert(visibilityKeysOf(baseTrade(facet.key)).includes(facet.key),
      `${facet.key} is covered by its trade`);
    assert(visibilityKeyLabel(facet.key) === facet.label, `${facet.key} prints its label`);
    assert((DEFAULT_OFF_KEYS as readonly string[]).includes(facet.key) === facet.defaultOff,
      `${facet.key} default follows the table`);
  }
  assert(visibilityKeysOf("concrete").join() === `concrete,${REBAR}`, "concrete covers rebar");
  assert(visibilityLabel() === "Rebar", "the chip reads Rebar");
  assert(memberTrades({ category: "rebar" }).join() === REBAR,
    "a rebar member takes the facet from its category");
  assert(primaryTrade([REBAR]) === "concrete", "a bar files under concrete");
}

const visibilityLabel = () => visibilityKeyLabel(REBAR);

function checkDefaultsAndCascade() {
  const fresh = defaultVisibleTrades();
  assert(fresh.concrete && !fresh[REBAR], "concrete starts on, rebar off");
  assert(groupState("concrete_masonry", fresh) === "mixed", "the group opens mixed");

  // The x-ray view: the pour off, the cage on.
  const xray = { ...defaultVisibleTrades(), concrete: false, [REBAR]: true };
  assert(anyTradeVisible([REBAR], xray), "concrete off leaves rebar as set (on)");
  assert(!anyTradeVisible(["concrete"], xray), "…while the pour hides");
  assert(!anyTradeVisible([REBAR], { ...xray, [REBAR]: false }), "its own chip hides it");

  // Routed through the real layer builder and the scene's visibility walk.
  const sets = [{ uid: "FT1", tag: "F-1", storey: "L1", host_kind: "Footing", scope: "footing",
    trades: ["concrete"], provenance: null, members: [{
      key: "F-1/bottom-x/001-1", parent_uid: "FT1", category: "rebar", profile: "#5",
      shape: "bar", width_m: 0.016, depth_m: 0.016, p0: [0, 0], p1: [2, 0], z0_m: 0.1,
      z1_m: 0.1, length_m: 2, path: [[0, 0, 0.1], [2, 0, 0.1]], closed: false,
      rebar: { role: "bottom-x", bar: 5, coating: "black", spacing_in: 12, piece: 1, pieces: 1,
        placed_m: 2, lap_m: 0, hook_m: 0, cut_m: 2, hook_kinds: [], weight_lb: 7, note: null },
    }] }] as RebarSet[];
  const root = new THREE.Group();
  const [group] = buildRebarGroups(sets, [0, 0], "schematic");
  root.add(group);
  assert(group.userData.trades.join() === REBAR, "bars carry ONLY the facet key");
  applyVisibility(root, xray, new Set());
  assert(group.visible, "concrete chip off: the bars still draw");
  applyVisibility(root, defaultVisibleTrades(), new Set());
  assert(!group.visible, "the default hides them");
  applyVisibility(root, xray, new Set(["L1"]));
  assert(!group.visible, "a hidden level hides its bars");
  applyVisibility(root, onlyTrades(["masonry"]), new Set());
  assert(!group.visible, "an isolation that names neither hides them");

  // The glb path honours `extras.facet` the same way.
  const glb = wholeHouseGlbAssignment("", { trades: ["concrete"], facet: REBAR });
  assert(glb?.trade === "concrete" && glb.facet === REBAR, "a glb rebar node carries its facet");
  assert(wholeHouseGlbAssignment("", { trades: ["concrete"], facet: "nope" })?.facet === null,
    "an unknown facet is dropped");
}

function checkPresetsAndLinks() {
  assert(expandRolePreset(ROLE_PRESETS.Structure).includes(REBAR), "Structure turns rebar on");
  assert(!expandRolePreset(ROLE_PRESETS.Site).includes(REBAR),
    "Site keeps the concrete but not the cage");
  assert(!parseViewParams("?preset=framer").visible?.includes(REBAR),
    "the framer link stays on the sticks");

  assert(parseViewParams(`?show=${REBAR}`).visible?.join() === REBAR, "show= addresses rebar");
  const model = { storeys: [{ tag: "main" }] } as unknown as Model;
  const printed = viewParamsFor({
    viewMode: "2d", threeMode: "nordic", visibleTrades: onlyTrades(["concrete", REBAR]),
    hiddenLevels: [], activeStorey: "main", labelMode: "hover", activeLens: "none",
    activeWorkspace: "design", detailView: "none", model,
  });
  assert(printed === `show=concrete,${REBAR}`, `rebar prints unescaped: ${printed}`);
  assert(parseViewParams(`?${printed}`).visible?.join() === `concrete,${REBAR}`,
    "show=concrete:rebar round-trips");
  const on = viewParamsFor({
    viewMode: "2d", threeMode: "nordic", visibleTrades: { ...defaultVisibleTrades(), [REBAR]: true },
    hiddenLevels: [], activeStorey: "main", labelMode: "hover", activeLens: "none",
    activeWorkspace: "design", detailView: "none", model,
  });
  assert(on.includes(REBAR), "turning rebar on is a non-default view and prints");
}

function checkMigration() {
  // A recipe saved before the facet existed names every other key and not this one.
  const old = Object.fromEntries(ALL_VISIBILITY_KEYS.filter((k) => k !== REBAR).map((k) => [k, true]));
  assert(!migrateSavedVisibility(old)[REBAR], "an old saved view comes back with rebar off");
  assert(!migrateSavedVisibility({ concrete: true })[REBAR], "a partial one too");
  assert(!migrateSavedVisibility({ concrete: false })[REBAR], "concrete off takes rebar down");
  const xray = migrateSavedVisibility({ concrete: false, [REBAR]: true });
  assert(!xray.concrete && xray[REBAR], "a saved x-ray view keeps its cage");
  const reversed = migrateSavedVisibility({ [REBAR]: true, concrete: false });
  assert(reversed[REBAR], "…whatever order the keys were saved in");
  const framing = migrateSavedVisibility({ framing: false });
  assert(!framing["framing:connector"] && !framing[REBAR], "the framing cascade is unchanged");
}

export function runTradeVisibilityFacetTests() {
  checkTable();
  checkDefaultsAndCascade();
  checkPresetsAndLinks();
  checkMigration();
  console.log("Visibility facet (rebar) tests passed.");
}
