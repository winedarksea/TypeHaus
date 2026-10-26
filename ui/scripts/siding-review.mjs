// Real Catlin wall and closure meshes, photographed through the production viewer builders.
import { createServer } from "vite";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { launchChromium, attachToPage, evaluate, captureScreenshot } from "./lib/cdp.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const snapshot = await readFile(resolve(root, "../houses/catlin/out/model.json"), "utf8");
const output = resolve(root, "../out/siding-review");
const server = await createServer({ root, configFile: false, plugins: [{ name: "siding-review",
  configureServer(server) { server.middlewares.use("/__siding-review-house", (_req, res) => {
    res.setHeader("Content-Type", "application/json"); res.end(snapshot);
  }); },
}], server: { port: 0, host: "127.0.0.1", hmr: false } });
await server.listen();
const browser = await launchChromium({ port: 9337 });
let session;
try {
  session = await attachToPage(browser.port);
  await session.send("Emulation.setDeviceMetricsOverride", { width: 1500, height: 1190, deviceScaleFactor: 1, mobile: false });
  await mkdir(output, { recursive: true });
  const views = [["board-and-batten", "north"], ["ribbed-panel", "east"], ["corrugated", "north"]];
  for (const [profile, face] of views) for (const detail of ["facade", "opening",
    ...(profile === "corrugated" ? ["head"] : [])]) {
    const label = `${profile}-${face}-${detail === "opening" ? "detail" : detail}`;
    const url = `http://127.0.0.1:${server.httpServer.address().port}/siding-review.html?profile=${profile}&face=${face}${detail === "facade" ? "" : `&detail=${detail}`}`;
    await session.send("Page.navigate", { url });
    const deadline = Date.now() + 60_000;
    while (!await evaluate(session, `return location.href === ${JSON.stringify(url)} && window.sidingReviewReady === true`)) {
      if (Date.now() > deadline) throw new Error(`Timed out rendering ${label}`);
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    const checks = await evaluate(session, "return window.sidingReviewChecks");
    if (checks.errors.length) throw new Error(checks.errors.join("\n"));
    await writeFile(resolve(output, `${label}.png`), await captureScreenshot(session));
    await writeFile(resolve(output, `${label}.json`), JSON.stringify(checks, null, 2));
    console.log(label, checks);
  }
} finally {
  await session?.close(); await browser.close(); await server.close();
}
