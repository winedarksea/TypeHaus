// Bundles a house's editable source into a JSON asset the standalone PWA loads by default, so a
// first-time visitor to type-house.com/app lands in the Catlin house with no folder-pick and no
// server (U9). The pyodide worker writes these { relpath: text } entries into its virtual FS
// exactly like a folder opened via the File System Access API.
//
// Only text the engine's plan loader consumes is shipped (mirrors openHouse.ts): plan/*.py,
// briefs, preferences, and project catalogs. Build output and caches are skipped.

import { readdirSync, statSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve, relative, join, sep } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");
const houseDir = resolve(repoRoot, "houses", "catlin");
const outDir = resolve(here, "..", "public");
const outFile = resolve(outDir, "catlin-house.json");

const TEXT_EXT = /\.(py|toml|md|json|txt|cfg|ini)$/i;
const SKIP_DIR = new Set(["out", "__pycache__", ".git", "node_modules", ".venv", "dist", ".claude"]);

function walk(dir, files) {
  for (const name of readdirSync(dir)) {
    const abs = join(dir, name);
    const st = statSync(abs);
    if (st.isDirectory()) {
      if (SKIP_DIR.has(name)) continue;
      walk(abs, files);
    } else if (TEXT_EXT.test(name)) {
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
mkdirSync(outDir, { recursive: true });
writeFileSync(outFile, JSON.stringify(files));
console.log(`[pwa] wrote ${outFile} (${Object.keys(files).length} files)`);
