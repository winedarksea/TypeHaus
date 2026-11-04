// Production-builder screenshots using the repository's Chromium/CDP harness.
import { createServer } from "vite";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { launchChromium, attachToPage, navigate, evaluate, captureScreenshot } from "./lib/cdp.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "../out/railing-review");
const snapshot = await readFile(resolve(root, "../houses/catlin/out/model.json"), "utf8");
const server = await createServer({ root, configFile: false,
  cacheDir: resolve(output, ".vite-cache"),
  optimizeDeps: { noDiscovery: true, include: ["three", "react", "react/jsx-runtime", "zustand"] },
  plugins: [{ name: "railing-review", configureServer(server) {
    server.middlewares.use("/__railing-review-house", (_req, res) => {
      res.setHeader("Content-Type", "application/json"); res.end(snapshot);
    });
  } }], server: { host: "127.0.0.1", port: 0, hmr: false } });
await server.listen();
const browser = await launchChromium({ port: 9335 });
let session;
try {
  session = await attachToPage(browser.port);
  await session.send("Emulation.setDeviceMetricsOverride", {
    width: 1600, height: 3210, deviceScaleFactor: 1, mobile: false,
  });
  await mkdir(output, { recursive: true });
  for (const theme of ["light", "dark", "schematic"]) {
    await navigate(session, `http://127.0.0.1:${server.httpServer.address().port}/railing-review.html?theme=${theme}`);
    const deadline = Date.now() + 60000;
    while (!(await evaluate(session, "return window.railingReviewReady === true"))) {
      if (Date.now() > deadline) throw new Error(`Review timed out: ${theme}`);
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    const checks = await evaluate(session, "return window.railingReviewChecks");
    if (checks.failures.length) throw new Error(checks.failures.join("\n"));
    await writeFile(resolve(output, `${theme}.png`), await captureScreenshot(session));
    await writeFile(resolve(output, `${theme}.json`), JSON.stringify(checks, null, 2));
    console.log(`Railing review: ${theme}`);
  }
} finally { session?.close(); await browser.close(); await server.close(); }
