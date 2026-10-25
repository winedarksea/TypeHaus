// Isolated production-builder review, using the same Chromium/CDP harness as wood review.
import { createServer } from "vite";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { launchChromium, attachToPage, navigate, evaluate, captureScreenshot } from "./lib/cdp.mjs";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const exterior = process.argv.includes("--exterior");
const output = resolve(root, exterior ? "../out/exterior-door-review" : "../out/door-review");
const before = process.argv.includes("--before"), label = before ? "before" : "after";
const snapshot = await readFile(resolve(root, exterior ? "../out/exterior-door-review/model.json"
  : before ? "../out/door-review/before-model.json"
  : "../houses/catlin/out/model.json"), "utf8");
const legacy = before ? await readFile(resolve(output, "before-openings.ts"), "utf8") : null;
const server = await createServer({ root, configFile: false,
  cacheDir: resolve(output, ".vite-cache"),
  optimizeDeps: { noDiscovery: true,
    include: ["three", "react", "react/jsx-runtime", "react/jsx-dev-runtime", "zustand"] },
  plugins: [{ name: "door-review",
  enforce: "pre",
  transform(_code, id) {
    if (legacy && id.endsWith("/three/builders/openings.ts")) {
      if (legacy.includes("options: OpeningProductOptions")) return legacy;
      return legacy.replace(
      "export function buildOpening(", "function legacyBuildOpening(") + `
      export function buildOpening(parent, opening, wall, center, mode, palette, options, picks, byUid) {
        return legacyBuildOpening(parent, opening, wall, center, mode, palette, options.operation,
          picks, byUid, options.glazed, options.trimless, options.bookcaseDoor, options.materials, options.leafSet);
      }`;
    }
  },
  configureServer(server) { server.middlewares.use("/__door-review-house", (_req, res) => {
    res.setHeader("Content-Type", "application/json"); res.end(snapshot);
  }); },
}], server: { host: "127.0.0.1", port: 0, hmr: false } });
await server.listen();
const browser = await launchChromium({ port: 9332 });
let session;
try {
  session = await attachToPage(browser.port);
  await session.send("Emulation.setDeviceMetricsOverride", {
    width: 1600, height: 1150, deviceScaleFactor: 1, mobile: false,
  });
  await mkdir(output, { recursive: true });
  for (const view of exterior ? ["exterior-faces", "exterior-jamb", "exterior-floor"]
    : ["faces", "jamb", "floor", "synthetic"]) {
    for (const theme of ["light", "dark", "schematic"]) {
      const url = `http://127.0.0.1:${server.httpServer.address().port}/door-review.html?view=${view}&theme=${theme}`;
      await navigate(session, url);
      const deadline = Date.now() + 60000;
      while (!(await evaluate(session, "return window.doorReviewReady === true"))) {
        if (Date.now() > deadline) throw new Error(`Review timed out: ${view}/${theme}`);
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      await evaluate(session, "window.scrollTo(0, 0); return true");
      const checks = await evaluate(session, "return window.doorReviewChecks");
      if (checks.failures.length) throw new Error(checks.failures.join("\n"));
      await writeFile(resolve(output, `${label}-${view}-${theme}.png`), await captureScreenshot(session));
      await writeFile(resolve(output, `${label}-${view}-${theme}.json`), JSON.stringify(checks, null, 2));
      console.log(`${label}: ${view}/${theme}`);
    }
  }
} finally { session?.close(); await browser.close(); await server.close(); }
