// The single zustand store. Holds the last-loaded model.json, view transform, selection,
// tool state, and the EngineClient wiring. Components read slices from here; all mutations
// go out through the client and come back as a fresh model on the next push (→ 21 editing
// loop: render → edit → patch → rebuild → WebSocket push → re-render).
//
// Three neighbours carry pieces of this: state/vocabulary.ts holds the enumerations and
// small records (Tool, Trade, SelectionKind, Selection, Toast…), state/locate.ts the pure
// uid → element lookup and the finding filters, and state/mutations.ts every action that
// writes through the EngineClient. The first two are importable without pulling in an
// EngineClient, which is why they are not re-exported from here.

import { create } from "zustand";
import type { EngineClient, EngineEvent } from "../engine/EngineClient";
import { HttpEngineClient } from "../engine/HttpEngineClient";
import { PyodideEngineClient } from "../engine/PyodideEngineClient";
import { loadBundledHouse, pickHouseDirectory } from "../engine/openHouse";

// The standalone PWA (built for type-house.com/app) has no local server: it boots the bundled
// Catlin house in the in-browser pyodide engine by default. `haus serve` builds leave this unset
// and keep the HttpEngineClient default.
const PWA_STANDALONE = import.meta.env.VITE_PWA_STANDALONE === "1";
import type { Model, Severity } from "../model/types";
import { ALL_LAYER_VISIBILITY_GROUPS, type LayerVisibilityGroup } from "../model/visibility";
import { locateUid } from "./locate";
import type { PanelId } from "./panels";
import { createMutationActions, type MutationActions } from "./mutations";
import {
  ALL_TRADES,
  DEFAULT_EARTH_OPACITY,
  type Conflict, type DetailView, type LabelMode, type Lens, type Representation, type Selection,
  type ThreeMode, type Toast, type Tool, type Trade,
  type ViewMode, type ViewTransform, type Workspace,
} from "./vocabulary";

export interface StoreState extends MutationActions {
  client: EngineClient;
  offline: boolean; // true once running against the in-browser pyodide engine
  offlineHouse: string | null;
  connected: boolean;
  loading: boolean;
  model: Model | null;
  error: string | null;

  tool: Tool;
  subOperation: boolean; // true mid-draw (e.g. wall chain in progress) — drives Esc hierarchy
  drawAssembly: string | null; // ContextBar-selected wall assembly for new walls
  chainDraw: boolean; // keep the wall tool armed after each segment
  // One left-hand panel at a time. Replaced three independent booleans whose mutual
  // exclusion was only half-wired (Issues closed neither of the other two).
  activePanel: PanelId | null;
  // Severity the issues drawer is narrowed to, or null for "everything". Set when a surface
  // opens the drawer *about* something specific (the load-error banner opens it on "error"),
  // so the user lands on the findings they were just told about instead of the whole list.
  issuesSeverityFilter: Severity | null;
  commandPaletteOpen: boolean; // ⌘K fuzzy command surface (Phase 4)
  recentCommands: string[]; // command ids, most-recent first (Phase 4)
  activeWorkspace: Workspace; // DESIGN / ANALYZE / DOCUMENT (Phase 6)
  representation: Representation; // conceptual → fabrication detail level (Phase 6)
  workbench: "assembly" | "stair" | null; // focus-mode workbench for complex edits (Phase 7)
  activeLens: Lens; // building-science lens (Phase 9)
  preview3DOpen: boolean; // floating synchronized 3D preview over the 2D plan (Phase 10)
  viewMode: ViewMode;
  threeMode: ThreeMode;
  selection: Selection;
  hoverUid: string | null;
  activeStorey: string | null;
  view: ViewTransform;
  // Derived from `representation`, never set directly: a separate toggle could disagree
  // with the representation the Views panel was reporting.
  showFraming: boolean;
  labelMode: LabelMode; // how much name text the 2D plan draws (rooms + objects; default hover)
  // One visibility model, read by both Canvas2D and Panel3D (→ model/visibility.ts): trades
  // answer "which discipline", layer groups answer "which band of the assembly".
  visibleTrades: Record<Trade, boolean>;
  visibleLayerGroups: Record<LayerVisibilityGroup, boolean>;
  // How solid the 3D site sheet is drawn, 0..1. Independent of `visibleTrades.earth`, which
  // is still what turns the ground off entirely: this only says how much of the basement the
  // ground you *are* showing lets through, from the translucent default up to real dirt.
  earthOpacity: number;
  detailView: DetailView; // assembly-details / BOM reader over the canvas
  conflict: Conflict | null;
  // Set when the engine reports a queued source writeback failed: the edit the user saw
  // applied has been reverted to source truth, so this must be shown, not swallowed.
  writebackFailure: string | null;
  toasts: Toast[];

