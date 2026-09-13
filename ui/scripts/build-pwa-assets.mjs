// Bundles the pure-Python engine sources into a tar that the pyodide Web Worker unpacks at
// runtime (→ 40 WP4.2, degraded offline mode). Runs before `vite build` (see package.json).
//
// Only the source tree is shipped — no wheels, no native deps. Inside pyodide the worker stubs
// libcst / ifcopenshell / pyproj, so the resolve → checks → model.json → glb path runs while
// the writeback/IFC seams stay "requires local install" per the M4 gate (→ 40-m4-gate.md).

import { execFileSync } from "node:child_process";
import { mkdirSync, existsSync, readdirSync, copyFileSync, rmSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");
const engineSrc = resolve(repoRoot, "packages", "engine", "src");
const outDir = resolve(here, "..", "public");
// The staging tar; what ships is the gzip beside it. See GZIP below.
const outTar = resolve(outDir, "typehaus-engine.tar");
const outTarGz = `${outTar}.gz`;

if (!existsSync(resolve(engineSrc, "typehaus"))) {
  console.error(`[pwa] engine sources not found at ${engineSrc}/typehaus`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });

// Gzipped tar: pyodide's unpackArchive takes any shutil.unpack_archive format, and "gztar" needs
// only zlib, which is in the pyodide stdlib. It matters because Cloudflare will not compress
// application/x-tar — the plain tar went over the wire at its full 8 MB on every cold boot, while
// the gzip is ~2.3 MB. Every other big asset (the app JS, the bundled house) already gets brotli
// from the CDN; this is the one that had to carry its own.
//
// Excludes keep it deterministic and lean (no __pycache__, no tests). Two roots: the engine
// (`typehaus`) plus the shared `library` package, which house plans import (→ 02 §Git
// topology) — both must be importable from the worker's sys.path offline.
const EXCLUDES = ["--exclude", "__pycache__", "--exclude", "*.pyc"];

// The built UI itself, staged into the package by scripts/package_ui.py so the wheel can serve
// it. Tarring the engine *after* that stage folded the whole app — including the previous
// generation of this very tarball — into the bundle, taking it from 9 MB to 45 MB and growing
// with each round. CI never saw it (fresh checkout, no stage); a local build would have shipped
// it. Spelled from the tar root, like IFC_PKG below, because that is what the pattern matches.
const STATIC_PKG = "typehaus/server/static";

// IFC export is an OPTIONAL extension, not part of the core offline bundle (U9): it needs
// ifcopenshell (+ pyproj), which have no standard pyodide wheels — only an experimental
// ifcopenshell wasm build. So the core tarball ships without typehaus/emit/ifc; nothing on the
// offline compute path (resolve → model.json → glb) imports it (the CLI/server import it lazily
// only when writing IFC). A future IFC extension ships emit/ifc + the wasm build separately and
// unpacks it onto the same sys.path, with no change to the core bundle.
const IFC_PKG = "typehaus/emit/ifc";
const CORE_EXCLUDES = [...EXCLUDES, "--exclude", IFC_PKG, "--exclude", STATIC_PKG];

// Create with typehaus (minus the IFC extension), then append library from the repo root.
execFileSync("tar", ["-cf", outTar, "-C", engineSrc, ...CORE_EXCLUDES, "typehaus"], {
  stdio: "inherit",
});
if (existsSync(resolve(repoRoot, "library", "__init__.py"))) {
  execFileSync("tar", ["-rf", outTar, "-C", repoRoot, ...EXCLUDES, "library"], {
    stdio: "inherit",
  });
}
// GZIP. `-n` omits the source name and mtime from the header, so the same sources produce the
// same bytes — the tar itself is already deterministic, and a build that is byte-stable is what
// lets the ETag behind it be stable, which is what makes sw.js's revalidation a 304 rather
// than a re-download on every boot.
rmSync(outTarGz, { force: true });
execFileSync("gzip", ["-9", "-n", outTar], { stdio: "inherit" });
console.log(`[pwa] wrote ${outTarGz} (core, IFC excluded) `
  + `${(statSync(outTarGz).size / 1e6).toFixed(2)} MB`);

// The optional IFC extension bundle — built but not loaded by the core PWA. A later
// ifcopenshell-wasm integration fetches this alongside the wasm module.
const ifcTar = resolve(outDir, "typehaus-ifc-ext.tar");
if (existsSync(resolve(engineSrc, IFC_PKG, "__init__.py"))) {
  execFileSync("tar", ["-cf", ifcTar, "-C", engineSrc, ...EXCLUDES, IFC_PKG], {
    stdio: "inherit",
  });
  console.log(`[pwa] wrote ${ifcTar} (optional IFC extension)`);
}

// Optional: vendor an ifcopenshell pyodide/wasm wheel so the client-side IFC export path
// activates. The wheel is NOT produced by this build and is NOT bundled in the repo — it must be
// sourced/built externally (see ../docs/ifc-wasm.md). If a maintainer drops one at ui/vendor/, we
// copy it into public/ so it ships in dist/ and is served same-origin by `haus serve`'s SPA
// static mount; VITE_IFC_WASM_URL can then point at it (or any URL). If no wheel is present this
// is a silent no-op — the build must still succeed exactly as before.
const vendorDir = resolve(here, "..", "vendor");
if (existsSync(vendorDir)) {
  const wheels = readdirSync(vendorDir).filter(
    (f) => f.startsWith("ifcopenshell") && f.endsWith(".whl"),
  );
  for (const wheel of wheels) {
    copyFileSync(resolve(vendorDir, wheel), resolve(outDir, wheel));
    console.log(`[pwa] copied vendored IFC wheel ${wheel} -> public/`);
  }
}
