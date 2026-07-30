import { useSyncExternalStore } from "react";
import { BREAKPOINTS, breakpointForWidth, type Breakpoint } from "../theme/breakpoints";

/**
 * The current viewport class, for the two things CSS genuinely cannot do:
 *
 *  1. Not mounting a component at all. The navigation rail and the bottom nav have different
 *     DOM, different aria-orientation and different focus order — rendering both and
 *     display:none-ing one would duplicate element ids and leave a hidden nav in the tab
 *     order.
 *  2. Behavioural coercions, like forcing the view off `split` on a phone.
 *
 * Everything that is merely a *style* stays in the media queries in tokens.css, which rewrite
 * the layout tokens; that reskins the whole shell with no re-render and no first-paint flash.
 *
 * useSyncExternalStore rather than useState+useEffect: one subscription, no tearing, and the
 * first render already has the right value instead of flashing the desktop layout.
 */

const QUERIES = [
  `(max-width: ${BREAKPOINTS.compact - 1}px)`,
  `(max-width: ${BREAKPOINTS.medium - 1}px)`,
  `(max-width: ${BREAKPOINTS.expanded - 1}px)`,
].map((query) => (typeof window === "undefined" ? null : window.matchMedia(query)));

function subscribe(onChange: () => void): () => void {
  for (const mq of QUERIES) mq?.addEventListener("change", onChange);
  return () => { for (const mq of QUERIES) mq?.removeEventListener("change", onChange); };
}

const getSnapshot = (): Breakpoint =>
  breakpointForWidth(typeof window === "undefined" ? BREAKPOINTS.expanded : window.innerWidth);

export function useBreakpoint(): Breakpoint {
  return useSyncExternalStore(subscribe, getSnapshot, () => "expanded" as Breakpoint);
}

/** Phone-class: the rail becomes a bottom bar and panels become sheets. */
export function useIsCompact(): boolean {
  return useBreakpoint() === "compact";
}
