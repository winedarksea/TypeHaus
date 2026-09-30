// Browser scenarios for the public snapshot fallback, retry, and returning visitor.
// Run after `node landing/build-site.mjs`.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { resolve, extname } from "node:path";
import { fileURLToPath } from "node:url";
import { attachToPage, evaluate, launchChromium, navigate } from "./lib/cdp.mjs";

const root = resolve(fileURLToPath(new URL("../../site/", import.meta.url)));
const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".wasm": "application/wasm", ".gz": "application/octet-stream",
  ".tar": "application/octet-stream", ".svg": "image/svg+xml" };
let mode = "normal";
const server = createServer(async (request, response) => {
  const path = new URL(request.url, "http://localhost").pathname;
  if (path.endsWith("/catlin-model.json") && mode === "missing") {
    response.writeHead(404); response.end("missing"); return;
  }
  if (path.endsWith("/catlin-model.json") && mode === "corrupt") {
    response.writeHead(200, { "Content-Type": "application/json" }); response.end("{broken"); return;
  }
  if (path.endsWith("/typehaus-engine.tar.gz") && mode === "engine-failure") {
    response.writeHead(503); response.end("engine unavailable"); return;
  }
  const file = resolve(root, "." + path.replace(/\/$/, "/index.html"));
  if (!file.startsWith(root)) { response.writeHead(403); response.end(); return; }
  try {
    const body = await readFile(file);
    response.writeHead(200, { "Content-Type": mime[extname(file)] ?? "application/octet-stream",
      "Cache-Control": path.endsWith(".json") || path.endsWith(".gz") ? "public, max-age=0, must-revalidate" : "no-cache" });
    response.end(body);
  } catch { response.writeHead(404); response.end("missing"); }
});
await new Promise((resolve) => server.listen(8878, "127.0.0.1", resolve));
const browser = await launchChromium({ port: 9334 });
const page = await attachToPage(browser.port);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function state() {
  return evaluate(page, `const s = window.__haus?.store?.getState(); return {
    preview: !!s?.model && !s.engineReady, ready: !!s?.engineReady,
    visible: !!document.querySelector('.canvas-svg .wall-fills'),
    error: s?.error ?? null, retry: !!document.querySelector('button') &&
      [...document.querySelectorAll('button')].some(b => b.textContent?.includes('Retry engine')),
  };`);
}
async function until(test, timeout = 30_000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const value = await state();
    if (test(value)) return value;
    await sleep(100);
  }
  throw new Error(`timeout in ${mode}: ${JSON.stringify(await state())}`);
}
try {
  for (const scenario of ["missing", "corrupt"]) {
    mode = scenario;
    await navigate(page, `http://127.0.0.1:8878/app/?scenario=${scenario}`);
    const outcome = await until((s) => s.ready);
    if (!outcome.visible || outcome.error) throw new Error(`${scenario}: ${JSON.stringify(outcome)}`);
    console.log(`${scenario} snapshot: engine fallback rendered the house`);
  }
  mode = "engine-failure";
  await navigate(page, "http://127.0.0.1:8878/app/?scenario=engine-failure");
  const failed = await until((s) => !!s.error);
  if (!failed.visible || !failed.retry) throw new Error(`engine failure: ${JSON.stringify(failed)}`);
  mode = "normal";
  await evaluate(page, "await window.__haus.store.getState().retryEngine(); return true;");
  const recovered = await until((s) => s.ready);
  if (!recovered.visible || recovered.error) throw new Error(`retry: ${JSON.stringify(recovered)}`);
  console.log("engine failure: preview stayed visible and retry recovered");

  await page.send("Network.setBypassServiceWorker", { bypass: false });
  await page.send("Network.setCacheDisabled", { cacheDisabled: false });
  await navigate(page, "http://127.0.0.1:8878/app/?scenario=populate-cache");
  await until((s) => s.ready);
  const cached = await evaluate(page, `
    const keys = await caches.keys();
    const urls = (await Promise.all(keys.map(async key =>
      (await (await caches.open(key)).keys()).map(request => request.url)))).flat();
    return ['catlin-model.json', 'catlin-house.json', 'typehaus-engine.tar.gz']
      .every(name => urls.some(url => url.endsWith('/' + name)));
  `);
  if (!cached) throw new Error("returning visitor assets were not cached");
  await navigate(page, "http://127.0.0.1:8878/app/?scenario=returning");
  const returning = await until((s) => s.ready);
  if (!returning.visible || returning.error) throw new Error(`returning: ${JSON.stringify(returning)}`);
  console.log("returning visitor: house and engine rendered with cache enabled");
} finally {
  page.close();
  await browser.close();
  server.close();
}