  // actions
  init: () => Promise<void>;
  reload: () => Promise<void>;
  // Revision-deduped reload: skips the fetch when the model already matches `revision`,
  // and coalesces the mutation-action reload with the WS-echo reload into one GET /model.
  reloadIfStale: (revision?: string) => Promise<void>;
  openOfflineHouse: () => Promise<void>;
  setTool: (t: Tool) => void;
  setSubOperation: (v: boolean) => void;
  setDrawAssembly: (tag: string | null) => void;
  setChainDraw: (v: boolean) => void;
  // Passing the id that is already active closes it, so a rail item toggles.
  setActivePanel: (panel: PanelId | null) => void;
  // Open (never toggle closed) the issues drawer, narrowed to `severity`.
  openIssues: (severity: Severity | null) => void;
  setCommandPaletteOpen: (v: boolean) => void;
  pushRecentCommand: (id: string) => void;
  setActiveWorkspace: (w: Workspace) => void;
  setRepresentation: (r: Representation) => void;
  setWorkbench: (w: "assembly" | "stair" | null) => void;
  setActiveLens: (l: Lens) => void;
  setPreview3DOpen: (v: boolean) => void;
  setViewMode: (v: ViewMode) => void;
  setThreeMode: (m: ThreeMode) => void;
  setLabelMode: (v: LabelMode) => void;
  setTradeVisible: (trade: Trade, visible: boolean) => void;
  setLayerGroupVisible: (group: LayerVisibilityGroup, visible: boolean) => void;
  setEarthOpacity: (opacity: number) => void;
  showEverything: () => void; // one-tap escape from an over-filtered view
  setDetailView: (v: DetailView) => void;
  select: (kind: Selection["kind"], uid: string | null) => void;
  selectByTag: (kind: Selection["kind"], tag: string) => void;
  setHover: (uid: string | null) => void;
  setActiveStorey: (tag: string | null) => void;
  setView: (v: Partial<ViewTransform>) => void;
  // Navigate to an element (Phase 5 issue jump): switch to its storey, select + highlight it,
  // and pan the 2D view so its centroid sits at the viewport center.
  zoomToUid: (uid: string) => void;
  dismissConflict: () => void;
  dismissWritebackFailure: () => void;
  toast: (message: string, kind?: Toast["kind"]) => void;
  dismissToast: (id: number) => void;
  clearToasts: () => void;

}

let toastSeq = 1;

let unsubscribeEvents: (() => void) | null = null;

// One in-flight GET /model at a time, tagged with the revision it targets. A second caller
// asking for the same (or an already-loaded) revision rides the existing promise instead of
// firing a duplicate fetch — this is what collapses the old action+WS double reload (1a).
let inflightReload: { revision: string | null; promise: Promise<void> } | null = null;

