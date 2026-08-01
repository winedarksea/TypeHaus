// Screenshot + assertion harness for the editor chrome.
//
// There is no Playwright and no UI test runner in this repo, so this is the automated gate
// for the layout work: it captures the shot matrix at three viewports x two themes x seven
// app states, and runs the probes in lib/assertions.mjs against each one.
//
// Usage (the engine must already be serving; `haus serve` serves ui/dist, so build first):
//   npm run shots                       — capture + judge
//   npm run shots -- --accept           — also overwrite the committed baselines
//   npm run shots -- --url http://…     — point at a different engine
//
// See plans/ for the staging this gate belongs to.

import { mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  attachToPage, captureScreenshot, evaluate, launchChromium, navigate, setViewport,
} from "./lib/cdp.mjs";
import {
  AWAIT_STABLE_VIEW, POSE_PREAMBLE, WAIT_FOR_MODEL, awaitSettled, settle, shotMatrix,
} from "./lib/shots.mjs";
import {
  PROBE_CLIPPED_CONTROLS, PROBE_DRAWING_FINGERPRINT, PROBE_OVERFLOW, PROBE_THREE_PANE_RECT,
  PROBE_TOUCH_TARGETS, judge,
} from "./lib/assertions.mjs";

const UI_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SHOTS_DIR = join(UI_ROOT, ".shots");
// Only the laptop/light set is committed: enough to review a change in a diff, few enough
// that the repo does not accumulate 42 binaries per stage.
const BASELINE_DIR = join(UI_ROOT, "shots-baseline");
const BASELINE_PREFIX = "laptop-light-";
// Drawing digests, on the other hand, are committed for every shot — they are small, and
// they are the guardrail that the chrome work never moves the drawing. Each carries the
// engine's model revision so an unrelated house edit reads as "not comparable" rather than
// as 34 drawing regressions.
const FINGERPRINTS_FILE = join(BASELINE_DIR, "fingerprints.json");

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? fallback : (args[index + 1] ?? true);
};
const targetUrl = flag("url", "http://127.0.0.1:8765");
const acceptBaselines = args.includes("--accept");

/**
 * Force the theme, belt and braces, BEFORE the page loads.
 *
 * Poking `documentElement.dataset.theme` after load is not enough: theme.ts re-applies the
 * resolved preference whenever a component using useTheme mounts, so the app quietly wins the
 * argument and the shot comes out in the wrong theme — which shows up as a light shot hashing
 * identical to its dark twin. Instead, emulate the OS preference (which "system" reads) and
 * seed the explicit preference into localStorage before any script runs, so every path the
 * app might take agrees.
 */
let seededThemeScriptId = null;

async function forceTheme(session, theme) {
  await session.send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-color-scheme", value: theme }],
  });
  // Replace rather than stack: these registrations accumulate for the page's lifetime.
  if (seededThemeScriptId) {
    await session.send("Page.removeScriptToEvaluateOnNewDocument", { identifier: seededThemeScriptId });
  }
  const { identifier } = await session.send("Page.addScriptToEvaluateOnNewDocument", {
    source: `window.localStorage.setItem("typehaus.theme-preference", ${JSON.stringify(theme)});`,
  });
  seededThemeScriptId = identifier;
}

/**
 * Retry an async attempt once. AWAIT_STABLE_VIEW now throws on timeout instead of quietly
 * handing back a mid-motion frame (see lib/shots.mjs) — a single transient miss (a resize
 * still in flight, an animation frame that landed late) is common enough that failing the
 * whole run on the first timeout would be noisy, so one retry is allowed before it counts.
 */
async function withOneRetry(attempt) {
  try {
    return await attempt();
  } catch {
    return await attempt();
  }
}

async function poseAndProbe(session, shot) {
  const pose = `${POSE_PREAMBLE} ${shot.state.pose} return true;`;
  await evaluate(session, pose);
  await settle(session);
  // Re-assert after settling. An effect that runs on mount can land after the pose and
  // quietly undo part of it — that showed up as one state's drawing digest occasionally
  // matching another's. Every pose is idempotent, so applying it twice is free insurance.
  await evaluate(session, pose);
  if (shot.state.settled) await evaluate(session, awaitSettled(shot.state.settled));
  await settle(session);
  await withOneRetry(() => evaluate(session, AWAIT_STABLE_VIEW));
  // Re-check immediately before probing. Settling can complete and then be undone by a late
  // effect or a resize that had not reached the SVG yet; measuring a state that has since
  // stopped holding is how a shot ends up filed under the wrong name.
  if (shot.state.settled) await evaluate(session, awaitSettled(shot.state.settled));

  const probes = {
    overflow: await evaluate(session, PROBE_OVERFLOW),
    clippedControls: await evaluate(session, PROBE_CLIPPED_CONTROLS),
    touchTargets: shot.viewport.mobile ? await evaluate(session, PROBE_TOUCH_TARGETS) : [],
    fingerprint: await evaluate(session, PROBE_DRAWING_FINGERPRINT),
    threePng: null,
  };

  // Clip a PNG to the 3D canvas so its compressed size can stand in for "did it draw".
  const threeRect = await evaluate(session, PROBE_THREE_PANE_RECT);
  if (threeRect) {
    const { data } = await session.send("Page.captureScreenshot", {
      format: "png",
      clip: { ...threeRect, scale: 1 },
      captureBeyondViewport: false,
    });
    probes.threePng = Buffer.from(data, "base64").length;
    // So the byte-size floor can scale with how many pixels were actually clipped, rather
    // than assuming every viewport clips the same laptop-sized pane (see lib/assertions.mjs).
    probes.threeClipArea = threeRect.width * threeRect.height;
  }
  return probes;
}

