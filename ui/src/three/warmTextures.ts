// Build the module-cached procedural maps ahead of the first scene, one per idle slot, so the
// first build after a 2D→3D switch finds them warm (→ Panel3DLazy preloadPanel3DWhenIdle).
// Only the model-independent maps: a tile style is per material, and is built on first use.
import { buildCarpetMaps } from "./carpetMaterial";
import { buildLoopMaps } from "./carpetLoopMaterial";
import { buildMarbleMap } from "./marbleMaterial";
import {
  buildWashMaps, CORRUGATED_PROFILE, metalPanelNormalMap, RIBBED_PANEL_PROFILE, SEAM_PROFILE,
} from "./materials";
import { frostWhiteMap } from "./quartzMaterial";
import { buildSprayFoamMaps } from "./sprayFoamMaterial";

const WARMERS: Array<() => unknown> = [
  () => metalPanelNormalMap(SEAM_PROFILE),
  () => metalPanelNormalMap(RIBBED_PANEL_PROFILE),
  () => metalPanelNormalMap(CORRUGATED_PROFILE),
  buildWashMaps, buildSprayFoamMaps, buildCarpetMaps, buildLoopMaps, buildMarbleMap, frostWhiteMap,
];

/** Run each warmer in its own `idle` slot; returns a cancel. */
export function warmProceduralTextures(idle: (run: () => void) => () => void): () => void {
  let cancel: (() => void) | null = null;
  const next = (index: number) => {
    if (index >= WARMERS.length) return;
    cancel = idle(() => {
      WARMERS[index]();
      next(index + 1);
    });
  };
  next(0);
  return () => cancel?.();
}
