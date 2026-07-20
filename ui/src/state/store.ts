// The single zustand store. Holds the last-loaded model.json, view transform, selection,
// tool state, and the EngineClient wiring. Components read slices from here; all mutations
// go out through the client and come back as a fresh model on the next push (→ 21 editing
// loop: render → edit → patch → rebuild → WebSocket push → re-render).

import { create } from "zustand";
import type {
  EngineClient,
  EngineEvent,
  MacroRequest,
  MacroResult,
  PatchOp,
  PreviewGeometry,
  UnderlayCalibration,
} from "../engine/EngineClient";
import { RevisionConflict } from "../engine/EngineClient";
import { HttpEngineClient } from "../engine/HttpEngineClient";
import { PyodideEngineClient } from "../engine/PyodideEngineClient";
import { pickHouseDirectory } from "../engine/openHouse";
import type { Finding, Model } from "../model/types";

export type Tool = "select" | "wall" | "opening" | "room" | "dimension";
export type ViewMode = "2d" | "split" | "3d";
export type ThreeMode = "nordic" | "schematic";

export interface Selection {
  kind: "wall" | "opening" | "room" | "stair" | null;
  uid: string | null;
}

export interface ViewTransform {
  scale: number; // pixels per meter
  tx: number; // pixel pan
  ty: number;
}

export interface Conflict {
  message: string;
  changed?: string[];
}

export interface Toast {
  id: number;
  message: string;
  kind: "info" | "error";
}

interface StoreState {
  client: EngineClient;
  offline: boolean; // true once running against the in-browser pyodide engine
  offlineHouse: string | null;
  connected: boolean;
  loading: boolean;
  model: Model | null;
  error: string | null;

  tool: Tool;
  viewMode: ViewMode;
  threeMode: ThreeMode;
  selection: Selection;
  hoverUid: string | null;
  activeStorey: string | null;
  view: ViewTransform;
  showFraming: boolean; // framed floorplan vs. schematic wall fills
  conflict: Conflict | null;
  toasts: Toast[];

  // actions
  init: () => Promise<void>;
  reload: () => Promise<void>;
  // Revision-deduped reload: skips the fetch when the model already matches `revision`,
  // and coalesces the mutation-action reload with the WS-echo reload into one GET /model.
  reloadIfStale: (revision?: string) => Promise<void>;
  openOfflineHouse: () => Promise<void>;
  setTool: (t: Tool) => void;
  setViewMode: (v: ViewMode) => void;
  setThreeMode: (m: ThreeMode) => void;
  setShowFraming: (v: boolean) => void;
  select: (kind: Selection["kind"], uid: string | null) => void;
  selectByTag: (kind: Selection["kind"], tag: string) => void;
  setHover: (uid: string | null) => void;
  setActiveStorey: (tag: string | null) => void;
  setView: (v: Partial<ViewTransform>) => void;
  dismissConflict: () => void;
  toast: (message: string, kind?: Toast["kind"]) => void;
  dismissToast: (id: number) => void;

  applyOps: (ops: PatchOp[]) => Promise<boolean>;
  runMacro: (request: MacroRequest) => Promise<MacroResult | null>;
  // Self-throttled live drag preview (→ Phase 4): coalesces to the latest request if a
  // preview is already in flight, so a fast pointermove stream never queues up requests.
  // Never journaled/mutating; swallows errors (offline, ops that can't preview) as `null`.
  previewMacro: (request: MacroRequest) => Promise<PreviewGeometry | null>;
  deleteSelection: () => Promise<void>;
  calibrateUnderlay: (calibration: UnderlayCalibration) => Promise<boolean>;
  undo: () => Promise<void>;
  redo: () => Promise<void>;
}

let toastSeq = 1;

let unsubscribeEvents: (() => void) | null = null;

// One in-flight GET /model at a time, tagged with the revision it targets. A second caller
// asking for the same (or an already-loaded) revision rides the existing promise instead of
// firing a duplicate fetch — this is what collapses the old action+WS double reload (1a).
let inflightReload: { revision: string | null; promise: Promise<void> } | null = null;

