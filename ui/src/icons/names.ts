/**
 * Every icon the chrome can draw.
 *
 * A string union rather than a bare string: TypeScript is the only automated gate this UI
 * has, so a mistyped icon name should be a build error rather than a silently blank button.
 */
export type IconName =
  // Navigation + panels
  | "menu"
  | "close"
  | "layers"
  | "folder"
  | "error"
  | "chevron-right"
  | "chevron-down"
  | "more-vertical"
  | "arrow-left"
  // Tools
  | "cursor"
  | "wall"
  | "room"
  | "stairs"
  | "opening"
  | "component"
  | "dimension"
  | "measure"
  | "framing"
  | "duplicate"
  | "delete"
  // Top bar
  | "undo"
  | "redo"
  | "search"
  | "install"
  | "report"
  | "view-2d"
  | "view-split"
  | "view-3d"
  // Canvas navigation
  | "zoom-in"
  | "zoom-out"
  // Preferences
  | "density-compact"
  | "density-comfortable"
  | "density-touch"
  | "theme-system"
  | "theme-light"
  | "theme-dark";
