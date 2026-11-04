// One model.json → an ordered list of named build stages, and the runner that builds them.
//
// The shell (site, foundations, decks, walls, roofs) comes first so the viewer can frame and
// draw the building while the rest — openings, finishes, MEP, furniture, plants — streams in
// under the loading overlay. Each stage is a list of one-element work items; the per-element
// builders stay in scene.ts and its siblings. `populateScene` runs them all synchronously for
// headless callers; `buildSceneProgressively` runs them under a frame budget.
import type * as THREE from "three";
import type { Model } from "../../model/types";
import type { SkinLine } from "../members";
import {
  primaryTrade, RECORD_FAMILY_TRADES, roofTrades, solidTrades, solidVisibilityKeys,
  type VisibilityKey, type VisibleTrades, wallTrades,
} from "../../model/tradeVisibility";
import { ALL_TRADES, type Trade } from "../../state/vocabulary";
import { buildLightRun } from "./lightRun";
import { baseRunTrade, buildBaseRun, buildCountertop, buildDoorCasing, buildWindowStool } from "./millwork";
import { buildAlarms } from "./alarms";
import { buildPlants, instancedPlantUids } from "./plants";
import { objectVisible } from "./registry";
import { buildEarth } from "./site";
import { buildOpening } from "./openings";
import { buildWall } from "./walls";
import {
  buildBrace, buildFloor, buildFootingBedding, buildRoof, buildRoomFloor,
  buildPaneling, buildSoffitFraming, buildSolarPanel, buildSolid, buildStair,
  storeyFloorTopM,
} from "./structure";
import {
  buildCanvasObjectItem, placeableElevationM, type PopulateSceneOptions, snapshot,
  type Snapshot, tagNew, tagStorey,
} from "./scene";

export interface SceneStage {
  name: string;
  /** Part of the building shell: framed and drawn before the rest streams in. */
  shell: boolean;
  items: Array<() => void>;
}

export interface BuildProgress {
  phase: string;
  done: number;
  total: number;
  complete: boolean;
}

// The solids whose primary trade is the pour or the masonry are the foundations and slabs;
// only the build ORDER reads this, never what they are or how they draw.
const SHELL_SOLID_TRADES = new Set<Trade>(["concrete", "masonry"]);

