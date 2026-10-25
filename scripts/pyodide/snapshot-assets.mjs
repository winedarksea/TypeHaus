import { createHash } from "node:crypto";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { packSnapshot, SNAPSHOT_FORMAT, SNAPSHOT_VERSION, SNAPSHOT_CHUNK_BYTES }
  from "../../ui/src/engine/snapshotFormat.mjs";

export function encodeSnapshot(model, chunkBytes = SNAPSHOT_CHUNK_BYTES) {
  if (!Number.isSafeInteger(chunkBytes) || chunkBytes <= 0 || chunkBytes > SNAPSHOT_CHUNK_BYTES) {
    throw new Error("invalid snapshot chunk size");
  }
  const bytes = Buffer.from(JSON.stringify(packSnapshot(model)), "utf8");
  const chunks = [];
  const files = new Map();
  for (let offset = 0; offset < bytes.length; offset += chunkBytes) {
    const body = bytes.subarray(offset, offset + chunkBytes);
    const sha256 = createHash("sha256").update(body).digest("hex");
    const file = `catlin-model/${sha256}.bin`;
    chunks.push({ file, byteLength: body.length, sha256 });
    files.set(file, body);
  }
  return { manifest: { format: SNAPSHOT_FORMAT, version: SNAPSHOT_VERSION,
    byteLength: bytes.length, chunks }, files };
}

export function clearSnapshotAssets(directory) {
  rmSync(join(directory, "catlin-model.json"), { force: true });
  rmSync(join(directory, "catlin-model"), { recursive: true, force: true });
}

export function writeSnapshotAssets(directory, model) {
  clearSnapshotAssets(directory);
  const { manifest, files } = encodeSnapshot(model);
  mkdirSync(join(directory, "catlin-model"), { recursive: true });
  for (const [file, bytes] of files) writeFileSync(join(directory, file), bytes);
  writeFileSync(join(directory, "catlin-model.json"), JSON.stringify(manifest));
  console.log(`[pwa] snapshot: ${Buffer.byteLength(JSON.stringify(model))} original bytes → `
    + `${manifest.byteLength} packed bytes; chunks: ${manifest.chunks.map(c => c.byteLength).join(", ")}`);
  return manifest;
}
