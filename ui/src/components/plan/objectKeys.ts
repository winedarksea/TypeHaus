// Keyboard edits of a selected plan object, as pure maths: an arrow is a world-space nudge
// (plan +y is up the screen), R is a quarter turn.
import type { Vec2 } from "../../model/types";
import { NUDGE_LARGE_M, NUDGE_M, ROTATE_STEP_DEG } from "./editorConfig";

const ARROW_DIRECTIONS: Record<string, Vec2> = {
  ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1],
};

export function nudgeVector(key: string, shift: boolean): Vec2 | null {
  const direction = ARROW_DIRECTIONS[key];
  if (!direction) return null;
  const step = shift ? NUDGE_LARGE_M : NUDGE_M;
  return [direction[0] * step, direction[1] * step];
}

// R turns counter-clockwise (the plan's positive rotation), Shift+R clockwise; the result is
// normalised to [0, 360).
export function rotateStep(current: number, reverse = false): number {
  const next = current + (reverse ? -ROTATE_STEP_DEG : ROTATE_STEP_DEG);
  return ((next % 360) + 360) % 360;
}
