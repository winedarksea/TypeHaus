// Authoring a detail annotation from the browser (→ 11b WP3, TODO "anchor-relative annotation
// drag → PatchOp editor").
//
// DetailCanvas can already drag an *authored* annotation and commit the move as a plain
// `update DetailAnnotation offset` PatchOp. What it could not do is produce one: a detail with
// no authored annotations draws only seed nodes, and a seed node carries `uid: null` — nothing
// to address, nothing to drag. This is the missing first step: turn a detail's elements into a
// valid anchor so `seed_detail_annotations` can mint a real DetailAnnotation, after which every
// further edit is the ordinary PatchOp path with no new machinery.
import type { Model } from "./types";

// The v1 wall anchor vocabulary (emit/draw/details.py::resolve_anchor):
// "top" | "bottom" | "ext-face" | "int-face" | "layer:<name>:out|in". A new note lands on the
// exterior face, which is the side a junction detail is almost always talking about and is the
// one face every wall has, whatever its assembly.
export const DEFAULT_ANNOTATION_ANCHOR_FACE = "ext-face";

export interface DetailAnnotationAnchor {
  anchor_uid: string;
  anchor_face: string;
}

/**
 * An anchor for a new note on the detail that cuts `elementTags`.
 *
 * A detail's index entry names its elements by authored *tag*; `resolve_anchor` wants the
 * minted *uid*, so this is the tag → uid hop, taking the first element that is a wall the model
 * still has. Null when none of them resolve — better no button than a note anchored to nothing,
 * which the engine would render with an "⚠ anchor?" flag.
 */
export function detailAnnotationAnchor(
  model: Model, elementTags: readonly string[],
): DetailAnnotationAnchor | null {
  for (const tag of elementTags) {
    const wall = model.walls.find((candidate) => candidate.tag === tag);
    if (wall) return { anchor_uid: wall.uid, anchor_face: DEFAULT_ANNOTATION_ANCHOR_FACE };
  }
  return null;
}

/** The spec `seed_detail_annotations` takes for one new note. */
export interface NewDetailAnnotationSpec {
  kind: string;
  anchor_uid: string;
  anchor_face: string;
  text: string;
  offset: [number, number];
}

/**
 * A note authored at the anchor itself (zero offset) — the drag is what moves it, and the drag
 * is stored anchor-relative, so starting at zero means the stored offset is exactly the
 * distance the user dragged it.
 */
export function newDetailAnnotationSpec(
  anchor: DetailAnnotationAnchor, text: string,
): NewDetailAnnotationSpec {
  return { kind: "note", ...anchor, text, offset: [0, 0] };
}
