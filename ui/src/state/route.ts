// Hash routing, and it exists for exactly one reason: the PWA icon on a phone has to open
// the board, not the design workbench.
//
// The app has had no URL handling at all — every surface is store state — and this is
// deliberately the smallest thing that changes that. Two site pages get a hash; the design
// surface keeps an empty one, so nothing about the existing app's addresses changes.

import type { SitePage, Surface } from "./site";

export interface RouteState {
  surface: Surface;
  sitePage: SitePage;
}

const SITE_PAGES: SitePage[] = ["board", "inspections"];

/** `#/site/board` -> the route it names, or null for anything this app does not own. */
export function parseHash(hash: string): RouteState | null {
  const path = hash.replace(/^#\/?/, "").replace(/\/$/, "");
  if (path === "" || path === "design") return { surface: "design", sitePage: "board" };
  const parts = path.split("/");
  if (parts[0] !== "site") return null;
  const page = parts[1] as SitePage | undefined;
  return {
    surface: "site",
    sitePage: page && SITE_PAGES.includes(page) ? page : "board",
  };
}

export function hashFor(state: RouteState): string {
  return state.surface === "site" ? `#/site/${state.sitePage}` : "";
}

interface RoutableStore {
  getState: () => RouteState & {
    setSurface: (surface: Surface) => void;
    setSitePage: (page: SitePage) => void;
  };
  subscribe: (listener: (state: RouteState) => void) => () => void;
}

/**
 * Keep `location.hash` and the store's surface in step, in both directions.
 *
 * Installed once from main.tsx before the first render, so a cold load of `#/site/board`
 * never paints the design workbench first — which would mount the canvas and fetch the
 * three.js chunk on a phone that is not going to use either.
 */
export function installRouteSync(store: RoutableStore): () => void {
  const fromHash = () => {
    const route = parseHash(window.location.hash);
    if (!route) return;
    const state = store.getState();
    if (state.surface !== route.surface) state.setSurface(route.surface);
    if (state.sitePage !== route.sitePage) state.setSitePage(route.sitePage);
  };

  fromHash();

  const unsubscribe = store.subscribe((state) => {
    const next = hashFor({ surface: state.surface, sitePage: state.sitePage });
    if (next === window.location.hash) return;
    if (next === "" && window.location.hash === "") return;
    // replaceState, not a hash assignment: the surface switch is a mode, not a page in the
    // history the back button walks. The one navigation that IS history is the phone's own
    // back gesture out of the app.
    window.history.replaceState(null, "", next || window.location.pathname);
  });

  window.addEventListener("hashchange", fromHash);
  return () => {
    unsubscribe();
    window.removeEventListener("hashchange", fromHash);
  };
}
