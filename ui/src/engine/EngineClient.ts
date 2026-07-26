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

// Reduced-resolve geometry for a live drag preview (→ responsiveness plan, Phase 4). Only
// what a ghost overlay draws — no layers/members/findings; not the model.json contract.
export interface PreviewWall {
  tag: string;
  storey: string;
  axis: [[number, number], [number, number]];
}
export interface PreviewOpening {
  tag: string;
  host: string;
  kind: "door" | "window" | "rough_opening";
  is_door: boolean;
  width_m: number;
  center_along_m: number;
}
export interface PreviewRoom {
  tag: string;
  storey: string;
  area_m2: number;
  clear_face: [number, number][];
}
export interface PreviewGeometry {
  walls: PreviewWall[];
  openings: PreviewOpening[];
  rooms: PreviewRoom[];
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
  | { macro: "move_nodes"; storey: string; nodes: string[]; dx: number | string; dy: number | string }
  | { macro: "split_wall"; storey: string; wall: string; at: [string, string] }
  | { macro: "heal_walls"; storey: string; node: string }
  | { macro: "place_opening"; storey: string; host: string; type_ref: string; along: string; is_door: boolean; sill?: string; hint_file?: string }
  | { macro: "place_rough_opening"; storey: string; host: string; width: string; height: string; along: string; sill?: string; hint_file?: string }
  | { macro: "move_opening"; storey: string; tag: string; along: string }
  | { macro: "rehost_opening"; storey: string; tag: string; host: string; along: string }
  | { macro: "place_room"; storey: string; seed: [string, string]; occupancy: string; floor_finish?: string; hint_file?: string }
  | { macro: "place_stair"; storey: string; seed: [string, string]; to_storey?: string; hint_file?: string; tag?: string }
  | { macro: "move_placeable"; storey: string; tag: string; position: [number | string, number | string] }
  | { macro: "rotate_placeable"; storey: string; tag: string; degrees: number; free_rotation?: boolean }
  | { macro: "attach_placeable"; storey: string; tag: string; wall: string; face: "left" | "right"; distance: number | string; gap?: number | string; rotation_offset?: number }
  | { macro: "detach_placeable"; storey: string; tag: string; position?: [string, string] }
  | { macro: "place_placeable"; storey: string; type_ref: string; position: [string, string]; hint_file?: string; tag?: string }
  | { macro: "assign_placeable_room"; storey: string; tag: string; room?: string | null }
  | { macro: "duplicate_canvas_object"; storey: string; tag: string }
  // Library macros (no storey): the assembly-editor clone-and-tweak flow (→ 21b WP2.4d/e).
  | { macro: "duplicate_assembly"; source: string; tag: string }
  | { macro: "blank_assembly"; tag: string }
  | { macro: "edit_assembly_layers"; tag: string; layers: { name: string; material: string; function: string; thickness: number | string }[] }
  | { macro: "add_material"; material: { tag: string; name: string; r_per_inch?: number; perm_rating?: number; density?: number } }
  // Materialize a transition detail's seed annotations into authored source (→ 11b WP3).
  | { macro: "seed_detail_annotations"; condition_key: string; annotations: { kind: string; anchor_uid: string; anchor_face: string; text: string; offset?: [number, number] }[] };

// A transition detail — a live-cut junction drawing (→ 11b). The index lists scaffolded
// details; getDetail returns the scene JSON (rendered client-side by DetailCanvas) plus its
// annotations and notes. Keys carry '|'/':' so getDetail passes them as a query param.
export interface DetailIndexEntry {
  key: string;
  kind: string;
  title: string;
  transition: string | null;
  overlay: string | null;
  elements: string[];
  state: "authored" | "seed";
}
export interface DetailAnnotationSpec {
  uid: string | null;
  // The authored element tag (e.g. "DA-WALL-ROOF-1") — the PatchOp address for an offset edit.
  tag: string;
  kind: string;
  anchor_uid: string;
  anchor_face: string;
  text: string;
  offset: [number, number] | null;
  state: string;
}
export interface DetailPayload {
  key: string;
  // The drawing IR scene (emit/draw/scene.py Scene.model_dump) — DetailCanvas renders it.
  // scene.notes carries pre-wrapped note lines that live OUTSIDE the drawing's coordinate
  // space; the UI shows the richer notes_markdown in its panel instead and never draws them.
  scene: { name: string; units: "in" | "mm"; nodes: Record<string, unknown>[]; notes?: string[] };
  annotations: DetailAnnotationSpec[];
  // House-relative path of the Transition.notes markdown file (identity, not content)…
  notes: string | null;
  // …and its raw content, rendered by the NotesPanel. null when the detail has no notes file.
  notes_markdown: string | null;
  findings: { check_id: string; message: string }[];
}

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
  // Transition details — read-only scene JSON, rendered client-side (→ 11b).
  getDetailIndex(): Promise<DetailIndexEntry[]>;
  getDetail(key: string): Promise<DetailPayload>;
  // Append one construction note to the detail's Transition.notes markdown file.
  // Resolves to the updated file content; rejects OfflineUnsupported without a server.
  appendDetailNote(key: string, text: string): Promise<string>;
  patchPlan(ops: PatchOp[], revision: string): Promise<PatchResult>;
  runMacro(request: MacroRequest, revision: string): Promise<MacroResult>;
  // Read-only, no revision precondition — never journaled, safe to call at drag-move
  // frequency. Rejects (OfflineUnsupported offline) if the macro's ops can't preview in
  // memory. Mirrors runMacro's request shape so a drag can reuse the same MacroRequest it
  // will later commit with runMacro on mouseup.
  previewMacro(request: MacroRequest): Promise<PreviewGeometry>;
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
