import type { Model } from "../model/types";
import { unpackSnapshot, validateSnapshotManifest } from "./snapshotFormat.mjs";

// A missing, stale HTML fallback, or truncated asset must leave boot on the engine path.
export async function loadModelSnapshot(file = "catlin-model.json"): Promise<Model> {
  const url = new URL(file, document.baseURI).href;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`model snapshot ${response.status} @ ${url}`);
  const manifest = validateSnapshotManifest(await response.json());
  const chunks = await Promise.all(manifest.chunks.map(async (chunk) => {
    const chunkResponse = await fetch(new URL(chunk.file, url));
    if (!chunkResponse.ok) throw new Error(`snapshot chunk ${chunkResponse.status}`);
    const bytes = await chunkResponse.arrayBuffer();
    if (bytes.byteLength !== chunk.byteLength) throw new Error("snapshot chunk length mismatch");
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    const hash = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
    if (hash !== chunk.sha256) throw new Error("snapshot chunk hash mismatch");
    return new Uint8Array(bytes);
  }));
  const bytes = new Uint8Array(manifest.byteLength);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  // Decode after concatenation: a chunk boundary may bisect a UTF-8 character.
  const model: unknown = unpackSnapshot(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)));
  if (!model || typeof model !== "object") throw new Error("model snapshot is invalid");
  const candidate = model as Partial<Model>;
  if (typeof candidate.revision !== "string" ||
      typeof candidate.project?.name !== "string" ||
      !Array.isArray(candidate.storeys) || !Array.isArray(candidate.walls) ||
      candidate.storeys.length === 0 || candidate.walls.length === 0 ||
      !candidate.storeys.every((storey) => typeof storey?.tag === "string") ||
      !candidate.walls.every((wall) => typeof wall?.uid === "string" &&
        Array.isArray(wall.axis) && wall.axis.length === 2 &&
        Array.isArray(wall.layers))) {
    throw new Error("model snapshot has no resolved house geometry");
  }
  return candidate as Model;
}
