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
import type { Model } from "../../model/types";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { disposeGroup } from "../members";
import { solidTrade } from "../solidMaterials";
import {
  projectPlanRotationToSceneRadians, projectPointToScene, type PlanCenter,
} from "../planGeometry";
import type { Trade } from "../../state/vocabulary";
import { buildCanvasObject, buildEarth } from "./site";
import { buildOpening, buildWall } from "./walls";
import {
  buildBrace, buildFloor, buildFootingBedding, buildLightRun, buildRoof, buildRoomFloor,
  buildSolarPanel, buildSolid, buildStair, storeyFloorTopM,
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
  registry: SceneRegistry;
  /** The scene generation at call time; an async glb that resolves after a rebuild is dropped. */
  generation: number;
  currentGeneration: () => number;
  requestRender: () => void;
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

function placeableGroup(
  tradeGroups: Record<Trade, THREE.Group>, domain: string | null | undefined,
): THREE.Group {
  if (domain === "plumbing") return tradeGroups.plumbing;
  if (domain === "electrical") return tradeGroups.electrical;
  if (domain === "mechanical") return tradeGroups.mechanical;
  return tradeGroups.furniture;
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
    tradeGroups, model, center, mode, palette, registry, generation, currentGeneration,
    requestRender,
  } = options;

  for (const wall of model.walls) {
    const wallOpenings = model.openings.filter((opening) => opening.host === wall.tag);
    buildWall(tradeGroups, wall, wallOpenings, center, mode, palette, registry.picks,
      registry.byUid, model.catalog?.materials);
    for (const opening of wallOpenings) {
      const doorType = model.catalog?.door_types.find((type) => type.tag === opening.type_ref);
      buildOpening(tradeGroups.openings, opening, wall, center, mode, palette, doorType?.operation,
        registry.picks, registry.byUid, doorType?.glazed ?? false, doorType?.trimless ?? false);
    }
  }
  // The site sheet is context, not an element: it has no uid in model.json, so it stays out
  // of the raycast set and a click through it falls to whatever building geometry is behind.
  buildEarth(tradeGroups.earth, model, center, mode);
  // A solid is not automatically concrete: a standalone beam or post is framing (the same
  // lumber as the studs and rafters it carries), a routed pipe run is plumbing, roof edge trim
  // is roof. The mapping is shared with the exporter — see solidTrade / emit/trades.py.
  for (const solid of model.solids ?? []) {
    buildSolid(tradeGroups[solidTrade(solid)], solid, center, mode, palette, model.catalog,
      registry.picks, registry.byUid);
  }
  for (const bedding of model.footing_beddings ?? []) {
    // Beddings have no category to consult: a footing's gravel bed is a pour by definition.
    buildFootingBedding(tradeGroups.concrete, bedding, center, mode, registry.picks, registry.byUid);
  }
  for (const floor of model.floors ?? []) {
    buildFloor(tradeGroups.floors, floor, center, mode, palette, registry.picks, registry.byUid,
      tradeGroups.framing);
  }
  // Room finishes go over the decks, so they build after every floor is in. Deck openings are
  // per storey, not per floor system, so they are gathered once and cut out of each finish —
  // without that a stair well ends up capped by the finish above it.
  for (const room of model.rooms ?? []) {
    const floors = model.floors ?? [];
    const openings = floors.filter((floor) => floor.storey === room.storey)
      .flatMap((floor) => floor.openings);
    const top = storeyFloorTopM(floors, room.storey, placeableElevationM(model, room.storey));
    buildRoomFloor(tradeGroups.floors, room, top, openings, center, mode, palette,
      model.catalog?.materials, registry.picks, registry.byUid);
  }
  for (const roof of model.roofs ?? []) {
    buildRoof(tradeGroups.roof, roof, center, mode, palette, model.catalog, registry.picks,
      registry.byUid, tradeGroups.framing);
  }
  for (const panel of model.solar_panels ?? []) {
    buildSolarPanel(tradeGroups.electrical, panel, center, mode, registry.picks, registry.byUid);
  }
  for (const run of model.light_runs ?? []) {
    buildLightRun(tradeGroups.electrical, run, center, mode, registry.picks, registry.byUid);
  }
  for (const stair of model.stairs ?? []) {
    buildStair(tradeGroups.stairs, stair, center, mode, palette, registry.picks, registry.byUid);
  }
  for (const brace of model.braces ?? []) {
    buildBrace(tradeGroups.framing, brace, center, mode, palette, registry.picks, registry.byUid);
  }

  const types = new Map((model.catalog?.canvas_object_types ?? []).map((type) => [type.tag, type]));
  for (const item of model.canvas_objects ?? []) {
    // Hosted openings retain their dedicated cut/fill meshes above. The normalized
    // record is for shared inspection and interchange, not a second 3D proxy.
    if (item.domain === "opening") continue;
    if (!item.position_m) continue;
    const group = placeableGroup(tradeGroups, item.domain);
    const type = types.get(item.type ?? "");
    const elevation = item.z_m ?? placeableElevationM(model, item.storey);
    const fallback = buildCanvasObject(group, item, type, center, mode, palette, elevation,
      registry.picks, registry.byUid);
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
