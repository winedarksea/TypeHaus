// Snapshot transport only: the engine and renderer continue to exchange ordinary Models.
export const SNAPSHOT_FORMAT = "typehaus-model-snapshot";
export const SNAPSHOT_VERSION = 1;
export const SNAPSHOT_CHUNK_BYTES = 8 * 1024 * 1024;

export function packSnapshot(model) {
  const meshes = [];
  const meshIndices = new Map();
  const packedModel = structuredClone(model);
  for (const type of packedModel.catalog?.canvas_object_types ?? []) {
    for (const part of type.model_parts ?? []) {
      if (!Object.hasOwn(part, "mesh")) continue;
      if (Object.hasOwn(part, "snapshot_mesh_index")) throw new Error("reserved snapshot mesh field");
      const serializedMesh = JSON.stringify(part.mesh);
      let index = meshIndices.get(serializedMesh);
      if (index === undefined) {
        index = meshes.length;
        meshIndices.set(serializedMesh, index);
        meshes.push(part.mesh);
      }
      delete part.mesh;
      part.snapshot_mesh_index = index;
    }
  }
  return { model: packedModel, meshes };
}

export function unpackSnapshot(packed) {
  if (!packed || typeof packed !== "object" || !packed.model ||
      typeof packed.model !== "object" || !Array.isArray(packed.meshes)) {
    throw new Error("invalid packed snapshot");
  }
  for (const type of packed.model.catalog?.canvas_object_types ?? []) {
    for (const part of type.model_parts ?? []) {
      if (!Object.hasOwn(part, "snapshot_mesh_index")) continue;
      const index = part.snapshot_mesh_index;
      if (!Number.isInteger(index) || index < 0 || index >= packed.meshes.length ||
          Object.hasOwn(part, "mesh")) throw new Error("invalid snapshot mesh reference");
      part.mesh = packed.meshes[index];
      delete part.snapshot_mesh_index;
    }
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
