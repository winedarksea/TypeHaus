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

// IFC export is an OPTIONAL extension, not part of the core offline bundle (U9): it needs
// ifcopenshell (+ pyproj), which have no standard pyodide wheels — only an experimental
// ifcopenshell wasm build. So the core tarball ships without typehaus/emit/ifc; nothing on the
// offline compute path (resolve → model.json → glb) imports it (the CLI/server import it lazily
// only when writing IFC). A future IFC extension ships emit/ifc + the wasm build separately and
// unpacks it onto the same sys.path, with no change to the core bundle.
const IFC_PKG = "typehaus/emit/ifc";
const CORE_EXCLUDES = [...EXCLUDES, "--exclude", IFC_PKG];

// Create with typehaus (minus the IFC extension), then append library from the repo root.
execFileSync("tar", ["-cf", outTar, "-C", engineSrc, ...CORE_EXCLUDES, "typehaus"], {
  stdio: "inherit",
});
if (existsSync(resolve(repoRoot, "library", "__init__.py"))) {
  execFileSync("tar", ["-rf", outTar, "-C", repoRoot, ...EXCLUDES, "library"], {
    stdio: "inherit",
  });
}
console.log(`[pwa] wrote ${outTar} (core, IFC excluded)`);

// The optional IFC extension bundle — built but not loaded by the core PWA. A later
// ifcopenshell-wasm integration fetches this alongside the wasm module.
const ifcTar = resolve(outDir, "typehaus-ifc-ext.tar");
if (existsSync(resolve(engineSrc, IFC_PKG, "__init__.py"))) {
  execFileSync("tar", ["-cf", ifcTar, "-C", engineSrc, ...EXCLUDES, IFC_PKG], {
    stdio: "inherit",
  });
  console.log(`[pwa] wrote ${ifcTar} (optional IFC extension)`);
}
