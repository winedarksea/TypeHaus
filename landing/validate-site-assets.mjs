import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { validateSnapshotManifest } from "../ui/src/engine/snapshotFormat.mjs";

export const MAX_ASSET_BYTES = 25 * 1024 * 1024;

export function validateSiteAssets(siteDirectory) {
  let largest = { file: "", byteLength: 0 };
  function inspect(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) { inspect(path); continue; }
      const byteLength = statSync(path).size;
      const file = relative(siteDirectory, path);
      if (byteLength > MAX_ASSET_BYTES) {
        throw new Error(`[site] ${file}: ${byteLength} bytes exceeds Cloudflare Pages' 25 MiB per-file limit`);
      }
      if (byteLength > largest.byteLength) largest = { file, byteLength };
    }
  }
  inspect(siteDirectory);
  const appDirectory = join(siteDirectory, "app");
  const manifest = validateSnapshotManifest(JSON.parse(readFileSync(join(appDirectory, "catlin-model.json"), "utf8")));
  for (const chunk of manifest.chunks) {
    const bytes = readFileSync(join(appDirectory, chunk.file));
    if (bytes.length !== chunk.byteLength ||
        createHash("sha256").update(bytes).digest("hex") !== chunk.sha256) {
      throw new Error(`[site] invalid snapshot chunk: ${chunk.file}`);
    }
  }
  console.log(`[site] largest asset: ${largest.file} (${largest.byteLength} bytes)`);
  return largest;
}
