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
  AWAIT_STABLE_VIEW, POSE_PREAMBLE, SETTLE, WAIT_FOR_MODEL, shotMatrix,
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
// Drawing digests, on the other hand, are committed for all 42 shots: they are 16 hex chars
// each, and they are the guardrail that the chrome work never moves the drawing.
const FINGERPRINTS_FILE = join(BASELINE_DIR, "fingerprints.json");

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? fallback : (args[index + 1] ?? true);
};
const targetUrl = flag("url", "http://127.0.0.1:8123");
const acceptBaselines = args.includes("--accept");

async function applyTheme(session, theme) {
  await evaluate(session, `
    document.documentElement.dataset.theme = ${JSON.stringify(theme)};
    window.localStorage.setItem("typehaus.theme-preference", ${JSON.stringify(theme)});
    return true;
  `);
}

async function poseAndProbe(session, shot) {
  await evaluate(session, `${POSE_PREAMBLE} ${shot.state.pose} return true;`);
  await evaluate(session, SETTLE);
  await evaluate(session, AWAIT_STABLE_VIEW);

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

async function compareBaselines() {
  if (!existsSync(BASELINE_DIR)) {
    console.log("\nNo committed baselines yet — run with --accept to create them.");
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
    ? `\nBaselines: all ${names.length} identical.`
    : `\nBaselines: ${changed} of ${names.length} changed (review .shots/, then --accept).`);
  return changed;
}

async function main() {
  await rm(SHOTS_DIR, { recursive: true, force: true });
  await mkdir(SHOTS_DIR, { recursive: true });

  const baselineFingerprints = existsSync(FINGERPRINTS_FILE)
    ? JSON.parse(await readFile(FINGERPRINTS_FILE, "utf8"))
    : {};
  const capturedFingerprints = {};

  const { child, port } = await launchChromium();
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
        await navigate(session, targetUrl);
        await applyTheme(session, shot.theme);
        await evaluate(session, WAIT_FOR_MODEL);
        currentTheme = shot.theme;
      }

      const probes = await poseAndProbe(session, shot);
      await writeFile(join(SHOTS_DIR, `${shot.name}.png`), await captureScreenshot(session));
      results.push(...judge(shot.name, probes, shot.viewport.mobile, baselineFingerprints));
      if (probes.fingerprintDigest) capturedFingerprints[shot.name] = probes.fingerprintDigest;
      process.stdout.write(".");
    }
    console.log(`\n\n${shots.length} shots -> ${SHOTS_DIR}`);
  } finally {
    session.close();
    child.kill();
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
