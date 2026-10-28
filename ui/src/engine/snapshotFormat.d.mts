export interface SnapshotChunk { file: string; byteLength: number; sha256: string }
export interface SnapshotManifest {
  format: "typehaus-model-snapshot";
  version: 3;
  byteLength: number;
  chunks: SnapshotChunk[];
}
export const SNAPSHOT_FORMAT: "typehaus-model-snapshot";
export const SNAPSHOT_VERSION: 3;
export const SNAPSHOT_CHUNK_BYTES: number;
export function packSnapshot(model: unknown): { model: unknown };
export function unpackSnapshot(packed: unknown): unknown;
export function validateSnapshotManifest(manifest: unknown): SnapshotManifest;
