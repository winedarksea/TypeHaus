// Arrow nudges and the R quarter-turn.
import { NUDGE_LARGE_M, NUDGE_M } from "./editorConfig";
import { nudgeVector, rotateStep } from "./objectKeys";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runObjectKeyTests(): void {
  const up = nudgeVector("ArrowUp", false);
  assert(up && up[0] === 0 && up[1] === NUDGE_M, "ArrowUp moves up the plan (+y) by an inch");
  const left = nudgeVector("ArrowLeft", true);
  assert(left && left[0] === -NUDGE_LARGE_M && left[1] === 0, "Shift+ArrowLeft moves a foot toward -x");
  assert(nudgeVector("a", false) === null, "a non-arrow key is not a nudge");

  assert(rotateStep(0) === 90, "R turns a quarter counter-clockwise");
  assert(rotateStep(270) === 0, "a full turn wraps to 0");
  assert(rotateStep(0, true) === 270, "Shift+R turns the other way and stays in [0, 360)");
  assert(rotateStep(45) === 135, "a skewed object keeps its skew");

  console.log("Object key tests passed.");
}
