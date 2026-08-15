import { createHash } from "node:crypto";

// In-page probes for the screenshot harness. Each probe returns plain data; the judging
// happens in Node so a failure reports numbers rather than just "false".
//
// `blocking: false` means the probe is a tracked baseline that is expected to be red until a
// later stage fixes it — it is reported, but does not fail the run. Flipping one to blocking
// is how a stage's acceptance criterion gets locked in.

/** Tokens the chrome work must never move: the SVG drawing surfaces read them by name. */
const FROZEN_TOKENS = [
  "--bg", "--ink", "--line", "--accent",
  "--canvas-dim", "--canvas-white", "--canvas-wood", "--canvas-wood-soft",
  "--canvas-selection", "--canvas-grid",
  "--detail-ink", "--detail-line", "--detail-muted", "--detail-symbol", "--detail-batt",
  "--detail-rigid", "--detail-osb", "--detail-lumber", "--detail-concrete", "--detail-foam",
  "--detail-foam-dot",
  "--material-lumber", "--material-osb", "--material-rigid", "--material-batt",
  "--material-gypsum", "--material-membrane", "--material-siding", "--material-metal",
  "--material-concrete", "--material-masonry", "--material-fallback",
  "--control-air", "--control-water", "--control-vapor", "--control-thermal",
];

// A minimum touch target of 44 CSS px (WCAG 2.5.5 / MD3's 48dp floor rounded to the iOS
// guidance the rest of this codebase already cites at styles.css:2-3).
const MIN_TOUCH_TARGET_PX = 44;

/**
 * Horizontal overflow. The single most useful responsive check: if the document is wider
 * than the viewport, some control has been pushed off-screen and is unreachable.
 */
export const PROBE_OVERFLOW = `
  const el = document.documentElement;
  return { scrollWidth: el.scrollWidth, innerWidth: window.innerWidth };
`;

/**
 * Undersized interactive targets. Buttons inside a scroll container that is itself off-view
 * are skipped (zero-area rects) — only things a finger could actually be aiming at count.
 */
export const PROBE_TOUCH_TARGETS = `
  const undersized = [];
  for (const el of document.querySelectorAll("button, [role='menuitem'], [role='tab']")) {
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;               // not rendered
    if (rect.bottom < 0 || rect.top > window.innerHeight) continue;    // scrolled out
    if (rect.width >= ${MIN_TOUCH_TARGET_PX} && rect.height >= ${MIN_TOUCH_TARGET_PX}) continue;
    undersized.push({
      label: (el.getAttribute("title") || el.textContent || el.className || "?").trim().slice(0, 40),
      w: Math.round(rect.width), h: Math.round(rect.height),
    });
  }
  return undersized;
`;

/**
 * Controls clipped outside the viewport.
 *
 * This is the probe that actually measures the reported bug. `no-horizontal-overflow` does
 * NOT catch it: the top bar is a flex row that *clips* its overflowing children rather than
 * growing the document, so at 390px everything past ASSEMBLY — CIRCUITS, the 2D/3D toggle,
 * undo/redo, the theme control — is simply unreachable while the page reports no overflow.
 * Anchored elements deliberately parked off-screen (menus, closed sheets) have zero-area
 * rects and are skipped, so only genuinely-lost controls are reported.
 */
export const PROBE_CLIPPED_CONTROLS = `
  const clipped = [];
  for (const el of document.querySelectorAll("button, [role='menuitem'], select")) {
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;
    if (rect.right <= window.innerWidth && rect.left >= 0) continue;
    clipped.push({
      label: (el.getAttribute("title") || el.textContent || el.className || "?").trim().slice(0, 30),
      left: Math.round(rect.left), right: Math.round(rect.right),
    });
  }
  return clipped;
`;

/**
 * Drawing fingerprint. Deliberately NOT a pixel crop of the canvas: the canvas legitimately
 * changes size as chrome moves, so a crop would go red on every intentional layout change and
 * teach us to ignore it. Hashing the SVG markup (with the root's size attributes stripped)
 * plus the resolved values of the frozen tokens checks what actually must not change — the
 * geometry, the structure, and the colors — independent of how big the viewport made it.
 */
export const PROBE_DRAWING_FINGERPRINT = `
  const svg = document.querySelector(".canvas-svg");
  if (!svg) return null;
  const clone = svg.cloneNode(true);
  for (const attr of ["width", "height", "viewBox", "style"]) clone.removeAttribute(attr);
  const computed = getComputedStyle(document.documentElement);
  const tokens = {};
  for (const name of ${JSON.stringify(FROZEN_TOKENS)}) {
    tokens[name] = computed.getPropertyValue(name).trim();
  }
  return {
    markup: clone.outerHTML,
    tokens,
    // The engine's plan content hash — stable across server restarts, unlike revision
    // (a fresh uuid per process, which can never again equal a committed baseline once the
    // server has restarted even once). Without this the check cannot tell "the chrome moved
    // the drawing" from "somebody edited the house", and an unrelated plan edit lights up all
    // 34 shots as failures — which is how a guard gets ignored.
    contentHash: window.__haus?.store?.getState().model?.contentHash ?? null,
  };
`;

/** Where the 3D pane is on screen, so the runner can clip a screenshot to it. */
export const PROBE_THREE_PANE_RECT = `
  const canvas = document.querySelector(".pane canvas");
  if (!canvas) return null;
  const r = canvas.getBoundingClientRect();
  if (r.width < 8 || r.height < 8) return null;
  return { x: r.x, y: r.y, width: r.width, height: r.height };
`;