// One in-flight POST /macro/preview at a time; a request arriving mid-flight replaces
// `pendingPreviewRequest` instead of firing another fetch, and the in-flight call's resolver
// re-fires itself once against the latest request when it lands — the drag only ever waits
// for one round trip, no matter how fast pointermove fires.
let previewInFlight = false;
let pendingPreviewRequest: MacroRequest | null = null;

export const useStore = create<StoreState>((set, get) => ({
  client: new HttpEngineClient(),
  offline: false,
  offlineHouse: null,
  connected: false,
  loading: true,
  model: null,
  error: null,

  tool: "select",
  viewMode: "2d",
  threeMode: "nordic",
  selection: { kind: null, uid: null },
  hoverUid: null,
  activeStorey: null,
  view: { scale: 120, tx: 80, ty: 80 },
  showFraming: true,
  conflict: null,
  toasts: [],

  init: async () => {
    const { client } = get();
    unsubscribeEvents?.();
    unsubscribeEvents = client.events(
      (e) => handleEvent(get, set, e),
      (up) => set({ connected: up }),
    );
    await get().reload();
  },

  // Switch to the offline in-browser engine (→ 40): pick a house folder via the File System
  // Access API and run the pyodide EngineClient. No server required.
  openOfflineHouse: async () => {
    try {
      const opened = await pickHouseDirectory();
      if (!opened) return; // user cancelled
      const client = new PyodideEngineClient(opened.files);
      set({
        client,
        offline: true,
        offlineHouse: opened.name,
        connected: false,
        loading: true,
        error: null,
        model: null,
      });
      await get().init();
    } catch (err) {
      get().toast((err as Error).message, "error");
    }
  },

  reload: async () => {
    const { client } = get();
    set({ loading: true, error: null });
    try {
      const model = await client.getModel();
      const prev = get();
      set({
        model,
        loading: false,
        conflict: null,
        activeStorey: prev.activeStorey ?? model.storeys[0]?.tag ?? null,
      });
    } catch (err) {
      set({ loading: false, error: (err as Error).message });
    }
  },

  reloadIfStale: (revision) => {
    // Already showing this exact revision and nothing in flight → nothing to do.
    const current = get().model?.revision;
    if (revision !== undefined && current === revision && !inflightReload) {
      return Promise.resolve();
    }
    // A fetch targeting this revision (or an untargeted one) is already running → join it.
    if (
      inflightReload &&
      (revision === undefined || inflightReload.revision === revision ||
        inflightReload.revision === null)
    ) {
      return inflightReload.promise;
    }
    const promise = get()
      .reload()
      .finally(() => {
        if (inflightReload?.promise === promise) inflightReload = null;
      });
    inflightReload = { revision: revision ?? null, promise };
    return promise;
  },

  setTool: (tool) => set({ tool }),
  setViewMode: (viewMode) => set({ viewMode }),
  setThreeMode: (threeMode) => set({ threeMode }),
  setShowFraming: (showFraming) => set({ showFraming }),
  select: (kind, uid) => set({ selection: { kind, uid } }),
  // Select an element by its authored tag (uids are minted server-side, so a freshly drawn
  // wall / placed opening is only addressable by tag until the next reload lands).
  selectByTag: (kind, tag) => {
    const model = get().model;
    if (!model) return;
    const pool =
      kind === "wall" ? model.walls : kind === "opening" ? model.openings
        : kind === "room" ? model.rooms : model.stairs ?? [];
    const hit = pool.find((e) => e.tag === tag);
    if (hit) set({ selection: { kind, uid: hit.uid } });
  },
  setHover: (hoverUid) => set({ hoverUid }),
  setActiveStorey: (activeStorey) => set({ activeStorey }),
  setView: (v) => set((s) => ({ view: { ...s.view, ...v } })),
  dismissConflict: () => set({ conflict: null }),
  toast: (message, kind = "info") =>
    set((s) => ({ toasts: [...s.toasts, { id: toastSeq++, message, kind }] })),
  dismissToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

  applyOps: async (ops) => {
    const { client, model } = get();
    if (!model) return false;
    try {
      const res = await client.patchPlan(ops, model.revision);
      // The server broadcasts "patched"; the WS handler also reloads. reloadIfStale keyed on
      // the post-patch revision coalesces the two into a single GET /model (1a).
      await get().reloadIfStale(res.revision);
      return true;
    } catch (err) {
      if (err instanceof RevisionConflict) {
        set({ conflict: { message: err.message } });
      } else {
        get().toast((err as Error).message, "error");
      }
      return false;
    }
  },

  // Geometry / library macros (server owns the math, → 21b). Same journaled patch path as
  // applyOps, but returns the MacroResult so callers can select minted elements and surface
  // any warnings (pinned nodes held, openings re-hosted on a split).
  runMacro: async (request) => {
    const { client, model } = get();
    if (!model) return null;
    try {
      const result = await client.runMacro(request, model.revision);
      await get().reloadIfStale(result.revision);
      for (const warning of result.warnings ?? []) get().toast(warning);
      return result;
    } catch (err) {
      if (err instanceof RevisionConflict) {
        set({ conflict: { message: err.message } });
      } else {
        get().toast((err as Error).message, "error");
      }
      return null;
    }
  },

  previewMacro: async (request) => {
    if (previewInFlight) {
      pendingPreviewRequest = request; // superseded: only the latest pointer position matters
      return null;
    }
    previewInFlight = true;
    try {
      return await get().client.previewMacro(request);
    } catch {
      return null; // offline, or ops that can't apply in memory — caller keeps last geometry
    } finally {
      previewInFlight = false;
      const next = pendingPreviewRequest;
      pendingPreviewRequest = null;
      if (next) void get().previewMacro(next);
    }
  },

  // Delete the current selection (Del key or the toolbar trash button, → 21b). Resolves
  // uid → {type, tag} from the live model since PatchOp addresses elements by tag.
  deleteSelection: async () => {
    const { model, selection, applyOps, select } = get();
    if (!model || !selection.uid) return;
    let type: string | null = null;
    let tag: string | null = null;
    if (selection.kind === "wall") {
      const w = model.walls.find((x) => x.uid === selection.uid);
      type = "Wall"; tag = w?.tag ?? null;
    } else if (selection.kind === "opening") {
      const o = model.openings.find((x) => x.uid === selection.uid);
      type = o?.is_door ? "Door" : "Window"; tag = o?.tag ?? null;
    } else if (selection.kind === "room") {
      const r = model.rooms.find((x) => x.uid === selection.uid);
      type = "Room"; tag = r?.tag ?? null;
    } else if (selection.kind === "stair") {
      const stair = (model.stairs ?? []).find((x) => x.uid === selection.uid);
      type = "Stair"; tag = stair?.tag ?? null;
    }
    if (!type || !tag) return;
    const ok = await applyOps([{ op: "delete", type, tag }]);
    if (ok) { get().toast(`${tag} deleted`); select(null, null); }
  },

  calibrateUnderlay: async (calibration) => {
    try {
      await get().client.calibrateUnderlay(calibration);
      await get().reload();
      get().toast("Underlay calibration saved");
      return true;
    } catch (err) {
      get().toast((err as Error).message, "error");
      return false;
    }
  },

  undo: async () => {
    try {
      const res = await get().client.undo();
      await get().reloadIfStale(res.revision);
    } catch (err) {
      get().toast((err as Error).message, "error");
    }
  },

  redo: async () => {
    try {
      const res = await get().client.redo();
      await get().reloadIfStale(res.revision);
    } catch (err) {
      get().toast((err as Error).message, "error");
    }
  },
}));

function handleEvent(
  get: () => StoreState,
  set: (partial: Partial<StoreState>) => void,
  e: EngineEvent,
): void {
  switch (e.type) {
    case "file-changed": {
      // External VSCode/Claude edit. If the user has no pending local edit, hot-reload
      // silently; the conflict banner is reserved for the 409 precondition path (#30).
      void get().reloadIfStale(e.revision);
      break;
    }
    case "patched":
    case "build":
    case "undo":
    case "redo":
      // Our own mutation already kicked a reloadIfStale keyed on this same revision, so this
      // echo joins that in-flight fetch (no double GET); for other tabs it fetches fresh (1a).
      void get().reloadIfStale(e.revision);
      break;
  }
  set({});
}

// Selector helpers ----------------------------------------------------------

export function findingsFor(model: Model | null, uid: string | null): Finding[] {
  if (!model || !uid) return [];
  return model.findings.filter(
    (f) => f.element === uid || (f.elements ?? []).includes(uid),
  );
}
