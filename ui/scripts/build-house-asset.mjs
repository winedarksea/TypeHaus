// Bundles a house's editable source into a JSON asset the standalone PWA loads by default, so a
// first-time visitor to type-house.com/app lands in the Catlin house with no folder-pick and no
// server (U9). The pyodide worker writes these { relpath: text } entries into its virtual FS
// exactly like a folder opened via the File System Access API.
//
// Only text the engine's plan loader consumes is shipped: plan/*.py, briefs, preferences, project
// catalogs, and any data file a plan module opens at import time. Build output and caches are
// skipped. The folder-pick path (ui/src/engine/openHouse.ts) keeps its own copy of this filter —
// the two lists must agree or a folder that works bundled will fail when picked, and vice versa.

import { readdirSync, statSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve, relative, join, sep } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");
const houseDir = resolve(repoRoot, "houses", "catlin");
const outDir = resolve(here, "..", "public");
const outFile = resolve(outDir, "catlin-house.json");

// Text the plan loader reads at *import* time. `geojson` is load-bearing, not decoration:
// houses/catlin/plan/manifest.py calls load_basemap_geojson(plan/basemap.geojson) while the
// module is being imported, so omitting it makes _import_manifest raise, the model resolve to
// None, and the PWA greet a first-time visitor with "Cannot reach engine". Any extension a plan
// module opens by path must be listed here.
const PLAN_TEXT_EXTENSIONS = /\.(py|toml|md|json|geojson|csv|txt|cfg|ini)$/i;
const SKIP_DIR = new Set(["out", "__pycache__", ".git", "node_modules", ".venv", "dist", ".claude"]);

// A plan whose manifest cannot be imported produces no model at all, so the bundle is worthless.
// Fail the build loudly here rather than shipping an asset that only breaks in the browser.
const REQUIRED_RELPATHS = ["plan/manifest.py", "plan/basemap.geojson", "preferences.toml"];

function walk(dir, files) {
  for (const name of readdirSync(dir)) {
    const abs = join(dir, name);
    const st = statSync(abs);
    if (st.isDirectory()) {
      if (SKIP_DIR.has(name)) continue;
      walk(abs, files);
    } else if (PLAN_TEXT_EXTENSIONS.test(name)) {
      const rel = relative(houseDir, abs).split(sep).join("/");
      files[rel] = readFileSync(abs, "utf-8");
    }
  }
}

try {
  statSync(join(houseDir, "plan"));
} catch {
  console.error(`[pwa] catlin house not found at ${houseDir}/plan`);
  process.exit(1);
}

const files = {};
walk(houseDir, files);

const missing = REQUIRED_RELPATHS.filter((rel) => !(rel in files));
if (missing.length > 0) {
  console.error(`[pwa] bundled house is missing required plan inputs: ${missing.join(", ")}`);
  console.error(`[pwa] add the extension to PLAN_TEXT_EXTENSIONS in ${import.meta.url}`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
writeFileSync(outFile, JSON.stringify(files));
console.log(`[pwa] wrote ${outFile} (${Object.keys(files).length} files)`);
