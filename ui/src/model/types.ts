// TypeScript mirror of the server's model.json contract (→ 20 §model.json,
// server/model_json.py). All geometry is canonical SI meters; the UI is a pure view
// over this document and never re-measures geometry (→ 21b: every number derives from
// model.json). Keep this file in lockstep with `model_to_dict`.

export type Vec2 = [number, number];

export interface Provenance {
  file: string;
  line: number;
}

export interface Layer {
  name: string;
  function: string;
  material: string;
  thickness_m: number;
  polygon: Vec2[];
  control: string[];
  // Insulation filling a STRUCTURE layer's framing bays: shares that layer's polygon and
  // adds no wall depth, so consumers must not treat it as a band of its own.
  is_cavity?: boolean;
  cavity_host?: string | null;
}

// Orientation convention (defined once, engine side: resolve/framing/profiles.py):
// width_m is always the "thickness" face — 1.5" for a stud along the wall axis, the
// narrow face of a joist/rafter along its span. depth_m is always the "wide" face —
// 3.5"+ through a wall, or the vertical depth of a joist/rafter/beam. Holds regardless
// of the member's plan orientation, including "i_joist" (there width_m is flange width).
export type MemberShape = "rect" | "i_joist";

export interface Member {
  key: string;
  category: string; // stud | plate | header | joist | rim | ridge_beam | ...
  profile: string; // never parsed client-side — shape/width_m/depth_m are pre-resolved below
  p0: Vec2;
  p1: Vec2;
  z0_m: number;
  z1_m: number;
  // A raked member has different lower/upper elevations at its second endpoint.
  z0_end_m: number | null;
  z1_end_m: number | null;
  shape: MemberShape;
  width_m: number;
  depth_m: number;
  flange_width_m: number | null; // i_joist only
  flange_thickness_m: number | null; // i_joist only
  web_thickness_m: number | null; // i_joist only
  plies: number;
  // Plan-frame axis a vertical member (p0 == p1) is oriented along, e.g. a stud's wall
  // direction — null for horizontal/sloped members, which carry their own axis in p0->p1.
  orient: Vec2 | null;
  // Free-form connection annotation (e.g. "ridge:adjustable-slope-hanger") for the 2D
  // detail pipeline; not structured, not geometry.
  connection: string | null;
}

export interface Wall {
  uid: string;
  tag: string;
  storey: string;
  assembly: string;
  provenance: Provenance | null;
  axis: [Vec2, Vec2];
  z0_m: number;
  z1_m: number;
  // A `ToRoof` wall's raked top elevations at its two axis endpoints (null for ordinary
  // rectangular walls, where z1_m alone is the top) — the same fields the 2D section
  // cutter uses to interpolate a sloped top (→ emit/draw/section.py::_wall_top_at_cut).
  top_z0_m: number | null;
  top_z1_m: number | null;
  is_foundation: boolean;
  layers: Layer[];
  members: Member[];
}

export interface Opening {
  uid: string;
  tag: string;
  // The engine serializes the authored host-wall tag (for example, "W-101"), not its
  // minted UID. Keep this aligned with model_json.py so 2D host resolution is reliable.
  host: string;
  // Semantic kind is authoritative. `is_door` remains for compatibility with existing
  // editor consumers while RoughOpening support reaches every presentation surface.
  kind: "door" | "window" | "rough_opening";
  is_door: boolean;
  provenance: Provenance | null;
  type_ref: string | null;
  width_m: number;
  height_m: number;
  sill_m: number;
  center_along_m: number;
  // A nonzero rise turns the rectangular head into a semicircular arch soffit.
  arch_rise_m: number;
  swing_clearance?: Vec2[];
  framing_bumper?: Vec2[];
  flip_hinge: boolean;
  flip_swing: boolean;
}

export interface PlanNode {
  tag: string;
  storey: string;
  x_m: number;
  y_m: number;
  open_end: boolean;
  provenance: Provenance | null;
}

export interface Junction {
  node: string;
  storey: string;
  point: Vec2;
  kind: "open_end" | "collinear" | "l" | "t" | "x" | "complex";
  incidents: {
    wall: string;
    endpoint: "start" | "end";
    direction: Vec2;
    assembly: string;
  }[];
  through_walls: string[];
  branch_walls: string[];
  framing_owner: string | null;
  supported: boolean;
  diagnostic: string | null;
}

export interface Room {
  uid: string;
  tag: string;
  storey: string;
  occupancy: string;
  provenance: Provenance | null;
  conditioned: boolean;
  area_m2: number;
  clear_face: Vec2[];
  floor_finish: string | null;
}

