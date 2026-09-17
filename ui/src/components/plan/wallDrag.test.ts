import type { Vec2 } from "../../model/types";
import { bodySpans, offsetDelta, perpendicularOffset, snapOffset, wallNormal } from "./wallDrag";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
const near = (a: number, b: number) => Math.abs(a - b) < 1e-9;

export function runWallDragTests(): void {
  const east: [Vec2, Vec2] = [[0, 0], [4, 0]];
  const n = wallNormal(east);
  assert(n && near(n[0], 0) && near(n[1], 1), "an east-running wall's normal points north");
  assert(wallNormal([[1, 1], [1, 1]]) === null, "a degenerate axis has no normal");

  assert(near(perpendicularOffset(east, [1, 0], [3, 0.7]), 0.7),
    "travel along the wall is discarded; only the perpendicular part moves it");
  assert(near(perpendicularOffset([[0, 0], [0, 4]], [0, 1], [0.5, 1]), -0.5),
    "a north-running wall reads eastward travel as a negative offset");

  assert(near(snapOffset(0.34, 0.3048 / 2), 0.3048), "offset snaps to the grid");
  assert(near(snapOffset(0.02, 0.0127), 0.0254), "fallback half-inch step");
  assert(Object.is(snapOffset(-0.001, 0.1), 0), "a sub-step drag snaps to +0, a no-op");

  const d = offsetDelta(east, 0.5);
  assert(near(d[0], 0) && near(d[1], 0.5), "delta is the normal scaled by the offset");

  const spans = bodySpans(4, [{ center_along_m: 2, width_m: 1 }]);
  assert(spans.length === 2 && near(spans[0][1], 1.5) && near(spans[1][0], 2.5),
    "a hosted opening leaves a gap in the grabbable body");
  assert(bodySpans(4, []).length === 1, "an unpierced wall is one span");
  assert(bodySpans(1, [{ center_along_m: 0.5, width_m: 2 }]).length === 0,
    "an opening wider than the wall leaves nothing to grab");
}
