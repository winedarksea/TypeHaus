import {
  CHAR_ASPECT, LEADER_TEXT_H, M_TO_IN, draggedOffsetMeters, leaderTextAlign, textExtents,
} from "./DetailCanvas";
import type { Model } from "../model/types";
import {
  DEFAULT_ANNOTATION_ANCHOR_FACE, detailAnnotationAnchor, newDetailAnnotationSpec,
} from "../model/detailAnnotations";

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

  // Leader note text grows away from its target (mirror of pdf_writer._leader_align): a
  // layer-ladder label left of the wall must be end-anchored or its lettering runs back
  // across the leader line into the drawing.
  if (leaderTextAlign([10, 0], [50, 0]) !== "end") {
    throw new Error("a note left of its target must be end-anchored");
  }
  if (leaderTextAlign([50, 0], [10, 0]) !== "start") {
    throw new Error("a note right of its target must be start-anchored");
  }
  if (leaderTextAlign([10, 0], [10, 0]) !== "start") {
    throw new Error("a note atop its target keeps the start-anchored default");
  }

  checkNewAnnotationAnchoring();
  checkTextExtents();
}

// The viewBox must reserve the room lettering occupies (port of pdf_writer._scene_bounds'
// text branch) — bounds over anchors alone crop the callout column off the panel's right
// edge, which is exactly how the notes/labels clipped in the v1 viewer.
function checkTextExtents() {
  const approx = (a: number, b: number) => Math.abs(a - b) < 1e-9;

  // Left-aligned text grows rightward from its anchor by chars × height × aspect.
  const t = textExtents({ node: "text", anchor: [10, 5], content: "abcde", height: 2 });
  if (!t || !approx(t.xs[0], 10) || !approx(t.xs[1], 10 + 5 * 2 * CHAR_ASPECT)) {
    throw new Error(`left text must grow right by len*h*aspect, got ${JSON.stringify(t)}`);
  }
  if (!approx(t.ys[0], 5 - 2) || !approx(t.ys[1], 5 + 2)) {
    throw new Error(`single-line text reserves ±height vertically, got ${JSON.stringify(t)}`);
  }

  // Right-aligned text grows leftward.
  const r = textExtents({ node: "text", anchor: [10, 5], content: "abcde", height: 2, align: "right" });
  if (!r || !approx(r.xs[0], 10 - 5 * 2 * CHAR_ASPECT) || !approx(r.xs[1], 10)) {
    throw new Error(`right text must grow left, got ${JSON.stringify(r)}`);
  }

  // Multi-line: width from the longest line, height stacked per line.
  const m = textExtents({ node: "text", anchor: [0, 0], content: "abc\nabcdef", height: 1 });
  if (!m || !approx(m.xs[1], 6 * CHAR_ASPECT) || !approx(m.ys[0], -2) || !approx(m.ys[1], 2)) {
    throw new Error(`multi-line extents use max line + line count, got ${JSON.stringify(m)}`);
  }

  // A leader left of its target is end-anchored, so its text grows leftward from `at`;
  // without an explicit height it letters at the shared LEADER_TEXT_H default.
  const l = textExtents({ node: "leader", at: [10, 0], to: [50, 0], text: "abcde" });
  if (!l || !approx(l.xs[1], 10) || !approx(l.xs[0], 10 - 5 * LEADER_TEXT_H * CHAR_ASPECT)) {
    throw new Error(`end-anchored leader text must grow left of at, got ${JSON.stringify(l)}`);
  }

  // Non-text nodes contribute no lettering extents.
  if (textExtents({ node: "polyline", points: [[0, 0], [1, 1]] }) !== null) {
    throw new Error("non-text nodes must yield no text extents");
  }
}

// A detail's own callouts are seeds with `uid: null` — unaddressable, so undraggable. The
// editor only becomes reachable once a detail can mint an *authored* annotation, which needs a
// resolvable anchor: the index entry names its elements by tag, `resolve_anchor` wants the uid.
function checkNewAnnotationAnchoring() {
  const model = {
    walls: [
      { uid: "W1AAAAAAAA", tag: "W-B-E1" },
      { uid: "W2AAAAAAAA", tag: "W-B-E2" },
    ],
  } as unknown as Model;

  const anchor = detailAnnotationAnchor(model, ["W-B-E1", "W-B-E2"]);
  if (anchor?.anchor_uid !== "W1AAAAAAAA") {
    throw new Error(`the anchor must be the first element's minted uid, got ${anchor?.anchor_uid}`);
  }
  if (anchor.anchor_face !== DEFAULT_ANNOTATION_ANCHOR_FACE) {
    throw new Error(`a new note anchors to a face resolve_anchor knows, got ${anchor.anchor_face}`);
  }

  // A detail whose elements are not walls this model still has must offer no anchor at all,
  // rather than an annotation the engine would draw with an "⚠ anchor?" flag.
  if (detailAnnotationAnchor(model, ["W-GONE"]) !== null) {
    throw new Error("an unresolvable element list must yield no anchor");
  }
  if (detailAnnotationAnchor(model, []) !== null) {
    throw new Error("a detail with no elements must yield no anchor");
  }
  // Skips past an element the model dropped rather than giving up on the whole detail.
  if (detailAnnotationAnchor(model, ["W-GONE", "W-B-E2"])?.anchor_uid !== "W2AAAAAAAA") {
    throw new Error("the anchor falls through to the first element that still resolves");
  }

  // A new note starts *at* its anchor: the drag is stored anchor-relative, so a zero start
  // means the committed offset is exactly the distance the user dragged.
  const spec = newDetailAnnotationSpec(anchor, "  drip edge  ".trim());
  if (spec.offset[0] !== 0 || spec.offset[1] !== 0) {
    throw new Error(`a new note starts at its anchor, got ${spec.offset}`);
  }
  if (spec.kind !== "note" || spec.text !== "drip edge" || spec.anchor_uid !== "W1AAAAAAAA") {
    throw new Error(`the macro spec must carry kind/text/anchor, got ${JSON.stringify(spec)}`);
  }
}
