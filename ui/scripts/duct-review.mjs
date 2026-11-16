// Duct joint screenshots through the production scene builders (Chromium/CDP, like railing-review).
// Needs a fresh `.venv/bin/haus build houses/catlin` (reads houses/catlin/out/model.json).
// Flags: --walls=solid (default ghosted) --theme=light|dark|schematic --eye=x,y,z (scene axes)
import { createServer } from "vite";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { launchChromium, attachToPage, navigate, evaluate } from "./lib/cdp.mjs";

const arg = (name, fallback) => process.argv.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "../out/duct-review");
const snapshot = await readFile(resolve(root, "../houses/catlin/out/model.json"), "utf8");
const server = await createServer({ root, configFile: false,
  cacheDir: resolve(output, ".vite-cache"),
  optimizeDeps: { noDiscovery: true, include: ["three", "react", "react/jsx-runtime", "zustand"] },
  plugins: [{ name: "duct-review", configureServer(server) {
    server.middlewares.use("/__duct-review-house", (_req, res) => {
      res.setHeader("Content-Type", "application/json"); res.end(snapshot);
    });
  } }], server: { host: "127.0.0.1", port: 0, hmr: false } });
await server.listen();
// A free DevTools port: a stale Chromium on a fixed one would silently answer instead.
const browser = await launchChromium({ port: 9000 + Math.floor(Math.random() * 900) });
let session;
try {
  session = await attachToPage(browser.port);
  await session.send("Emulation.setDeviceMetricsOverride", { width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false });
  await mkdir(output, { recursive: true });
  const query = ["walls", "theme", "eye"].filter(k => arg(k)).map(k => `${k}=${arg(k)}`).join("&");
  await navigate(session, `http://127.0.0.1:${server.httpServer.address().port}/duct-review.html?${query}`);
  const deadline = Date.now() + 180000;
  while (!(await evaluate(session, "return window.ductReviewReady === true"))) {
    if (Date.now() > deadline) throw new Error("Duct review timed out");
    await new Promise(r => setTimeout(r, 200));
  }
  const checks = await evaluate(session, "return window.ductReviewChecks");
  const shots = await evaluate(session, "return window.ductReviewShots");
  const manifest = [];
  for (const shot of shots) {
    await writeFile(resolve(output, `${shot.file}.png`), Buffer.from(shot.png.split(",")[1], "base64"));
    manifest.push({ file: `${shot.file}.png`, name: shot.name, focusTags: shot.focusTags, box: shot.box });
    console.log(`Duct review: ${output}/${shot.file}.png`);
  }
  await writeFile(resolve(output, "shots.json"), JSON.stringify({ failures: checks.failures, manifest }, null, 2));
  if (checks.failures.length) throw new Error(checks.failures.join("\n"));
} finally { session?.close(); await browser.close(); await server.close(); }
