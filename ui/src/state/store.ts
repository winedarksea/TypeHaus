// The single zustand store. Holds the last-loaded model.json, view transform, selection,
// tool state, and the EngineClient wiring. Components read slices from here; all mutations
// go out through the client and come back as a fresh model on the next push (→ 21 editing
// loop: render → edit → patch → rebuild → WebSocket push → re-render).

import { create } from "zustand";
import type { EngineClient, EngineEvent, PatchOp, UnderlayCalibration } from "../engine/EngineClient";
import { RevisionConflict } from "../engine/EngineClient";
import { HttpEngineClient } from "../engine/HttpEngineClient";
import { PyodideEngineClient } from "../engine/PyodideEngineClient";
import { pickHouseDirectory } from "../engine/openHouse";
import type { Finding, Model } from "../model/types";

export type Tool = "select" | "wall" | "opening" | "room" | "dimension";
export type ViewMode = "2d" | "split" | "3d";
export type ThreeMode = "nordic" | "schematic";

export interface Selection {
  kind: "wall" | "opening" | "room" | null;
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
  openOfflineHouse: () => Promise<void>;
  setTool: (t: Tool) => void;
  setViewMode: (v: ViewMode) => void;
  setThreeMode: (m: ThreeMode) => void;
  setShowFraming: (v: boolean) => void;
  select: (kind: Selection["kind"], uid: string | null) => void;
  setHover: (uid: string | null) => void;
  setActiveStorey: (tag: string | null) => void;
  setView: (v: Partial<ViewTransform>) => void;
  dismissConflict: () => void;
  toast: (message: string, kind?: Toast["kind"]) => void;
  dismissToast: (id: number) => void;

  applyOps: (ops: PatchOp[]) => Promise<boolean>;
  calibrateUnderlay: (calibration: UnderlayCalibration) => Promise<boolean>;
  undo: () => Promise<void>;
  redo: () => Promise<void>;
}

let toastSeq = 1;

let unsubscribeEvents: (() => void) | null = null;

export const useStore = create<StoreState>((set, get) => ({
  client: new HttpEngineClient(),
  offline: false,
  offlineHouse: null,
  connected: false,
  loading: true,
  model: null,
  error: null,

  tool: "select",
  viewMode: "split",
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

  setTool: (tool) => set({ tool }),
  setViewMode: (viewMode) => set({ viewMode }),
  setThreeMode: (threeMode) => set({ threeMode }),
  setShowFraming: (showFraming) => set({ showFraming }),
  select: (kind, uid) => set({ selection: { kind, uid } }),
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
      await client.patchPlan(ops, model.revision);
      // The server broadcasts "patched"; the WS handler reloads. Reload here too so the
      // action resolves against fresh state even if the socket is down.
      await get().reload();
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
      await get().client.undo();
      await get().reload();
    } catch (err) {
      get().toast((err as Error).message, "error");
    }
  },

  redo: async () => {
    try {
      await get().client.redo();
      await get().reload();
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
      void get().reload();
      break;
    }
    case "patched":
    case "build":
    case "undo":
    case "redo":
      // Our own mutations already reload() in the action; a bare reload here keeps other
      // tabs / the two-screen workflow in sync without double-fetching aggressively.
      void get().reload();
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
