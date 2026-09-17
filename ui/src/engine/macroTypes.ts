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
  // Walls for every missing rectangle edge (T-splitting walls it lands on) plus the Room.
  | { macro: "draw_room_rect"; storey: string; a: [number, number]; b: [number, number]; assembly: string; occupancy: string; floor_finish?: string; hint_file?: string }
  // Refused (422) while backing/MEP refs name the wall; merges rooms, drops orphan nodes.
  | { macro: "delete_wall"; storey: string; wall: string; keep_room?: string }
  | { macro: "copy_storey_layout"; storey: string; from: string }
  | { macro: "place_stair"; storey: string; seed: [string, string]; to_storey?: string; hint_file?: string; tag?: string }
  | { macro: "move_placeable"; storey: string; tag: string; position: [number | string, number | string] }
  | { macro: "rotate_placeable"; storey: string; tag: string; degrees: number; free_rotation?: boolean }
  | { macro: "attach_placeable"; storey: string; tag: string; wall: string; face: "left" | "right"; distance: number | string; gap?: number | string; rotation_offset?: number }
  | { macro: "set_placeable_mount"; storey: string; tag: string; elevation: number | string }
  | { macro: "detach_placeable"; storey: string; tag: string; position?: [string, string] }
  | { macro: "place_placeable"; storey: string; type_ref: string; position: [string, string]; hint_file?: string; tag?: string; rotation?: number; kind?: string }
  // Slide a wall-attached object along its host: replaces only distance_from_start (metres).
  | { macro: "slide_placeable"; storey: string; tag: string; distance: number }
  // Refused (400) while a run, sleeve, control or host references the tag.
  | { macro: "delete_placeable"; storey: string; tag: string }
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
