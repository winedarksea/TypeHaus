import { M_TO_IN, draggedOffsetMeters } from "./DetailCanvas";

// U10: an annotation drag must persist as an offset relative to the resolved anchor, in metres,
// not as absolute pixels. These lock the local-frame → anchor-relative-metres conversion the
// commit path relies on (must mirror emit/draw/details.py: at = anchor + offset * M_TO_IN).
export function runDetailAnnotationTests() {
  const approx = (a: number, b: number) => Math.abs(a - b) < 1e-9;

  // One metre right in scene-x is M_TO_IN inches of local dx → offset.x grows by exactly 1 m.
  const right = draggedOffsetMeters([0, 0], M_TO_IN, 0);
  if (!approx(right[0], 1) || !approx(right[1], 0)) {
    throw new Error(`drag right must add 1 m to offset.x, got ${right}`);
  }

  // Local y grows downward while scene z grows up, so dragging *down* must decrease offset.y.
  const down = draggedOffsetMeters([0, 0], 0, M_TO_IN);
  if (!approx(down[1], -1) || !approx(down[0], 0)) {
    throw new Error(`drag down must subtract 1 m from offset.y, got ${down}`);
  }

  // Anchor-relative: a drag accumulates onto the existing offset, never replaces it.
  const base: [number, number] = [0.25, -0.4];
  const moved = draggedOffsetMeters(base, M_TO_IN / 2, -M_TO_IN / 4);
  if (!approx(moved[0], 0.75) || !approx(moved[1], -0.15)) {
    throw new Error(`drag must accumulate onto the prior offset, got ${moved}`);
  }

  // A zero drag is a no-op — a click on an annotation must not shift its stored offset.
  const still = draggedOffsetMeters(base, 0, 0);
  if (!approx(still[0], base[0]) || !approx(still[1], base[1])) {
    throw new Error(`zero drag must preserve the offset, got ${still}`);
  }
}
