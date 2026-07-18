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
}

export interface Member {
  key: string;
  category: string; // stud | plate | header | joist | ...
  profile: string;
  p0: Vec2;
  p1: Vec2;
  z0_m: number;
  z1_m: number;
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
  is_foundation: boolean;
  layers: Layer[];
  members: Member[];
}

export interface Opening {
  uid: string;
  tag: string;
  host: string; // host wall uid
  is_door: boolean;
  provenance: Provenance | null;
  width_m: number;
  height_m: number;
  sill_m: number;
  center_along_m: number;
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

export type Severity = "error" | "warn" | "info";

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
  [k: string]: unknown;
}

export interface Model {
  revision: string;
  units: string;
  projectNorth: number;
  findings: Finding[];
  project: { name: string; uuid: string };
  storeys: Storey[];
  walls: Wall[];
  openings: Opening[];
  rooms: Room[];
  conditions: Condition[];
  stack_edges: StackEdge[];
  building_science?: BuildingScience | null;
  ok?: boolean; // server/offline resolve status (state.py / bootstrap.py add this)
}
