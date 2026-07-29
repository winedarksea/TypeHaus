// A drag on a canvas object is a source writeback, so the canvas must refuse the gesture on
// an object no editable plan file hosts — otherwise the object follows the pointer, the
// engine rejects the move, and it snaps back with no explanation.
import type { CanvasObject, Vec2 } from "../../model/types";
import { placeableDragBlockedReason } from "./ObjectShapes";
import { DRAG_THRESHOLD_PX, draggedCenter, exceedsDragThreshold, grabOffsetFor } from "./objectDrag";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function obj(provenance: CanvasObject["provenance"]): CanvasObject {
  return {
    uid: "OBJ0000001", tag: "FX-WC-1", storey: "L1", kind: "Fixture", type: "FX-TOILET-STD",
    domain: "plumbing", room: "RM-Bath", position_m: [1, 2], rotation: 0, host: null,
    attachment: null, provenance,
  } as CanvasObject;
}

export function runPlaceableDragTests(): void {
  assert(
    placeableDragBlockedReason(obj({ file: "plan/storeys/main.py", line: 12, editable: true })) === null,
    "an object authored in an editable file drags normally",
  );

  const generated = placeableDragBlockedReason(
    obj({ file: "params/layout.py", line: 3, editable: false }),
  );
  assert(generated && generated.includes("params/layout.py"),
    "a generated object names the file to edit instead of dragging");

  assert(placeableDragBlockedReason(obj(null)),
    "an object with no captured authorship has nowhere to write a move back to");

  // Older model.json payloads publish no provenance at all; absence must not disable
  // dragging for every object in the house.
  assert(placeableDragBlockedReason(obj(undefined)) === null,
    "a payload without provenance keeps the existing drag behaviour");

  console.log("Placeable drag-affordance tests passed.");
}

// The click-vs-drag maths, the fix for objects "moving randomly" when they were only clicked.
export function runObjectDragMathTests(): void {
  const down: Vec2 = [400, 300];

  assert(!exceedsDragThreshold(down, [400, 300]), "a pointer that never moved is not a drag");
  assert(!exceedsDragThreshold(down, [404, 300]),
    "a few pixels of tremor stays a click, not a 4-pixel move");
  // The boundary is exclusive: exactly the threshold is still a click.
  assert(!exceedsDragThreshold(down, [400 + DRAG_THRESHOLD_PX, 300]),
    "travel equal to the threshold has not exceeded it");
  assert(exceedsDragThreshold(down, [400 + DRAG_THRESHOLD_PX + 1, 300]),
    "one pixel past the threshold begins a drag");
  // Diagonal travel counts as its hypotenuse, not per-axis: 3-4-5.
  assert(!exceedsDragThreshold(down, [403, 304]), "3,4 travel is 5px — exactly the threshold");
  assert(exceedsDragThreshold(down, [406, 308]), "6,8 travel is 10px — a drag");

  // Grabbing a wide object near its edge must not teleport its centre onto the cursor: the
  // offset from grab point to centre is preserved for the whole gesture.
  const centre: Vec2 = [3, 2];
  const grabbedAt: Vec2 = [3.9, 2.1]; // near the right edge of a 2 m-wide object
  const offset = grabOffsetFor(centre, grabbedAt);
  const held = draggedCenter(offset, grabbedAt);
  assert(Math.hypot(held[0] - centre[0], held[1] - centre[1]) < 1e-9,
    "a grab with no travel leaves the object exactly where it was");

  const moved = draggedCenter(offset, [5.9, 4.1]); // cursor travels +2, +2
  assert(Math.abs(moved[0] - 5) < 1e-9 && Math.abs(moved[1] - 4) < 1e-9,
    "the centre follows the cursor's delta, keeping the grab point under the pointer");

  console.log("Object drag-maths tests passed.");
}
