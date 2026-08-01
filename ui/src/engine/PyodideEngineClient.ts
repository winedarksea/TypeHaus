// The offline EngineClient (→ 40 WP4.2; editing added in U9). Runs the engine in a pyodide Web
// Worker; no server, no network after first load. Read/compute is fully supported — getModel,
// getChecks, build, getArtifact("glb"). Editing (patchPlan/undo/redo) is now served in-browser by
// the pure-Python, libcst-free writeback backend, so the PWA is a real editor offline. Macros
// (generative params/ logic) stay local-serve features. IFC export now live-loads the packaged
// extension tarball client-side (V6); until an ifcopenshell-wasm wheel is bundled it still
// surfaces a clear "requires local install" degradation. This is the second implementation of the same interface
// HttpEngineClient satisfies.

import type { Finding, Model } from "../model/types";
import PyodideWorker from "./pyodide/worker?worker";
import {
  type BuildResult,
  type DetailIndexEntry,
  type EngineBom,
  type DetailPayload,
  EngineError,
  type EngineArtifact,
  type EngineClient,
  type EngineEvent,
  type HistoryResult,
  type MacroRequest,
  type MacroResult,
  type PatchOp,
  type PatchResult,
  type PreviewGeometry,
  type UnderlayCalibration,
} from "./EngineClient";

// A house loaded from disk via the File System Access API: relative path -> text content.
export type HouseFiles = Record<string, string>;

const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.2/full/";

// The optional IFC extension (built by scripts/build-pwa-assets.mjs). The tarball ships the
// `typehaus/emit/ifc` sources the core bundle excludes; it is fetched + unpacked lazily on the
// first IFC export, not at boot. `VITE_IFC_WASM_URL`, when set to an ifcopenshell-wasm wheel,
// completes the client-side export path; without it the user gets a precise "run haus serve
// locally" degradation (see worker.ts ensureIfc). Same-origin, so it works from the served PWA.
const IFC_EXT_TAR = "typehaus-ifc-ext.tar";
const IFC_WASM_URL: string | undefined = import.meta.env.VITE_IFC_WASM_URL || undefined;

// Thrown for calls that the offline engine cannot serve without a local install.
export class OfflineUnsupported extends EngineError {
  constructor(what: string) {
    super(`${what} requires the local engine — run \`haus serve\` (offline PWA is view-only)`, 501);
    this.name = "OfflineUnsupported";
  }
}

interface Pending {
  resolve: (v: unknown) => void;
  reject: (e: Error) => void;
}

export class PyodideEngineClient implements EngineClient {
  private readonly worker: Worker;
  private readonly pending = new Map<number, Pending>();
  private seq = 1;
  private initialized: Promise<void>;
  private statusListeners = new Set<(up: boolean) => void>();

  constructor(private files: HouseFiles, private readonly root = "/house") {
    this.worker = new PyodideWorker();
    this.worker.onmessage = (e: MessageEvent) => this.onMessage(e.data);
    this.worker.onerror = (e) => this.failAll(new Error(e.message || "worker error"));
    this.initialized = this.boot();
  }

  private onMessage(data: { id: number; ok: boolean; result?: unknown; error?: string }): void {
    const p = this.pending.get(data.id);
    if (!p) return;
    this.pending.delete(data.id);
    if (data.ok) p.resolve(data.result);
    else p.reject(new EngineError(data.error ?? "engine error", 500));
  }

  private failAll(err: Error): void {
    for (const p of this.pending.values()) p.reject(err);
    this.pending.clear();
    for (const l of this.statusListeners) l(false);
  }

  private call<T>(type: string, extra: Record<string, unknown> = {}): Promise<T> {
    const id = this.seq++;
    return new Promise<T>((resolve, reject) => {
      this.pending.set(id, { resolve: resolve as (v: unknown) => void, reject });
      this.worker.postMessage({ id, type, ...extra });
    });
  }

  private async boot(): Promise<void> {
    await this.call("init", {
      pyodideIndexUrl: PYODIDE_INDEX_URL,
      engineTarUrl: new URL("typehaus-engine.tar", document.baseURI).href,
      ifcExtTarUrl: new URL(IFC_EXT_TAR, document.baseURI).href,
      ifcWasmUrl: IFC_WASM_URL,
    });
    await this.call("loadHouse", { root: this.root, files: this.files });
    for (const l of this.statusListeners) l(true);
  }

