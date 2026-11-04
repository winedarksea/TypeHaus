// Tile maps arrive in two steps, as in woodMaps.ts: a flat placeholder now (face colour, flat
// normal, the face's roughness), the worker's 1024² raster a moment later. A style was ~0.45 s of
// main-thread pixel work per first use. Texture identity never changes, so the shader is final.
import * as THREE from "three";
import { textureTimer } from "./buildTimings";
import { renderTilePixels, TILE_RENDER_SETTINGS, type TilePixels, type TileStyle } from "./tilePixels";
import TileWorker from "./tileMaps.worker?worker";

export interface TileMaps { color: THREE.Texture; normal: THREE.Texture; roughness: THREE.Texture }
interface Pending { readonly id: number; readonly style: TileStyle }
const cache = new Map<TileStyle, TileMaps>();
const queue: Pending[] = [];
const fallback: Pending[] = [];
const listeners = new Set<() => void>();
let settleWaiters: (() => void)[] = [];
let nextId = 0, inFlight = 0, fallbackScheduled = false;
let pool: { worker: Worker; busy: Pending | null }[] | null = null;

function filled(r: number, g: number, b: number) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 4;
  const context = canvas.getContext("2d");
  if (!context) return null;
  context.fillStyle = `rgb(${r},${g},${b})`; context.fillRect(0, 0, 4, 4);
  return canvas;
}

function texture(canvas: HTMLCanvasElement, color: boolean) {
  const map = new THREE.CanvasTexture(canvas);
  map.wrapS = map.wrapT = THREE.RepeatWrapping;
  map.colorSpace = color ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  map.anisotropy = TILE_RENDER_SETTINGS.anisotropy;
  return map;
}

/** Placeholder maps at once, the raster queued; null headless or for a printed style. */
export function buildTileMaps(style: TileStyle): TileMaps | null {
  if (style.print) return null; // printed styles use buildOnyxMaps
  const cached = cache.get(style);
  if (cached) return cached;
  if (typeof document === "undefined") return null;
  const rough = Math.round(style.roughness * 255);
  const canvases = [filled(...style.color), filled(128, 128, 255), filled(rough, rough, rough)];
  if (canvases.some(c => !c)) throw new Error("2D canvas unavailable for tile maps");
  const [color, normal, roughness] = canvases as HTMLCanvasElement[];
  const maps = { color: texture(color, true), normal: texture(normal, false), roughness: texture(roughness, false) };
  cache.set(style, maps);
  queue.push({ id: nextId++, style });
  inFlight++;
  pump();
  return maps;
}

function workers() {
  if (pool) return pool;
  pool = [];
  if (typeof Worker === "undefined") return pool;
  const size = Math.max(1, Math.min(2, (navigator.hardwareConcurrency ?? 2) - 1));
  try {
    for (let i = 0; i < size; i++) {
      const slot: { worker: Worker; busy: Pending | null } = { worker: new TileWorker(), busy: null };
      slot.worker.onmessage = (event: MessageEvent<{ pixels?: TilePixels }>) => {
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

function pump() {
  const slots = workers();
  if (!slots.length) fallback.push(...queue.splice(0));
  for (const slot of slots) {
    if (slot.busy || !queue.length) continue;
    slot.busy = queue.shift()!;
    slot.worker.postMessage({ id: slot.busy.id, style: slot.busy.style });
  }
  // One style per macrotask, so no single frame is held for the whole set.
  if (fallback.length && !fallbackScheduled) {
    fallbackScheduled = true;
    setTimeout(() => {
      fallbackScheduled = false;
      const next = fallback.shift()!;
      let pixels: TilePixels | null = null;
      const timed = textureTimer("tile");
      try { if (cache.has(next.style)) pixels = renderTilePixels(next.style); } catch { /* stays flat */ }
      timed();
      finish(next, pixels);
      pump();
    }, 0);
  }
}

function finish(done: Pending, pixels: TilePixels | null) {
  inFlight--;
  const maps = cache.get(done.style);
  // A reply for a style disposed since it was queued is dropped.
  if (pixels && maps) {
    const images = [pixels.color, pixels.normal, pixels.roughness];
    [maps.color, maps.normal, maps.roughness].forEach((map, i) => {
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = pixels.size;
      canvas.getContext("2d")!.putImageData(new ImageData(images[i], pixels.size, pixels.size), 0, 0);
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

/** Called after each finished style; returns its unsubscribe. */
export function onTileMapsReady(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

/** Resolves once every queued style has its raster. */
export function tileMapsSettled(): Promise<void> {
  if (inFlight === 0) return Promise.resolve();
  return new Promise(resolve => settleWaiters.push(resolve));
}

export function disposeTileMaps(): void {
  for (const maps of cache.values()) Object.values(maps).forEach(map => map.dispose());
  cache.clear();
}