export interface Fixture {
  uid: string;
  tag: string;
  storey: string;
  type: string;
  room: string;
  wall_ref: string | null;
  position: Vec2;
  footprint_m: [number, number];
  clearance_m: [number, number, number, number] | null;
  needs: string[];
}

export interface Furniture {
  uid: string;
  tag: string;
  storey: string;
  type: string;
  position: Vec2;
  footprint_m: [number, number];
  height_m: number;
  storage: boolean;
  clearance_m: [number, number, number, number] | null;
  mesh: string | null;
}

// All non-topological placeables share this transport shape. Detailed legacy fixture and
// furniture fields remain above during the transition, while the canvas uses this list
// for appliances, mechanical, and electrical domains too.
export interface CanvasObject {
  uid: string;
  tag: string;
  storey: string;
  kind: string;
  type: string | null;
  domain: string;
  room: string | null;
  position_m: Vec2 | null;
  z_m?: number;
  rotation: number | null;
  host: string | null;
  attachment: { wall: string; face: string } | null;
  footprint?: Vec2[];
  required_clearances?: Vec2[][];
  recommended_clearances?: Vec2[][];
  framing_bumper?: Vec2[];
  ports?: { tag: string; service: string }[];
  plan_svg?: string | null;
  model_glb?: string | null;
  model_primitive?: string | null;
}

export interface CanvasObjectType {
  tag: string;
  name: string;
  domain: string;
  kind: string;
  placement: "opening_hosted" | "free_placed" | "wall_attached";
  footprint_m: [number, number] | null;
  footprint_shape_m?: Vec2[] | null;
  height_m: number | null;
  clearances?: { footprint_m: Vec2[]; purpose: string; policy: "required" | "recommended"; source: string | null; code_profile?: string | null }[];
  mount?: { kind: "floor" | "wall" | "ceiling"; elevation_m: number | null; drop_m: number | null } | null;
  ports: { tag: string; service: string }[];
  plan_svg?: string | null;
  model_glb?: string | null;
  model_primitive?: string | null;
}

export interface SpaceSummaryRow {
  storey?: string;
  conditioned_sf: number;
  unconditioned_sf: number;
  usable_sf: number;
  storage_sf: number;
  storage_ratio: number;
}

export interface SpaceSummary {
  storeys: (SpaceSummaryRow & { storey: string })[];
  overall: SpaceSummaryRow;
}

export interface BuildingHeightRow {
  roof_tag: string;
  midpoint_above_grade_m: number;
  peak_above_grade_m: number;
}

export interface BuildingHeightSummary {
  average_ground_grade_m: number;
  roofs: BuildingHeightRow[];
}

export interface Underlay {
  path: string;
  storey: string;
  origin_x_m: number;
  origin_y_m: number;
  width_m: number;
  height_m: number;
  rotation_deg: number;
  opacity: number;
  url: string;
}

export interface Condition {
  kind: string;
  key: string;
  elements: string[];
}

export interface StackEdge {
  lower: string;
  upper: string;
  overlap_m: number;
  width_change: boolean;
}

export interface FacadeWWR {
  facade: "N" | "E" | "S" | "W";
  gross_wall_area_ft2: number;
  glazing_area_ft2: number;
  ratio: number;
}

export interface CondensationProfile {
  assembly: string;
  status: "safe" | "risk" | "unknown";
  crossing_layer: string | null;
  crossing_fraction: number | null;
  unknown_materials: string[];
  points: { position: number; temperature_c: number; vapor_pressure_pa: number; saturation_pressure_pa: number }[];
}

export interface EnergyReport {
  heating_load_btu_per_hour: number;
  cooling_load_btu_per_hour: number;
  cooling_tons: number;
  unknown_inputs: string[];
  wall_comparison: {
    baseline_assembly: string;
    upgrade_assembly: string;
    area_ft2: number;
    heating_savings_btu_per_hour: number;
  } | null;
}

export interface BuildingScience {
  wwr: FacadeWWR[];
  condensation: CondensationProfile[];
  energy: EnergyReport;
}

export interface Storey {
  tag: string;
  elevation_m: number;
  ceiling_m: number;
}

// --- Authoring catalog (→ server model_json._catalog). The palette the placement and
// assembly tools draw from: product types to place, the occupancy vocabulary, and every
// assembly with its resolved layer stack. `editable` assemblies live in the house's plan/
// source (a layer edit can write back); the rest are library presets — duplicate to tweak.
export interface WindowTypeSpec {
  tag: string;
  width_m: number;
  height_m: number;
  operation: string;
}

