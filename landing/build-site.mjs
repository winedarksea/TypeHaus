// Assembles the full static site for type-house.com into ./site:
//   /            -> landing page + install scripts (this directory)
//   /app         -> the standalone PWA (ui build, VITE_PWA_STANDALONE=1)
//
// Build (does NOT deploy):  node landing/build-site.mjs
// Then serve ./site with any static server; the landing links to /app and /install.sh.

import { execFileSync } from "node:child_process";
import { cpSync, mkdirSync, rmSync, readdirSync, statSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..");
const uiDir = resolve(repoRoot, "ui");
const siteDir = resolve(repoRoot, "site");

console.log("[site] building standalone PWA...");
execFileSync("npm", ["run", "build"], {
  cwd: uiDir,
  stdio: "inherit",
  env: { ...process.env, VITE_PWA_STANDALONE: "1" },
});

console.log(`[site] assembling ${siteDir}`);
rmSync(siteDir, { recursive: true, force: true });
mkdirSync(siteDir, { recursive: true });

// Landing files at the root (everything in this dir except the build machinery).
const SKIP = new Set(["build-site.mjs", "node_modules"]);
for (const name of readdirSync(here)) {
  if (SKIP.has(name)) continue;
  const src = join(here, name);
  cpSync(src, join(siteDir, name), { recursive: statSync(src).isDirectory() });
}

// PWA under /app.
cpSync(resolve(uiDir, "dist"), join(siteDir, "app"), { recursive: true });

console.log("[site] done. Serve ./site (root = landing, /app = PWA).");
