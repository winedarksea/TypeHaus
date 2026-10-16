// Starts its own local Vite and browser; no house server or app state is required.
import { execFileSync } from "node:child_process";
import { createServer } from "vite";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { launchChromium, attachToPage, evaluate, captureScreenshot } from "./lib/cdp.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "../out/wood-review");
const label = process.argv.includes("--before") ? "before" : "after";
const selectedView = process.argv.includes("--view") ? process.argv[process.argv.indexOf("--view") + 1] : null;
const houseSnapshot = process.argv.includes("--house")
  ? await readFile(resolve(root, "../houses/catlin/out/model.json"), "utf8") : null;
const palette = execFileSync(resolve(root, "../.venv/bin/python"), ["-c",
  "import json; from typehaus.library.wood_appearance import NATURAL_WOOD_COLORS, WOOD_SPECIES_NAMES; print(json.dumps([{'species':s,'name':WOOD_SPECIES_NAMES[s],'color':c} for s,c in NATURAL_WOOD_COLORS.items()]))"], { encoding: "utf8" });
const server = await createServer({ root, configFile: false, plugins: [{ name: "wood-review-palette",
  configureServer(server) { server.middlewares.use("/__wood-review-palette", (_req, res) => {
    res.setHeader("Content-Type", "application/json"); res.end(palette);
  });
  if (houseSnapshot) server.middlewares.use("/__wood-review-house", (_req, res) => {
    res.setHeader("Content-Type", "application/json"); res.end(houseSnapshot);
  }); },
}], server: { port: 0, host: "127.0.0.1", hmr: false } });
await server.listen();
const address = server.httpServer.address();
const browser = await launchChromium({ port: 9331 });
let session;
try {
  session = await attachToPage(browser.port);
  await session.send("Emulation.setDeviceMetricsOverride", { width: 1800, height: 1490, deviceScaleFactor: 1, mobile: false });
  await mkdir(output, { recursive: true });
  for (const [name, query] of [["overview", ""], ["distance", "?far"], ["detail", "?detail"],
    ...(houseSnapshot ? [["catlin", "?house"], ["suite", "?room"]] : [])]) {
    if (selectedView && selectedView !== name) continue;
    const url = `http://127.0.0.1:${address.port}/wood-review.html${query}${label === "before" ? (query ? "&legacy" : "?legacy") : ""}`;
    console.log(`Rendering ${name}…`);
    await session.send("Page.navigate", { url });
    const deadline = Date.now() + 60_000;
    while (true) {
      const result = await session.send("Runtime.evaluate", {
        expression: `location.href === ${JSON.stringify(url)} && window.woodReviewReady === true`,
        returnByValue: true,
      });
      if (result.result?.value === true) break;
      if (Date.now() > deadline) throw new Error(`Timed out generating ${name}`);
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    const checks = await evaluate(session, "return window.woodReviewChecks ?? null");
    if (checks?.failures?.length) throw new Error(checks.failures.join("\n"));
    await writeFile(resolve(output, `${label}-${name}.png`), await captureScreenshot(session));
    if (checks) await writeFile(resolve(output, `${label}-${name}-checks.json`), JSON.stringify(checks, null, 2));
  }
  console.log(`Wood review: ${label} images -> ${output}`);
} finally {
  session?.close(); await browser.close(); await server.close();
}
