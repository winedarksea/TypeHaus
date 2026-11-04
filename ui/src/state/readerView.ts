// How readers are shown: full-size or as the centred card, and the Estimate reader's
// grouping and sort (lifted here so `?egroup=` / `?esort=` deep links can name them).
import type { StateCreator } from "zustand";
import type { GroupKey, SortKey } from "../model/estimateGroups";
import type { StoreState } from "./store";

export interface EstimateViewState {
  group: GroupKey;
  sort: SortKey;
}

export const DEFAULT_ESTIMATE_VIEW: EstimateViewState = { group: "trade", sort: "cost" };

export interface ReaderViewSlice {
  /** True: readers fill the workspace. False: the centred card. Remembered per viewer. */
  readerFull: boolean;
  setReaderFull: (full: boolean) => void;
  estimateView: EstimateViewState;
  setEstimateView: (next: Partial<EstimateViewState>) => void;
}

const FULL_KEY = "typehaus.readerFull";

// A per-viewer convenience: storage may be absent or throw (private window, previews).
function readFull(): boolean {
  try {
    return globalThis.localStorage?.getItem(FULL_KEY) !== "0";
  } catch {
    return true;
  }
}

function writeFull(full: boolean): void {
  try {
    globalThis.localStorage?.setItem(FULL_KEY, full ? "1" : "0");
  } catch {
    // Not remembered; the toggle still works for this session.
  }
}

export const createReaderViewSlice: StateCreator<StoreState, [], [], ReaderViewSlice> = (set) => ({
  readerFull: readFull(),
  setReaderFull: (readerFull) => {
    writeFull(readerFull);
    set({ readerFull });
  },
  estimateView: DEFAULT_ESTIMATE_VIEW,
  setEstimateView: (next) => set((s) => ({ estimateView: { ...s.estimateView, ...next } })),
});
