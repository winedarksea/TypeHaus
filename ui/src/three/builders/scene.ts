// One model.json → one populated set of trade groups.
//
// Split out of components/Panel3D.tsx's setModel, which was doing three jobs at once: work out
// the plan centre, walk every record family into its builder, and re-frame the camera. Only the
// middle one is about the *model*, and it is the part that grows every time the resolver learns
// to emit something new — so it lives here, with the builders it dispatches to.
//
// The registry is passed as an object rather than as two loose values because the async
// furniture loader below *replaces* the pick list (it drops the fallback massing's picks when
// the real glb lands); a plain array parameter could not carry that back out.
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Model, RebarSet } from "../../model/types";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { disposeGroup, type SkinLine } from "../members";
import {
  canvasObjectTrades, primaryTrade, RECORD_FAMILY_TRADES, roofTrades, solidTrades,
  solidVisibilityKeys, type VisibilityKey, wallTrades,
} from "../../model/tradeVisibility";
import {
  projectPlanRotationToSceneRadians, projectPointToScene, type PlanCenter,
} from "../planGeometry";
import { ALL_TRADES, type EarthTone, type Trade } from "../../state/vocabulary";
import { buildLightRun } from "./lightRun";
import { buildWindowStool } from "./millwork";
import { buildPlants, instancedPlantUids } from "./plants";
import type { RebarLayer } from "./rebar";
import { tagStorey as tagStoreyChildren, tagTrades } from "./registry";
import { buildCanvasObject, buildEarth, buildSuspension } from "./site";
import { buildOpening } from "./openings";
import { buildWall } from "./walls";
import {
  buildBrace, buildFloor, buildFootingBedding, buildRoof, buildRoomFloor,
  buildPaneling, buildSoffitFraming, buildSolarPanel, buildSolid, buildStair,
  storeyFloorTopM,
} from "./structure";

/** What a click can land on, and which materials the highlight pass drives per uid. */
export interface SceneRegistry {
  picks: THREE.Mesh[];
  byUid: Map<string, THREE.Material[]>;
}

export interface PopulateSceneOptions {
  tradeGroups: Record<Trade, THREE.Group>;
  model: Model;
  center: PlanCenter;
  mode: "nordic" | "schematic";
  palette: ResolvedNordicPalette;
  /** Site-sheet opacity at build time; the panel slider retargets it live afterwards. */
  earthOpacity: number;
  /** Its colour at build time, retargeted live the same way (→ Panel3D setEarthTone). */
  earthTone: EarthTone;
  registry: SceneRegistry;
  /** The scene generation at call time; an async glb that resolves after a rebuild is dropped. */
  generation: number;
  currentGeneration: () => number;
  requestRender: () => void;
  /** The trade and level filters at the moment an async placeable asset lands, so it arrives
   *  hidden when its trade or storey is. Optional: a caller with no filter shows everything. */
  tradeVisible?: (trades: readonly string[], storey: string | null) => boolean;
  /** The lazily fetched bars already loaded for THIS model, and the layer they draw into.
   *  Absent until the Rebar chip first turns on (→ engine/rebarCache.ts). */
  rebar?: { layer: RebarLayer; sets: readonly RebarSet[] | null };
}

/**
 * The plan centre every builder projects around: the mean of the wall axis endpoints, so the
 * building sits near the scene origin whatever its site coordinates are.
 */
export function planCenterOf(model: Model): PlanCenter {
  let cx = 0;
  let cz = 0;
  let n = 0;
  for (const wall of model.walls) {
    for (const point of wall.axis) {
      cx += point[0];
      cz += point[1];
      n++;
    }
  }
  return n ? [cx / n, cz / n] : [0, 0];
}

/** The storey elevation a placeable sits on when it declares no z of its own. */
function placeableElevationM(model: Model, storeyTag: string | null | undefined): number {
  return model.storeys.find((storey) => storey.tag === storeyTag)?.elevation_m ?? 0;
}

// Every builder writes into one or more trade containers; the container is the element's
// PRIMARY trade and the meshes carry the element's whole trade SET (fill-in: a builder that
// already tagged finer sets — a wall's bands, a roof's skin buckets — keeps them). Snapshot
// every container before a builder call, tag what appeared afterwards.
export type Snapshot = Record<Trade, number>;

