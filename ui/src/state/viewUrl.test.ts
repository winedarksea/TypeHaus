// Deep links. What must hold: a link reproduces the view, a stale one degrades to the default
// rather than throwing, and the hash (the surface) is never ours to touch.
import { DEFAULT_OFF_KEYS, defaultVisibleTrades, expandRolePreset, onlyTrades, ROLE_PRESETS } from "../model/tradeVisibility";
import type { Model } from "../model/types";
import { mergeSearch, parseViewParams, viewParamsFor, type ViewSnapshot } from "./viewUrl";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const model = { storeys: [{ tag: "basement" }, { tag: "main" }] } as unknown as Model;

function snapshot(over: Partial<ViewSnapshot> = {}): ViewSnapshot {
  return {
    viewMode: "2d", threeMode: "nordic",
    visibleTrades: defaultVisibleTrades(), hiddenLevels: [], activeStorey: "main", labelMode: "hover",
    activeLens: "none", activeWorkspace: "design", detailView: "none", model, ...over,
  };
}

export function runViewUrlTests(): void {
  assert(viewParamsFor(snapshot()) === "", "the default view prints nothing");

  const view = snapshot({
    viewMode: "3d", threeMode: "schematic", hiddenLevels: ["basement", "attic"],
    visibleTrades: onlyTrades(["framing", "concrete"]), activeStorey: "basement",
    labelMode: "off", activeLens: "thermal", activeWorkspace: "analyze", detailView: "bom",
  });
  const printed = viewParamsFor(view);
  assert(printed.includes("show=concrete,framing"), `commas unescaped: ${printed}`);
  const back = parseViewParams(`?${printed}`);
  assert(back.viewMode === "3d"
    && back.threeMode === "schematic" && back.labelMode === "off" && back.activeLens === "thermal"
    && back.activeWorkspace === "analyze" && back.detailView === "bom"
    && back.activeStorey === "basement", "round-trips every field");
  assert(back.visible?.join() === "concrete,framing", "visibility round-trips literally");
  assert(printed.includes("hideLevels=basement,attic"), `hidden levels print: ${printed}`);
  assert(back.hiddenLevels?.join() === "basement,attic", "hidden levels round-trip");
  assert(Object.keys(parseViewParams("?rep=conceptual")).length === 0, "a retired ?rep= is ignored");

  const junk = parseViewParams("?mode=4d&rep=x&reader=none&show=nope&lens=&hideLevels=");
  assert(Object.keys(junk).length === 0, `unknown values are dropped: ${JSON.stringify(junk)}`);
  assert(parseViewParams("?show=framing:connector").visible?.join() === "framing:connector",
    "a facet is addressable");

  const framer = parseViewParams("?preset=framer");
  assert(framer.viewMode === "3d", "preset expands");
  assert(framer.visible?.join() === expandRolePreset(ROLE_PRESETS.Structure)
    .filter((k) => !(DEFAULT_OFF_KEYS as readonly string[]).includes(k)).join(),
    "framer shows the Structure role, sticks without the stand-in bands");
  assert(parseViewParams("?preset=framer&mode=split").viewMode === "split",
    "an explicit param overrides the preset");
  assert(parseViewParams("?preset=FRAMER&show=roofing").visible?.join() === "roofing",
    "and so does an explicit show");

  assert(parseViewParams("?group=concrete_masonry").visible?.join() === "concrete,masonry",
    "a group id expands to its trades");
  assert(parseViewParams("?group=mep").visible?.includes("drainage"),
    "a role preset name is a group too");

  assert(mergeSearch("?foo=1&mode=3d&preset=framer", "mode=split") === "?foo=1&mode=split",
    "foreign params survive, ours are replaced");
  assert(mergeSearch("?preset=framer", "") === "", "an empty view clears the query");
  assert(!mergeSearch("", "mode=3d").includes("#"), "the hash is never written by the query");

  console.log("View-URL tests passed.");
}
