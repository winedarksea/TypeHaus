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
  | { type: "file-changed"; revision: string; ok: boolean }
  // A queued source writeback failed; the server reverted to source truth, so the edit the
  // user already saw applied is gone. Detail is the engine's WritebackError message.
  | { type: "writeback-failed"; revision: string; detail: string };

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
  | { macro: "set_placeable_mount"; storey: string; tag: string; elevation: number | string }
  | { macro: "detach_placeable"; storey: string; tag: string; position?: [string, string] }
  | { macro: "place_placeable"; storey: string; type_ref: string; position: [string, string]; hint_file?: string; tag?: string }
  | { macro: "assign_placeable_room"; storey: string; tag: string; room?: string | null }
  | { macro: "duplicate_canvas_object"; storey: string; tag: string }
  // Swap a placeable's product type; the engine re-anchors a wall-backed unit's mounted
  // face under the footprint change and returns warnings for authored references
  // (serves lists, sleeves, …) that were sized against the old type.
  | { macro: "retype_placeable"; storey: string; tag: string; type_ref: string }
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
  // The *effective* curation flag for this condition key (Transition.stars(key)): starred
  // details make the primary drawing export (`haus print --details primary`) and are
  // highlighted in the navigator.
  star: boolean;
  // The raw authored state behind it — the transition's pattern-wide default plus the
  // per-condition overrides, so a star toggle can edit the right list instead of flipping
  // the default out from under every sibling condition (model/detailStar.ts).
  transition_star: boolean;
  starred_conditions: string[];
  unstarred_conditions: string[];
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
export interface DetailFrame {
  paper: [number, number];
  viewport: [number, number, number, number];
  center: [number, number];
  /** ARCH_SCALES' number: paper inches per model foot (1.5 for 1-1/2" = 1'-0"). */
  scale: number;
  scale_label: string;
  bands: Record<string, [number, number, number, number]>;
}

export interface DetailPayload {
  key: string;
  // The drawing IR scene (emit/draw/scene.py Scene.model_dump) — DetailCanvas renders it.
  // scene.notes carries pre-wrapped note lines that live OUTSIDE the drawing's coordinate
  // space; the UI shows the richer notes_markdown in its panel instead and never draws them.
  scene: {
    name: string;
    units: "in" | "mm";
    nodes: Record<string, unknown>[];
    notes?: string[];
    // The paper the drawing was laid out on (emit/draw/scene.py Frame). Present once the
    // engine has chosen a sheet and a scale; null means the frameless fit-to-content path,
    // which is what every detail was before paper space.
    frame?: DetailFrame | null;
  };
  annotations: DetailAnnotationSpec[];
  // House-relative path of the Transition.notes markdown file (identity, not content)…
  notes: string | null;
  // …and its raw content, rendered by the NotesPanel. null when the detail has no notes file.
  notes_markdown: string | null;
  findings: { check_id: string; message: string }[];
}

/**
 * The engine's bill of materials, verbatim.
 *
 * `takeoff/bom.py::bill_of_materials` returns a dict of sections: mostly `list[dict]` row
 * sets, plus a few scalar/dict summaries (`service_load`, `lighting_load`). It is deliberately
 * NOT remapped to a browser row type here — the browser's own second BOM implementation is
 * what this replaces, and re-shaping the payload would just rebuild the drift. The section
 * keys are the contract; `packages/engine/tests/test_bom_sweep.py` pins them, and
 * `ui/src/model/engineBom.ts` infers columns from whatever the rows actually carry so a new
 * engine section cannot silently vanish from the view.
 */
export type EngineBom = Record<string, unknown>;

// --- Cost tracking (server/costs_api.py over takeoff/costs.py) ---------------------------
// State lives in the house's costs.toml, durable and git-versioned; the UI only edits it
// through PUT /costs ops. Deliberately outside the plan patch/undo journal — paying a bill
// is not a plan edit.

export interface EnginePriceRange {
  low: number;
  high: number;
}
export interface EngineCostEntry {
  paid: boolean;
  paid_date: string | null;
  product: string | null;
  actual_cost: number | null;
  note: string | null;
}
export interface EngineExtraItem {
  id: string;
  name: string;
  cost: EnginePriceRange | null;
  paid: boolean;
  product: string | null;
  category: string | null;
  note: string | null;
}
export interface EngineEstimateRow {
  key: string;
  // Absent on a row the price table names but the BOM does not describe (an allowance).
  description?: string | null;
  quantity: number;
  unit: string;
  unit_price: EnginePriceRange;
  cost: EnginePriceRange;
  cost_fmt: string;
  // "material" | "labour" | "installed" — how the authored unit price is meant. An
  // `installed` price with no declared split lands wholly in `merged`, and a merged number
  // is never divided (→ takeoff/cost_model.py).
  basis?: string;
  material?: EnginePriceRange;
  labour?: EnginePriceRange;
  merged?: EnginePriceRange;
  waste_pct?: number;
  tax_included?: boolean;
  // True for a section whose BOM quantity already carries its waste, so `order_quantity`
  // equals `quantity` rather than growing by `waste_pct`.
  waste_in_quantity?: boolean;
  order_quantity?: number;
  // The product the PLAN specifies for this line — "LG WKHC252HBA" — where a material or a
  // product type names one (→ takeoff/product_labels.py). A label and nothing more: it is
  // never a price and takes no part in any total. Absent where the plan specifies no
  // particular product, which is the ordinary state of most of a house.
  product?: string | null;
  // Cost codes (takeoff/cost_codes.py): the NAHB account, the CSI division where one
  // applies, and the viewer trade — the same 13-value vocabulary as `Trade`.
  nahb_code?: string;
  csi_code?: string | null;
  trade?: string;
}
/** One rung of the `net → waste → ordered → contingency → overhead → profit → tax → total`
 *  ladder. `rate` is present only on the stages that are a percentage of something. */