export function snapshot(tradeGroups: Record<Trade, THREE.Group>): Snapshot {
  return Object.fromEntries(
    ALL_TRADES.map((trade) => [trade, tradeGroups[trade].children.length]),
  ) as Snapshot;
}

export function tagNew(tradeGroups: Record<Trade, THREE.Group>, before: Snapshot,
  trades: readonly VisibilityKey[]) {
  // A caller that already named a framing FACET meant it, and flattening it here is what
  // made the Connectors toggle silently do nothing: the marker arrived correctly routed and
  // was immediately relabelled `framing`. Narrowed to the case the force-tag is actually for
  // — a wall or a roof whose incidental framing landed in the container without a set of its
  // own. `wallSkinMembers` self-tags for exactly the same reason.
  const namedFacets = trades.filter((key) => key.startsWith("framing:"));
  for (const trade of ALL_TRADES) {
    const set = trade === "framing"
      ? (namedFacets.length ? namedFacets : ["framing"])
      : trades;
    tagTrades(tradeGroups[trade], before[trade], set);
  }
}

/** Stamp the storey an element is filed on onto everything it added, in every container. */
export function tagStorey(tradeGroups: Record<Trade, THREE.Group>, before: Snapshot,
  storey: string | null) {
  for (const trade of ALL_TRADES) tagStoreyChildren(tradeGroups[trade], before[trade], storey);
}

// One loader and one in-flight load per asset URL, kept across rebuilds.
//
// The loader was constructed inside the placement loop, so N chairs of one type meant N fetches
// and N parses of the same .glb — repeated in full on every setModel (an edit, a theme flip, a
// nordic/schematic toggle). Nothing about the asset varies per placement, so the parse is
// hoisted and each placement takes a copy.
const placeableLoader = new GLTFLoader();
const placeableAssets = new Map<string, Promise<THREE.Object3D>>();

function loadPlaceableAsset(url: string): Promise<THREE.Object3D> {
  let pending = placeableAssets.get(url);
  if (!pending) {
    pending = new Promise<THREE.Object3D>((resolve, reject) => {
      placeableLoader.load(url, (gltf) => resolve(gltf.scene), undefined, reject);
    });
    // A failed load must not be cached as a permanent failure — the PWA loses the network and
    // gets it back — but a rejected promise nobody awaits is an unhandled rejection, so the
    // entry is dropped rather than left to reject again on the next rebuild.
    pending.catch(() => placeableAssets.delete(url));
    placeableAssets.set(url, pending);
  }
  return pending;
}

/**
 * A private copy of a cached asset.
 *
 * Geometry and material are copied too, not shared with the cached original: `disposeGroup`
 * frees whatever is in a trade group when the scene is rebuilt, which would otherwise gut the
 * cache, and the highlight pass drives the selected object's *own* materials — sharing them
 * would light up every instance of the type. Copying a parsed buffer is still far cheaper than
 * re-fetching and re-parsing the file.
 */
function instantiatePlaceableAsset(prototype: THREE.Object3D): THREE.Object3D {
  const copy = prototype.clone(true);
  copy.traverse((node) => {
    if (!(node instanceof THREE.Mesh)) return;
    node.geometry = node.geometry.clone();
    node.material = Array.isArray(node.material)
      ? node.material.map((material) => material.clone())
      : node.material.clone();
  });
  return copy;
}

