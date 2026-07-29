// A drag on a canvas object is a source writeback, so the canvas must refuse the gesture on
// an object no editable plan file hosts — otherwise the object follows the pointer, the
// engine rejects the move, and it snaps back with no explanation.
import type { CanvasObject } from "../../model/types";
import { placeableDragBlockedReason } from "./ObjectShapes";

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
