// Pending-edit state: the overlay a committed transform shows until the engine's model
// catches up, plus the Saving…/Saved/Save failed state the status rail reads.
//
// Revisions are random uuids, so reconciliation is by client `seq` and equality only: an
// overlay is cleared by the commit that set it (or a later one's settle), never by comparing
// revision order. Selection is never touched by a commit.
import type { StateCreator } from "zustand";
import type { MacroRequest, MacroResult } from "../engine/EngineClient";
import type { Vec2 } from "../model/types";
import type { StoreState } from "./store";

export interface PendingTransform {
  position_m?: Vec2;
  rotation?: number;
  seq: number;
}

export type SaveState = "idle" | "saving" | "saved" | "failed";

export interface PendingSlice {
  pendingTransforms: Record<string, PendingTransform>;
  saveState: SaveState;
  // The revision of the last `saved` event: the engine's source writeback drained there.
  savedRevision: string | null;
  setSaveState: (saveState: SaveState) => void;
  // Show `overlay` on `item` at once, then run `request` through the serialized queue.
  commitTransform: (
    item: { uid: string },
    overlay: { position_m?: Vec2; rotation?: number },
    request: MacroRequest,
  ) => Promise<MacroResult | null>;
  clearPendingTransforms: () => void;
}

let transformSeq = 0;

function withoutEntry(
  transforms: Record<string, PendingTransform>, uid: string, seq: number,
): Record<string, PendingTransform> | null {
  if (transforms[uid]?.seq !== seq) return null;
  const next = { ...transforms };
  delete next[uid];
  return next;
}

export const createPendingSlice: StateCreator<StoreState, [], [], PendingSlice> = (set, get) => ({
  pendingTransforms: {},
  saveState: "idle",
  savedRevision: null,
  setSaveState: (saveState) => set({ saveState }),
  clearPendingTransforms: () => set({ pendingTransforms: {} }),

  commitTransform: async (item, overlay, request) => {
    const seq = ++transformSeq;
    const previous = get().pendingTransforms[item.uid];
    set({
      pendingTransforms: {
        ...get().pendingTransforms,
        [item.uid]: { ...previous, ...overlay, seq },
      },
    });
    const result = await get().runMacro(request);
    // runMacro reloads to its own revision, but a concurrent WS echo may have landed an
    // older fetch in between; the overlay must not clear onto a model without this edit.
    if (result && get().model?.revision !== result.revision) {
      await get().reloadIfStale(result.revision);
    }
    // A failed commit clears too: snapping to the authoritative position is right for a
    // rejected edit, and runMacro has already said why.
    const cleared = withoutEntry(get().pendingTransforms, item.uid, seq);
    if (cleared) set({ pendingTransforms: cleared });
    return result;
  },
});
