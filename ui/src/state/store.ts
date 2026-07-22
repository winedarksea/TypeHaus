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
import { EngineError, RevisionConflict } from "../engine/EngineClient";
import { HttpEngineClient } from "../engine/HttpEngineClient";
import { PyodideEngineClient } from "../engine/PyodideEngineClient";
import { pickHouseDirectory } from "../engine/openHouse";
import type { Finding, Model } from "../model/types";

export type Tool = "select" | "wall" | "opening" | "placeable" | "room" | "stair" | "dimension";
// Task-rail groups (Phase 2): high-level buckets whose flyout palettes expand to the
// concrete Tools above. `null` = no flyout open.
export type ToolGroup = "select" | "build" | "openings" | "components" | "measure";
export type ViewMode = "2d" | "split" | "3d";
export type ThreeMode = "nordic" | "schematic";
// Phase 6 — three previously-conflated concepts pulled apart:
export type Workspace = "design" | "analyze" | "document"; // tool/drawer emphasis
export type Representation = "conceptual" | "schematic" | "detailed" | "fabrication"; // detail level
// Building-science lenses (Phase 9): a lens semantically re-frames the model to answer one
// question. Shipping air · water · thermal first.
export type Lens = "none" | "air" | "water" | "thermal";

// 3D trade visibility (→ 21 §3D panel WP7): one THREE.Group per trade so toggling never
// rebuilds the scene, just flips group.visible. "walls" is layer polygons (sheathing,
// insulation, cladding); "framing" is wall members (studs/plates/headers); "floors" is
// floor decks (hideable for stair continuity); "concrete" is resolved solids (slabs,
// footings, pads); "roof" is the roof surface + its members (incl. ridge beam); "earth"
// is the translucent site context sheet.
export type Trade = "walls" | "openings" | "framing" | "floors" | "concrete" | "roof" | "stairs" | "furniture" | "plumbing" | "electrical" | "mechanical" | "earth";
export const ALL_TRADES: Trade[] = [
  "walls", "openings", "framing", "floors", "concrete", "roof", "stairs", "furniture", "plumbing", "electrical", "mechanical", "earth",
];

export interface Selection {
  kind: "wall" | "opening" | "room" | "stair" | "canvas_object" | null;
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
  toolGroup: ToolGroup | null; // which task-rail flyout is open
  subOperation: boolean; // true mid-draw (e.g. wall chain in progress) — drives Esc hierarchy
  drawAssembly: string | null; // ContextBar-selected wall assembly for new walls
  chainDraw: boolean; // keep the wall tool armed after each segment
  projectDrawerOpen: boolean; // left project drawer (dashboards, hierarchy — Phase 6)
  commandPaletteOpen: boolean; // ⌘K fuzzy command surface (Phase 4)
  recentCommands: string[]; // command ids, most-recent first (Phase 4)
  issuesDrawerOpen: boolean; // bottom Issues drawer (Phase 5)
  activeWorkspace: Workspace; // DESIGN / ANALYZE / DOCUMENT (Phase 6)
  representation: Representation; // conceptual → fabrication detail level (Phase 6)
  viewsPanelOpen: boolean; // Views control panel (Phase 6)
  workbench: "assembly" | "stair" | null; // focus-mode workbench for complex edits (Phase 7)
  activeLens: Lens; // building-science lens (Phase 9)
  preview3DOpen: boolean; // floating synchronized 3D preview over the 2D plan (Phase 10)
  viewMode: ViewMode;
  threeMode: ThreeMode;
  selection: Selection;
  hoverUid: string | null;
  activeStorey: string | null;
  view: ViewTransform;
  showFraming: boolean; // framed floorplan vs. schematic wall fills
  visibleTrades: Record<Trade, boolean>;
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
  setToolGroup: (g: ToolGroup | null) => void;
  setSubOperation: (v: boolean) => void;
  setDrawAssembly: (tag: string | null) => void;
  setChainDraw: (v: boolean) => void;
  setProjectDrawerOpen: (v: boolean) => void;
  setCommandPaletteOpen: (v: boolean) => void;
  pushRecentCommand: (id: string) => void;
  setIssuesDrawerOpen: (v: boolean) => void;
  setActiveWorkspace: (w: Workspace) => void;
  setRepresentation: (r: Representation) => void;
  setViewsPanelOpen: (v: boolean) => void;
  setWorkbench: (w: "assembly" | "stair" | null) => void;
  setActiveLens: (l: Lens) => void;
  setPreview3DOpen: (v: boolean) => void;
  setViewMode: (v: ViewMode) => void;
  setThreeMode: (m: ThreeMode) => void;
  setShowFraming: (v: boolean) => void;
  setTradeVisible: (trade: Trade, visible: boolean) => void;
  select: (kind: Selection["kind"], uid: string | null) => void;
  selectByTag: (kind: Selection["kind"], tag: string) => void;
  setHover: (uid: string | null) => void;
  setActiveStorey: (tag: string | null) => void;
  setView: (v: Partial<ViewTransform>) => void;
  // Navigate to an element (Phase 5 issue jump): switch to its storey, select + highlight it,
  // and pan the 2D view so its centroid sits at the viewport center.
  zoomToUid: (uid: string) => void;
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
  duplicateSelection: () => Promise<void>;
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
  toolGroup: null,
  subOperation: false,
  drawAssembly: null,
  chainDraw: true,
  projectDrawerOpen: false,
  commandPaletteOpen: false,
  recentCommands: [],
  issuesDrawerOpen: false,
  activeWorkspace: "design",
  representation: "detailed",
  viewsPanelOpen: false,
  workbench: null,
  activeLens: "none",
  preview3DOpen: false,
  viewMode: "2d",
  threeMode: "nordic",
  selection: { kind: null, uid: null },
  hoverUid: null,
  activeStorey: null,
  view: { scale: 120, tx: 80, ty: 80 },
  showFraming: true,
  visibleTrades: {
    walls: true, openings: true, framing: true, floors: true, concrete: true, roof: true,
    stairs: true, furniture: true, plumbing: true, electrical: true, mechanical: true, earth: true,
  },
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

