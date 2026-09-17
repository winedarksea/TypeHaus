// Plan-editor gesture tunables in one place (AGENTS.md: no magic numbers at call sites).
export { DRAG_THRESHOLD_PX } from "./objectDrag";

export const NUDGE_M = 0.0254; // arrow key: 1"
export const NUDGE_LARGE_M = 0.3048; // Shift+arrow: 1'
export const ROTATE_STEP_DEG = 90; // R
export const ROTATE_HANDLE_SNAP_DEG = 15; // rotate handle without Shift
export const WALL_GUIDE_M = 0.35; // a dragged object this close to a wall face shows the guide
export const WALL_SNAP_M = 0.15; // …and this close snaps flush on release (Alt skips)
export const WALL_SNAP_PARALLEL_DEG = 15; // only an object within this of square to the wall snaps

export interface WallSnapConfig {
  guideM: number;
  snapM: number;
  parallelDeg: number;
}

export const WALL_SNAP_CONFIG: WallSnapConfig = {
  guideM: WALL_GUIDE_M, snapM: WALL_SNAP_M, parallelDeg: WALL_SNAP_PARALLEL_DEG,
};
