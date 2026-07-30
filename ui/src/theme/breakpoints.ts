/**
 * Viewport classes.
 *
 * Kept in sync by hand with the media queries in styles/tokens.css — there is no native
 * @custom-media, and generating CSS from TypeScript is not worth a build step for three
 * integers. The comment in tokens.css points back here.
 *
 * `compact` is 680, not MD3's 600: below roughly 680 the top bar's minimum useful content
 * and a 320px side panel stop being able to coexist, and that — not a spec table — is where
 * this layout actually breaks.
 */
export const BREAKPOINTS = {
  compact: 680,
  medium: 1024,
  expanded: 1440,
} as const;

export type Breakpoint = "compact" | "medium" | "expanded" | "large";

export function breakpointForWidth(width: number): Breakpoint {
  if (width < BREAKPOINTS.compact) return "compact";
  if (width < BREAKPOINTS.medium) return "medium";
  if (width < BREAKPOINTS.expanded) return "expanded";
  return "large";
}
