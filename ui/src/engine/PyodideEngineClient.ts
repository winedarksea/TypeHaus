// The offline EngineClient (→ 40 WP4.2, gate outcome b). Runs the engine in a pyodide Web
// Worker; no server, no network after first load. Read/compute is fully supported — getModel,
// getChecks, build, getArtifact("glb"). Mutation (patchPlan/runMacro/undo/redo) and IFC export
// are libcst/ifcopenshell-gated and surface as a clear "requires local install" degradation
// (#15: the local FastAPI mode stays the primary editing path). No editor code changes: this is
// the second implementation of the same interface HttpEngineClient satisfies.

import type { Finding, Model } from "../model/types";
import PyodideWorker from "./pyodide/worker?worker";
import {
  type BuildResult,
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

  async build(): Promise<BuildResult> {
    await this.initialized;
    // A no-op re-resolve happened on load; report the current revision.
    const model = await this.getModel();
    return { ok: model.ok !== false, revision: model.revision };
  }

  async getArtifact(kind: EngineArtifact): Promise<Blob> {
    await this.initialized;
    if (kind === "ifc") throw new OfflineUnsupported("IFC export");
    const bytes = await this.call<Uint8Array>("glb");
    return new Blob([bytes as unknown as BlobPart], { type: "model/gltf-binary" });
  }

  calibrateUnderlay(_calibration: UnderlayCalibration): Promise<void> {
    return Promise.reject(new OfflineUnsupported("Saving underlay calibration"));
  }

  // --- Mutation surface: libcst-gated, unavailable offline (→ 40 gate outcome b) -----------
  patchPlan(_ops: PatchOp[], _revision: string): Promise<PatchResult> {
    return Promise.reject(new OfflineUnsupported("Editing the plan"));
  }
  runMacro(_request: MacroRequest, _revision: string): Promise<MacroResult> {
    return Promise.reject(new OfflineUnsupported("Editing the plan"));
  }
  previewMacro(_request: MacroRequest): Promise<PreviewGeometry> {
    return Promise.reject(new OfflineUnsupported("Drag preview"));
  }
  undo(): Promise<HistoryResult> {
    return Promise.reject(new OfflineUnsupported("Undo"));
  }
  redo(): Promise<HistoryResult> {
    return Promise.reject(new OfflineUnsupported("Redo"));
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
