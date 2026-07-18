// The single typed boundary through which all engine access flows (→ 21 §EngineClient
// boundary, #15). No component touches the network directly. The M2 implementation is
// HttpEngineClient; a PyodideEngineClient (in-browser engine in a Web Worker) can slot in
// for the offline PWA (→ 40) without touching any editor code.

import type { Finding, Model } from "../model/types";

// A patch op mirrors the server's PatchOp (source/ops.py): element-level and flat.
// `fields` carry authored-unit strings ("12'-6\"") and plain scalars; the server encodes
// them into dialect source via libcst writeback.
export interface PatchOp {
  op: "add" | "update" | "delete";
  type: string; // element kind name, e.g. "Wall"
  tag: string;
  fields?: Record<string, unknown>;
  hint_file?: string | null;
  hint_list?: string | null;
}

export interface PatchResult {
  revision: string;
  minted: Record<string, string>;
  undo: number;
  redo: number;
}

export interface HistoryResult {
  revision: string;
  undo: number;
  redo: number;
}

export interface BuildResult {
  ok: boolean;
  revision: string;
}

// Server push events over the WebSocket (server/app.py broadcasts).
export type EngineEvent =
  | { type: "patched"; revision: string; minted: Record<string, string>; undo: number; redo: number }
  | { type: "build"; revision: string }
  | { type: "undo"; revision: string; undo: number; redo: number }
  | { type: "redo"; revision: string; undo: number; redo: number }
  | { type: "file-changed"; revision: string; ok: boolean };

export type EngineArtifact = "ifc";

export interface EngineClient {
  getModel(): Promise<Model>;
  getChecks(): Promise<Finding[]>;
  patchPlan(ops: PatchOp[], revision: string): Promise<PatchResult>;
  build(): Promise<BuildResult>;
  undo(): Promise<HistoryResult>;
  redo(): Promise<HistoryResult>;
  getArtifact(kind: EngineArtifact): Promise<Blob>;
  // Subscribe to server push; returns an unsubscribe function.
  events(onEvent: (e: EngineEvent) => void, onStatus?: (up: boolean) => void): () => void;
}

// Raised on a 409 revision precondition failure — the conflict banner path (#30).
export class RevisionConflict extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RevisionConflict";
  }
}

export class EngineError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "EngineError";
  }
}
