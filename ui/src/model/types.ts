// TypeScript mirror of the server's model.json contract (→ 20 §model.json,
// server/model_json.py). All geometry is canonical SI meters; the UI is a pure view
// over this document and never re-measures geometry (→ 21b: every number derives from
// model.json). Keep this file in lockstep with `model_to_dict`.

export type Vec2 = [number, number];

/** Mirror of the engine's `DoorOperation` enum (model/enums.py). */
export type DoorOperation =
  | "swing"
  | "double_swing"
  | "slide"
  | "pocket"
  | "bifold"
  | "overhead";

/** Mirror of the engine's `WindowOperation` enum (model/enums.py). */
export type WindowOperation =
  | "fixed"
  | "casement"
  | "double_hung"
  | "slider"
  | "awning"
  | "tilt_turn";

export interface Provenance {
  file: string;
  line: number;
  // false → runtime-captured (params-generated) authorship: a read-only "defined here"
  // pointer, never a writeback destination.
  editable: boolean;
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
  // Semantic, resolver-minted, unique within the parent wall/roof/floor/stair ("stud-007",
  // "plate-bottom"). Joined to the parent uid it is the member's stable identity — see
  // model/memberIdentity.ts, which is what per-member 3D picking selects with.
  key: string;
  category: string; // stud | plate | header | joist | rim | ridge_beam | ...
  profile: string; // never parsed client-side — shape/width_m/depth_m are pre-resolved below
  p0: Vec2;
  p1: Vec2;
  z0_m: number;
  z1_m: number;
  // The resolver's own run length. Not derivable from p0/p1 client-side: a vertical stud has
  // no plan run at all, and a raked rafter's plan run is shorter than the stick it cuts.
  length_m: number;
  // A raked member has different lower/upper elevations at its second endpoint.
  z0_end_m: number | null;
  z1_end_m: number | null;
  plan_outline?: Vec2[] | null;
  // A straight tread's riser face — the going*i line the 2D stair icon marks. The axis
  // p0/p1 is the board centreline, half a going past it (drawing the axis made uniform
  // flights read as unevenly stepped). Absent on winders: their axis IS the fan line.
  riser_line?: [Vec2, Vec2] | null;
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
  // Catalog material ref for members that are envelope *skin* rather than lumber — the
  // wall->roof closure bands, derived eave/rake trim, the roof-edge cladding. Coloured (and
  // finished, for standing seam) like the wall and roof layer stacks instead of by category.
  // Null for ordinary framing.
  material: string | null;
  // Explicit visibility trade, when the resolver had to override the category-derived default —
  // a fascia is envelope trim by category but the carpenter frames it. Null leaves the consumer
  // on its own default (three/members.ts's ROOF_SKIN_CATEGORIES split).
  trade: string | null;
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
  // The *authored* mount, beside the resolved `z_m` it produced. The inspector edits this one:
  // "46 in above this floor" is what someone wrote, and it survives a storey datum change in a
  // way a resolved absolute height does not. Absent on an object authored with no mount.
  mount?: { kind: "floor" | "wall" | "ceiling"; elevation_m: number | null; drop_m: number | null; recessed_into_host_surface?: boolean } | null;
  // Set on an object the engine recovered as an occupant of another object's clearance zone
  // (a chair at its table) — the group's uid. Members do not conflict with each other's
  // recommended clearance, and dragging the group's owner should carry them along.
  placement_group?: string | null;
  // The circuit that feeds this object, for the placeables that consume power; null for a
  // sofa, absent on older model.json. Pairs with model.electrical.panel_schedule[].devices —
  // the same edge read from the device end.
  circuit?: string | null;
  footprint?: Vec2[];
  required_clearances?: Vec2[][];
  recommended_clearances?: Vec2[][];
  framing_bumper?: Vec2[];
  ports?: { tag: string; service: string }[];
  plan_svg?: string | null;
  model_glb?: string | null;
  model_primitive?: string | null;
  // Where this object was authored. `editable: false` (or a null record) means no editable
  // plan file hosts it, so dragging it could never be written back — the 2D canvas blocks
  // the drag rather than letting it apply and snap back.
  provenance?: Provenance | null;
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
  // `recessed_into_host_surface` = the body is let into its host surface rather than standing
  // on it (a floor register dropping into its boot), so its solid runs *below* the mount
  // plane and it projects nothing into the room. Clear-floor obstruction reads this.
  mount?: { kind: "floor" | "wall" | "ceiling"; elevation_m: number | null; drop_m: number | null; recessed_into_host_surface?: boolean } | null;
  ports: { tag: string; service: string }[];
  plan_svg?: string | null;
  model_glb?: string | null;
  model_primitive?: string | null;
  // Generated plan glyph + boxy massing for types with no imported asset. Both are in the
  // type's local frame (origin at the footprint centre, +y toward the object's back, z=0 at
  // its base); the engine owns the geometry, the UI only places and draws it.
  plan_strokes?: PlanStroke[];
  model_parts?: ModelPart[];
}

