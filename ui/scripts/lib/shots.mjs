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
  { id: "reader-circuits", pose: `s.getState().setDetailView("circuits");`,
    settled: `return !!document.querySelector(".workbench");` },
  // The estimate reader fetches /costs before it can draw anything, so "the workbench
  // exists" is not enough here — the shot would catch the empty shell. Wait for a group
  // header, which only exists once the payload has been ranked.
  { id: "reader-estimate", pose: `s.getState().setDetailView("estimate");`,
    settled: `return !!document.querySelector(".estimate-group-head, .estimate-warn");` },
  // Split does not exist at compact — the app coerces it to 2D, because two ~195px panes
  // render the plan illegibly. Photographing it there would just capture the 2D state under
  // a misleading name, and its digest would drift with whatever 2D happened to be doing.
  {
    id: "split",
    pose: `s.getState().setViewMode("split");`,
    // Setting store state is not the same as the layout having happened. Waiting for the
    // split grid to actually exist is what stops this shot from occasionally capturing the
    // single-pane fit and hashing identical to `default`.
    // Both that the split grid exists AND that the plan pane has actually been laid out at
    // roughly half width. The DOM condition alone can be true a frame before the resize
    // reaches the SVG, which is when this shot captured the single-pane fit and hashed
    // identical to `default`.
    settled: `
      const stage = document.querySelector(".stage.split");
      const svg = document.querySelector(".canvas-svg");
      if (!stage || !svg || document.querySelectorAll(".pane").length !== 2) return false;
      return svg.getBoundingClientRect().width < window.innerWidth * 0.7;
    `,
    skipCompact: true,
  },
  {
    id: "three-d",
    pose: `s.getState().setViewMode("3d");`,
    settled: `return !document.querySelector(".canvas-svg");`,
  },
];

/** Every shot in the matrix, as {name, viewport, theme, state}. */
export function shotMatrix() {
  const shots = [];
  for (const viewport of VIEWPORTS) {
    for (const theme of THEMES) {
      for (const state of STATES) {
        if (state.skipCompact && viewport.mobile) continue;
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

  // Panel posing indirection — see STATES above. Writes the state directly rather than
  // calling setActivePanel, because that setter toggles: posing the same panel twice would
  // close it, which makes the pose non-idempotent and therefore not safe to re-assert.
  const openPanel = (id) => { s.setState({ activePanel: id }); };

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
  // The pane's size is part of the signal, not just the transform. Switching to split
  // halves the pane, which triggers the ResizeObserver, which refits — but the refit has
  // not necessarily *started* by the time this begins polling, so watching the transform
  // alone could report "stable" while still holding the full-width 2D fit. That is what
  // made split shots occasionally hash identical to their default twin.
  const read = () => {
    const svg = document.querySelector(".canvas-svg");
    const rect = svg ? svg.getBoundingClientRect() : { width: 0, height: 0 };
    return JSON.stringify([
      window.__haus.store.getState().view,
      Math.round(rect.width),
      Math.round(rect.height),
    ]);
  };
  let previous = read();
  let stableFrames = 0;
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline && stableFrames < 8) {
    await new Promise((r) => requestAnimationFrame(r));
    const current = read();
    stableFrames = current === previous ? stableFrames + 1 : 0;
    previous = current;
  }
  // A timed-out wait must not silently hand back whatever frame happened to be current —
  // that is exactly how a mid-animation frame used to flow into the blocking fingerprint.
  // The caller is expected to retry once rather than treat this as fatal on the first miss.
  if (stableFrames < 8) throw new Error(\`View never stabilized (AWAIT_STABLE_VIEW timed out): \${previous}\`);
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

const SETTLE_BEAT_MS = 350;
const SETTLE_DEADLINE_MS = 5000;

/**
 * The in-page probe a settle attempt compares. Deliberately NOT a pixel screenshot: an actual
 * capture-compare-by-PNG-bytes was tried here first and it does not work in this app — a
 * software (swiftshader) 3D render and CSS panel-open transitions mean *something* is
 * legitimately still moving often enough that two full-page captures came back byte-identical
 * only by luck, and one state (a panel mid-transition) never converged inside the deadline at
 * all. What SETTLE actually needs to know is "did React commit and has nothing left mid-flight" —
 * DOM size, any Web Animations API animation/transition still `running`, and the document's
 * own box all answer that without needing pixels, and are exactly reproducible frame to frame.
 */
const SETTLE_PROBE = `
  JSON.stringify({
    html: document.body.innerHTML.length,
    animating: Array.from(document.getAnimations()).some((a) => a.playState === "running"),
    rect: (() => {
      const r = document.documentElement.getBoundingClientRect();
      return [Math.round(r.width), Math.round(r.height)];
    })(),
  })
`;

/**
 * Two animation frames, then a capture-compare loop: repeatedly probe the page and wait for
 * two consecutive probes to come back identical before calling it settled.
 *
 * The previous version raced a flat 350ms against React's commit + three.js's first draw — on
 * a slow run that beat could elapse mid-animation and the harness would photograph a
 * transitional frame without ever knowing it. Comparing actual probes means "settled" is
 * verified rather than assumed; 350ms is kept as the beat between attempts, not as the whole
 * budget. `session` is the CDP session (see lib/cdp.mjs).
 */
export async function settle(session) {
  await session.send("Runtime.evaluate", {
    expression: "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))",
    awaitPromise: true,
  });
  const deadline = Date.now() + SETTLE_DEADLINE_MS;
  let previous = null;
  while (Date.now() < deadline) {
    const result = await session.send("Runtime.evaluate", {
      expression: SETTLE_PROBE,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      const detail = result.exceptionDetails.exception?.description ?? result.exceptionDetails.text;
      throw new Error(`SETTLE probe threw: ${detail}`);
    }
    const current = result.result.value;
    if (previous !== null && previous === current) return;
    previous = current;
    await new Promise((r) => setTimeout(r, SETTLE_BEAT_MS));
  }
  throw new Error(`View never settled (SETTLE deadline exceeded): ${previous}`);
}

/** Poll a state's `settled` predicate until the DOM actually reflects the pose. */
export function awaitSettled(predicate) {
  return `
    const check = () => { ${predicate} };
    const deadline = Date.now() + 5000;
    while (Date.now() < deadline) {
      if (check()) return true;
      await new Promise((r) => requestAnimationFrame(r));
    }
    throw new Error("Pose never became observable in the DOM");
  `;
}

