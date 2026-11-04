import type * as THREE from "three";

/** What the last full rebuild cost, by stage and by procedural texture (→ perf-check). */
export interface SceneBuildCost {
  buildMs: number;
  stageMs: Record<string, number>;
  textureMs: Record<string, number>;
  compileMs: number;
}

// Scene cost of the last rebuild, on `window.__haus.perf` for `npm run perf-check`. Draw calls
// and the build time are what lag tracks; a headless frame time is not (swiftshader).
export function publishPerf(renderer: THREE.WebGLRenderer, cost: SceneBuildCost, renderMs: number) {
  const haus = (window as unknown as { __haus?: Record<string, unknown> }).__haus;
  if (!haus) return;
  const { render, memory } = renderer.info;
  const { stageMs, textureMs, ...rest } = cost;
  haus.perf = {
    ...rest, renderMs, builders: stageMs, textureBreakdown: textureMs,
    texturesMs: Object.values(textureMs).reduce((sum, ms) => sum + ms, 0),
    calls: render.calls, triangles: render.triangles,
    geometries: memory.geometries, textures: memory.textures,
  };
}

// A later frame (orbit, dolly) without a rebuild: what the camera alone costs to redraw.
export function publishFrame(renderer: THREE.WebGLRenderer) {
  const perf = (window as unknown as { __haus?: { perf?: Record<string, unknown> } }).__haus?.perf;
  if (perf) perf.frameCalls = renderer.info.render.calls;
}

/** `window.__haus.sceneBuilding` while a progressive build runs, so a harness can wait it out. */
export function publishBuilding(building: boolean) {
  const haus = (window as unknown as { __haus?: Record<string, unknown> }).__haus;
  if (haus) haus.sceneBuilding = building;
}
