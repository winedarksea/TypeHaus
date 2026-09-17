// The Place tool's armed state: which catalog type a tap places, whether the tool stays armed
// after a placement, the rotation the ghost and the placed object take, and the catalog
// popover's visibility.
import type { StateCreator } from "zustand";
import type { StoreState } from "./store";

export interface PlacementSlice {
  placementType: string | null;
  placementRepeat: boolean;
  placementRotation: number;
  placementCatalogOpen: boolean;
  setPlacementType: (tag: string | null) => void;
  setPlacementRepeat: (repeat: boolean) => void;
  setPlacementRotation: (degrees: number) => void;
  setPlacementCatalogOpen: (open: boolean) => void;
}

export function normalizeDegrees(degrees: number): number {
  return ((degrees % 360) + 360) % 360;
}

export const createPlacementSlice: StateCreator<StoreState, [], [], PlacementSlice> = (set) => ({
  placementType: null,
  placementRepeat: false,
  placementRotation: 0,
  placementCatalogOpen: false,
  // Choosing a type closes the catalog: the next thing the user does is tap the plan.
  setPlacementType: (placementType) => set({ placementType, placementCatalogOpen: false }),
  setPlacementRepeat: (placementRepeat) => set({ placementRepeat }),
  setPlacementRotation: (degrees) => set({ placementRotation: normalizeDegrees(degrees) }),
  setPlacementCatalogOpen: (placementCatalogOpen) => set({ placementCatalogOpen }),
});
