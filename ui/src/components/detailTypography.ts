// Lettering constants shared with the engine — the TypeScript half of
// packages/engine/src/typehaus/emit/draw/typography.py.
//
// A drawing has two coordinate systems. Model space is the building, in inches, at whatever
// scale the sheet chose; paper space is the printed page, in inches, at 1:1. Text is the one
// thing that crosses: a note is not 1.6" of building, it is a fixed number of points of
// paper, and both renderers have to agree on the sizes or the same detail letters
// differently in the viewer than it prints.
//
// Its own module rather than a corner of DetailCanvas.tsx because
// packages/engine/tests/test_typography_parity.py reads this file as *text* and asserts
// every value matches the Python side — so a `.tsx` full of JSX is the wrong thing to point
// a regex at, and a drift here fails in the engine suite rather than only in a browser.
// DetailCanvas re-exports these so existing imports keep resolving.

// Monospace advance width as a fraction of cap height. Only ever used to reserve room.
export const CHAR_ASPECT = 0.62;
// Vertical advance per text line, in multiples of the text height.
export const LINE_SPACING = 1.4;
// The legibility floor at 300 dpi, points.
export const MIN_PT = 4.0;
// Default printed sizes, points.
export const TEXT_PT = 7.0;
export const LEADER_TEXT_PT = 7.0;
export const DIM_TEXT_PT = 6.5;
export const NOTES_PT = 9.0;
// Columns a long leader note wraps at.
export const LEADER_WRAP_COLUMNS = 40;

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
