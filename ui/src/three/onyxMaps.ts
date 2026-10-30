// Onyx maps arrive in two steps: a face-mean placeholder now, the worker-rendered print once all
// faces are in (one upload per map). Texture identity never changes, as in woodMaps.ts.
import * as THREE from "three";
import type { TileStyle } from "./tileMaterial";
import { ONYX_PRINTS, hexRgb, renderOnyxFacePixels, type OnyxPixelJob, type OnyxPixels } from "./onyxPixels";
import OnyxWorker from "./onyxMaps.worker?worker";

export interface OnyxMaps { readonly color: THREE.Texture; readonly normal: THREE.Texture; readonly orm: THREE.Texture }
interface Entry { readonly maps: OnyxMaps; readonly cells: number[]; readonly faces: (OnyxPixels | null)[];
  remaining: number; cols: number }
interface Pending { readonly id: number; readonly key: string; readonly face: number; readonly job: OnyxPixelJob }
const cache = new Map<string, Entry>();
const queue: Pending[] = [];
const fallback: Pending[] = [];
const listeners = new Set<() => void>();
let settleWaiters: (() => void)[] = [];
let nextId = 0, inFlight = 0, fallbackScheduled = false;
let pool: { worker: Worker; busy: Pending | null }[] | null = null;
const FACE_PX = [512, 1024] as const; // colour px per face cell; 838 px/m

function texture(canvas: HTMLCanvasElement, color = false) {
  const map = new THREE.CanvasTexture(canvas);
  map.wrapS = map.wrapT = THREE.RepeatWrapping;
  map.colorSpace = color ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  map.anisotropy = 8;
  return map;
}
function filled(r: number, g: number, b: number) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 4;
  const context = canvas.getContext("2d");
  if (!context) return null;
  context.fillStyle = `rgb(${r},${g},${b})`; context.fillRect(0, 0, 4, 4);
  return canvas;
}

/** Placeholder at once, faces queued; null headless. Falls to quarter area off the worker path. */
export function buildOnyxMaps(style: TileStyle): OnyxMaps | null {
  if (typeof document === "undefined" || !style.print) return null;
  const key = JSON.stringify([style.print, style.sizeM, style.jointM, style.repeat, style.grout]);
  const hit = cache.get(key);
  if (hit) return hit.maps;
  const print = ONYX_PRINTS[style.print];
  const [r, g, b] = hexRgb(print.faceMean);
  const canvases = [filled(r, g, b), filled(128, 128, 255), filled(255, 18, 0)];
  if (canvases.some(c => !c)) return null;
  const [cc, nc, oc] = canvases as HTMLCanvasElement[];
  const maps = { color: texture(cc, true), normal: texture(nc), orm: texture(oc) };
  const [cols, rows] = style.repeat ?? [2, 2];
  const cells = Array.from({ length: cols * rows }, (_, c) => c % print.faces);
  const distinct = [...new Set(cells)];
  cache.set(key, { maps, cells, faces: [], remaining: distinct.length, cols });
  const job = (face: number): OnyxPixelJob => ({
    print: style.print!, face, grout: style.grout, jointM: style.jointM,
    pitchM: [style.sizeM[0] + style.jointM, style.sizeM[1] + style.jointM],
    width: FACE_PX[0], height: FACE_PX[1] });
  for (const face of distinct) { queue.push({ id: nextId++, key, face, job: job(face) }); inFlight++; }
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
      const slot: { worker: Worker; busy: Pending | null } = { worker: new OnyxWorker(), busy: null };
      slot.worker.onmessage = (event: MessageEvent<{ pixels?: OnyxPixels }>) => {
        const done = slot.busy!;
        slot.busy = null;
        if (event.data.pixels) finish(done, event.data.pixels); else fallback.push(done);
        pump();
      };
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
    slot.worker.postMessage({ id: slot.busy.id, job: slot.busy.job });
  }
  // Quarter area, one face per macrotask, so no frame is held for the whole set.
  if (fallback.length && !fallbackScheduled) {
    fallbackScheduled = true;
    setTimeout(() => {
      fallbackScheduled = false;
      const next = fallback.shift()!;
      let pixels: OnyxPixels | null = null;
      try {
        if (cache.has(next.key)) pixels = renderOnyxFacePixels(
          { ...next.job, width: next.job.width >> 1, height: next.job.height >> 1 });
      } catch { /* stays flat */ }
      finish(next, pixels);
      pump();
    }, 0);
  }
}

function blit(entry: Entry, pick: (p: OnyxPixels) => [Uint8ClampedArray, number, number], map: THREE.Texture) {
  const largest = entry.faces.filter(f => f).reduce((a, b) => (pick(b!)[1] > pick(a!)[1] ? b : a))!;
  const [, w, h] = pick(largest);
  const rows = Math.ceil(entry.cells.length / entry.cols);
  const canvas = document.createElement("canvas");
  canvas.width = w * entry.cols; canvas.height = h * rows;
  const context = canvas.getContext("2d")!;
  entry.cells.forEach((face, cell) => {
    const [data, fw, fh] = pick(entry.faces[face]!);
    const image = new ImageData(data as Uint8ClampedArray<ArrayBuffer>, fw, fh);
    const x = (cell % entry.cols) * w, y = Math.floor(cell / entry.cols) * h;
    if (fw === w && fh === h) { context.putImageData(image, x, y); return; }
    // A quarter-area fallback face beside worker faces: scale it into its cell.
    const scratch = document.createElement("canvas");
    scratch.width = fw; scratch.height = fh;
    scratch.getContext("2d")!.putImageData(image, 0, 0);
    context.drawImage(scratch, x, y, w, h);
  });
  map.dispose(); // the 4x4 placeholder's GPU storage is immutable
  map.image = canvas;
  map.needsUpdate = true;
}

function finish(done: Pending, pixels: OnyxPixels | null) {
  inFlight--;
  const entry = cache.get(done.key);
  // A face already in (a reply queued before a dispose and rebuild) must not count twice.
  if (entry && pixels && !entry.faces[done.face]) {
    entry.faces[done.face] = pixels;
    if (--entry.remaining === 0) {
      blit(entry, p => [p.color, p.width, p.height], entry.maps.color);
      blit(entry, p => [p.normal, p.mapWidth, p.mapHeight], entry.maps.normal);
      blit(entry, p => [p.orm, p.mapWidth, p.mapHeight], entry.maps.orm);
      for (const listener of listeners) listener();
    }
  }
  if (inFlight === 0) {
    const waiters = settleWaiters;
    settleWaiters = [];
    for (const resolve of waiters) resolve();
  }
}

/** Called once a print's maps are all in; returns its unsubscribe. */
export function onOnyxMapsReady(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

/** Resolves once every queued face has arrived. */
export function onyxMapsSettled(): Promise<void> {
  if (inFlight === 0) return Promise.resolve();
  return new Promise(resolve => settleWaiters.push(resolve));
}

export function disposeOnyxTextures(): void {
  for (const { maps } of cache.values()) Object.values(maps).forEach(m => m.dispose());
  cache.clear();
}
