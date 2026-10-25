export interface SnapshotChunk { file: string; byteLength: number; sha256: string }
export interface SnapshotManifest {
  format: "typehaus-model-snapshot";
  version: 1;
  byteLength: number;
  chunks: SnapshotChunk[];
}
export const SNAPSHOT_FORMAT: "typehaus-model-snapshot";
export const SNAPSHOT_VERSION: 1;
export const SNAPSHOT_CHUNK_BYTES: number;
export function packSnapshot(model: unknown): { model: unknown; meshes: unknown[] };
export function unpackSnapshot(packed: unknown): unknown;
export function validateSnapshotManifest(manifest: unknown): SnapshotManifest;
