// The Canvas2D editor's local vocabulary: every in-flight gesture or anchored popover the
// SVG floorplan tracks as component state, plus the shared screen-pixel hit tolerances.
// Split from components/Canvas2D.tsx so the interaction hooks, the tool dispatch and the
// overlay layer all speak the same types without importing the component itself.
import type { Opening, Vec2, Wall } from "../../model/types";

export interface Pending {
  opening: Opening;
  field: "position" | "sill_height";
  initial: string;
}

// A two-click wall stroke in progress; `start` is already snapped.
export interface WallDraft {
  start: Vec2;
  startNode: string | null;
}

// A two-tap measurement. `start` is already snapped; `end` is null while the second tap is
// still pending (the canvas rubber-bands to the cursor), and set once the segment is fixed.
// A tap on a fixed segment starts the next measurement — nothing is ever written to the model.
export interface MeasureDraft {
  start: Vec2;
  end: Vec2 | null;
}

// A node being dragged (stretch). `tag` is the authored node tag the macro moves.
export interface NodeDrag {
  tag: string;
  from: Vec2;
  to: Vec2;
}

export interface OpeningDragPreview {
  opening: Opening;
  host: Wall;
  valid: boolean;
}

// A placement popover request (opening on a wall, or a room seed) anchored at screen px.
export type Placement =
  | { kind: "opening"; screen: Vec2; wall: Wall; along_m: number }
  | { kind: "placeable"; screen: Vec2; position: Vec2 }
  | { kind: "room"; screen: Vec2; seed: Vec2 };

// A read-only wall summary kept local to the canvas. The inspector remains the source for
// edits; this card only makes the essential assembly information available at the click.
export interface WallAssemblyPopup {
  wallUid: string;
  screen: Vec2;
}

// An opening settings popover request (door: type/handing; window: type), anchored at the
// opening's screen point.
export interface DoorPopup {
  opening: Opening;
  screen: Vec2;
}

// The live rubber-band of the wall tool: the snapped (and possibly ortho-locked) endpoint
// the next tap would commit, plus its length for the on-canvas readout and length keypad.
export interface RubberBand {
  end: Vec2;
  len: number;
}

// Exact-length entry for the wall being drawn (CAD precision): type a length and the next
// segment lands at that distance along the current rubber-band direction. `dir` is a unit
// vector captured when the keypad opens; committing draws start → start + dir·length.
export interface LengthEntry {
  start: Vec2;
  dir: Vec2;
  initial: string;
}

export const TAP_PX = 6; // pointer travel under this on up = a tap, not a pan
export const HIT_PX = 16; // wall pick tolerance in screen px
export const WARNING_MARKER_HIT_PX = 12; // diagnostic-marker pick tolerance (the dot is r=6.5)
