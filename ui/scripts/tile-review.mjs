// Actual room-floor builder and procedural canvas maps, at room and close-up scales.
import { createServer } from "vite";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { launchChromium, attachToPage, evaluate, captureScreenshot } from "./lib/cdp.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "../out/tile-review");
const snapshot = await readFile(resolve(root, "../houses/catlin/out/model.json"), "utf8");
const server = await createServer({ root, configFile: false, plugins: [{ name: "tile-review",
  configureServer(server) { server.middlewares.use("/__tile-review-house", (_req, res) => {
    res.setHeader("Content-Type", "application/json"); res.end(snapshot);
  }); },
}], server: { host: "127.0.0.1", port: 0, hmr: false } });
await server.listen();
let browser, session;
try {
  browser = await launchChromium({ port: 9333 });
  session = await attachToPage(browser.port);
  await session.send("Emulation.setDeviceMetricsOverride", {
    width: 1600, height: 1220, deviceScaleFactor: 1, mobile: false,
  });
  await mkdir(output, { recursive: true });
  for (const view of ["rooms", "detail"]) {
    const url = `http://127.0.0.1:${server.httpServer.address().port}/tile-review.html${view === "detail" ? "?detail" : ""}`;
    await session.send("Page.navigate", { url });
    const deadline = Date.now() + 60000;
    while (!(await evaluate(session, "return window.tileReviewReady === true"))) {
      if (Date.now() > deadline) throw new Error(`Review timed out: ${view}`);
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    await evaluate(session, "await document.fonts.ready; return true");
    await new Promise(resolve => setTimeout(resolve, 300));
    const checks = await evaluate(session, "return window.tileReviewChecks");
    if (checks.failures.length) throw new Error(checks.failures.join("\n"));
    await writeFile(resolve(output, `${view}.png`), await captureScreenshot(session));
    await writeFile(resolve(output, `${view}.json`), JSON.stringify(checks, null, 2));
    console.log(`Tile review passed: ${view}`);
  }
} finally { session?.close(); if (browser) await browser.close(); await server.close(); }
