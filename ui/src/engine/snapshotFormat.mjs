// Snapshot transport only: the engine and renderer continue to exchange ordinary Models.
export const SNAPSHOT_FORMAT = "typehaus-model-snapshot";
// 2: product meshes arrive deduplicated in `catalog.meshes` from the engine itself, so the
// envelope no longer carries a mesh table of its own.
// 3: mesh streams are delta-coded (server/model_json_mesh.py).
export const SNAPSHOT_VERSION = 3;
export const SNAPSHOT_CHUNK_BYTES = 8 * 1024 * 1024;

export function packSnapshot(model) {
  return { model };
}

export function unpackSnapshot(packed) {
  if (!packed || typeof packed !== "object" || !packed.model || typeof packed.model !== "object") {
    throw new Error("invalid packed snapshot");
  }
  return packed.model;
}

export function validateSnapshotManifest(manifest) {
  if (!manifest || manifest.format !== SNAPSHOT_FORMAT || manifest.version !== SNAPSHOT_VERSION ||
      !Number.isSafeInteger(manifest.byteLength) || manifest.byteLength <= 0 ||
      !Array.isArray(manifest.chunks) || manifest.chunks.length === 0) {
    throw new Error("invalid snapshot manifest");
  }
  let totalBytes = 0;
  for (const chunk of manifest.chunks) {
    if (!chunk || typeof chunk.sha256 !== "string" || !/^[a-f0-9]{64}$/.test(chunk.sha256) ||
        chunk.file !== `catlin-model/${chunk.sha256}.bin` ||
        !Number.isSafeInteger(chunk.byteLength) || chunk.byteLength <= 0 ||
        chunk.byteLength > SNAPSHOT_CHUNK_BYTES) throw new Error("invalid snapshot chunk manifest");
    totalBytes += chunk.byteLength;
  }
  if (!Number.isSafeInteger(totalBytes) || totalBytes !== manifest.byteLength) {
    throw new Error("snapshot manifest length mismatch");
  }
  return manifest;
}