export function populateScene(options: PopulateSceneOptions) {
  const {
    tradeGroups, model, center, mode, palette, earthOpacity, earthTone, registry, generation,
    currentGeneration, requestRender, tradeVisible, rebar,
  } = options;
  const build = (trades: readonly VisibilityKey[], storey: string | null | undefined,
    run: () => void) => {
    const before = snapshot(tradeGroups);
    run();
    tagNew(tradeGroups, before, trades);
    tagStorey(tradeGroups, before, storey ?? null);
  };
  const family = (name: string) => RECORD_FAMILY_TRADES[name] ?? ["concrete"];
  const container = (trades: readonly Trade[]) => tradeGroups[primaryTrade(trades)];

  for (const wall of model.walls) {
    const wallOpenings = model.openings.filter((opening) => opening.host === wall.tag);
    build(wallTrades(wall), wall.storey, () => buildWall(tradeGroups, wall, wallOpenings, center, mode,
      palette, registry.picks, registry.byUid, model.catalog?.materials));
    for (const opening of wallOpenings) {
      const doorType = model.catalog?.door_types.find((type) => type.tag === opening.type_ref);
      build(family("opening"), wall.storey, () => buildOpening(tradeGroups.openings, opening, wall, center,
        mode, palette, doorType?.operation, registry.picks, registry.byUid,
        doorType?.glazed ?? false, doorType?.trimless ?? false));
    }
  }
  for (const stool of model.window_stools ?? []) {
    build(["millwork"], stool.storey, () => buildWindowStool(
      tradeGroups.millwork, stool, center, mode, palette, model.catalog?.materials,
      registry.picks, registry.byUid));
  }
  // The site sheet is context, not an element: it has no uid in model.json, so it stays out
  // of the raycast set and a click through it falls to whatever building geometry is behind.
  build(family("earth"), null, () => buildEarth(tradeGroups.earth, model, center, mode, earthOpacity, earthTone));
  // A solid is not automatically concrete: a standalone beam or post is framing, a routed pipe
  // run is plumbing, a cast column is concrete. The set is stamped by the engine
  // (model.json `trades`) and falls back to the generated category map.
  // A plant with a procedural model draws as an instance below, not as its bounding prism.
  const instancedPlants = instancedPlantUids(model.plants, model.plant_models);
  for (const solid of model.solids ?? []) {
    if (solid.category === "plant" && instancedPlants.has(solid.uid)) continue;
    // Two answers, deliberately. `solidTrades` decides the CONTAINER (a connector's is
    // framing, and `primaryTrade` maps its facet back to framing anyway); the keys decide
    // what it is TAGGED with, which is what its own toggle reaches.
    const trades = solidTrades(solid);
    build(solidVisibilityKeys(solid), solid.storey, () => buildSolid(container(trades), solid, center,
      mode, palette, model.catalog, registry.picks, registry.byUid,
      model.catalog?.materials));
  }
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
  for (const [storey, plants] of plantsByStorey) {
    const solid = solidsByUid.get(plants[0].uid);
    const trades = solid ? solidTrades(solid) : family("plant");
    build(solid ? solidVisibilityKeys(solid) : trades, storey, () => buildPlants(container(trades),
      plants, model.plant_models ?? [], center, mode, registry.picks, plantMaterials));
  }
  // A paneling band is the millworker's applied surface on a wall.
  for (const band of model.panelings ?? []) {
    const trades = (band.trades?.length ? band.trades : family("paneling")) as Trade[];
    build(trades, band.storey, () => buildPaneling(container(trades), band, center, mode, palette,
      model.catalog?.materials, registry.picks, registry.byUid));
  }
  for (const bedding of model.footing_beddings ?? []) {
    // Washed stone with the tile bedded in it: drainage first, and the excavator's too.
    const trades = (bedding.trades?.length ? bedding.trades : family("footing_bedding")) as Trade[];
    build(trades, bedding.storey, () => buildFootingBedding(container(trades), bedding, center, mode,
      registry.picks, registry.byUid));
  }
  for (const floor of model.floors ?? []) {
    build(family("floor_deck"), floor.storey, () => buildFloor(tradeGroups.framing, floor, center, mode,
      palette, registry.picks, registry.byUid, tradeGroups.framing, model.catalog?.materials));
  }
  // Room finishes go over the decks, so they build after every floor is in. Each room's
  // `field_finish` is already cut by the wells at its level (resolve/room_finish.py).
  for (const room of model.rooms ?? []) {
    const floors = model.floors ?? [];
    const top = storeyFloorTopM(floors, room.storey, placeableElevationM(model, room.storey));
    build(family("room_floor"), room.storey, () => buildRoomFloor(container(family("room_floor")), room, top,
      center, mode, palette, model.catalog?.materials, registry.picks, registry.byUid));
  }
  // The facade datums every wall's cladding is framed on (builders/walls.ts uses the same
  // `layout_axis ?? axis`), handed to the roofs so a wall→roof closure band's panel module
  // continues the wall's instead of restarting at the band (→ members.ts skinUvSpanM).
  const skinLines: SkinLine[] = (model.walls ?? []).map((wall) => ({
    axis: wall.axis, datum: wall.layout_axis ?? wall.axis,
  }));
  for (const roof of model.roofs ?? []) {
    const trades = roofTrades(roof);
    build(trades, roof.storey, () => buildRoof(container(trades), roof, center, mode, palette,
      model.catalog, registry.picks, registry.byUid, tradeGroups.framing, skinLines,
      tradeGroups));
  }
  for (const panel of model.solar_panels ?? []) {
    build(family("solar_panel"), panel.storey, () => buildSolarPanel(tradeGroups.electrical, panel, center,
      mode, registry.picks, registry.byUid));
  }
  for (const run of model.light_runs ?? []) {
    build(family("light_run"), run.storey, () => buildLightRun(tradeGroups.electrical, run, center, mode,
      registry.picks, registry.byUid));
  }
  for (const stair of model.stairs ?? []) {
    build(family("stair"), stair.storey, () => buildStair(tradeGroups.stairs, stair, center, mode, palette,
      registry.picks, registry.byUid, model.catalog?.materials));
  }
  for (const soffit of model.soffits ?? []) {
    build(family("soffit_framing"), soffit.storey, () => buildSoffitFraming(tradeGroups.framing, soffit,
      center, mode, palette, registry.picks, registry.byUid, model.catalog?.materials));
  }

  for (const brace of model.braces ?? []) {
    build(family("brace"), brace.storey, () => buildBrace(tradeGroups.framing, brace, center, mode, palette,
      registry.picks, registry.byUid, model.catalog?.materials));
  }

  // Bars ride their own layer (builders/rebar.ts), tagged with the facet alone.
  if (rebar) {
    if (rebar.sets) rebar.layer.show(rebar.sets, center, mode);
    else rebar.layer.clear();
  }

  const types = new Map((model.catalog?.canvas_object_types ?? []).map((type) => [type.tag, type]));
  for (const item of model.canvas_objects ?? []) {
    // Hosted openings retain their dedicated cut/fill meshes above. The normalized
    // record is for shared inspection and interchange, not a second 3D proxy.
    if (item.domain === "opening") continue;
    if (!item.position_m) continue;
    const trades = canvasObjectTrades(item);
    const group = container(trades);
    const type = types.get(item.type ?? "");
    const elevation = item.z_m ?? placeableElevationM(model, item.storey);
    const before = snapshot(tradeGroups);
    const fallback = buildCanvasObject(group, item, type, center, mode, palette, elevation,
      registry.picks, registry.byUid);
    buildSuspension(group, item, center, mode, registry.picks, registry.byUid);
    tagNew(tradeGroups, before, trades);
    tagStorey(tradeGroups, before, item.storey ?? null);
    if (!type?.model_glb || !fallback) continue;
    loadPlaceableAsset(type.model_glb).then((prototype) => {
      if (generation !== currentGeneration() || !item.position_m) return;
      const visual = instantiatePlaceableAsset(prototype);
      // The fallback may be a whole group of massing parts now, not one mesh, so drop
      // every pick it owns and dispose it as a subtree.
      group.remove(fallback);
      const replaced = new Set<THREE.Object3D>();
      fallback.traverse((node) => replaced.add(node));
      disposeGroup(fallback);
      registry.picks = registry.picks.filter((mesh) => !replaced.has(mesh));
      visual.position.copy(projectPointToScene(item.position_m, elevation, center));
      visual.rotation.y = projectPlanRotationToSceneRadians(item.rotation ?? 0);
      visual.userData.trades = [...trades];
      if (item.storey) visual.userData.storey = item.storey;
      visual.visible = tradeVisible?.(trades, item.storey ?? null) ?? true;
      const materials: THREE.Material[] = [];
      visual.traverse((node) => {
        if (!(node instanceof THREE.Mesh)) return;
        node.castShadow = true;
        node.receiveShadow = true;
        node.userData.uid = item.uid;
        node.userData.selectionKind = "canvas_object";
        registry.picks.push(node);
        const material = node.material;
        materials.push(...(Array.isArray(material) ? material : [material]));
      });
      registry.byUid.set(item.uid, materials);
      group.add(visual);
      requestRender();
    }).catch(() => { /* keep the fallback massing the placement already drew */ });
  }
}