export function sceneStages(options: PopulateSceneOptions): SceneStage[] {
  const {
    tradeGroups, model, center, mode, palette, earthOpacity, earthTone, registry, rebar,
  } = options;
  const materials = model.catalog?.materials;
  const build = (trades: readonly VisibilityKey[], storey: string | null | undefined,
    run: () => void) => {
    const before = snapshot(tradeGroups);
    run();
    tagNew(tradeGroups, before, trades);
    tagStorey(tradeGroups, before, storey ?? null);
  };
  const family = (name: string) => RECORD_FAMILY_TRADES[name] ?? ["concrete"];
  const container = (trades: readonly Trade[]) => tradeGroups[primaryTrade(trades)];
  const each = <T>(records: readonly T[] | null | undefined, run: (record: T) => void) =>
    (records ?? []).map((record) => () => run(record));

  const openingsByHost = new Map<string, NonNullable<Model["openings"]>>();
  for (const opening of model.openings ?? []) {
    const list = openingsByHost.get(opening.host) ?? [];
    list.push(opening);
    openingsByHost.set(opening.host, list);
  }
  const doorTypes = new Map((model.catalog?.door_types ?? []).map((type) => [type.tag, type]));

  // A solid is not automatically concrete: a standalone beam or post is framing, a routed pipe
  // run is plumbing, a cast column is concrete. The set is stamped by the engine
  // (model.json `trades`) and falls back to the generated category map.
  // A plant with a procedural model draws as an instance below, not as its bounding prism.
  const instancedPlants = instancedPlantUids(model.plants, model.plant_models);
  // Solids of one part (a gutter's boards, a guard) pick as the first of the group.
  const groupLeader = new Map<string, string>();
  for (const solid of model.solids ?? []) {
    if (solid.group && !groupLeader.has(solid.group)) groupLeader.set(solid.group, solid.uid);
  }
  const solids = (model.solids ?? []).filter((solid) =>
    !(solid.category === "plant" && instancedPlants.has(solid.uid)));
  const isShellSolid = (solid: (typeof solids)[number]) =>
    SHELL_SOLID_TRADES.has(primaryTrade(solidTrades(solid)));
  const solidItem = (solid: (typeof solids)[number]) => {
    // Two answers, deliberately. `solidTrades` decides the CONTAINER (a connector's is
    // framing, and `primaryTrade` maps its facet back to framing anyway); the keys decide
    // what it is TAGGED with, which is what its own toggle reaches.
    const trades = solidTrades(solid);
    build(solidVisibilityKeys(solid), solid.storey, () => buildSolid(container(trades), solid, center,
      mode, palette, model.catalog, registry.picks, registry.byUid, materials, earthOpacity,
      solid.group ? groupLeader.get(solid.group) : undefined));
  };

  // Plants, instanced per storey; each takes its solid's trade set (landscaping).
  const solidsByUid = new Map((model.solids ?? []).map((solid) => [solid.uid, solid]));
  const plantMaterials = new Map<string, THREE.Material>();
  const plantsByStorey = new Map<string, NonNullable<Model["plants"]>>();
  for (const plant of model.plants ?? []) {
    if (!instancedPlants.has(plant.uid)) continue;
    const list = plantsByStorey.get(plant.storey) ?? [];
    list.push(plant);
    plantsByStorey.set(plant.storey, list);
  }
  const alarmsByStorey = new Map<string, NonNullable<Model["alarms"]>>();
  for (const alarm of model.alarms ?? []) {
    const list = alarmsByStorey.get(alarm.storey) ?? [];
    list.push(alarm);
    alarmsByStorey.set(alarm.storey, list);
  }
  // The facade datums every wall's cladding is framed on (builders/walls.ts uses the same
  // `layout_axis ?? axis`), handed to the roofs so a wall→roof closure band's panel module
  // continues the wall's instead of restarting at the band (→ members.ts skinUvSpanM).
  const skinLines: SkinLine[] = (model.walls ?? []).map((wall) => ({
    axis: wall.axis, datum: wall.layout_axis ?? wall.axis,
  }));
  const canvasTypes = new Map((model.catalog?.canvas_object_types ?? []).map((type) => [type.tag, type]));
  const walls = new Map(model.walls.map((wall) => [wall.tag, wall]));

  return [
    // The site sheet is context, not an element: it has no uid in model.json, so it stays out
    // of the raycast set and a click through it falls to whatever building geometry is behind.
    { name: "site", shell: true, items: [() => build(family("earth"), null,
      () => buildEarth(tradeGroups.earth, model, center, mode, earthOpacity, earthTone))] },
    { name: "foundations", shell: true, items: each(solids.filter(isShellSolid), solidItem) },
    { name: "floors", shell: true, items: each(model.floors, (floor) => build(family("floor_deck"),
      floor.storey, () => buildFloor(tradeGroups.framing, floor, center, mode, palette,
        registry.picks, registry.byUid, tradeGroups.framing, materials))) },
    { name: "walls", shell: true, items: each(model.walls, (wall) => build(wallTrades(wall), wall.storey,
      () => buildWall(tradeGroups, wall, openingsByHost.get(wall.tag) ?? [], center, mode, palette,
        registry.picks, registry.byUid, materials))) },
    { name: "roofs", shell: true, items: each(model.roofs, (roof) => {
      const trades = roofTrades(roof);
      build(trades, roof.storey, () => buildRoof(container(trades), roof, center, mode, palette,
        model.catalog, registry.picks, registry.byUid, tradeGroups.framing, skinLines, tradeGroups));
    }) },
    { name: "openings", shell: false, items: each(model.openings, (opening) => {
      const wall = walls.get(opening.host);
      if (!wall) return;
      const doorType = doorTypes.get(opening.type_ref ?? "");
      build(family("opening"), wall.storey, () => buildOpening(tradeGroups.openings, opening, wall,
        center, mode, palette, { bookcaseDoor: doorType?.bookcase_door, materials },
        registry.picks, registry.byUid));
    }) },
    { name: "stairs", shell: false, items: each(model.stairs, (stair) => build(family("stair"),
      stair.storey, () => buildStair(tradeGroups.stairs, stair, center, mode, palette,
        registry.picks, registry.byUid, materials))) },
    { name: "finishes", shell: false, items: [
      // Room finishes go over the decks. Each room's `field_finish` is already cut by the
      // wells at its level (resolve/room_finish.py).
      ...each(model.rooms, (room) => {
        const top = storeyFloorTopM(model.floors ?? [], room.storey, placeableElevationM(model, room.storey));
        build(family("room_floor"), room.storey, () => buildRoomFloor(container(family("room_floor")),
          room, top, center, mode, palette, materials, registry.picks, registry.byUid));
      }),
      // A paneling band is the millworker's applied surface on a wall.
      ...each(model.panelings, (band) => {
        const trades = (band.trades?.length ? band.trades : family("paneling")) as Trade[];
        build(trades, band.storey, () => buildPaneling(container(trades), band, center, mode, palette,
          materials, registry.picks, registry.byUid));
      }),
      ...each(model.window_stools, (stool) => build(["millwork"], stool.storey, () => buildWindowStool(
        tradeGroups.millwork, stool, center, mode, palette, materials, registry.picks, registry.byUid))),
      ...each(model.base_runs, (run) => {
        const trade = baseRunTrade(run);
        build([trade], run.storey, () => buildBaseRun(tradeGroups[trade], run, center, mode, palette,
          materials, registry.picks, registry.byUid));
      }),
      ...each(model.door_casings, (casing) => build(["millwork"], casing.storey, () => buildDoorCasing(
        tradeGroups.millwork, casing, center, mode, palette, materials, registry.picks, registry.byUid))),
      ...each(model.countertops, (top) => build(["millwork"], top.storey, () => buildCountertop(
        tradeGroups.millwork, top, center, mode, palette, materials, registry.picks, registry.byUid))),
      ...each(model.soffits, (soffit) => build(family("soffit_framing"), soffit.storey,
        () => buildSoffitFraming(tradeGroups.framing, soffit, center, mode, palette, registry.picks,
          registry.byUid, materials))),
      ...each(model.braces, (brace) => build(family("brace"), brace.storey, () => buildBrace(
        tradeGroups.framing, brace, center, mode, palette, registry.picks, registry.byUid, materials))),
      // Washed stone with the tile bedded in it: drainage first, and the excavator's too.
      ...each(model.footing_beddings, (bedding) => {
        const trades = (bedding.trades?.length ? bedding.trades : family("footing_bedding")) as Trade[];
        build(trades, bedding.storey, () => buildFootingBedding(container(trades), bedding, center,
          mode, registry.picks, registry.byUid));
      }),
    ] },
    { name: "components", shell: false, items: each(solids.filter((solid) => !isShellSolid(solid)), solidItem) },
    { name: "furniture", shell: false, items: each(model.canvas_objects,
      (item) => buildCanvasObjectItem(options, item, canvasTypes)) },
    { name: "electrical", shell: false, items: [
      ...each(model.solar_panels, (panel) => build(family("solar_panel"), panel.storey,
        () => buildSolarPanel(tradeGroups.electrical, panel, center, mode, registry.picks, registry.byUid))),
      ...each([...alarmsByStorey], ([storey, alarms]) => build(["electrical"], storey, () => buildAlarms(
        tradeGroups.electrical, alarms, center, mode, palette, registry.picks, registry.byUid))),
      ...each(model.light_runs, (run) => build(family("light_run"), run.storey, () => buildLightRun(
        tradeGroups.electrical, run, center, mode, registry.picks, registry.byUid))),
    ] },
    { name: "plants", shell: false, items: each([...plantsByStorey], ([storey, plants]) => {
      const solid = solidsByUid.get(plants[0].uid);
      const trades = solid ? solidTrades(solid) : family("plant");
      build(solid ? solidVisibilityKeys(solid) : trades, storey, () => buildPlants(container(trades),
        plants, model.plant_models ?? [], center, mode, registry.picks, plantMaterials));
    }) },
    // Bars ride their own layer (builders/rebar.ts), tagged with the facet alone.
    { name: "rebar", shell: false, items: rebar ? [() => {
      if (rebar.sets) rebar.layer.show(rebar.sets, center, mode);
      else rebar.layer.clear();
    }] : [] },
  ];
}

