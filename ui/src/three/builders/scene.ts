// The shared pieces of one model.json → one populated set of trade groups: the plan centre,
// the snapshot-and-tag bookkeeping every builder call goes through, and the placed-object
// builder with its async glb swap. The stage order and the runner live in sceneStages.ts.
//
// The registry is passed as an object rather than as two loose values because the async
// furniture loader below *replaces* the pick list (it drops the fallback massing's picks when
// the real glb lands); a plain array parameter could not carry that back out.
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Model, RebarSet } from "../../model/types";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { disposeGroup } from "../members";
import { canvasObjectTrades, primaryTrade, type VisibilityKey } from "../../model/tradeVisibility";
import {
  projectPlanRotationToSceneRadians, projectPointToScene, type PlanCenter,
} from "../planGeometry";
import { ALL_TRADES, type EarthTone, type Trade } from "../../state/vocabulary";
import type { RebarLayer } from "./rebar";
import { tagStorey as tagStoreyChildren, tagTrades } from "./registry";
import { buildCanvasObject, buildSuspension, type PartGeometries } from "./site";

/** What a click can land on, and which materials the highlight pass drives per uid. */
export interface SceneRegistry {
  picks: THREE.Mesh[];
  byUid: Map<string, THREE.Material[]>;
  /** Meshes of each opening piece, keyed `uid|piece` (→ registry.indexPieces). */
  byPiece?: Map<string, THREE.Mesh[]>;
  /** Product part geometry the scene's instances share; disposed by whoever clears the scene. */
  partGeometries?: PartGeometries;
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
export function placeableElevationM(model: Model, storeyTag: string | null | undefined): number {
  return (storeyTag != null ? storeyElevations(model).get(storeyTag) : undefined) ?? 0;
}

// One tag → elevation map per model, not a `.find` per placeable.
const elevationsByModel = new WeakMap<Model, Map<string, number>>();
function storeyElevations(model: Model): Map<string, number> {
  let map = elevationsByModel.get(model);
  if (!map) {
    map = new Map();
    for (const storey of model.storeys) if (!map.has(storey.tag)) map.set(storey.tag, storey.elevation_m);
    elevationsByModel.set(model, map);
  }
  return map;
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

type CanvasObject = NonNullable<Model["canvas_objects"]>[number];
type CanvasObjectType = NonNullable<NonNullable<Model["catalog"]>["canvas_object_types"]>[number];

/** One placed canvas object: its fallback massing now, its glb in place of it when that lands. */
export function buildCanvasObjectItem(options: PopulateSceneOptions, item: CanvasObject,
  types: ReadonlyMap<string, CanvasObjectType>) {
  const {
    tradeGroups, model, center, mode, palette, registry, generation, currentGeneration,
    requestRender, tradeVisible,
  } = options;
  const container = (trades: readonly Trade[]) => tradeGroups[primaryTrade(trades)];
  // Hosted openings keep their dedicated cut/fill meshes (the openings stage). The normalized
  // record is for shared inspection and interchange, not a second 3D proxy.
  if (item.domain === "opening" || !item.position_m) return;
  const trades = canvasObjectTrades(item);
  const group = container(trades);
  const type = types.get(item.type ?? "");
  const elevation = item.z_m ?? placeableElevationM(model, item.storey);
  const before = snapshot(tradeGroups);
  const fallback = buildCanvasObject(group, item, type, center, mode, palette, elevation,
    registry.picks, registry.byUid, model.catalog?.materials, model.catalog?.meshes,
    registry.partGeometries);
  buildSuspension(group, item, center, mode, registry.picks, registry.byUid);
  tagNew(tradeGroups, before, trades);
  tagStorey(tradeGroups, before, item.storey ?? null);
  if (!type?.model_glb || !fallback) return;
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
