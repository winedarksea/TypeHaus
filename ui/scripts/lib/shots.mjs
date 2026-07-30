// The shot matrix: which viewports, themes and app states get captured.
//
// States are posed through the store (`window.__haus.store`, set up in src/main.tsx) rather
// than by clicking chrome, because the chrome is what the layout work rewrites — a harness
// that clicks "Views ▾" stops working exactly when it is needed to prove nothing broke.

export const VIEWPORTS = [
  { id: "laptop", width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false },
  { id: "tablet", width: 1024, height: 768, deviceScaleFactor: 1, mobile: false },
  { id: "phone", width: 390, height: 844, deviceScaleFactor: 3, mobile: true },
];

export const THEMES = ["light", "dark"];


/**
 * Page-side state posing. Each entry is a JS snippet evaluated with `s` bound to the store
 * API. Kept as source strings (not functions) so the whole pose is visible in one place.
 *
 * `panel` is routed through a helper rather than written inline because Stage 5 replaces the
 * three panel booleans with a single `activePanel` enum — one edit here, not seven.
 */
export const STATES = [
  { id: "default", pose: `` },
  { id: "views", pose: `openPanel("views");` },
  { id: "project", pose: `openPanel("project");` },
  { id: "inspector", pose: `selectFirstWall();` },
  { id: "reader-circuits", pose: `s.getState().setDetailView("circuits");` },
  { id: "split", pose: `s.getState().setViewMode("split");` },
  { id: "three-d", pose: `s.getState().setViewMode("3d");` },
];

/** Every shot in the matrix, as {name, viewport, theme, state}. */
export function shotMatrix() {
  const shots = [];
  for (const viewport of VIEWPORTS) {
    for (const theme of THEMES) {
      for (const state of STATES) {
        shots.push({ name: `${viewport.id}-${theme}-${state.id}`, viewport, theme, state });
      }
    }
  }
  return shots;
}

/** In-page preamble: helpers + a deterministic baseline the pose snippets build on. */
export const POSE_PREAMBLE = `
  const s = window.__haus?.store;
  if (!s) throw new Error("window.__haus missing — is this a build with the harness hook?");

  // Panel posing indirection — see STATES above.
  const openPanel = (id) => {
    const state = s.getState();
    if (state.setActivePanel) { state.setActivePanel(id); return; }
    state.setProjectDrawerOpen(id === "project");
    state.setViewsPanelOpen(id === "views");
    state.setIssuesDrawerOpen(id === "issues");
  };

  const selectFirstWall = () => {
    const wall = s.getState().model?.walls?.[0];
    if (wall) s.getState().select("wall", wall.uid);
  };

  // Reset to a known baseline so shots never inherit the previous pose.
  const reset = s.getState();
  openPanel(null);
  reset.setDetailView("none");
  reset.setViewMode("2d");
  reset.setTool("select");
  reset.setActiveLens("none");
  reset.setWorkbench(null);
  reset.setCommandPaletteOpen(false);
  reset.setPreview3DOpen(false);
  reset.select(null, null);
  reset.clearToasts();
  reset.setActiveStorey(reset.model?.storeys?.[0]?.tag ?? null);
`;

/**
 * Wait for the plan's view transform to stop moving.
 *
 * usePanZoom fits the plan once per storey from a ResizeObserver callback
 * (usePanZoom.ts:47-81), so the view keeps changing for an indeterminate beat after the pose.
 * An early attempt pinned an arbitrary transform instead — that raced the fit (one shot's
 * digest flickered between runs) and framed the plan badly, which matters because these
 * images are meant to be reviewed. Letting the app's own fit run and waiting for it to settle
 * gives both a well-framed shot and a stable digest; the fingerprint baseline is keyed per
 * shot name, so the fit being viewport-dependent is expected rather than a problem.
 */
export const AWAIT_STABLE_VIEW = `
  const read = () => JSON.stringify(window.__haus.store.getState().view);
  let previous = read();
  let stableFrames = 0;
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline && stableFrames < 5) {
    await new Promise((r) => requestAnimationFrame(r));
    const current = read();
    stableFrames = current === previous ? stableFrames + 1 : 0;
    previous = current;
  }
  return previous;
`;

/** Resolves once the engine model has landed; without it early shots capture "Loading model…". */
export const WAIT_FOR_MODEL = `
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    const state = window.__haus?.store?.getState();
    if (state?.model) return true;
    if (state?.error) throw new Error("Engine unreachable: " + state.error);
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("Model never loaded");
`;

/** Two animation frames + a settle beat: React commit, then three.js draws at least once. */
export const SETTLE = `
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  await new Promise((r) => setTimeout(r, 350));
  return true;
`;
