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
}

