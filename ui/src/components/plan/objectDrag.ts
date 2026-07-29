// Drag maths for a plan object, split out of ObjectShapes.tsx so the click-vs-drag decision is
// testable without a DOM. Two rules, both learned from objects "moving randomly" on a click:
//
//   1. A pointerdown that never travels is a *select*, not a zero-length move. Screen space is
//      the right frame for that threshold — a few pixels of finger tremor is a few pixels at
//      any zoom, whereas a world-space epsilon shrinks as you zoom in.
//   2. An object follows the *grab point*, not its own centre. Grabbing a 2 m sofa near its
//      arm and having it teleport centre-to-cursor is the other half of the same complaint.
import type { Vec2 } from "../../model/types";

export const DRAG_THRESHOLD_PX = 5;

export function exceedsDragThreshold(
  downScreen: Vec2,
  currentScreen: Vec2,
  thresholdPx: number = DRAG_THRESHOLD_PX,
): boolean {
  return Math.hypot(currentScreen[0] - downScreen[0], currentScreen[1] - downScreen[1]) > thresholdPx;
}

// grabOffset = item.position_m − toWorld(pointerdown): the vector from the point the user
// grabbed to the object's origin, held constant for the life of the gesture.
export function grabOffsetFor(centre: Vec2, downWorld: Vec2): Vec2 {
  return [centre[0] - downWorld[0], centre[1] - downWorld[1]];
}

export function draggedCenter(grabOffset: Vec2, cursorWorld: Vec2): Vec2 {
  return [cursorWorld[0] + grabOffset[0], cursorWorld[1] + grabOffset[1]];
}
