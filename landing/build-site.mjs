// Assembles the full static site for type-haus.com into ./site:
//   /            -> landing page + install scripts (this directory)
//   /app         -> the standalone PWA (ui build, VITE_PWA_STANDALONE=1)
//
// Build (does NOT deploy):  node landing/build-site.mjs
// Then serve ./site with any static server; the landing links to /app and /install.sh.
// Deployment (host, DNS, CI) is documented in landing/DEPLOY.md.

import { execFileSync } from "node:child_process";
import { cpSync, mkdirSync, rmSync, readdirSync, statSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..");
const uiDir = resolve(repoRoot, "ui");
const siteDir = resolve(repoRoot, "site");

// Canonical origin. Only used to stamp the sitemap; every in-page link is host-relative so the
// same artifact serves correctly from a preview deployment on a different hostname.
const SITE_ORIGIN = process.env.SITE_ORIGIN ?? "https://type-haus.com";

// Landing sources that are build machinery or docs, not shipped files.
const NOT_SHIPPED = new Set(["build-site.mjs", "DEPLOY.md", "node_modules"]);

// The offline PWA is worthless without these: the engine sources it unpacks into Pyodide and
// the bundled house a first-time visitor lands in. A missing one only fails in the browser, so
// assert here instead of shipping a deploy that boots to "Cannot reach engine".
const REQUIRED_APP_FILES = ["index.html", "sw.js", "manifest.webmanifest", "typehaus-engine.tar",
  "catlin-house.json", "sheets/permit_set.json"];

// The permit set the app's Drawings tab reads. Composed by `haus print` (in CI, before this
// script runs — see landing/DEPLOY.md), never here: matplotlib cannot run in Pyodide, so the
// published app ships a pre-rendered PDF rather than drawing one. Copied out of the house's
// `out/` into `app/sheets/` rather than into `ui/public/`, or every local `haus serve` build
// would carry a 24 MB drawing set too.
const houseOut = resolve(repoRoot, "houses", "catlin", "out");
const SHEET_FILES = ["permit_set.pdf", "permit_set.json"];
// Cloudflare Pages refuses a file over 25 MB. A set that crosses it fails the deploy at
// upload time with nothing to point at; better to say so here, naming the file.
const MAX_ASSET_BYTES = 25 * 1024 * 1024;

console.log("[site] building standalone PWA...");
execFileSync("npm", ["run", "build"], {
  cwd: uiDir,
  stdio: "inherit",
  // VITE_PUBLIC_SITE gates the pages (the Estimate reader, the BOM's cost columns);
  // HAUS_PUBLIC keeps prices.toml / costs.toml / tasks.toml out of the bundled house
  // entirely, so the numbers are not merely hidden but absent (→ ui/src/state/public.ts).
  env: { ...process.env, VITE_PWA_STANDALONE: "1", VITE_PUBLIC_SITE: "1", HAUS_PUBLIC: "1" },
});

console.log(`[site] assembling ${siteDir}`);
rmSync(siteDir, { recursive: true, force: true });
mkdirSync(siteDir, { recursive: true });

// Landing files at the root.
for (const name of readdirSync(here)) {
  if (NOT_SHIPPED.has(name)) continue;
  const src = join(here, name);
  cpSync(src, join(siteDir, name), { recursive: statSync(src).isDirectory() });
}

// PWA under /app.
cpSync(resolve(uiDir, "dist"), join(siteDir, "app"), { recursive: true });

// The drawings, beside the app.
const sheetsDir = join(siteDir, "app", "sheets");
mkdirSync(sheetsDir, { recursive: true });
for (const name of SHEET_FILES) {
  const src = join(houseOut, name);
  if (!existsSync(src)) continue; // REQUIRED_APP_FILES below is what actually fails the build
  const size = statSync(src).size;
  if (size > MAX_ASSET_BYTES) {
    console.error(`[site] ${name} is ${(size / 1e6).toFixed(1)} MB — over the 25 MB `
      + `per-file cap on Cloudflare Pages. Print at --paper ledger, or thin the set.`);
    process.exit(1);
  }
  cpSync(src, join(sheetsDir, name));
}

const missing = REQUIRED_APP_FILES.filter((f) => !existsSync(join(siteDir, "app", f)));
if (missing.length > 0) {
  console.error(`[site] /app is missing required files: ${missing.join(", ")}`);
  if (missing.some((f) => f.startsWith("sheets/"))) {
    console.error("[site] run `haus print houses/catlin --fmt pdf` first — it writes "
      + "out/permit_set.{pdf,json}, and it refuses while the permit checklist does not pass.");
  }
  process.exit(1);
}

// Sitemap is generated rather than committed so lastmod reflects the deploy, not a stale edit.
// Only the landing page is listed — /app is a client-side SPA with nothing to crawl.
const lastModifiedIsoDate = new Date().toISOString().slice(0, 10);
writeFileSync(
  join(siteDir, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    `  <url><loc>${SITE_ORIGIN}/</loc><lastmod>${lastModifiedIsoDate}</lastmod></url>\n` +
    `</urlset>\n`,
);

console.log("[site] done. Serve ./site (root = landing, /app = PWA).");
