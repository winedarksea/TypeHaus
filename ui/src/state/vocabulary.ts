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
export type Workspace = "design" | "analyze" | "document"; // tool/drawer emphasis
export type Representation = "conceptual" | "schematic" | "detailed" | "fabrication"; // detail level
// Building-science lenses (Phase 9): a lens semantically re-frames the model to answer one
// question. Air · water · thermal shipped first; vapour joined them once materials carried a
// sourced permeance (Material.vapor_permeance_at), which is what lets that lens report the
// actual perms per layer rather than only "this layer is tagged vapour".
export type Lens = "none" | "air" | "water" | "thermal" | "vapor";

// 3D trade visibility (→ 21 §3D panel WP7): one THREE.Group per trade so toggling never
// rebuilds the scene, just flips group.visible. "walls" is layer polygons (sheathing,
// insulation, cladding); "framing" is every stick in the building — wall members
// (studs/plates/headers), floor joists, roof rafters and the ridge beam, plus the standalone
// Beam/Post solids the resolver emits; "floors" is floor decks (hideable for stair continuity)
// and dropped soffits; "concrete" is the pours (slabs, footings, pads) and the fallback for any
// solid category not yet classified; "roof" is the roof shell and its edge trim, but not its
// sticks; "earth" is the translucent site context sheet; "drainage" is the whole stormwater run
// — gutters, leaders, the perimeter tile ring, trenches, drywells and the sump pit, which used
// to be split between the roof and concrete toggles. Which trade a resolved solid lands on
// is the shared table in three/solidMaterials.ts::SOLID_CATEGORY_TRADE.
export type Trade = "walls" | "openings" | "framing" | "floors" | "concrete" | "roof" | "stairs" | "furniture" | "plumbing" | "electrical" | "mechanical" | "earth" | "drainage";
export const ALL_TRADES: Trade[] = [
  "walls", "openings", "framing", "floors", "concrete", "roof", "stairs", "furniture", "plumbing", "electrical", "mechanical", "earth", "drainage",
];

// The work surfaces that replaced the old DESIGN/ANALYZE topbar buttons: the assembly /
// transition reader, the whole-model bill of parts, the panel schedule, and the luminaire
// schedule. Only one is up at a time — they are full-width readers, not inspectors, so
// stacking them would just hide the model. "circuits" and "lighting" are deliberately two
// readers over one `electrical` payload: an electrician sizing a breaker and a designer
// choosing a colour temperature are not looking for the same page.
// "data" is a fourth reader over the same `electrical` payload, beside "circuits" and
// "lighting", for the same reason those two are separate: an electrician sizing a breaker, a
// designer choosing a colour temperature and a low-voltage tech pulling CAT6 are not looking
// for the same page — and comms may not even share a raceway with the other two.
// "estimate" is a fifth reader over the takeoff payload, beside "bom": the BOM says what
// is in the house, the estimate ranks what it costs. Read-only — prices.toml is
// hand-authored and stays that way.
export type DetailView = "none" | "assembly" | "bom" | "circuits" | "lighting" | "hvac" | "plumbing" | "data" | "estimate";

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
