// Wood maps arrive in two steps: a flat placeholder now, the worker's figure a moment later.
// The texture objects never change identity, so the material's shader is the final one.
import * as THREE from "three";
import type { PlankStyle } from "./plankLayout";
import { WOOD_RENDER_SETTINGS as SETTINGS, type WoodSpeciesProfile, type WoodSurface } from "./woodSpecies";
import { renderWoodPixels, type WoodPixelJob, type WoodPixels } from "./woodPixels";
import WoodWorker from "./woodMaps.worker?worker";

export interface WoodMaps {
  readonly colorMap: THREE.Texture;
  readonly normalMap: THREE.Texture;
  readonly roughnessMap: THREE.Texture;
}
interface Pending { readonly id: number; readonly key: string; readonly job: WoodPixelJob }
const cache = new Map<string, WoodMaps>();
const queue: Pending[] = [];
const listeners = new Set<() => void>();
let settleWaiters: (() => void)[] = [];
let nextId = 0, inFlight = 0;
let pool: { worker: Worker; busy: Pending | null }[] | null = null;
const PLACEHOLDER_EDGE = 4;

function texture(canvas: HTMLCanvasElement, color = false) {
  const map = new THREE.CanvasTexture(canvas);
  map.wrapS = map.wrapT = THREE.RepeatWrapping;
  map.colorSpace = color ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  map.anisotropy = 4;
  return map;
}

function filled(fill: string) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = PLACEHOLDER_EDGE;
  const context = canvas.getContext("2d");
  if (!context) return null;
  context.fillStyle = fill; context.fillRect(0, 0, PLACEHOLDER_EDGE, PLACEHOLDER_EDGE);
  return canvas;
}

const byte = (v: number) => Math.round(Math.max(0, Math.min(1, v)) * 255);

/** Full-colour maps: the texture carries the authored base plus positive AND negative variation. */
export function buildSpeciesWoodMaps(style: PlankStyle, profile: WoodSpeciesProfile,
  color: THREE.ColorRepresentation, surface: WoodSurface, endGrain = false): WoodMaps | null {
  if (typeof document === "undefined") return null;
  const baseColor = new THREE.Color(color);
  const key = JSON.stringify([style, profile, baseColor.getHexString(), surface, endGrain]);
  const cached = cache.get(key);
  if (cached) return cached;
  const srgb = baseColor.clone().convertLinearToSRGB();
  const painted = surface === "painted";
  const shade = endGrain && !painted ? SETTINGS.endGrainDarkening : 1;
  const rough = byte(1 - SETTINGS.roughnessVariation * (painted ? 1 : 0.5));
  const canvases = [
    filled(`rgb(${byte(srgb.r * shade)},${byte(srgb.g * shade)},${byte(srgb.b * shade)})`),
    filled("rgb(128,128,255)"), filled(`rgb(${rough},${rough},${rough})`),
  ];
  if (canvases.some(c => !c)) return null;
  const [colorCanvas, normalCanvas, roughnessCanvas] = canvases as HTMLCanvasElement[];
  const maps = { colorMap: texture(colorCanvas, true), normalMap: texture(normalCanvas),
    roughnessMap: texture(roughnessCanvas) };
  cache.set(key, maps);
  const job = { style, profile, base: [srgb.r, srgb.g, srgb.b] as const, surface, endGrain };
  // Face maps first: end grain is small and only seen on crosscuts.
  const firstEnd = queue.findIndex(p => p.job.endGrain);
  queue.splice(endGrain || firstEnd < 0 ? queue.length : firstEnd, 0, { id: nextId++, key, job });
  inFlight++;
  pump();
  return maps;
}

function workers() {
  if (pool) return pool;
  pool = [];
  if (typeof Worker === "undefined") return pool;
  const size = Math.max(1, Math.min(4, (navigator.hardwareConcurrency ?? 2) - 1));
  try {
    for (let i = 0; i < size; i++) {
      const slot: { worker: Worker; busy: Pending | null } = { worker: new WoodWorker(), busy: null };
      slot.worker.onmessage = (event: MessageEvent<{ pixels?: WoodPixels }>) => {
        const done = slot.busy!;
        slot.busy = null;
        if (event.data.pixels) finish(done, event.data.pixels); else fallback.push(done);
        pump();
      };
      // A worker that cannot load leaves the pool; its job falls back to the main thread.
      slot.worker.onerror = () => {
        if (slot.busy) fallback.push(slot.busy);
        pool!.splice(pool!.indexOf(slot), 1);
        slot.worker.terminate();
        pump();
      };
      pool.push(slot);
    }
  } catch { /* no module workers here: the main-thread path renders */ }
  return pool;
}

const fallback: Pending[] = [];
let fallbackScheduled = false;
function pump() {
  const slots = workers();
  if (!slots.length) fallback.push(...queue.splice(0));
  for (const slot of slots) {
    if (slot.busy || !queue.length) continue;
    slot.busy = queue.shift()!;
    slot.worker.postMessage({ id: slot.busy.id, job: slot.busy.job });
  }
  // One job per macrotask, so no single frame is held for the whole set.
  if (fallback.length && !fallbackScheduled) {
    fallbackScheduled = true;
    setTimeout(() => {
      fallbackScheduled = false;
      const next = fallback.shift()!;
      let pixels: WoodPixels | null = null;
      try { if (cache.has(next.key)) pixels = renderWoodPixels(next.job); } catch { /* stays flat */ }
      finish(next, pixels);
      pump();
    }, 0);
  }
}

function finish(done: Pending, pixels: WoodPixels | null) {
  inFlight--;
  const maps = cache.get(done.key);
  // A reply for a key disposed since it was queued is dropped.
  if (pixels && maps) {
    const images = [pixels.color, pixels.normal, pixels.roughness];
    [maps.colorMap, maps.normalMap, maps.roughnessMap].forEach((map, i) => {
      const canvas = document.createElement("canvas");
      canvas.width = pixels.width; canvas.height = pixels.height;
      canvas.getContext("2d")!.putImageData(
        new ImageData(images[i] as Uint8ClampedArray<ArrayBuffer>, pixels.width, pixels.height), 0, 0);
      // The placeholder's GPU storage is immutable at 4×4; a fresh upload needs it freed.
      map.dispose();
      map.image = canvas;
      map.needsUpdate = true;
    });
    for (const listener of listeners) listener();
  }
  if (inFlight === 0) {
    const waiters = settleWaiters;
    settleWaiters = [];
    for (const resolve of waiters) resolve();
  }
}

/** Called after each finished map set; returns its unsubscribe. */
export function onWoodMapsReady(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

/** Resolves once every queued map set has its figure. */
export function woodMapsSettled(): Promise<void> {
  if (inFlight === 0) return Promise.resolve();
  return new Promise(resolve => settleWaiters.push(resolve));
}

/** Drop the process-wide wood maps — only for teardown in tests/hot reload. */
export function disposeWoodTextures(): void {
  for (const { colorMap, normalMap, roughnessMap } of cache.values()) {
    colorMap.dispose(); normalMap.dispose(); roughnessMap.dispose();
  }
  cache.clear();
}
