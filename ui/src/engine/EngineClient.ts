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

export interface UnderlayCalibration {
  path: string;
  storey: string;
  origin_x_m: number;
  origin_y_m: number;
  width_m: number;
  height_m: number;
  rotation_deg: number;
  opacity: number;
}

// Server push events over the WebSocket (server/app.py broadcasts).
export type EngineEvent =
  | { type: "patched"; revision: string; minted: Record<string, string>; undo: number; redo: number }
  | { type: "build"; revision: string }
  | { type: "undo"; revision: string; undo: number; redo: number }
  | { type: "redo"; revision: string; undo: number; redo: number }
  | { type: "file-changed"; revision: string; ok: boolean };

export type EngineArtifact = "ifc" | "glb";

// A server-side geometry macro (server/macros_api.py). The UI sends screen intent (draw
// endpoints, the wall to split, a drag delta) as authored-unit strings; the engine owns all
// geometry math and returns ordinary journaled ops plus the #33 reference remap.
export type MacroRequest =
  | { macro: "draw_wall"; storey: string; start: [string, string]; end: [string, string]; assembly: string; tag?: string; hint_file?: string }
  | { macro: "move_nodes"; storey: string; nodes: string[]; dx: string; dy: string }
  | { macro: "split_wall"; storey: string; wall: string; at: [string, string] }
  | { macro: "heal_walls"; storey: string; node: string }
  // Library macros (no storey): the assembly-editor clone-and-tweak flow (→ 21b WP2.4d/e).
  | { macro: "duplicate_assembly"; source: string; tag: string }
  | { macro: "blank_assembly"; tag: string }
  | { macro: "add_material"; material: { tag: string; name: string; r_per_inch?: number; perm_rating?: number; density?: number } };

export interface ReferenceRemap {
  renamed: Record<string, string>;
  deleted: string[];
  rehost: Record<string, string>;
}

export interface MacroResult extends PatchResult {
  remap: ReferenceRemap;
  deleted: string[];
  warnings: string[];
}

export interface EngineClient {
  getModel(): Promise<Model>;
  getChecks(): Promise<Finding[]>;
  patchPlan(ops: PatchOp[], revision: string): Promise<PatchResult>;
  runMacro(request: MacroRequest, revision: string): Promise<MacroResult>;
  build(): Promise<BuildResult>;
  undo(): Promise<HistoryResult>;
  redo(): Promise<HistoryResult>;
  getArtifact(kind: EngineArtifact): Promise<Blob>;
  calibrateUnderlay(calibration: UnderlayCalibration): Promise<void>;
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
