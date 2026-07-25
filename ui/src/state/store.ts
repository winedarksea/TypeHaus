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
import { loadBundledHouse, pickHouseDirectory } from "../engine/openHouse";

// The standalone PWA (built for type-house.com/app) has no local server: it boots the bundled
// Catlin house in the in-browser pyodide engine by default. `haus serve` builds leave this unset
// and keep the HttpEngineClient default.
const PWA_STANDALONE = import.meta.env.VITE_PWA_STANDALONE === "1";
import type { Finding, Model, Provenance, Vec2 } from "../model/types";

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

// Every kind of model record the UI can hold selected. The first five are authored elements a
// patch can edit or delete; the last four are *derived* geometry the resolver computes (a post
// or beam solid, a footing's gravel bed, a roof, a framed floor) — selectable and inspectable in
// 3D, but only editable through the element they came from. The same vocabulary is written into
// glTF node extras (emit/gltf/emitter.py::_SELECTION_KINDS) and emitted by the 3D pick handler
// (components/Panel3D.tsx), so all three surfaces agree on what a click resolves to.
export type SelectionKind =
  | "wall" | "opening" | "room" | "stair" | "canvas_object"
  | "solid" | "footing_bedding" | "floor" | "roof";
export const ALL_SELECTION_KINDS: SelectionKind[] = [
  "wall", "opening", "room", "stair", "canvas_object", "solid", "footing_bedding", "floor", "roof",
];
export const DERIVED_SELECTION_KINDS: SelectionKind[] = ["solid", "footing_bedding", "floor", "roof"];

export interface Selection {
  kind: SelectionKind | null;
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
  showSpaceLabels: boolean; // room/area name (or id) label overlay in the 2D plan (default on)
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
  setShowSpaceLabels: (v: boolean) => void;
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
  clearToasts: () => void;

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
  showSpaceLabels: true,
  visibleTrades: {
    walls: true, openings: true, framing: true, floors: true, concrete: true, roof: true,
    stairs: true, furniture: true, plumbing: true, electrical: true, mechanical: true, earth: true,
  },
  conflict: null,
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
  setShowSpaceLabels: (showSpaceLabels) => set({ showSpaceLabels }),
  setTradeVisible: (trade, visible) =>
    set((s) => ({ visibleTrades: { ...s.visibleTrades, [trade]: visible } })),
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
    if (viewMode === "3d") set({ viewMode: "split" }); // make sure the 2D plan is visible
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
  toast: (message, kind = "info") =>
    set((s) => ({ toasts: [...s.toasts, { id: toastSeq++, message, kind }] })),
  dismissToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  clearToasts: () => set({ toasts: [] }),

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
    // Derived geometry has no authored record to address: a "column" solid may come from a
    // Post, a "railing" solid from one Railing's many balusters, and a construction return
    // from a library rule that owns no element at all. Rather than guess an element type from
    // its category (a wrong guess silently deletes the wrong thing) or no-op in silence, say
    // where the geometry comes from so the user can edit that source instead.
    if (selection.kind !== null && DERIVED_SELECTION_KINDS.includes(selection.kind)) {
      const derived = locateUid(model, selection.uid);
      get().toast(derived
        ? `${derived.tag} is derived geometry — edit its source (${derived.source ?? "plan code"}) instead`
        : "That element is derived geometry and cannot be deleted directly");
      return;
    }
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

// uid resolution ------------------------------------------------------------

export interface LocatedElement {
  kind: SelectionKind;
  tag: string;
  storey: string | null;
  centroid: [number, number] | null; // plan-space centre, for the 2D pan-to-element
  source: string | null; // "file:line" of the authoring statement, when the loader captured one
}

function ringCentroid(points: readonly Vec2[]): [number, number] | null {
  if (!points.length) return null;
  return [
    points.reduce((sum, p) => sum + p[0], 0) / points.length,
    points.reduce((sum, p) => sum + p[1], 0) / points.length,
  ];
}

function sourceOf(provenance: Provenance | null | undefined): string | null {
  return provenance ? `${provenance.file}:${provenance.line}` : null;
}

// Resolve a uid against every selectable record — authored elements first, then the derived
// geometry a 3D pick can land on. One lookup shared by zoomToUid, deleteSelection, and the
// Inspector, so all three agree on what a uid *is*.
export function locateUid(model: Model, uid: string): LocatedElement | null {
  const wall = model.walls.find((w) => w.uid === uid);
  if (wall) return { kind: "wall", tag: wall.tag, storey: wall.storey, source: sourceOf(wall.provenance),
    centroid: [(wall.axis[0][0] + wall.axis[1][0]) / 2, (wall.axis[0][1] + wall.axis[1][1]) / 2] };

  const opening = model.openings.find((o) => o.uid === uid);
  if (opening) {
    const host = model.walls.find((w) => w.tag === opening.host);
    return { kind: "opening", tag: opening.tag, storey: host?.storey ?? null,
      source: sourceOf(opening.provenance),
      centroid: host ? [(host.axis[0][0] + host.axis[1][0]) / 2, (host.axis[0][1] + host.axis[1][1]) / 2] : null };
  }

  const room = model.rooms.find((r) => r.uid === uid);
  if (room) return { kind: "room", tag: room.tag, storey: room.storey,
    source: sourceOf(room.provenance), centroid: ringCentroid(room.clear_face) };

  const stair = (model.stairs ?? []).find((x) => x.uid === uid);
  if (stair) return { kind: "stair", tag: stair.tag, storey: stair.storey,
    source: sourceOf(stair.provenance), centroid: ringCentroid(stair.outline) };

  // Placeables carry no provenance in model.json — they are addressed by tag, not file:line.
  const item = (model.canvas_objects ?? []).find((x) => x.uid === uid);
  if (item) return { kind: "canvas_object", tag: item.tag, storey: item.storey,
    source: null, centroid: item.position_m ?? null };

  const solid = (model.solids ?? []).find((x) => x.uid === uid);
  if (solid) return { kind: "solid", tag: solid.tag, storey: solid.storey,
    source: sourceOf(solid.provenance), centroid: ringCentroid(solid.outline) };

  const bedding = (model.footing_beddings ?? []).find((x) => x.uid === uid);
  if (bedding) return { kind: "footing_bedding", tag: bedding.tag, storey: bedding.storey,
    source: sourceOf(bedding.provenance), centroid: ringCentroid(bedding.outline) };

  const roof = (model.roofs ?? []).find((x) => x.uid === uid);
  if (roof) return { kind: "roof", tag: roof.tag, storey: roof.storey,
    source: sourceOf(roof.provenance), centroid: ringCentroid(roof.footprint) };

  const floor = (model.floors ?? []).find((x) => x.uid === uid);
  if (floor) return { kind: "floor", tag: floor.tag, storey: floor.storey,
    source: sourceOf(floor.provenance),
    // A framed floor carries no outline of its own; its joist endpoints bound the deck.
    centroid: ringCentroid(floor.members.flatMap((member) => [member.p0, member.p1])) };

  return null;
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
