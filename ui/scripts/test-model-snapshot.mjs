import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, truncateSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "vite";
import { encodeSnapshot, writeSnapshotAssets, clearSnapshotAssets } from "../../scripts/pyodide/snapshot-assets.mjs";
import { packSnapshot, unpackSnapshot, validateSnapshotManifest, SNAPSHOT_CHUNK_BYTES } from "../src/engine/snapshotFormat.mjs";
import { MAX_ASSET_BYTES, validateSiteAssets } from "../../landing/validate-site-assets.mjs";

const mesh = { vertices: [[0, 0, 0], [0.1234567890123, 1, 0]], triangles: [[0, 1, 0]] };
const model = { revision: "test", project: { name: "Catlin 家 🏠" },
  storeys: [{ tag: "main" }], walls: [{ uid: "wall", axis: [[0, 0], [1, 0]], layers: [] }],
  catalog: { canvas_object_types: [{ tag: "fixture", model_parts: [
    { mesh, color: "red" }, { mesh: structuredClone(mesh), color: "blue" },
    { mesh: { ...mesh, vertices: [[0, 0, 0], [0.1234567890124, 1, 0]] }, color: "red" },
    { color: "green", size: [1, 2, 3] },
  ] }] } };
const original = structuredClone(model);
const packed = packSnapshot(model);
assert.equal(packed.meshes.length, 2);
assert.deepEqual(unpackSnapshot(packed), model);
assert.deepEqual(model, original, "packing must not mutate the source");
assert.throws(() => unpackSnapshot({ model: { catalog: { canvas_object_types: [
  { model_parts: [{ snapshot_mesh_index: 99 }] }] } }, meshes: [] }), /mesh reference/);
assert.throws(() => unpackSnapshot(null), /invalid/);

const encoded = encodeSnapshot(model, 1); // Every multibyte character crosses a boundary.
assert.deepEqual(encodeSnapshot(model, 1), encoded, "encoding must be deterministic");
assert.deepEqual(validateSnapshotManifest(encoded.manifest), encoded.manifest);
for (const patch of [{ version: 99 }, { byteLength: 0 }, { chunks: [] }, { byteLength: 2 }]) {
  assert.throws(() => validateSnapshotManifest({ ...encoded.manifest, ...patch }), /manifest/);
}
for (const patch of [{ file: "../bad" }, { sha256: "bad" }, { byteLength: SNAPSHOT_CHUNK_BYTES + 1 }]) {
  assert.throws(() => validateSnapshotManifest({ ...encoded.manifest,
    chunks: [{ ...encoded.manifest.chunks[0], ...patch }] }), /manifest/);
}
for (const size of [1, 127, SNAPSHOT_CHUNK_BYTES]) {
  const encodedBoundary = encodeSnapshot(model, size);
  assert(encodedBoundary.manifest.chunks.every(c => c.byteLength <= size));
  assert.deepEqual(unpackSnapshot(JSON.parse(Buffer.concat(encodedBoundary.manifest.chunks
    .map(c => encodedBoundary.files.get(c.file))).toString("utf8"))), model);
}
const largeModel = { ...model, padding: "x".repeat(SNAPSHOT_CHUNK_BYTES) };
assert.equal(encodeSnapshot(largeModel).manifest.chunks[0].byteLength, SNAPSHOT_CHUNK_BYTES);
assert.equal(encodeSnapshot(largeModel).manifest.chunks.length, 2);

const server = await createServer({ configFile: false, server: { middlewareMode: true }, appType: "custom" });
const oldFetch = globalThis.fetch;
const oldDocument = globalThis.document;
const temporary = mkdtempSync(join(tmpdir(), "typehaus-snapshot-"));
try {
  const { loadModelSnapshot } = await server.ssrLoadModule("/src/engine/modelSnapshot.ts");
  globalThis.document = { baseURI: "https://example.com/nested/app/" };
  let failure = "";
  globalThis.fetch = async (url) => {
    const path = new URL(url).pathname;
    assert(path.startsWith("/nested/app/"), "assets resolve relative to the app");
    if (path.endsWith("catlin-model.json")) return Response.json(encoded.manifest);
    const bytes = encoded.files.get(path.replace("/nested/app/", ""));
    if (!bytes || failure === "missing") return new Response("missing", { status: 404 });
    if (failure === "html") return new Response("<!doctype html>");
    if (failure === "length") return new Response(new Uint8Array());
    if (failure === "hash") return new Response(Buffer.from([bytes[0] ^ 1]));
    return new Response(bytes);
  };
  assert.deepEqual(await loadModelSnapshot(), model);
  for (failure of ["missing", "html", "length", "hash"]) await assert.rejects(loadModelSnapshot());

  const app = join(temporary, "app");
  mkdirSync(app);
  writeSnapshotAssets(app, model);
  validateSiteAssets(temporary);
  const oversized = join(temporary, "oversized.bin");
  writeFileSync(oversized, "");
  truncateSync(oversized, MAX_ASSET_BYTES + 1);
  assert.throws(() => validateSiteAssets(temporary), /oversized.bin.*25 MiB/);
  rmSync(oversized);
  const { manifest } = encodeSnapshot(model);
  writeFileSync(join(app, manifest.chunks[0].file), "corrupt");
  assert.throws(() => validateSiteAssets(temporary), /invalid snapshot chunk/);
  rmSync(join(app, manifest.chunks[0].file));
  assert.throws(() => validateSiteAssets(temporary), /ENOENT/);
  writeSnapshotAssets(app, model);
  writeFileSync(join(app, "catlin-model", "stale.bin"), "stale");
  writeSnapshotAssets(app, model);
  assert(!existsSync(join(app, "catlin-model", "stale.bin")));
  clearSnapshotAssets(app);
  assert(!existsSync(join(app, "catlin-model.json")) && !existsSync(join(app, "catlin-model")));
  console.log("Snapshot round-trip, corruption, chunking, and site asset checks passed.");
} finally {
  globalThis.fetch = oldFetch;
  if (oldDocument === undefined) delete globalThis.document;
  else globalThis.document = oldDocument;
  rmSync(temporary, { recursive: true, force: true });
  await server.close();
}
