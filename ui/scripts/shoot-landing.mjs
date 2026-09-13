// Capture the three editor screenshots the marketing site publishes.
//
// These images were hand-captured once and then went six weeks stale with nobody able to
// say how they had been made — the whole reason this file exists. They are NOT the shot
// matrix: shoot.mjs photographs 42 states to judge the chrome against assertions and
// baselines, while these are three chosen frames at the exact size landing/index.html lays
// out. Sharing lib/ means the posing, the theme forcing and the "has it stopped moving yet"
// logic have one implementation, not two that drift.
//
// Usage (the engine must already be serving; `haus serve` serves ui/dist, so build first):
//   node scripts/shoot-landing.mjs
//   node scripts/shoot-landing.mjs --url http://127.0.0.1:8765
//   node scripts/shoot-landing.mjs --out ../landing/assets

import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  attachToPage, captureScreenshot, evaluate, launchChromium, navigate, setViewport,
} from "./lib/cdp.mjs";
import { AWAIT_STABLE_VIEW, POSE_PREAMBLE, WAIT_FOR_MODEL, awaitSettled, settle } from "./lib/shots.mjs";

const UI_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

// 1600x879 is what the committed images are and what index.html's layout was tuned against.
// Captured at the viewport rather than cropped from 1600x1000, so the app lays itself out
// for the frame that ships instead of being trimmed to fit it.
const VIEWPORT = { width: 1600, height: 879, deviceScaleFactor: 1, mobile: false };
// Dark: the site's hero sits on a dark ground, and a light shot reads as a hole in the page.
const THEME = "dark";

// Filenames are the contract — landing/index.html references each by name (and og:image
// points at editor-split.png), so these are overwritten in place, never renamed.
const SHOTS = [
  {
    file: "editor-plan-basement.png",
    storey: "basement",
    pose: `s.getState().setViewMode("2d");`,
    settled: `return !!document.querySelector(".canvas-svg");`,
  },
  {
    file: "editor-split.png",
    storey: "main",
    pose: `s.getState().setViewMode("split");`,
    // Both that the split grid exists AND that the plan pane has actually been laid out at
    // roughly half width — the DOM condition alone can hold a frame before the resize
    // reaches the SVG, which is how a "split" shot ends up being the single-pane fit.
    settled: `
      const stage = document.querySelector(".stage.split");
      const svg = document.querySelector(".canvas-svg");
      if (!stage || !svg || document.querySelectorAll(".pane").length !== 2) return false;
      return svg.getBoundingClientRect().width < window.innerWidth * 0.7;
    `,
  },
  {
    file: "editor-3d.png",
    storey: "main",
    pose: `s.getState().setViewMode("3d");`,
    settled: `return !document.querySelector(".canvas-svg");`,
  },
];

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? fallback : (args[index + 1] ?? fallback);
};
const targetUrl = flag("url", "http://127.0.0.1:8765");
const outDir = resolve(UI_ROOT, flag("out", "../landing/assets"));

/**
 * Force the theme BEFORE the page loads — see the same function in shoot.mjs. Poking
 * `documentElement.dataset.theme` after load loses the argument to theme.ts, which re-applies
 * the resolved preference on every useTheme mount.
 */
async function forceTheme(session, theme) {
  await session.send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-color-scheme", value: theme }],
  });
  await session.send("Page.addScriptToEvaluateOnNewDocument", {
    source: `window.localStorage.setItem("typehaus.theme-preference", ${JSON.stringify(theme)});`,
  });
}

// AWAIT_STABLE_VIEW throws rather than handing back a mid-motion frame, and a single
// transient miss (a resize still in flight, a late animation frame) is common enough that
// one retry is allowed before it counts. Same bargain shoot.mjs strikes.
async function withOneRetry(attempt) {
  try { return await attempt(); } catch { return await attempt(); }
}

// Named rather than positional: POSE_PREAMBLE resets to storeys[0], which happens to be the
// basement today. Two of these three shots want `main`, and a storey added ahead of the
// basement should not silently re-aim them.
const selectStorey = (tag) => `
  const storey = s.getState().model?.storeys?.find((x) => x.tag === ${JSON.stringify(tag)});
  if (!storey) throw new Error("no storey tagged ${tag} — did the house rename it?");
  s.getState().setActiveStorey(storey.tag);
`;

async function main() {
  await mkdir(outDir, { recursive: true });
  const { port, close } = await launchChromium();
  const session = await attachToPage(port);

  try {
    await setViewport(session, VIEWPORT);
    await forceTheme(session, THEME);
    await navigate(session, targetUrl);
    await evaluate(session, WAIT_FOR_MODEL);

    for (const shot of SHOTS) {
      const pose = `${POSE_PREAMBLE} ${selectStorey(shot.storey)} ${shot.pose} return true;`;
      await evaluate(session, pose);
      await settle(session);
      // Re-assert after settling: an effect running on mount can land after the pose and
      // quietly undo part of it. Every pose here is idempotent, so applying it twice is free.
      await evaluate(session, pose);
      await evaluate(session, awaitSettled(shot.settled));
      await settle(session);
      await withOneRetry(() => evaluate(session, AWAIT_STABLE_VIEW));
      await evaluate(session, awaitSettled(shot.settled));

      const png = await captureScreenshot(session);
      await writeFile(join(outDir, shot.file), png);
      console.log(`  ${shot.file}  ${VIEWPORT.width}x${VIEWPORT.height}  ${png.length} bytes`);
    }
    console.log(`\n${SHOTS.length} landing shots -> ${outDir}`);
  } finally {
    session.close();
    await close(); // waits for Chromium to die before removing its profile dir
  }
}

await main();
