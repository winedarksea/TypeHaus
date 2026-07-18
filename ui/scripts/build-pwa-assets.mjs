// Bundles the pure-Python engine sources into a tar that the pyodide Web Worker unpacks at
// runtime (→ 40 WP4.2, degraded offline mode). Runs before `vite build` (see package.json).
//
// Only the source tree is shipped — no wheels, no native deps. Inside pyodide the worker stubs
// libcst / ifcopenshell / pyproj, so the resolve → checks → model.json → glb path runs while
// the writeback/IFC seams stay "requires local install" per the M4 gate (→ 40-m4-gate.md).

import { execFileSync } from "node:child_process";
import { mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");
const engineSrc = resolve(repoRoot, "packages", "engine", "src");
const outDir = resolve(here, "..", "public");
const outTar = resolve(outDir, "typehaus-engine.tar");

if (!existsSync(resolve(engineSrc, "typehaus"))) {
  console.error(`[pwa] engine sources not found at ${engineSrc}/typehaus`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });

// Uncompressed tar so pyodide's built-in unpackArchive("tar") can extract it with no zlib.
// Excludes keep it deterministic and lean (no __pycache__, no tests). Two roots: the engine
// (`typehaus`) plus the shared `library` package, which house plans import (→ 02 §Git
// topology) — both must be importable from the worker's sys.path offline.
const EXCLUDES = ["--exclude", "__pycache__", "--exclude", "*.pyc"];

// Create with typehaus, then append library from the repo root.
execFileSync("tar", ["-cf", outTar, "-C", engineSrc, ...EXCLUDES, "typehaus"], {
  stdio: "inherit",
});
if (existsSync(resolve(repoRoot, "library", "__init__.py"))) {
  execFileSync("tar", ["-rf", outTar, "-C", repoRoot, ...EXCLUDES, "library"], {
    stdio: "inherit",
  });
}

console.log(`[pwa] wrote ${outTar}`);
