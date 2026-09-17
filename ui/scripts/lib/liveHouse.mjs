// A throwaway copy of a house served by `haus serve`, with Chromium attached over CDP.
// Shared by edit-check.mjs (Stage 1, furniture) and rooms-check.mjs (Stage 2, rooms/floors).
import { spawn, execFileSync } from "node:child_process";
import { cpSync, mkdtempSync, rmSync, writeFileSync, mkdirSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { attachToPage, captureScreenshot, launchChromium } from "./cdp.mjs";

export const UI = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
export const ROOT = join(UI, "..");
export const S = "window.__haus.store.getState()";
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export const freePort = () => new Promise((resolve) => {
  const srv = createServer().listen(0, "127.0.0.1", () => {
    const { port } = srv.address();
    srv.close(() => resolve(port));
  });
});

export function buildUi(skipEnv) {
  if (!process.env[skipEnv]) execFileSync("npm", ["run", "build"], { cwd: UI, stdio: "inherit" });
}

/** Copy houses/<template>, serve it on a free port, attach a browser. */
export async function openLiveHouse(template, { env = {} } = {}) {
  const house = join(mkdtempSync(join(tmpdir(), "haus-edit-")), template);
  cpSync(join(ROOT, "houses", template), house, {
    recursive: true, filter: (src) => !/(__pycache__|[/\\]out)$/.test(src),
  });
  const port = await freePort();
  const log = { text: "" };
  const server = spawn(join(ROOT, ".venv", "bin", "haus"),
    ["serve", house, "--port", String(port), "--ui-dir", join(UI, "dist")],
    { env: { ...process.env, ...env }, stdio: ["ignore", "pipe", "pipe"] });
  for (const stream of [server.stdout, server.stderr]) stream.on("data", (d) => { log.text += d; });
  for (let deadline = Date.now() + 60_000; ; await sleep(250)) {
    // A busy port makes serve exit while another process answers: trust only our own log.
    if (/address already in use/i.test(log.text) || server.exitCode !== null) {
      throw new Error(`haus serve failed to start:\n${log.text}`);
    }
    if (/Uvicorn running/.test(log.text)) break;
    if (Date.now() > deadline) throw new Error(`haus serve never came up:\n${log.text}`);
  }
  const cdpPort = await freePort();
  const browser = await launchChromium({ port: cdpPort });
  const session = await attachToPage(cdpPort);
  const close = async () => {
    session.close();
    await browser.close();
    server.kill();
    rmSync(dirname(house), { recursive: true, force: true });
  };
  return { house, base: `http://127.0.0.1:${port}`, session, log, close };
}

/** Named scenarios: log PASS/FAIL, screenshot + `dump()` on failure. */
export function scenarioRunner(session, shotsDir, dump) {
  mkdirSync(shotsDir, { recursive: true });
  const results = [];
  const scenario = async (name, body) => {
    const started = Date.now();
    try {
      await body();
      results.push({ name, ok: true });
      console.log(`PASS ${name} (${Date.now() - started} ms)`);
    } catch (error) {
      results.push({ name, ok: false });
      console.log(`FAIL ${name}: ${error.message}`);
      console.log(`     ${JSON.stringify(await dump().catch((e) => e.message))}`);
      const png = await captureScreenshot(session).catch(() => null);
      if (png) writeFileSync(join(shotsDir, `${name.replace(/\W+/g, "-")}.png`), png);
    }
  };
  return { scenario, results };
}

/** Fold the in-memory/source divergence check in, print the tally, exit 1 on any failure. */
export function finish(results, serverLog) {
  // Reconcile adopting source means the in-memory fast path and the writeback disagreed.
  const diverged = serverLog.split("\n").filter((line) => /diverged from source/.test(line));
  results.push({ name: "no in-memory/source divergence", ok: diverged.length === 0 });
  if (diverged.length) console.log(`FAIL server diverged:\n${diverged.join("\n")}`);
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} scenarios passed`);
  if (failed.length) process.exit(1);
}

export const assert = (cond, message) => { if (!cond) throw new Error(message); };
export const near = (a, b, tol = 0.02) => Math.abs(a - b) <= tol;

/** World metres → client pixels on the plan canvas. */
export const toScreen = (session, evaluate, [x, y]) => evaluate(session, `const s = ${S};
  const r = document.querySelector("svg.canvas-svg").getBoundingClientRect();
  return [r.left + s.view.tx + ${x} * s.view.scale, r.top + s.view.ty - ${y} * s.view.scale];`);
