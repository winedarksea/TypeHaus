// Minimal Chrome DevTools Protocol client for the screenshot harness.
//
// Deliberately not puppeteer: the repo carries exactly four runtime deps and adding a
// 300MB browser-automation package to take screenshots is not a trade worth making. Node's
// global WebSocket (>= 22) covers the whole protocol surface we need.

import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// Chromium needs a real GL backend or Panel3D renders nothing — `--disable-gpu` yields a
// blank 3D pane with no error anywhere, so swiftshader is mandatory, not an optimization.
const CHROMIUM_FLAGS = [
  "--headless=new",
  "--use-gl=angle",
  "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader",
  "--hide-scrollbars",
  "--force-device-scale-factor=1",
  "--no-first-run",
  "--no-default-browser-check",
];

const CHROMIUM_CANDIDATES = [
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  `${process.env.HOME}/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/`
    + "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
];

function findChromiumBinary() {
  const found = CHROMIUM_CANDIDATES.find((candidate) => existsSync(candidate));
  if (!found) {
    throw new Error(
      `No Chromium found. Looked in:\n  ${CHROMIUM_CANDIDATES.join("\n  ")}`,
    );
  }
  return found;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForDevToolsEndpoint(port, timeoutMs = 20_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (response.ok) return await response.json();
    } catch (error) {
      lastError = error;
    }
    await sleep(150);
  }
  throw new Error(`DevTools endpoint never came up on :${port} (${lastError?.message})`);
}

/**
 * A fresh profile per run, always.
 *
 * This app registers a service worker, and a reused --user-data-dir keeps that worker
 * and its asset cache alive across runs — so the harness ends up photographing a mixture
 * of the current build and a previously-cached one. It presents as digests that shift on
 * every run and states that hash identically to each other, which reads like a flaky app
 * rather than a poisoned browser profile. Combined with Network.setBypassServiceWorker
 * below, every run now sees exactly what the server is serving.
 */
export async function launchChromium({ port = 9222, userDataDir = null } = {}) {
  // Only a dir *we* mkdtemp'd is ours to delete. A caller-supplied --user-data-dir is theirs —
  // removing it out from under them would be a much worse bug than the leak this fixes.
  const ownsProfileDir = userDataDir == null;
  const profileDir = userDataDir ?? mkdtempSync(join(tmpdir(), "haus-shots-"));

  let cleanedUp = false;
  const cleanupProfileDir = () => {
    if (!ownsProfileDir || cleanedUp) return;
    cleanedUp = true;
    rmSync(profileDir, { recursive: true, force: true });
  };
  // Armed here, *before* the launch can fail. A Chromium that never comes up throws out of
  // waitForDevToolsEndpoint below, and arming after that await is how the small 4-entry
  // profile dirs leaked. "exit" alone is not enough either: it does not fire for SIGINT or
  // SIGTERM, so a Ctrl-C mid-run leaked a full profile. Handlers must be synchronous, which
  // is exactly what rmSync gives us; the signal handlers re-raise so the exit code is honest.
  if (ownsProfileDir) {
    process.on("exit", cleanupProfileDir);
    for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) {
      process.on(signal, () => {
        cleanupProfileDir();
        process.exit(signal === "SIGINT" ? 130 : 143);
      });
    }
  }

  const binary = findChromiumBinary();
  const child = spawn(
    binary,
    [...CHROMIUM_FLAGS, `--remote-debugging-port=${port}`, `--user-data-dir=${profileDir}`, "about:blank"],
    { stdio: "ignore", detached: false },
  );
  const version = await waitForDevToolsEndpoint(port);

  /** Kill the browser, wait for it to actually die, then remove its profile dir.
   *
   * The wait is not ceremony: Chromium keeps writing its profile as it shuts down, so
   * removing the tree the instant after `kill()` races those final writes and they simply
   * recreate the directory behind us — which is why a "cleaned up" run still left a
   * 39-entry `haus-shots-*` dir. Bounded, because a browser that will not die must not hang
   * the harness; the "exit" handler above is the backstop if we give up waiting.
   */
  const close = async () => {
    if (child.exitCode === null && child.signalCode === null) {
      const dead = new Promise((resolve) => child.once("exit", resolve));
      child.kill();
      await Promise.race([dead, new Promise((resolve) => setTimeout(resolve, 3000))]);
    }
    cleanupProfileDir();
  };

  return { child, port, version, profileDir, close };
}

/** Attach to the browser's first page target and return a request/response session. */
export async function attachToPage(port) {
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const page = targets.find((target) => target.type === "page");
  if (!page) throw new Error("No page target to attach to");

  const socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", () => reject(new Error("CDP socket failed to open")), { once: true });
  });

  let nextMessageId = 1;
  const pending = new Map();
  const eventListeners = new Map();

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id !== undefined) {
      const settle = pending.get(message.id);
      if (!settle) return;
      pending.delete(message.id);
      if (message.error) settle.reject(new Error(`${settle.method}: ${message.error.message}`));
      else settle.resolve(message.result);
      return;
    }
    for (const listener of eventListeners.get(message.method) ?? []) listener(message.params);
  });

  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const id = nextMessageId++;
      pending.set(id, { resolve, reject, method });
      socket.send(JSON.stringify({ id, method, params }));
    });

  const once = (method) =>
    new Promise((resolve) => {
      const listeners = eventListeners.get(method) ?? [];
      const listener = (params) => {
        eventListeners.set(method, (eventListeners.get(method) ?? []).filter((l) => l !== listener));
        resolve(params);
      };
      eventListeners.set(method, [...listeners, listener]);
    });

  await send("Page.enable");
  await send("Runtime.enable");
  await send("Network.enable");
  // Belt and braces with the fresh profile above: never let the PWA's service worker
  // answer a request, so a shot can only ever show the build currently being served.
  await send("Network.setBypassServiceWorker", { bypass: true });
  await send("Network.setCacheDisabled", { cacheDisabled: true });

  return { send, once, close: () => socket.close() };
}

/**
 * Evaluate an expression in the page and return its value. `expression` may be an async
 * function body; exceptions surface as rejections rather than as a silent `undefined`,
 * which is the failure mode that makes CDP harnesses lie about passing.
 */
export async function evaluate(session, expression) {
  const result = await session.send("Runtime.evaluate", {
    expression: `(async () => { ${expression} })()`,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    const detail = result.exceptionDetails.exception?.description
      ?? result.exceptionDetails.text;
    throw new Error(`Page evaluation threw: ${detail}`);
  }
  return result.result.value;
}

export async function navigate(session, url) {
  const loaded = session.once("Page.loadEventFired");
  await session.send("Page.navigate", { url });
  await loaded;
}

/**
 * Resize the viewport without relaunching the browser. `mobile` matters: it is what makes
 * `(pointer: coarse)` / `(hover: none)` media queries and the visual viewport behave like a
 * real phone, so a shot at 390px wide is not just a narrow desktop.
 */
export async function setViewport(session, { width, height, deviceScaleFactor = 1, mobile = false }) {
  await session.send("Emulation.setDeviceMetricsOverride", {
    width, height, deviceScaleFactor, mobile,
    screenWidth: width, screenHeight: height,
  });
  // maxTouchPoints must stay in 1..16 even when disabling; CDP rejects 0 outright.
  await session.send("Emulation.setTouchEmulationEnabled", { enabled: mobile, maxTouchPoints: 5 });
}

export async function captureScreenshot(session) {
  const { data } = await session.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  return Buffer.from(data, "base64");
}