// A PNG of a uniformly-colored region compresses to almost nothing. An actually-rendered
// scene — Nordic shading plus edge linework — never does. Byte size is a crude signal, but
// it is the only one available without a PNG decoder, and it catches the failure that
// matters: Panel3D silently drawing nothing while every screenshot still "passes".
//
// This constant was derived by eyeballing a laptop-viewport (1600x1000, deviceScaleFactor 1)
// capture, so used as-is it is meaningless at other viewport sizes: the tablet pane clips far
// fewer pixels than the laptop pane, and the phone pane clips more pixels at 3x device scale —
// both would either false-fail or stop meaning anything against a fixed byte floor. Scaling it
// by the clipped area (in device pixels, i.e. CSS area x deviceScaleFactor^2) relative to the
// laptop viewport's own area keeps the same "did it actually render" signal at every size.
const MIN_RENDERED_3D_PNG_BYTES_AT_LAPTOP_REFERENCE = 12_000;
const LAPTOP_REFERENCE_WIDTH = 1600;
const LAPTOP_REFERENCE_HEIGHT = 1000;
const LAPTOP_REFERENCE_DEVICE_SCALE_FACTOR = 1;
const LAPTOP_REFERENCE_AREA =
  LAPTOP_REFERENCE_WIDTH * LAPTOP_REFERENCE_HEIGHT * LAPTOP_REFERENCE_DEVICE_SCALE_FACTOR ** 2;

function minRendered3dPngBytes(clipArea, deviceScaleFactor) {
  if (!clipArea) return MIN_RENDERED_3D_PNG_BYTES_AT_LAPTOP_REFERENCE;
  const deviceArea = clipArea * deviceScaleFactor ** 2;
  return MIN_RENDERED_3D_PNG_BYTES_AT_LAPTOP_REFERENCE * (deviceArea / LAPTOP_REFERENCE_AREA);
}

export function judge(shotName, probes, isPhone, baselineFingerprints, deviceScaleFactor = 1) {
  const results = [];
  const add = (id, ok, detail, blocking = true) =>
    results.push({ shot: shotName, id, ok, detail, blocking });

  const { scrollWidth, innerWidth } = probes.overflow;
  add(
    "no-horizontal-overflow",
    scrollWidth <= innerWidth + 1,
    `scrollWidth ${scrollWidth} vs viewport ${innerWidth}`,
  );

  const clipped = probes.clippedControls;
  add(
    "controls-reachable",
    clipped.length === 0,
    clipped.length === 0
      ? "no controls clipped off-viewport"
      : `${clipped.length} unreachable: `
        + clipped.slice(0, 6).map((c) => `${c.label}@${c.left}..${c.right}`).join(", "),
    // Red at phone/tablet until Stage 4 (Reports menu) and Stage 7 (compact breakpoint).
    false,
  );

  if (isPhone) {
    const undersized = probes.touchTargets;
    add(
      "touch-targets-44px",
      undersized.length === 0,
      undersized.length === 0
        ? "all targets >= 44px"
        : `${undersized.length} undersized: `
          + undersized.slice(0, 6).map((t) => `${t.label}(${t.w}x${t.h})`).join(", "),
      // Red until Stage 7 lands the compact breakpoint. Tracked, not blocking, so the
      // intervening stages can still go green on the checks they are responsible for.
      false,
    );
  }

  // The drawing must survive the chrome work untouched. Compared per-shot against a
  // committed digest rather than across viewports: the SVG legitimately renders a different
  // visible extent when the pane is a different size, so cross-viewport equality was never
  // the property we wanted — "this viewport draws the same thing it drew last stage" is.
  if (probes.fingerprint) {
    const digest = hashFingerprint(probes.fingerprint);
    probes.fingerprintDigest = digest;
    probes.modelContentHash = probes.fingerprint.contentHash;
    const baseline = baselineFingerprints[shotName];
    if (baseline !== undefined) {
      // A different content hash means the house's plan source itself changed, so the
      // digests are simply not comparable — say so rather than reporting a drawing regression.
      const staleModel = baseline.contentHash && probes.fingerprint.contentHash
        && baseline.contentHash !== probes.fingerprint.contentHash;
      if (staleModel) {
        add("drawing-unchanged", true,
          `plan content changed (${baseline.contentHash} -> ${probes.fingerprint.contentHash}); not comparable`);
      } else {
        add("drawing-unchanged", baseline.digest === digest,
          baseline.digest === digest ? "identical" : `digest ${baseline.digest} -> ${digest}`);
      }
    }
  }

  if (probes.threePng !== undefined && probes.threePng !== null) {
    const floor = minRendered3dPngBytes(probes.threeClipArea, deviceScaleFactor);
    add(
      "3d-pane-rendered",
      probes.threePng >= floor,
      `clipped 3D PNG ${probes.threePng} bytes (floor ${Math.round(floor)})`,
    );
  }

  return results;
}

export function hashFingerprint(fingerprint) {
  return createHash("sha256")
    .update(fingerprint.markup)
    .update(JSON.stringify(fingerprint.tokens))
    .digest("hex")
    .slice(0, 16);
}

/** True when the served house is not the one the baseline digests were taken against. */
export function modelContentChanged(fingerprint, baseline) {
  return Boolean(
    fingerprint?.contentHash && baseline?.contentHash
      && fingerprint.contentHash !== baseline.contentHash,
  );
}