export interface EngineBidStage {
  label: string;
  low: number;
  high: number;
  fmt: string;
  rate?: number;
}
export interface EngineEstimateSection {
  rows: EngineEstimateRow[];
  subtotal: EnginePriceRange;
  subtotal_fmt: string;
  // False for a section reported beside the construction total (furnishings).
  in_total?: boolean;
  basis?: string;
  basis_note?: string | null;
  basis_subtotals?: Record<string, EnginePriceRange>;
  waste?: EnginePriceRange;
  material_tax_already_paid?: EnginePriceRange;
  waste_in_quantity?: boolean;
}
/** `{low, high}` per named denominator ("conditioned", "gross"). */
export type EnginePerSf = Record<string, EnginePriceRange>;
export interface EngineEstimate {
  sections: Record<string, EngineEstimateSection>;
  // The *construction* total: sections with in_total false are not in it.
  total: EnginePriceRange;
  total_fmt: string;
  excluded_sections?: string[];
  excluded_total?: EnginePriceRange;
  excluded_total_fmt?: string;
  grand_total?: EnginePriceRange;
  grand_total_fmt?: string;
  // False when prices.toml declares no [basis] at all — the material/labour split is then
  // a default, not a statement, and the page says so rather than implying precision.
  basis_declared?: boolean;
  basis?: Record<string, string>;
  basis_notes?: Record<string, string | null>;
  bid?: {
    // material / labour / merged, plus a parallel `fmt` map of the same three as strings —
    // hence the union: a consumer reads the three names it knows and ignores the rest.
    net: Record<string, EnginePriceRange | Record<string, string>>;
    stages: EngineBidStage[];
    subtotal_net: EnginePriceRange;
    subtotal_ordered: EnginePriceRange;
    total: EnginePriceRange;
    total_fmt: string;
    // Material+labour the tax stage could not see, because the price is merged.
    untaxed_merged: EnginePriceRange;
    // Material the tax stage skipped because its authored price already carries tax.
    material_tax_already_paid: EnginePriceRange;
    taxable_material: EnginePriceRange;
  };
  // Both present only when the caller supplied denominators (server/costs_api.py does).
  areas?: Record<string, number>;
  per_sf?: {
    total: EnginePerSf;
    bid_total: EnginePerSf;
    sections: Record<string, EnginePerSf>;
  };
  unpriced: { section: string; key: string; quantity: number; unit: string }[];
}
export interface EngineCostsJoin {
  bom_key: string;
  key_field: string;
  quantity_field: string;
  unit: string;
  // False for a section reported beside the construction total. Two sections can share a
  // bom_key (placeables feeds both "placeables" and "furnishings").
  in_total?: boolean;
}
export interface EngineCosts {
  prices_loaded: boolean;
  estimate: EngineEstimate | null;
  // How each estimate section maps onto BOM rows — authored once in cli/prices.py
  // ESTIMATE_PLANS, so the client never re-guesses the (section, key) join.
  join: Record<string, EngineCostsJoin>;
  entries: Record<string, Record<string, EngineCostEntry>>;
  extra: EngineExtraItem[];
  // Entries whose (section, key) matches no current BOM row — surfaced, never dropped.
  stale: { section: string; key: string }[];
  totals: Record<string, unknown>;
}

export type CostsOp =
  | { op: "set_entry"; section: string; key: string; entry: Partial<Omit<EngineCostEntry, never>> }
  | { op: "set_extra"; item: Partial<EngineExtraItem> & { name: string; cost?: EnginePriceRange | number | null } }
  | { op: "delete_extra"; id: string };

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
  // The bill of materials — computed by the engine, never in the browser (see EngineBom).
  getBom(): Promise<EngineBom>;
  // Cost tracking: the costs.toml state joined against the live BOM and price estimate.
  getCosts(): Promise<EngineCosts>;
  // Fold ops over costs.toml and return the fresh payload; rejects OfflineUnsupported
  // without a server (the offline house snapshot is read-only).
  patchCosts(ops: CostsOp[]): Promise<EngineCosts>;
  // Append one construction note to the detail's Transition.notes markdown file.
  // Resolves to the updated file content; rejects OfflineUnsupported without a server.
  appendDetailNote(key: string, text: string): Promise<string>;
  patchPlan(ops: PatchOp[], revision: string): Promise<PatchResult>;
  runMacro(request: MacroRequest, revision: string): Promise<MacroResult>;
  // Read-only, no revision precondition — never journaled, safe to call at drag-move
  // frequency. Rejects (OfflineUnsupported offline) if the macro's ops can't preview in
  // memory. Mirrors runMacro's request shape so a drag can reuse the same MacroRequest it
  // will later commit with runMacro on mouseup.
  //
  // ``rehearse`` additionally asks the server whether this edit could ever be written back,
  // rejecting with a 422 EngineError when it can't. It re-reads every editable source file,
  // so callers pass it on a gesture's *first* preview only — never per drag-move frame.
  previewMacro(request: MacroRequest, rehearse?: boolean): Promise<PreviewGeometry>;
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
