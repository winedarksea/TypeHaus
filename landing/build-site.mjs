// Assembles the full static site for type-house.com into ./site:
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
const SITE_ORIGIN = process.env.SITE_ORIGIN ?? "https://type-house.com";

// Landing sources that are build machinery or docs, not shipped files.
const NOT_SHIPPED = new Set(["build-site.mjs", "DEPLOY.md", "node_modules"]);

// The offline PWA is worthless without these: the engine sources it unpacks into Pyodide and
// the bundled house a first-time visitor lands in. A missing one only fails in the browser, so
// assert here instead of shipping a deploy that boots to "Cannot reach engine".
const REQUIRED_APP_FILES = ["index.html", "sw.js", "manifest.webmanifest", "typehaus-engine.tar", "catlin-house.json"];

console.log("[site] building standalone PWA...");
execFileSync("npm", ["run", "build"], {
  cwd: uiDir,
  stdio: "inherit",
  env: { ...process.env, VITE_PWA_STANDALONE: "1" },
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

const missing = REQUIRED_APP_FILES.filter((f) => !existsSync(join(siteDir, "app", f)));
if (missing.length > 0) {
  console.error(`[site] /app is missing required files: ${missing.join(", ")}`);
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
