// Minimal Chrome DevTools Protocol client for the screenshot harness.
//
// Deliberately not puppeteer: the repo carries exactly four runtime deps and adding a
// 300MB browser-automation package to take screenshots is not a trade worth making. Node's
// global WebSocket (>= 22) covers the whole protocol surface we need.

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";

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

export async function launchChromium({ port = 9222, userDataDir = "/tmp/chrome-haus-shots" } = {}) {
  const binary = findChromiumBinary();
  const child = spawn(
    binary,
    [...CHROMIUM_FLAGS, `--remote-debugging-port=${port}`, `--user-data-dir=${userDataDir}`, "about:blank"],
    { stdio: "ignore", detached: false },
  );
  const version = await waitForDevToolsEndpoint(port);
  return { child, port, version };
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
