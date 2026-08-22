// Lettering constants shared with the engine — the TypeScript half of
// packages/engine/src/typehaus/emit/draw/typography.py.
//
// A drawing has two coordinate systems. Model space is the building, in inches, at whatever
// scale the sheet chose; paper space is the printed page, in inches, at 1:1. Text is the one
// thing that crosses: a note is not 1.6" of building, it is a fixed number of points of
// paper, and both renderers have to agree on the sizes or the same detail letters
// differently in the viewer than it prints.
//
// Its own module rather than a corner of DetailCanvas.tsx because a `.tsx` full of JSX is the
// wrong thing to import a JSON manifest into for a handful of constants — this module stays
// plain enough that the sizing values below are the only things anybody diffs.
// DetailCanvas re-exports these so existing imports keep resolving.
//
// The eight constants below are generated from emit/draw/typography.py — see
// packages/engine/src/typehaus/emit/vocabulary_manifest.py — and no longer authored here.
// Change a size in typography.py and regenerate ui/src/generated/vocabulary.json; do not
// hand-edit these values. `modelInPerPt`/`paperInPerModelIn`/`wrapColumnsFor` below are logic,
// not data, and stay hand-written in both languages on purpose
// (packages/engine/tests/test_typography_parity.py checks the arithmetic, not these values).
import vocabulary from "../generated/vocabulary.json";

// Monospace advance width as a fraction of cap height. Only ever used to reserve room.
export const CHAR_ASPECT: number = vocabulary.typography.CHAR_ASPECT;
// Vertical advance per text line, in multiples of the text height.
export const LINE_SPACING: number = vocabulary.typography.LINE_SPACING;
// The legibility floor at 300 dpi, points.
export const MIN_PT: number = vocabulary.typography.MIN_PT;
// Default printed sizes, points.
export const TEXT_PT: number = vocabulary.typography.TEXT_PT;
export const LEADER_TEXT_PT: number = vocabulary.typography.LEADER_TEXT_PT;
export const DIM_TEXT_PT: number = vocabulary.typography.DIM_TEXT_PT;
export const NOTES_PT: number = vocabulary.typography.NOTES_PT;
// Columns a long leader note wraps at.
export const LEADER_WRAP_COLUMNS: number = vocabulary.typography.LEADER_WRAP_COLUMNS;

// Model-space fallbacks, still in inches: what a node letters at when it carries no
// height_pt and there is no frame to convert one through. LEADER_TEXT_H matches
// scene.py Leader.height's default.
export const LEADER_TEXT_H = 1.6;
export const DIM_TEXT_H = 2.0;

// `scale` is what sheet_writer.ARCH_SCALES carries: paper inches per model foot (1.5 for
// 1-1/2" = 1'-0"). How many model inches one printed point covers at that scale:
export function modelInPerPt(scale: number): number {
  return 12.0 / scale / 72.0;
}

// How much paper one model inch takes up.
export function paperInPerModelIn(scale: number): number {
  return scale / 12.0;
}

// How many monospace characters fit across a `bandIn`-wide paper band at `sizePt`.
export function wrapColumnsFor(bandIn: number, sizePt: number): number {
  if (sizePt <= 0.0) return 1;
  return Math.max(1, Math.floor((bandIn * 72.0) / (sizePt * CHAR_ASPECT)));
}