  // Replace the loaded house (a new directory opened via FS Access) and re-resolve.
  async openHouse(files: HouseFiles): Promise<void> {
    this.files = files;
    await this.initialized;
    await this.call("loadHouse", { root: this.root, files });
  }

  async getModel(): Promise<Model> {
    await this.initialized;
    return this.call<Model>("model");
  }

  async getChecks(): Promise<Finding[]> {
    await this.initialized;
    return this.call<Finding[]>("checks");
  }

  async getDetailIndex(): Promise<DetailIndexEntry[]> {
    await this.initialized;
    return this.call<DetailIndexEntry[]>("detailIndex");
  }

  async getBom(): Promise<EngineBom> {
    await this.initialized;
    return this.call<EngineBom>("bom");
  }

  async getDetail(key: string): Promise<DetailPayload> {
    await this.initialized;
    const payload = await this.call<DetailPayload | null>("detail", { key });
    if (payload === null) throw new EngineError(`no detail ${key}`, 404);
    return payload;
  }

  async appendDetailNote(): Promise<string> {
    // The offline house is a read-only snapshot — there is no notes/*.md to write back to.
    throw new OfflineUnsupported("Adding construction notes");
  }

  async build(): Promise<BuildResult> {
    await this.initialized;
    // A no-op re-resolve happened on load; report the current revision.
    const model = await this.getModel();
    return { ok: model.ok !== false, revision: model.revision };
  }

  async getArtifact(kind: EngineArtifact): Promise<Blob> {
    await this.initialized;
    if (kind === "ifc") {
      // Live-load the packaged IFC extension and emit client-side (V6). The worker fetches +
      // unpacks typehaus-ifc-ext.tar and, when a wasm wheel is configured, instantiates
      // ifcopenshell; otherwise it rejects with the documented "requires ifcopenshell-wasm /
      // run haus serve" message, which we normalise to OfflineUnsupported for the UI banner.
      try {
        const bytes = await this.call<Uint8Array>("ifc");
        return new Blob([bytes as unknown as BlobPart], { type: "application/x-step" });
      } catch (err) {
        // Surface the precise worker reason (no wasm wheel bundled, tarball fetch failure, …)
        // while keeping the OfflineUnsupported type the UI degradation banner keys off.
        const reason = err instanceof Error ? err.message : String(err);
        const wrapped = new OfflineUnsupported("IFC export");
        wrapped.message = reason;
        throw wrapped;
      }
    }
    const bytes = await this.call<Uint8Array>("glb");
    return new Blob([bytes as unknown as BlobPart], { type: "model/gltf-binary" });
  }

  calibrateUnderlay(_calibration: UnderlayCalibration): Promise<void> {
    return Promise.reject(new OfflineUnsupported("Saving underlay calibration"));
  }

  // --- Mutation surface: the pure-Python (libcst-free) writeback backend runs in-worker (U9).
  async patchPlan(ops: PatchOp[], revision: string): Promise<PatchResult> {
    await this.initialized;
    return this.call<PatchResult>("patch", { ops, revision });
  }
  // Macros (parametric multi-element edits, e.g. drag-to-add) remain a local-serve feature:
  // they run generative params/ logic the offline compute path doesn't host.
  runMacro(_request: MacroRequest, _revision: string): Promise<MacroResult> {
    return Promise.reject(new OfflineUnsupported("This tool"));
  }
  previewMacro(_request: MacroRequest, _rehearse?: boolean): Promise<PreviewGeometry> {
    return Promise.reject(new OfflineUnsupported("Drag preview"));
  }
  async undo(): Promise<HistoryResult> {
    await this.initialized;
    return this.call<HistoryResult>("undo");
  }
  async redo(): Promise<HistoryResult> {
    await this.initialized;
    return this.call<HistoryResult>("redo");
  }

  // No server push offline; report readiness once the worker has booted the house.
  events(_onEvent: (e: EngineEvent) => void, onStatus?: (up: boolean) => void): () => void {
    if (onStatus) {
      this.statusListeners.add(onStatus);
      this.initialized.then(() => onStatus(true)).catch(() => onStatus(false));
    }
    return () => {
      if (onStatus) this.statusListeners.delete(onStatus);
    };
  }

  dispose(): void {
    this.worker.terminate();
  }
}