/** Every stage, synchronously — the headless path, and anything that wants the whole scene now. */
export function populateScene(options: PopulateSceneOptions) {
  for (const stage of sceneStages(options)) for (const item of stage.items) item();
}

export interface ProgressiveBuild {
  tradeGroups: Record<Trade, THREE.Group>;
  /** Per-slice time budget; the runner yields to the browser between slices. */
  budgetMs?: number;
  /** True once a newer build (or a dispose) has superseded this one. */
  aborted: () => boolean;
  onProgress?: (progress: BuildProgress) => void;
  /** After every slice: what it added to the trade groups, for the visibility filter. */
  onSlice?: (before: Snapshot) => void;
  /** Once the shell stages are in: frame the camera and draw it (awaited). */
  onShell?: () => void | Promise<void>;
}

type Scheduler = { yield?: () => Promise<void> };
const scheduler = (globalThis as { scheduler?: Scheduler }).scheduler;
const channel = typeof MessageChannel === "undefined" ? null : new MessageChannel();
const tick = (): Promise<void> => {
  if (scheduler?.yield) return scheduler.yield();
  if (!channel) return new Promise((resolve) => setTimeout(resolve, 0));
  return new Promise((resolve) => {
    channel.port1.onmessage = () => resolve();
    channel.port2.postMessage(null);
  });
};
/** One painted frame (overlay, shell). rAF stalls in a hidden tab, so a timeout backs it. */
const nextFrame = (): Promise<void> => new Promise((resolve) => {
  if (typeof requestAnimationFrame === "undefined") { setTimeout(resolve, 0); return; }
  const timer = setTimeout(resolve, 100);
  requestAnimationFrame(() => setTimeout(() => { clearTimeout(timer); resolve(); }, 0));
});