  setTool: (tool) => set({ tool, toolGroup: null, subOperation: false }),
  setToolGroup: (toolGroup) => set({ toolGroup }),
  setSubOperation: (subOperation) => set({ subOperation }),
  setDrawAssembly: (drawAssembly) => set({ drawAssembly }),
  setChainDraw: (chainDraw) => set({ chainDraw }),
  // Left side hosts one large panel at a time (reviewer rule): opening one closes the other.
  setProjectDrawerOpen: (projectDrawerOpen) =>
    set(projectDrawerOpen ? { projectDrawerOpen, viewsPanelOpen: false } : { projectDrawerOpen }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
  pushRecentCommand: (id) =>
    set((s) => ({ recentCommands: [id, ...s.recentCommands.filter((c) => c !== id)].slice(0, 6) })),
  setIssuesDrawerOpen: (issuesDrawerOpen) => set({ issuesDrawerOpen }),
  setActiveWorkspace: (activeWorkspace) => set({ activeWorkspace }),
  // Representation generalizes the old showFraming boolean: detailed/fabrication show framing,
  // conceptual/schematic show wall fills only.
  setRepresentation: (representation) =>
    set({ representation, showFraming: representation === "detailed" || representation === "fabrication" }),
  setViewsPanelOpen: (viewsPanelOpen) =>
    set(viewsPanelOpen ? { viewsPanelOpen, projectDrawerOpen: false } : { viewsPanelOpen }),
  setWorkbench: (workbench) => set({ workbench }),
  setActiveLens: (activeLens) => set({ activeLens }),
  setPreview3DOpen: (preview3DOpen) => set({ preview3DOpen }),
  setViewMode: (viewMode) => set({ viewMode }),
  setThreeMode: (threeMode) => set({ threeMode }),
  setShowFraming: (showFraming) => set({ showFraming }),
  setTradeVisible: (trade, visible) =>
    set((s) => ({ visibleTrades: { ...s.visibleTrades, [trade]: visible } })),
  select: (kind, uid) => set({ selection: { kind, uid } }),
  // Select an element by its authored tag (uids are minted server-side, so a freshly drawn
  // wall / placed opening is only addressable by tag until the next reload lands).
  selectByTag: (kind, tag) => {
    const model = get().model;
    if (!model) return;
    const pool =
      kind === "wall" ? model.walls : kind === "opening" ? model.openings
        : kind === "room" ? model.rooms : kind === "canvas_object" ? model.canvas_objects ?? []
          : model.stairs ?? [];
    const hit = pool.find((e) => e.tag === tag);
    if (hit) set({ selection: { kind, uid: hit.uid } });
  },
  setHover: (hoverUid) => set({ hoverUid }),
  setActiveStorey: (activeStorey) => set({ activeStorey }),
  setView: (v) => set((s) => ({ view: { ...s.view, ...v } })),
  zoomToUid: (uid) => {
    const { model, view, viewMode } = get();
    if (!model) return;
    // Resolve the element, its kind, storey, and a plan-space centroid.
    let kind: Selection["kind"] = null;
    let storey: string | null = null;
    let centroid: [number, number] | null = null;
    const wall = model.walls.find((w) => w.uid === uid);
    if (wall) {
      kind = "wall"; storey = wall.storey;
      centroid = [(wall.axis[0][0] + wall.axis[1][0]) / 2, (wall.axis[0][1] + wall.axis[1][1]) / 2];
    }
    const opening = !wall ? model.openings.find((o) => o.uid === uid) : undefined;
    if (opening) {
      const host = model.walls.find((w) => w.tag === opening.host);
      kind = "opening"; storey = host?.storey ?? null;
      if (host) centroid = [(host.axis[0][0] + host.axis[1][0]) / 2, (host.axis[0][1] + host.axis[1][1]) / 2];
    }
    const room = !wall && !opening ? model.rooms.find((r) => r.uid === uid) : undefined;
    if (room) {
      kind = "room"; storey = room.storey;
      const pts = room.clear_face;
      if (pts.length) centroid = [
        pts.reduce((a, p) => a + p[0], 0) / pts.length,
        pts.reduce((a, p) => a + p[1], 0) / pts.length,
      ];
    }
    const stair = !wall && !opening && !room ? (model.stairs ?? []).find((x) => x.uid === uid) : undefined;
    if (stair) {
      kind = "stair"; storey = stair.storey;
      const pts = stair.outline;
      if (pts.length) centroid = [
        pts.reduce((a, p) => a + p[0], 0) / pts.length,
        pts.reduce((a, p) => a + p[1], 0) / pts.length,
      ];
    }
    if (!kind) return;
    if (viewMode === "3d") set({ viewMode: "split" }); // make sure the 2D plan is visible
    if (storey) set({ activeStorey: storey });
    set({ selection: { kind, uid }, hoverUid: uid });
    // Pan so the centroid lands at the viewport center (project: sx = tx + x·scale, sy = ty − y·scale).
    if (centroid) {
      const w = typeof window !== "undefined" ? window.innerWidth : 1200;
      const h = typeof window !== "undefined" ? window.innerHeight : 800;
      set({ view: { ...view, tx: w / 2 - centroid[0] * view.scale, ty: h / 2 + centroid[1] * view.scale } });
    }
  },
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
      type = o?.kind === "rough_opening" ? "RoughOpening" : o?.is_door ? "Door" : "Window";
      tag = o?.tag ?? null;
    } else if (selection.kind === "room") {
      const r = model.rooms.find((x) => x.uid === selection.uid);
      type = "Room"; tag = r?.tag ?? null;
    } else if (selection.kind === "stair") {
      const stair = (model.stairs ?? []).find((x) => x.uid === selection.uid);
      type = "Stair"; tag = stair?.tag ?? null;
    } else if (selection.kind === "canvas_object") {
      const item = (model.canvas_objects ?? []).find((x) => x.uid === selection.uid);
      type = item?.kind ?? null; tag = item?.tag ?? null;
    }
    if (!type || !tag) return;
    const ok = await applyOps([{ op: "delete", type, tag }]);
    if (ok) { get().toast(`${tag} deleted`); select(null, null); }
  },

  duplicateSelection: async () => {
    const { model, selection, runMacro } = get();
    if (!model || !selection.uid) return;
    let tag: string | null = null;
    let storey: string | null = null;
    if (selection.kind === "canvas_object") {
      const item = (model.canvas_objects ?? []).find((x) => x.uid === selection.uid);
      tag = item?.tag ?? null;
      storey = item?.storey ?? null;
    } else if (selection.kind === "opening") {
      const opening = model.openings.find((x) => x.uid === selection.uid);
      const host = opening && model.walls.find((wall) => wall.tag === opening.host);
      tag = opening?.tag ?? null;
      storey = host?.storey ?? null;
    }
    if (!tag || !storey) return;
    const result = await runMacro({ macro: "duplicate_canvas_object", storey, tag });
    if (result) get().toast(`${tag} duplicated`);
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
      // An empty history (409) isn't an error — a stray Undo after a no-op edit
      // shouldn't flash a red toast; report it as neutral info instead.
      if (err instanceof EngineError && err.status === 409) get().toast(err.message, "info");
      else get().toast((err as Error).message, "error");
    }
  },

  redo: async () => {
    try {
      const res = await get().client.redo();
      await get().reloadIfStale(res.revision);
    } catch (err) {
      if (err instanceof EngineError && err.status === 409) get().toast(err.message, "info");
      else get().toast((err as Error).message, "error");
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

// Passing checks still travel through model.findings (the tri-state PASS/FAIL/UNKNOWN
// result is tracked separately from severity), but the UI only surfaces the ones that
// need attention.
export function visibleFindings(findings: Finding[]): Finding[] {
  return findings.filter((f) => f.result !== "pass");
}

export function findingsFor(model: Model | null, uid: string | null): Finding[] {
  if (!model || !uid) return [];
  return visibleFindings(
    model.findings.filter((f) => f.element === uid || (f.elements ?? []).includes(uid)),
  );
}
