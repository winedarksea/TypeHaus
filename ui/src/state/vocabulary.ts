// The UI's shared vocabulary: the enumerations and small records every surface names when it
// talks about state — which tool is armed, which view is up, what a click resolved to, what a
// toast is. Split out of state/store.ts, which holds the store *machinery*; these are the
// nouns, and half the components import only these.
//
// They live one level below the store on purpose: model/visibility.ts and the 3D panel both
// need `Trade` and `SelectionKind`, and neither should have to reach through a module that
// constructs an EngineClient to get them.

export type Tool = "select" | "wall" | "opening" | "placeable" | "room" | "stair" | "dimension" | "measure";
// Task-rail groups (Phase 2): high-level buckets whose flyout palettes expand to the
// concrete Tools above. `null` = no flyout open.
export type ToolGroup = "select" | "build" | "openings" | "components" | "measure";
export type ViewMode = "2d" | "split" | "3d";
export type ThreeMode = "nordic" | "schematic";
// How much name text the 2D plan carries. One control for both room labels and object names,
// because a plan dense enough to want fewer room labels wants fewer object labels too.
// "hover" shows a label only under the pointer (a selected element always shows its own).
export type LabelMode = "all" | "hover" | "off";
// Phase 6 — three previously-conflated concepts pulled apart:
export type Workspace = "design" | "analyze" | "document"; // tool/drawer emphasis
export type Representation = "conceptual" | "schematic" | "detailed" | "fabrication"; // detail level
// Building-science lenses (Phase 9): a lens semantically re-frames the model to answer one
// question. Air · water · thermal shipped first; vapour joined them once materials carried a
// sourced permeance (Material.vapor_permeance_at), which is what lets that lens report the
// actual perms per layer rather than only "this layer is tagged vapour".
export type Lens = "none" | "air" | "water" | "thermal" | "vapor";

// 3D trade visibility (→ 21 §3D panel WP7): one THREE.Group per trade so toggling never
// rebuilds the scene, just flips group.visible. "walls" is layer polygons (sheathing,
// insulation, cladding); "framing" is wall members (studs/plates/headers); "floors" is
// floor decks (hideable for stair continuity); "concrete" is resolved solids (slabs,
// footings, pads); "roof" is the roof surface + its members (incl. ridge beam); "earth"
// is the translucent site context sheet.
export type Trade = "walls" | "openings" | "framing" | "floors" | "concrete" | "roof" | "stairs" | "furniture" | "plumbing" | "electrical" | "mechanical" | "earth";
export const ALL_TRADES: Trade[] = [
  "walls", "openings", "framing", "floors", "concrete", "roof", "stairs", "furniture", "plumbing", "electrical", "mechanical", "earth",
];

// The work surfaces that replaced the old DESIGN/ANALYZE topbar buttons: the assembly /
// transition reader, the whole-model bill of parts, the panel schedule, and the luminaire
// schedule. Only one is up at a time — they are full-width readers, not inspectors, so
// stacking them would just hide the model. "circuits" and "lighting" are deliberately two
// readers over one `electrical` payload: an electrician sizing a breaker and a designer
// choosing a colour temperature are not looking for the same page.
export type DetailView = "none" | "assembly" | "bom" | "circuits" | "lighting" | "hvac" | "plumbing";

// Every kind of model record the UI can hold selected. The first five are authored elements a
// patch can edit or delete; the rest are *derived* geometry the resolver computes (a post
// or beam solid, a footing's gravel bed, a roof, a framed floor, one framing member) —
// selectable and inspectable in 3D, but only editable through the element they came from. The
// same vocabulary is written into glTF node extras (emit/gltf/emitter.py::_SELECTION_KINDS) and
// emitted by the 3D pick handler (components/Panel3D.tsx), so all three surfaces agree on what
// a click resolves to. "member" is UI-only for now: the glb emitter merges framing into shared
// nodes, so only the model.json render path can resolve a click to a single stick.
export type SelectionKind =
  | "wall" | "opening" | "room" | "stair" | "canvas_object"
  | "solid" | "footing_bedding" | "floor" | "roof" | "brace" | "member";
export const ALL_SELECTION_KINDS: SelectionKind[] = [
  "wall", "opening", "room", "stair", "canvas_object", "solid", "footing_bedding", "floor", "roof",
  "brace", "member",
];
export const DERIVED_SELECTION_KINDS: SelectionKind[] = [
  "solid", "footing_bedding", "floor", "roof", "brace", "member",
];

export interface Selection {
  kind: SelectionKind | null;
  uid: string | null;
}

export interface ViewTransform {
  scale: number; // pixels per meter
  tx: number; // pixel pan
  ty: number;
}

export interface Conflict {
  message: string;
  changed?: string[];
}

export interface Toast {
  id: number;
  message: string;
  kind: "info" | "error";
}