export interface PlanStroke {
  points: Vec2[];
  closed: boolean;
  fill: string | null;
  weight: number;
}

export interface ModelPart {
  center: [number, number, number];
  size: [number, number, number];
  color: string;
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

// The electrical take-off, carried verbatim from takeoff/electrical.py (→ model_json.py
// "electrical"). Field names match the Python dicts exactly and the arithmetic is already
// done: the circuits reader renders these, it never recomputes them, because the same six
// derivations print the E-601 panel-schedule sheet that goes out for permit.
export interface PanelScheduleRow {
  circuit: string;
  description: string;
  breaker_amps: number;
  poles: number;
  volts: number;
  nema: string;
  gfci: boolean;
  backup: boolean;
  backup_tier: string; // "" | "always_on" | "shed"
  panel: string;
  source: boolean; // a power-source interconnection, excluded from the service load
  connected_va: number;
  devices: string[];
}

export interface ServiceLoad {
  method: string;
  floor_area_ft2: number;
  general_lighting_va: number;
  fixed_appliance_va: number;
  hvac_va: number;
  ev_va: number;
  demand_va: number;
  demand_amps: number;
  service_amps: number;
  panel_rating_amps: number;
  within_service: boolean;
}

export interface ConduitRow {
  trade_size_in: number;
  runs: number;
  length_ft: number;
  tags: string[];
}

export interface DeviceCountRow {
  kind: string;
  type: string;
  name: string;
  nema: string;
  count: number;
}

export interface SolarTakeoff {
  panels: number;
  total_watts: number;
  rsd_transmitters: number;
  by_product: { product: string; panels: number; watts: number; tags: string[] }[];
  // Per series string. Either Voc sum is null when a module in the string does not declare
  // that voltage — a partial sum of a series string is a wrong number, not a smaller one.
  by_string: {
    string: string; panels: number; watts: number;
    voc_v: number | null; voc_cold_v: number | null;
    rsd_modules: number; tags: string[];
  }[];
}

export interface BackupComponentRow {
  component: string;
  count: number;
  basis: string;
}

// The backup runtime estimate, carried verbatim from takeoff/backup_calc.py. Every
// nullable field below is null for "not computable from what is authored" and must render
// as such — a zero here would read as a measured fact about how long the house runs.
export interface BackupTierSummary {
  circuits: {
    circuit: string; description: string; connected_va: number;
    duty_cycle: number | null; average_w: number | null;
  }[];
  connected_va: number;
  average_w: number;
  daily_kwh: number;
  unknown_duty_cycle: string[];
  complete: boolean;
}

export interface BackupRuntime {
  modeled: boolean;
  estimate?: boolean;
  complete?: boolean;
  batteries?: { equipment: string; type: string; storage_kwh: number | null }[];
  batteries_without_capacity?: string[];
  inverters?: {
    equipment: string; type: string;
    kw_continuous: number | null; kw_surge: number | null; pv_input_kw: number | null;
  }[];
  pv_input_kw?: number | null;
  tiers?: { always_on: BackupTierSummary; shed: BackupTierSummary };
  peak?: {
    simultaneous_va: number; always_on_va: number;
    inverter_kw_continuous: number | null; inverter_kw_surge: number | null;
    largest_motor_start_va: number; motor_start_multiple: number;
    within_continuous: boolean | null; always_on_within_continuous: boolean | null;
    within_surge: boolean | null;
  };
  autonomy?: {
    usable_kwh: number; nameplate_kwh: number; depth_of_discharge: number;
    hours_all_tiers: number | null; hours_always_on_only: number | null; basis: string;
  };
  cycle_48h?: {
    array_kw: number; strong_day_kwh_per_kw: number; solar_day_kwh: number;
    two_day_load_kwh_all_tiers: number; two_day_load_kwh_always_on: number;
    net_kwh_all_tiers: number; net_kwh_always_on: number;
    sustains_all_tiers: boolean; sustains_always_on: boolean; basis: string;
  };
  verdict?: string;
}

// The lighting take-off, mirroring takeoff/lighting.py field for field. Every optional here
// is optional in the Python too: a fixture whose type states no lumens reports null rather
// than a plausible number, and the reader has to render that as "—" instead of "0".
export interface LuminaireScheduleRow {
  mark: string;
  type: string;
  description: string;
  form: string;
  lamp: string | null;
  watts: number | null;
  watts_per_ft: number | null;
  lumens: number | null;
  cct_k: number | null;
  cri: number | null;
  volts: number;
  mount: string;
  dimming: string;
  rating: string; // "dry" | "damp" | "wet"
  count: number;
  length_ft: number | null; // linear types are billed by the foot, not counted
  rooms: string[];
  source: string | null;
}

export interface LightingControlRow {
  tag: string;
  kind: string; // "fixture" | "run"
  mark: string;
  room: string | null;
  circuit: string | null;
  psu: string | null;
  switches: string[];
  controls: string[]; // "toggle" | "dimmer" | "timer" | "smart" | "(missing)"
  ways: number;
  integral_switch: boolean;
  cross_circuit: string[];
}

export interface LightRunRow {
  tag: string;
  type: string;
  mark: string;
  storey: string;
  room: string | null;
  length_ft: number;
  watts: number;
  volts: number;
  psu: string | null;
  circuit: string | null;
}

export interface LightRunSupplyRow {
  psu: string;
  type: string | null;
  runs: string[];
  length_ft: number;
  connected_watts: number;
  required_watts: number;
  rated_watts: number | null;
  adequate: boolean | null; // null when the supply type states no rating
}

export interface LightRunTakeoff {
  runs: LightRunRow[];
  by_type: { type: string; mark: string; runs: number; length_ft: number; watts: number }[];
  supplies: LightRunSupplyRow[];
  total_length_ft: number;
}

export interface LightingLoad {
  per_circuit: { circuit: string; fixtures: number; connected_va: number }[];
  total_connected_va: number;
  conditioned_area_ft2: number;
  allowance_va_per_ft2: number;
  allowance_va: number;
  basis: string;
}

export interface Lighting {
  schedule: LuminaireScheduleRow[];
  controls: LightingControlRow[];
  runs: LightRunTakeoff;
  connected_va: LightingLoad;
}

// The low-voltage take-off, carried verbatim from takeoff/data.py (→ model_json.py
// "electrical.data"). `poe_watts` is null, never zero, for a product that states no PoE
// draw — the budget counts those separately rather than hiding them in a total.
export interface DataDeviceRow {
  tag: string;
  type_ref: string;
  type_name: string;
  room: string;
  mount: string;
  mount_elevation_ft: number | null;
  poe_watts: number | null;
  circuit: string;
}

export interface DataRacewayRow {
  trade_size_in: number;
  service: string; // "data" | "spare"
  runs: number;
  length_ft: number;
  tags: string[];
}

export interface PoeBudget {
  devices?: number;
  powered_devices?: number;
  unknown_devices?: number;
  connected_watts?: number;
  basis?: string;
}

export interface DataTakeoff {
  devices: DataDeviceRow[];
  raceways: DataRacewayRow[];
  poe_budget: PoeBudget;
}

export interface Electrical {
  panel_schedule: PanelScheduleRow[];
  // null for a house that authors no circuits — the summary would be an estimate over nothing.
  service_load: ServiceLoad | null;
  conduit: ConduitRow[];
  devices: DeviceCountRow[];
  solar: SolarTakeoff;
  backup_components: BackupComponentRow[];
  backup_runtime?: BackupRuntime; // absent on a model.json built before the ESS refactor
  lighting?: Lighting | null; // absent on a model.json built before the lighting plan
  data?: DataTakeoff | null; // absent on a model.json built before structured cabling
}

// The HVAC take-off, carried verbatim from takeoff/hvac.py (→ model_json.py "hvac"). Field
// names match the Python dicts exactly; the zone arithmetic is the same call
// checks/mep/hvac.py::heating_capacity makes, so this reader and the finding can never
// disagree. Every capacity is optional because a datasheet number that is not authored must
// read as unknown, never as zero.
export interface HvacEquipmentRow {
  tag: string;
  uid: string;
  storey: string;
  kind: string;
  name: string | null;
  type_ref: string | null;
  room: string | null;
  zone_rooms: string[];
  outdoor_ref: string | null;
  circuit: string | null;
  heating_capacity_btuh: number | null;
  heating_capacity_at_design_btuh: number | null;
  cooling_capacity_btuh: number | null;
  min_operating_temp_f: number | null;
  ventilation_cfm: number | null;
  sensible_recovery_effectiveness: number | null;
}

export interface HvacZoneRow {
  name: string;
  equipment_tag: string;
  type_tag: string | null;
  rooms: string[];
  indoor_tags: string[];
  heating_load_btu_per_hour: number;
  heating_capacity_at_design_btuh: number | null;
  // Resistance heat inside the zone's rooms (mats, electric fireplace) and the tags it came
  // from. Already folded into heating_margin_btuh — shown separately so a margin that only
  // clears with supplemental heat reads as exactly that.
  supplemental_btuh: number;
  supplemental_tags: string[];
  heating_margin_btuh: number | null;
  cooling_load_btu_per_hour: number;
  cooling_capacity_btuh: number | null;
  cooling_margin_btuh: number | null;
  min_operating_temp_f: number | null;
  unknown_inputs: string[];
}

export interface HvacDuctRow {
  tag: string;
  uid: string;
  storey: string;
  system: string;
  routing: string;
  length_ft: number;
  width_in: number;
  depth_in: number;
  design_cfm: number | null;
  floor_ref: string | null;
}

export interface HvacRegisterRow {
  tag: string;
  uid: string;
  storey: string;
  kind: string;
  room: string | null;
  duct_ref: string | null;
  type_ref: string | null;
  type_name: string | null;
  ventilation_terminal: boolean;
}

export interface HvacVentilation {
  units: HvacEquipmentRow[];
  total_ventilation_cfm: number | null;
  terminal_count: number;
  supply_terminals: number;
  stale_terminals: number;
}

export interface Hvac {
  equipment: HvacEquipmentRow[];
  zones: HvacZoneRow[];
  unclaimed_conditioned_rooms: string[];
  ducts: HvacDuctRow[];
  registers: HvacRegisterRow[];
  ventilation: HvacVentilation;
}

// The plumbing take-off, carried verbatim from takeoff/plumbing.py (→ model_json.py
// "plumbing"). The fixture-unit arithmetic is the same takeoff/plumbing_calc.py the
// mep.pipe_sizing check grades with, so this reader and the finding can never disagree.
// Riser vertices are raw routed geometry — the reader projects, never re-derives.
export interface PlumbingRiserRun {
  tag: string;
  uid: string;
  storey: string;
  system: string;
  diameter_in: number;
  material: string | null;
  length_ft: number;
  serves: string[];
  wall_refs: string[];
  vertices: [number, number, number | null][]; // metres; z null = no authored invert
}

export interface PlumbingFixtureRow {
  tag: string;
  symbol: string;
  room: string | null;
  dfu: number | null;
  wsfu_total: number | null;
  wsfu_hot: number | null;
  wsfu_cold: number | null;
}

export interface PlumbingRunLoadRow {
  tag: string;
  uid: string;
  system: string;
  diameter_in: number;
  serves: string[];
  load: number | null;
  unit: string; // "DFU" | "WSFU"
  required_in: number | null;
  status: string | null; // "pass" | "fail" | "unknown" | null
  unresolved: string[];
}

export interface PlumbingPipeGroup {
  system: string;
  material: string;
  /** Applied coating, e.g. "lacquered" over copper — part of the grouping key, since the
   *  lacquer is a separate product and separate labour from the pipe it goes on. */
  finish: string;
  diameter_in: number;
  runs: number;
  length_ft: number;
  tags: string[];
}

export interface PlumbingFittingRow {
  system: string;
  diameter_in: number;
  fitting: string;
  count: number;
}

export interface PlumbingCastInRow {
  tag: string;
  uid: string;
  storey: string;
  host: string;
  host_category: string;
  axis: string;
  purpose: string;
  x_ft: number;
  y_ft: number;
  center_z_ft: number | null;
  pipe_in: number;
  sleeve_in: number;
  serves: string | null;
  offset_in: number | null;
}

export interface PlumbingHydrantRow {
  tag: string;
  uid: string;
  storey: string;
  type_ref: string | null;
  room: string | null;
  supply_runs: string[];
  source: string | null;
}

/** One in-line supply device: a shutoff, backflow preventer, arrestor, RO stub or the
 *  gasket/bracket/foam kit sealing an envelope penetration. */
export interface PlumbingAccessoryRow {
  tag: string;
  kind: string;
  storey: string;
  system: string | null;
  pipe_ref: string | null;
  room: string | null;
  model: string;
  accessible: boolean;
  serves: string[];
  install_parts: string[];
}

export interface Plumbing {
  riser: PlumbingRiserRun[];
  fixture_units: {
    fixtures: PlumbingFixtureRow[];
    runs: PlumbingRunLoadRow[];
    total_dfu: number | null;
    total_wsfu: number | null;
  };
  takeoff: {
    pipe: PlumbingPipeGroup[];
    fittings: PlumbingFittingRow[];
    cast_in: PlumbingCastInRow[];
    hydrants: PlumbingHydrantRow[];
    accessories: PlumbingAccessoryRow[];
  };
}

export interface Condition {
  kind: string;
  key: string;
  elements: string[];
}

// A library Transition: post-resolve *documentation* of how one condition pattern is detailed
// (control-layer continuity from face to face, plus per-layer joins). Never construction
// geometry — the assembly-details reader is its first UI consumer (→ model_json.py
// "transitions").
export interface TransitionContinuity {
  control: string;
  from_face: string;
  to_face: string;
}

export interface TransitionJoin {
  layer: string;
  side: string;
  termination_m: number;
  treatment: string;
}

export interface Transition {
  tag: string;
  pattern: string; // condition pattern this transition details, e.g. "wall_roof:*"
  overlay: string | null; // detail-overlay recipe id
  notes: string | null; // repo-relative notes path
  continuity: TransitionContinuity[];
  joins: TransitionJoin[];
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
  // Closed vocabulary mirroring the engine's `WindowOperation` enum; it selects the plan
  // symbol and separates a fixed picture unit from an operable sash of the same size.
  operation: WindowOperation;
}

export interface DoorTypeSpec {
  tag: string;
  width_m: number;
  height_m: number;
  // Closed vocabulary mirroring the engine's `DoorOperation` enum; it selects the plan
  // symbol, the framing pattern and the IFC operation type.
  operation: DoorOperation;
  exterior: boolean;
  glazed: boolean;
  // No applied casing — drywall return jamb; the viewer draws no frame boxes for it.
  trimless: boolean;
}

export interface MaterialSpec {
  tag: string;
  name: string;
  r_per_inch: number | null;
  // Water-vapour *permeability* — US perm-inch, so it scales with layer depth. For bulk
  // materials (foam, mineral wool, lumber, concrete).
  perm_rating: number | null;
  // Water-vapour *permeance* of the finished product — US perms, thickness-independent, from
  // its ASTM E96 rating (housewrap, metal cladding, foil facers, composite sheathing). Takes
  // precedence over `perm_rating`; `0` is a real vapour barrier, distinct from `null`
  // ("not authored" → report UNKNOWN, never substitute). Resolve the two through
  // `vaporPermeanceAt` (model/vapor.ts), which mirrors Material.vapor_permeance_at.
  vapor_permeance_perms?: number | null;
  density: number | null;
  // Freeform provenance for the numbers above — a URL, a standard, or "generic assumption".
  source?: string | null;
  // Authored appearance (server/model_json.py). `color` is the material's own hex; `finish`
  // names its 3D recipe ("brick" | "white-brick" | "cmu" | ...). Both are optional: a material
  // that authors neither falls back to the family inferred from its tag (nordic/palette.ts).
  color?: string | null;
  finish?: string | null;
  // A coating — sealer, stain, paint — rather than a covering: it bills by coverage area but
  // adds no thickness, so `buildRoomFloor` draws no finish plane for it. Without this a
  // sealed slab renders as two floors: the slab and a finish plane on the same face.
  coating?: boolean | null;
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

// Per-layer plan setback (m, positive inward) from the roof footprint edge — the golden
// eave detail's clip faces, computed by the engine (resolve/roof_layer_setbacks.py).
export interface RoofLayerSetback {
  layer: string;
  west: number;
  east: number;
  south: number;
  north: number;
}

export interface Roof {
  uid: string;
  tag: string;
  storey: string;
  form: string;
  footprint: Vec2[];
  // eave_z_m is the rafter-top (deck) plane; bearing_z_m is the plate top below it.
  eave_z_m: number;
  ridge_z_m: number;
  ridge_direction: "x" | "y";
  assembly: string;
  surface_area_m2: number;
  members: Member[];
  provenance: Provenance | null;
  bearing_z_m?: number | null;
  layer_edge_setbacks?: RoofLayerSetback[];
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
  // The material the authored element named directly, for the solids that have one instead of
  // an assembly (the trim-run family). Mirrors ResolvedSolid.material.
  material?: string | null;
  provenance: Provenance | null;
}

// A ConstructionRule return (→ resolve/model.py ResolvedConstructionReturn): the membrane /
// foam / liner / masonry lap that closes a resolved junction. Documentation + take-off, not
// render geometry — a correctly-placed return duplicates the mitred layer polygon its host
// wall already draws, so nothing in 3D draws these; the Inspector reads them.
export interface ConstructionReturn {
  uid: string;
  tag: string; // the ConstructionRule tag, e.g. "CR-CONC-TO-FRAMED-SILL"
  storey: string;
  kind: string; // bearing_plate | blocking | ...
  takeoff_category: string | null;
  material_ref: string;
  element_tags: string[]; // participating wall/junction tags
  outline: Vec2[];
  z0_m: number;
  z1_m: number;
  thickness_m: number;
  length_m: number;
  lap_m: number;
  thermal_continuity: boolean;
  air_vapor_continuity: boolean;
  sealant: string | null;
  flashing: string | null;
  returning_layer: string | null;
  condition_key: string | null;
  provenance: Provenance | null;
}

// Compacted washed-stone bed dug beneath a strip footing (→ resolve/model.py
// ResolvedFootingBedding). Drawn in 3D as a gravel prism between z0_m and z1_m.
// Rooftop PV module: the resolver's tilted box as two matching corner rings (metres).
export interface SolarPanel {
  uid: string;
  tag: string;
  storey: string;
  roof_ref: string;
  corners_bottom: number[][];
  corners_top: number[][];
  watts: number;
  product: string;
  provenance: Provenance | null;
}

export interface FootingBedding {
  uid: string;
  tag: string;
  storey: string;
  host_footing: string;
  outline: Vec2[];
  z0_m: number;
  z1_m: number;
  aggregate: string;
  geotextile: boolean;
  drain_tile: boolean;
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

// A diagonal brace hosts its own member the way a floor or roof hosts its sticks: it belongs
// to no deck or wall, so it carries the storey and the uid that picking and highlighting key on.
export interface Brace {
  uid: string;
  tag: string;
  storey: string;
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
  // Authored turn-landing depth (u_split_landing only); null reproduces the historical
  // "reserve one stair width" behaviour. The resolver floors it at the stair width
  // (IRC R311.7.6).
  landing_depth_m: number | null;
  authored_tread_depth_m: number | null;
  authored_nosing_depth_m: number | null;
  start: Vec2 | null;
  riser_count: number;
  riser_height_m: number;
  tread_depth_m: number;
  going_depth_m: number;
  nosing_depth_m: number;
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
  project: {
    name: string;
    uuid: string;
    active_code_profile?: string | null;
    // Default 3D framing offset, as (right, down) pan-button clicks on top of the whole-
    // building fit. Absent on older model.json, which leaves the fit unadjusted.
    default_view_pan?: [number, number];
  };
  site?: {
    lat: number;
    lon: number;
    true_north_deg: number;
    grade_m?: number | null;
    parcel?: Vec2[];
    // Plan rings the site earth sheet is cut by — one disjoint outer boundary per excavated
    // structure, resolved from every slab finishing at or below grade
    // (resolve/site_earth.py). Absent on older model.json, which leaves the sheet uncut.
    earth_voids?: Vec2[][];
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
  construction_returns?: ConstructionReturn[];
  footing_beddings?: FootingBedding[];
  solar_panels?: SolarPanel[];
  floors?: Floor[];
  stairs?: Stair[];
  braces?: Brace[];
  fixtures?: Fixture[];
  furniture?: Furniture[];
  canvas_objects?: CanvasObject[];
  rooms: Room[];
  space_summary?: SpaceSummary;
  building_height_summary?: BuildingHeightSummary;
  conditions: Condition[];
  transitions?: Transition[]; // library transition documentation; absent on older model.json
  electrical?: Electrical | null; // the electrical take-off; absent on older model.json
  hvac?: Hvac | null; // the HVAC take-off; null without preferences, absent on older model.json
  plumbing?: Plumbing | null; // the plumbing take-off; absent on older model.json
  stack_edges: StackEdge[];
  building_science?: BuildingScience | null;
  catalog?: Catalog; // authoring palette (→ _catalog); absent on older model.json
  ok?: boolean; // server/offline resolve status (state.py / bootstrap.py add this)
}
