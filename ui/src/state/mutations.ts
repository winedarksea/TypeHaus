// Every store action that writes through the EngineClient, in one place.
//
// Split out of state/store.ts (which was well past the 500-line guideline): these eight share
// one shape — call the client, reconcile the revision, and turn a failure into either the
// conflict banner (a 409 precondition, which needs the user to decide) or a toast. Keeping
// them together is what makes that policy reviewable in one screen; the store keeps the plain
// UI-state setters, which have no failure mode at all.
//
// They stay a zustand slice rather than free functions: each needs `get()` to read the live
// model and `set()` to raise the conflict banner, so the store spreads this factory into its
// initializer and every call site keeps working unchanged.
import type {
  MacroRequest, MacroResult, PatchOp, PreviewGeometry, UnderlayCalibration,
} from "../engine/EngineClient";
import { EngineError, RevisionConflict } from "../engine/EngineClient";
import { locateUid } from "./locate";
import { DERIVED_SELECTION_KINDS } from "./vocabulary";
import type { StoreState } from "./store";

export interface MutationActions {
  applyOps: (ops: PatchOp[]) => Promise<boolean>;
  runMacro: (request: MacroRequest) => Promise<MacroResult | null>;
  // Self-throttled live drag preview (→ Phase 4): coalesces to the latest request if a
  // preview is already in flight, so a fast pointermove stream never queues up requests.
  // Never journaled/mutating; swallows errors (offline, ops that can't preview) as `null`.
  //
  // Pass `rehearse` on a gesture's FIRST preview to also pre-check writeback routing. A
  // refusal resolves to the "refused" sentinel (and toasts once) rather than `null`, because
  // the two mean opposite things to a drag: `null` is a transient miss the drag rides out
  // holding its last geometry, "refused" is a verdict that this edit can never land.
  previewMacro: (request: MacroRequest, rehearse?: boolean) => Promise<PreviewGeometry | null | "refused">;
  deleteSelection: () => Promise<void>;
  duplicateSelection: () => Promise<void>;
  calibrateUnderlay: (calibration: UnderlayCalibration) => Promise<boolean>;
  undo: () => Promise<void>;
  redo: () => Promise<void>;
}

// One in-flight POST /macro/preview at a time; a request arriving mid-flight replaces
// `pendingPreviewRequest` instead of firing another fetch, and the in-flight call's resolver
// re-fires itself once against the latest request when it lands — the drag only ever waits
// for one round trip, no matter how fast pointermove fires.
let previewInFlight = false;
let pendingPreviewRequest: MacroRequest | null = null;

export function createMutationActions(
  set: (partial: Partial<StoreState>) => void,
  get: () => StoreState,
): MutationActions {
  return {
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

  previewMacro: async (request, rehearse = false) => {
    if (previewInFlight) {
      pendingPreviewRequest = request; // superseded: only the latest pointer position matters
      return null;
    }
    previewInFlight = true;
    try {
      return await get().client.previewMacro(request, rehearse);
    } catch (err) {
      // Only a rehearsal can produce a *verdict*; a plain preview 422 ("can't apply in
      // memory") is the ordinary transient miss and stays swallowed. Surfacing the reason
      // here is the whole point of rehearsing — the user learns why at drag-start instead of
      // watching the element snap back after mouseup.
      if (rehearse && err instanceof EngineError && err.status === 422) {
        get().toast((err as Error).message, "error");
        return "refused" as const;
      }
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
    // Nothing above claimed the selection (an unhandled kind, or a record the model no longer
    // carries). Say so — a Del key that does nothing at all reads as a broken keyboard.
    if (!type || !tag) {
      get().toast("Nothing deletable is selected", "info");
      return;
    }
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
    // Duplication is defined only for placeables and openings (both need a host storey).
    // Everything else — walls, rooms, framing — has no meaningful "copy" macro yet.
    if (!tag || !storey) {
      get().toast("That selection can't be duplicated", "info");
      return;
    }
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
  };
}
