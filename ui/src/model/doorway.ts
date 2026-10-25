export interface DoorwayProductSpec {
  product_ref: string;
  variant: string;
  role: "sill" | "track" | "guide" | "bottom_seal" | "transition";
  source_url: string;
  source_drawing: string;
  installation: string;
  positive_normal_sign: number;
  purchase: "separate" | "factory_included" | "kit_included";
  parts: { name: string; material_ref: string; polygon_m: [number, number][];
    material_key?: "door_hardware" | "door_frame" | "shadow_gap" }[];
}
export interface ExteriorDoorPlacement {
  outward_sign: number;
  frame_inner_m: number;
  frame_outer_m: number;
  leaf_normal_m: number;
  interior_finish_stop_m: number;
  exterior_finish_stop_m: number;
  factory_depth_documented: boolean;
  boards: { name: string; width_m: number; height_m: number; depth_m: number;
    along_m: number; z_m: number; normal_m: number; material_ref: string;
    material_key: string; role?: string }[];
  sections?: { name: string; polygon_m: [number, number][]; span_m: number;
    along_m: number; material_ref: string; material_key: string; purchase: string }[];
  sill_design_status?: "UNKNOWN" | "SCHEMATIC";
}
export interface DoorwayAssembly {
  rough_opening_z_m: number;
  adjacent_floors: ({ deck_tag: string; deck_top_m: number; room_tag: string | null;
    finish_ref: string | null; finish_in: number | null } | null)[];
  floor_treatment: string;
  joint_normal_m: number;
  components: { specification: DoorwayProductSpec; base_z_m: number;
    normal_m: number; span_m: number; along_m: number }[];
  unknown: string[];
  conflicts: string[];
  status: "VERIFIED" | "UNKNOWN" | "FAIL";
  leaf_bottom_z_m: number | null;
  jamb_bottom_z_m?: number | null;
  exterior_placement?: ExteriorDoorPlacement | null;
  section_status?: "DOCUMENTED" | "UNKNOWN";
  supplier_status?: "CONFIRMED" | "PENDING";
  fit_status?: "VERIFIED" | "UNKNOWN" | "FAIL";
}

