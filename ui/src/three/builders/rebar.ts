// The rebar layer of the 3D scene: the lazily fetched bars, one group per storey, tagged
// with ONLY the `concrete:rebar` facet. That is the visibility rule: the Rebar chip shows and
// hides them, and dropping the `concrete` chip leaves the cage standing inside the hidden
// pour (the x-ray view). Hiding a level hides its bars like everything else on it.
//
// It lives outside the trade containers so a scene rebuild (and the view fit, which bounds
// the trade containers) never has to know about it; Panel3D redraws it after a rebuild.
import * as THREE from "three";
import type { RebarSet } from "../../model/types";
import { disposeGroup } from "../members";
import type { PlanCenter } from "../planGeometry";
import { buildRebarMeshes } from "../rebar";
import type { SceneRegistry } from "./scene";

export const REBAR_VISIBILITY_KEYS = ["concrete:rebar"] as const;

export interface RebarLayer {
  root: THREE.Group;
  /** Replace whatever is drawn with `sets`. */
  show: (sets: readonly RebarSet[], center: PlanCenter, mode: "nordic" | "schematic") => void;
  clear: () => void;
}

/** One group per storey, each tagged for the trade and level filters. Exported for tests. */
export function buildRebarGroups(sets: readonly RebarSet[], center: PlanCenter,
  mode: "nordic" | "schematic"): THREE.Group[] {
  const byStorey = new Map<string, RebarSet[]>();
  for (const set of sets) byStorey.set(set.storey, [...(byStorey.get(set.storey) ?? []), set]);
  return [...byStorey].map(([storey, storeySets]) => {
    const group = new THREE.Group();
    group.userData.trades = [...REBAR_VISIBILITY_KEYS];
    if (storey) group.userData.storey = storey;
    for (const mesh of buildRebarMeshes(storeySets, center, mode)) group.add(mesh);
    return group;
  });
}

export function createRebarLayer(parent: THREE.Object3D, registry: SceneRegistry): RebarLayer {
  const root = new THREE.Group();
  parent.add(root);
  let picks = new Set<THREE.Object3D>();

  const clear = () => {
    disposeGroup(root);
    root.clear();
    // `registry.picks` is replaced wholesale on a rebuild, so filter the live list.
    if (picks.size) registry.picks = registry.picks.filter((mesh) => !picks.has(mesh));
    picks = new Set();
  };

  const show = (sets: readonly RebarSet[], center: PlanCenter, mode: "nordic" | "schematic") => {
    clear();
    for (const group of buildRebarGroups(sets, center, mode)) {
      root.add(group);
      group.traverse((node) => {
        if (!(node instanceof THREE.Mesh)) return;
        registry.picks.push(node);
        picks.add(node);
      });
    }
  };

  return { root, show, clear };
}
