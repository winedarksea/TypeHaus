import type { ReactNode } from "react";
import type { IconName } from "./names";

/**
 * Icon geometry, hand-authored on a 24x24 grid in the Material 24dp idiom: 2px strokes,
 * round caps and joins, shapes aligned to even coordinates so they stay crisp at 1x.
 *
 * Drawn rather than copied from an icon font for two reasons. The zero-dependency rule rules
 * out a package, and self-hosting Material Symbols as a webfont costs 300KB+ for the ~30
 * glyphs used here. Authoring them from primitives also means each one can be checked by
 * reading it, which a 300-character path string cannot.
 *
 * What this replaces is the real problem: the chrome previously drew its icons as Unicode
 * glyphs (⌖ ▟ ❒ ▦ ↔ ☰ ▪ ▫ ▢), which come from different Unicode blocks, resolve through
 * different fallback fonts, and therefore cannot be made to match each other at any size —
 * besides rendering as tofu on Android and older Safari.
 *
 * `stroke` and `fill` are set on the <svg> by Icon.tsx, so nothing here names a color.
 */
export const ICON_PATHS: Record<IconName, ReactNode> = {
  // ── Navigation + panels ──────────────────────────────────────────────────
  menu: <><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></>,
  close: <><path d="M6 6l12 12" /><path d="M18 6L6 18" /></>,
  // Stacked sheets — the view/visibility panel.
  layers: <><path d="M12 3l9 5-9 5-9-5 9-5z" /><path d="M3 13l9 5 9-5" /></>,
  folder: <path d="M3 6a1 1 0 011-1h5l2 2h9a1 1 0 011 1v10a1 1 0 01-1 1H4a1 1 0 01-1-1V6z" />,
  error: <><circle cx="12" cy="12" r="9" /><path d="M12 7v6" /><path d="M12 16.5v.5" /></>,
  "chevron-right": <path d="M9 5l7 7-7 7" />,
  "chevron-down": <path d="M5 9l7 7 7-7" />,
  "more-vertical": (
    <><circle cx="12" cy="5" r="1.4" /><circle cx="12" cy="12" r="1.4" /><circle cx="12" cy="19" r="1.4" /></>
  ),
  "arrow-left": <><path d="M20 12H4" /><path d="M10 6l-6 6 6 6" /></>,

  // ── Tools ────────────────────────────────────────────────────────────────
  cursor: <><path d="M12 4v4" /><path d="M12 16v4" /><path d="M4 12h4" /><path d="M16 12h4" /><circle cx="12" cy="12" r="3" /></>,
  // A wall in plan: two parallel faces with their cavity implied between.
  wall: <><rect x="3" y="9" width="18" height="6" rx="0.5" /><path d="M3 12h18" /></>,
  room: <><rect x="4" y="4" width="16" height="16" rx="1" /><path d="M8 20v-6h8v6" /></>,
  stairs: <path d="M4 20h4v-4h4v-4h4V8h4" />,
  // A door swing — the opening tool covers both windows and doors.
  opening: <><path d="M5 20V5h8v15" /><path d="M13 20a8 8 0 00-8-8" /></>,
  component: <><rect x="3" y="3" width="8" height="8" rx="1" /><rect x="13" y="3" width="8" height="8" rx="1" /><rect x="3" y="13" width="8" height="8" rx="1" /><rect x="13" y="13" width="8" height="8" rx="1" /></>,
  dimension: <><path d="M4 8v8" /><path d="M20 8v8" /><path d="M4 12h16" /></>,
  measure: <><path d="M3 12h18" /><path d="M7 8l-4 4 4 4" /><path d="M17 8l4 4-4 4" /></>,
  // Stud bay repetition — the framed-floorplan toggle.
  framing: <><rect x="3" y="4" width="18" height="16" rx="1" /><path d="M8 4v16" /><path d="M13 4v16" /><path d="M18 4v16" /></>,
  duplicate: <><rect x="9" y="9" width="12" height="12" rx="1.5" /><path d="M6 15H4a1 1 0 01-1-1V4a1 1 0 011-1h10a1 1 0 011 1v2" /></>,
  delete: <><path d="M4 7h16" /><path d="M10 11v6" /><path d="M14 11v6" /><path d="M6 7l1 13h10l1-13" /><path d="M9 7V4h6v3" /></>,

  // ── Top bar ──────────────────────────────────────────────────────────────
  undo: <><path d="M4 9h11a5 5 0 010 10h-6" /><path d="M8 5L4 9l4 4" /></>,
  redo: <><path d="M20 9H9a5 5 0 000 10h6" /><path d="M16 5l4 4-4 4" /></>,
  search: <><circle cx="11" cy="11" r="6" /><path d="M20 20l-4.5-4.5" /></>,
  install: <><path d="M12 4v10" /><path d="M8 11l4 4 4-4" /><path d="M4 19h16" /></>,
  // A schedule/table — the readers are all tabular.
  report: <><rect x="4" y="3" width="16" height="18" rx="1.5" /><path d="M8 8h8" /><path d="M8 12h8" /><path d="M8 16h5" /></>,
  "view-2d": <><rect x="3" y="4" width="18" height="16" rx="1" /><path d="M3 9h18" /><path d="M9 9v11" /></>,
  "view-split": <><rect x="3" y="4" width="18" height="16" rx="1" /><path d="M12 4v16" /></>,
  "view-3d": <><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" /><path d="M12 12l8-4.5" /><path d="M12 12v9" /><path d="M12 12L4 7.5" /></>,

  // ── Canvas navigation ────────────────────────────────────────────────────
  // The `search` lens with a sign in it, so the zoom pair reads as one family with it.
  "zoom-in": <><circle cx="11" cy="11" r="6" /><path d="M20 20l-4.5-4.5" /><path d="M8 11h6" /><path d="M11 8v6" /></>,
  "zoom-out": <><circle cx="11" cy="11" r="6" /><path d="M20 20l-4.5-4.5" /><path d="M8 11h6" /></>,

  // ── Preferences ──────────────────────────────────────────────────────────
  // Density reads as row spacing: the same rows, further apart.
  "density-compact": <><path d="M4 7h16" /><path d="M4 10.5h16" /><path d="M4 14h16" /><path d="M4 17.5h16" /></>,
  "density-comfortable": <><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></>,
  "density-touch": <><path d="M4 8h16" /><path d="M4 16h16" /></>,
  "theme-system": <><circle cx="12" cy="12" r="8" /><path d="M12 4a8 8 0 010 16z" fill="currentColor" stroke="none" /></>,
  "theme-light": (
    <><circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="M2 12h2" />
      <path d="M20 12h2" /><path d="M5 5l1.5 1.5" /><path d="M17.5 17.5L19 19" /><path d="M19 5l-1.5 1.5" />
      <path d="M6.5 17.5L5 19" /></>
  ),
  "theme-dark": <path d="M20 14.5A8.5 8.5 0 019.5 4a8.5 8.5 0 100 17 8.5 8.5 0 0010.5-6.5z" />,
};