function report(results) {
  const blocking = results.filter((r) => r.blocking);
  const failures = blocking.filter((r) => !r.ok);
  const tracked = results.filter((r) => !r.blocking && !r.ok);

  const byId = new Map();
  for (const r of blocking) {
    const entry = byId.get(r.id) ?? { pass: 0, fail: 0 };
    entry[r.ok ? "pass" : "fail"] += 1;
    byId.set(r.id, entry);
  }
  console.log("\nAssertions");
  for (const [id, { pass, fail }] of byId) {
    console.log(`  ${fail === 0 ? "PASS" : "FAIL"}  ${id}  ${pass} passed, ${fail} failed`);
  }

  if (tracked.length > 0) {
    console.log(`\nTracked (non-blocking) — ${tracked.length} findings:`);
    for (const r of tracked.slice(0, 8)) console.log(`  ~ ${r.shot}: ${r.id} — ${r.detail}`);
    if (tracked.length > 8) console.log(`  … and ${tracked.length - 8} more`);
  }

  if (failures.length > 0) {
    console.log(`\n${failures.length} blocking failures:`);
    for (const r of failures) console.log(`  x ${r.shot}: ${r.id} — ${r.detail}`);
  }
  return failures.length;
}

// This comparison is deliberately advisory, never blocking (it does not add to `results` and
// so cannot fail the run — see the header comment in main()). It is raw byte-equals against a
// laptop/light-only committed set, so it is fragile in ways the blocking assertions are not:
// host font rendering, subpixel AA and Chromium version drift can all flip a pixel with zero
// meaningful change to the drawing. Treat a "changed" line here as "go look", not as a defect.
async function compareBaselines() {
  console.log("\nBaseline PNG comparison — ADVISORY ONLY (raw byte-equals; laptop/light "
    + "reference set only; sensitive to host font rendering and Chromium version — not a "
    + "blocking gate, review before trusting a diff here):");
  if (!existsSync(BASELINE_DIR)) {
    console.log("  No committed baselines yet — run with --accept to create them.");
    return 0;
  }
  const names = (await readdir(BASELINE_DIR)).filter((n) => n.endsWith(".png"));
  let changed = 0;
  for (const name of names) {
    const [before, after] = await Promise.all([
      readFile(join(BASELINE_DIR, name)),
      readFile(join(SHOTS_DIR, name)).catch(() => null),
    ]);
    if (!after) { console.log(`  ? ${name} — not captured this run`); changed++; continue; }
    if (!before.equals(after)) { console.log(`  ~ ${name} — differs from baseline`); changed++; }
  }
  console.log(changed === 0
    ? `  All ${names.length} identical.`
    : `  ${changed} of ${names.length} changed (review .shots/, then --accept).`);
  return changed;
}

async function main() {
  await rm(SHOTS_DIR, { recursive: true, force: true });
  await mkdir(SHOTS_DIR, { recursive: true });

  const baselineFingerprints = existsSync(FINGERPRINTS_FILE)
    ? JSON.parse(await readFile(FINGERPRINTS_FILE, "utf8"))
    : {};
  const capturedFingerprints = {};

  const { port, close } = await launchChromium();
  const session = await attachToPage(port);
  const results = [];

  try {
    const shots = shotMatrix();
    let currentTheme = null;
    let currentViewport = null;

    for (const shot of shots) {
      if (currentViewport !== shot.viewport.id) {
        await setViewport(session, shot.viewport);
        currentViewport = shot.viewport.id;
        currentTheme = null;      // re-navigate below re-reads the theme from storage
      }
      if (currentTheme !== shot.theme) {
        await forceTheme(session, shot.theme);   // must precede the load, not follow it
        await navigate(session, targetUrl);
        await evaluate(session, WAIT_FOR_MODEL);
        currentTheme = shot.theme;
      }

      const probes = await poseAndProbe(session, shot);
      await writeFile(join(SHOTS_DIR, `${shot.name}.png`), await captureScreenshot(session));
      results.push(...judge(
        shot.name, probes, shot.viewport.mobile, baselineFingerprints, shot.viewport.deviceScaleFactor,
      ));
      if (probes.fingerprintDigest) {
        capturedFingerprints[shot.name] = { digest: probes.fingerprintDigest, revision: probes.modelRevision };
      }
      process.stdout.write(".");
    }
    console.log(`\n\n${shots.length} shots -> ${SHOTS_DIR}`);
  } finally {
    session.close();
    await close(); // waits for Chromium to die before removing its profile dir
  }

  const failureCount = report(results);

  if (acceptBaselines) {
    await mkdir(BASELINE_DIR, { recursive: true });
    const names = (await readdir(SHOTS_DIR)).filter((n) => n.startsWith(BASELINE_PREFIX));
    for (const name of names) {
      await writeFile(join(BASELINE_DIR, name), await readFile(join(SHOTS_DIR, name)));
    }
    await writeFile(FINGERPRINTS_FILE, `${JSON.stringify(capturedFingerprints, null, 2)}\n`);
    console.log(`\nAccepted ${names.length} baseline images`
      + ` + ${Object.keys(capturedFingerprints).length} drawing digests into shots-baseline/.`);
  } else {
    await compareBaselines();
  }

  process.exit(failureCount > 0 ? 1 : 0);
}

await main();