/**
 * Build `stages` under a time budget, yielding between slices. Resolves with the ms spent per
 * stage, or null when `aborted()` turned true first (the partial scene is the next build's to
 * clear).
 */
export async function buildSceneProgressively(
  stages: readonly SceneStage[], options: ProgressiveBuild,
): Promise<Record<string, number> | null> {
  const { tradeGroups, budgetMs = 30, aborted, onProgress, onSlice, onShell } = options;
  const total = stages.reduce((sum, stage) => sum + stage.items.length, 0);
  const stageMs: Record<string, number> = {};
  let done = 0;
  let shellDrawn = false;
  // Let the overlay paint before the first slice takes the main thread.
  onProgress?.({ phase: stages[0]?.name ?? "", done, total, complete: false });
  await nextFrame();
  for (const stage of stages) {
    if (!shellDrawn && !stage.shell) {
      shellDrawn = true;
      if (aborted()) return null;
      await onShell?.();
      await nextFrame();
    }
    let index = 0;
    while (index < stage.items.length) {
      if (aborted()) return null;
      const sliceStart = performance.now();
      const before = onSlice ? snapshot(tradeGroups) : null;
      while (index < stage.items.length && performance.now() - sliceStart < budgetMs) {
        stage.items[index++]();
        done++;
      }
      stageMs[stage.name] = (stageMs[stage.name] ?? 0) + performance.now() - sliceStart;
      if (before) onSlice?.(before);
      onProgress?.({ phase: stage.name, done, total, complete: false });
      await tick();
    }
    stageMs[stage.name] ??= 0;
  }
  if (aborted()) return null;
  if (!shellDrawn) await onShell?.();
  onProgress?.({ phase: "", done, total, complete: true });
  return stageMs;
}

/** Apply the trade/level filter to what a slice added since `before` (→ registry.applyVisibility). */
export function applyVisibilitySince(
  tradeGroups: Record<Trade, THREE.Group>, before: Snapshot,
  visible: VisibleTrades, hiddenStoreys: ReadonlySet<string>,
) {
  for (const trade of ALL_TRADES) {
    const children = tradeGroups[trade].children;
    for (let index = before[trade]; index < children.length; index++) {
      children[index].traverse((object) => {
        if (object.userData.trades || object.userData.storey) {
          object.visible = objectVisible(object.userData, visible, hiddenStoreys);
        }
      });
    }
  }
}