export interface DoorTypeSpec {
  tag: string;
  width_m: number;
  height_m: number;
  operation: string;
  exterior: boolean;
}

export interface MaterialSpec {
  tag: string;
  name: string;
  r_per_inch: number | null;
  perm_rating: number | null;
  density: number | null;
}

export interface CatalogLayer {
  name: string;
  material: string;
  function: string;
  thickness_m: number;
}

export interface AssemblySpec {
  tag: string;
  editable: boolean;
  provenance: Provenance | null;
  stc: number | null;
  variant_of: string | null;
  layers: CatalogLayer[];
}

export interface Catalog {
  window_types: WindowTypeSpec[];
  door_types: DoorTypeSpec[];
  occupancies: string[];
  materials: MaterialSpec[];
  assemblies: AssemblySpec[];
  canvas_object_types?: CanvasObjectType[];
}

export interface Roof {
  uid: string;
  tag: string;
  storey: string;
  form: string;
  footprint: Vec2[];
  eave_z_m: number;
  ridge_z_m: number;
  ridge_direction: "x" | "y";
  assembly: string;
  surface_area_m2: number;
  members: Member[];
  provenance: Provenance | null;
}

// Slabs, pads, and footings — a resolved horizontal or below-grade solid with a plan
// outline (→ resolve/model.py ResolvedSolid).
export interface Solid {
  uid: string;
  tag: string;
  storey: string;
  category: string; // slab | footing | pad
  outline: Vec2[];
  voids: Vec2[][];
  z0_m: number;
  z1_m: number;
  assembly: string | null;
  provenance: Provenance | null;
}

export interface Floor {
  uid: string;
  tag: string;
  storey: string;
  direction: "x" | "y";
  subfloor: { material: string; thickness_m: number } | null;
  openings: Vec2[][];
  provenance: Provenance | null;
  members: Member[];
}

// A stair's scalar inputs are authored, while its risers, treads, and framing members are
// resolver output. Keeping both in this contract lets the designer preview its next valid
// solve without treating client-side arithmetic as the source of truth.
export interface Stair {
  uid: string;
  tag: string;
  storey: string;
  to_storey: string;
  floor_opening: string;
  outline: Vec2[];
  width_m: number;
  run_direction: "x" | "y";
  run_reversed: boolean;
  layout: "straight" | "u_split_landing" | "right_angle_winder";
  turn_direction: "left" | "right" | null;
  winder_count: number;
  start: Vec2 | null;
  riser_count: number;
  riser_height_m: number;
  tread_depth_m: number;
  members: Member[];
  provenance: Provenance | null;
}

export type Severity = "error" | "warn" | "info";

export type CheckResult = "pass" | "fail" | "unknown";

export interface Finding {
  // The checks framework's Finding (→ 12 §Checks). Fields are permissive because
  // different check families carry different metadata; the UI reads the common ones.
  code?: string;
  severity: Severity;
  message: string;
  element?: string | null;
  elements?: string[];
  file?: string | null;
  line?: number | null;
  result?: CheckResult;
  [k: string]: unknown;
}

export interface Model {
  revision: string;
  units: string;
  projectNorth: number;
  findings: Finding[];
  project: { name: string; uuid: string; active_code_profile?: string | null };
  site?: {
    lat: number;
    lon: number;
    true_north_deg: number;
    grade_m?: number | null;
    parcel?: Vec2[];
    spot_elevations?: { position: Vec2; elevation_m: number }[];
  };
  underlays?: Underlay[];
  storeys: Storey[];
  walls: Wall[];
  junctions?: Junction[];
  nodes?: PlanNode[]; // authored wall-graph vertices (→ _catalog sibling); absent on older json
  openings: Opening[];
  roofs?: Roof[];
  solids?: Solid[];
  floors?: Floor[];
  stairs?: Stair[];
  fixtures?: Fixture[];
  furniture?: Furniture[];
  canvas_objects?: CanvasObject[];
  rooms: Room[];
  space_summary?: SpaceSummary;
  building_height_summary?: BuildingHeightSummary;
  conditions: Condition[];
  stack_edges: StackEdge[];
  building_science?: BuildingScience | null;
  catalog?: Catalog; // authoring palette (→ _catalog); absent on older model.json
  ok?: boolean; // server/offline resolve status (state.py / bootstrap.py add this)
}