export const useStore = create<StoreState>((set, get) => ({
  client: new HttpEngineClient(),
  offline: false,
  offlineHouse: null,
  connected: false,
  loading: true,
  model: null,
  error: null,

  tool: "select",
  subOperation: false,
  drawAssembly: null,
  chainDraw: true,
  activePanel: null,
  issuesSeverityFilter: null,
  commandPaletteOpen: false,
  recentCommands: [],
  activeWorkspace: "design",
  representation: "detailed",
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
  labelMode: "hover",
  visibleTrades: {
    walls: true, openings: true, framing: true, floors: true, concrete: true, roof: true,
    stairs: true, furniture: true, plumbing: true, electrical: true, mechanical: true, earth: true,
    drainage: true,
  },
  visibleLayerGroups: Object.fromEntries(
    ALL_LAYER_VISIBILITY_GROUPS.map((group) => [group, true]),
  ) as Record<LayerVisibilityGroup, boolean>,
  earthOpacity: DEFAULT_EARTH_OPACITY,
  detailView: "none",
  conflict: null,
  writebackFailure: null,
  toasts: [],

  init: async () => {
    // Standalone PWA first boot: replace the default HttpEngineClient with the offline pyodide
    // engine seeded with the bundled Catlin house, so new visitors get a working editor with no
    // server and no folder pick.
    if (PWA_STANDALONE && !get().offline) {
      try {
        const opened = await loadBundledHouse();
        set({
          client: new PyodideEngineClient(opened.files),
          offline: true,
          offlineHouse: opened.name,
          model: null,
          loading: true,
        });
      } catch (err) {
        get().toast(`offline demo failed: ${(err as Error).message}`, "error");
      }
    }
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
        activeStorey:
          prev.activeStorey ??
          model.storeys.find((s) => s.tag === "main")?.tag ??
          model.storeys[0]?.tag ??
          null,
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

  setTool: (tool) => set({ tool, subOperation: false }),
  setSubOperation: (subOperation) => set({ subOperation }),
  setDrawAssembly: (drawAssembly) => set({ drawAssembly }),
  setChainDraw: (chainDraw) => set({ chainDraw }),
  // Left side hosts one large panel at a time (reviewer rule).
  setActivePanel: (panel) => set((s) => ({ activePanel: s.activePanel === panel ? null : panel,
    // A hand-driven open starts unfiltered; only openIssues narrows it.
    issuesSeverityFilter: panel === "issues" ? null : s.issuesSeverityFilter })),
  openIssues: (issuesSeverityFilter) => set({ activePanel: "issues", issuesSeverityFilter }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
  pushRecentCommand: (id) =>
    set((s) => ({ recentCommands: [id, ...s.recentCommands.filter((c) => c !== id)].slice(0, 6) })),
  setActiveWorkspace: (activeWorkspace) => set({ activeWorkspace }),
  // Representation generalizes showFraming: detailed/fabrication show framing, conceptual/
  // schematic show wall fills only.
  setRepresentation: (representation) =>
    set({ representation, showFraming: representation === "detailed" || representation === "fabrication" }),
  setWorkbench: (workbench) => set({ workbench }),
  setActiveLens: (activeLens) => set({ activeLens }),
  setPreview3DOpen: (preview3DOpen) => set({ preview3DOpen }),
  setViewMode: (viewMode) => set({ viewMode }),
  setThreeMode: (threeMode) => set({ threeMode }),
  setLabelMode: (labelMode) => set({ labelMode }),
  setTradeVisible: (trade, visible) =>
    set((s) => ({ visibleTrades: { ...s.visibleTrades, [trade]: visible } })),
  setLayerGroupVisible: (group, visible) =>
    set((s) => ({ visibleLayerGroups: { ...s.visibleLayerGroups, [group]: visible } })),
  setEarthOpacity: (opacity) => set({ earthOpacity: Math.min(1, Math.max(0, opacity)) }),
  showEverything: () =>
    set({
      visibleTrades: Object.fromEntries(ALL_TRADES.map((trade) => [trade, true])) as Record<Trade, boolean>,
      visibleLayerGroups: Object.fromEntries(
        ALL_LAYER_VISIBILITY_GROUPS.map((group) => [group, true]),
      ) as Record<LayerVisibilityGroup, boolean>,
    }),
  setDetailView: (detailView) => set({ detailView }),
  select: (kind, uid) => set({ selection: { kind, uid } }),
  // Select an element by its authored tag (uids are minted server-side, so a freshly drawn
  // wall / placed opening is only addressable by tag until the next reload lands).
  selectByTag: (kind, tag) => {
    const model = get().model;
    if (!model) return;
    // Tags only address the authored elements a tool can mint; derived geometry (solids,
    // beddings, floors, roofs) is reached by uid from a 3D pick, never by tag.
    const pool =
      kind === "wall" ? model.walls : kind === "opening" ? model.openings
        : kind === "room" ? model.rooms : kind === "canvas_object" ? model.canvas_objects ?? []
          : kind === "stair" ? model.stairs ?? [] : null;
    const hit = pool?.find((e) => e.tag === tag);
    if (hit) set({ selection: { kind, uid: hit.uid } });
  },
  setHover: (hoverUid) => set({ hoverUid }),
  setActiveStorey: (activeStorey) => set({ activeStorey }),
  setView: (v) => set((s) => ({ view: { ...s.view, ...v } })),
  zoomToUid: (uid) => {
    const { model, view, viewMode } = get();
    if (!model) return;
    const located = locateUid(model, uid);
    if (!located) return;
    // Show the plan outright rather than half of it: the user asked to look at a
    // specific element, and a half-width plan was never the better answer.
    if (viewMode === "3d") set({ viewMode: "2d" });
    if (located.storey) set({ activeStorey: located.storey });
    set({ selection: { kind: located.kind, uid }, hoverUid: uid });
    // Pan so the centroid lands at the viewport center (project: sx = tx + x·scale, sy = ty − y·scale).
    if (located.centroid) {
      const w = typeof window !== "undefined" ? window.innerWidth : 1200;
      const h = typeof window !== "undefined" ? window.innerHeight : 800;
      set({ view: { ...view, tx: w / 2 - located.centroid[0] * view.scale, ty: h / 2 + located.centroid[1] * view.scale } });
    }
  },
  dismissConflict: () => set({ conflict: null }),
  dismissWritebackFailure: () => set({ writebackFailure: null }),
  toast: (message, kind = "info") =>
    set((s) => ({ toasts: [...s.toasts, { id: toastSeq++, message, kind }] })),
  dismissToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  clearToasts: () => set({ toasts: [] }),
  ...createMutationActions(set, get),
}));

// Exported for the event-handling suite: the writeback-failed path has no other seam.
export function handleEvent(
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
    case "writeback-failed": {
      // The engine already reverted to source truth; reload so the canvas matches, and say
      // why the edit disappeared instead of hot-reloading it away silently.
      set({ writebackFailure: e.detail });
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
