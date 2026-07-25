import { buildBillOfMaterials, memberLengthM, ringAreaM2 } from "./bom";
import type { Member, Model, Wall } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const FEET_PER_METER = 1 / 0.3048;

function member(overrides: Partial<Member>): Member {
  return {
    key: "m", category: "stud", profile: "2x6", p0: [0, 0], p1: [0, 0], z0_m: 0, z1_m: 3,
    length_m: 3, z0_end_m: null, z1_end_m: null, shape: "rect", width_m: 0.038, depth_m: 0.14,
    flange_width_m: null, flange_thickness_m: null, web_thickness_m: null, plies: 1,
    orient: null, connection: null, material: null, trade: null, ...overrides,
  };
}

function wall(members: Member[], layers: Wall["layers"]): Wall {
  return {
    uid: "W1", tag: "W-1", storey: "L1", assembly: "A-1", provenance: null,
    axis: [[0, 0], [10, 0]], z0_m: 0, z1_m: 3, top_z0_m: null, top_z1_m: null,
    is_foundation: false, layers, members,
  };
}

function model(overrides: Partial<Model>): Model {
  return {
    revision: "r", units: "imperial", projectNorth: 0, findings: [],
    project: { name: "T", uuid: "u" }, storeys: [], walls: [], openings: [], rooms: [],
    conditions: [], stack_edges: [], ...overrides,
  };
}

export function runBomTests() {
  assert(Math.abs(ringAreaM2([[0, 0], [2, 0], [2, 3], [0, 3]]) - 6) < 1e-9,
    "Shoelace area of a 2x3 rectangle is 6");
  assert(Math.abs(ringAreaM2([[0, 0], [0, 3], [2, 3], [2, 0]]) - 6) < 1e-9,
    "Winding direction must not change the billed area");

  // A stud is billed by its height; a raked rafter by its true sloped run, not its plan run.
  assert(Math.abs(memberLengthM(member({})) - 3) < 1e-9, "A vertical member's length is its height");
  const rafter = member({ p0: [0, 0], p1: [3, 0], z0_m: 0, z0_end_m: 4, z1_end_m: 4.1 });
  assert(Math.abs(memberLengthM(rafter) - 5) < 1e-9,
    "A raked member is billed along its slope (3-4-5), not its plan projection");

  const sections = buildBillOfMaterials(model({
    walls: [wall(
      [member({ profile: "2x6", category: "stud" }), member({ profile: "2x6", category: "stud" }),
        member({ profile: "2x4", category: "plate", p0: [0, 0], p1: [10, 0], z0_m: 0, z1_m: 0.038 }),
        // A skin band names a material: it is envelope, and must not be billed as lumber.
        member({ profile: "band", category: "cladding", material: "standing-seam" })],
      [{ name: "sheath", function: "sheathing", material: "zip-r", thickness_m: 0.02,
        polygon: [], control: [] }],
    )],
    solids: [{ uid: "S1", tag: "SL-1", storey: "L1", category: "slab",
      outline: [[0, 0], [3, 0], [3, 3], [0, 3]], voids: [[[0, 0], [1, 0], [1, 1], [0, 1]]],
      z0_m: 0, z1_m: 0.1, assembly: "SLAB-4", provenance: null }],
    openings: [{ uid: "O1", tag: "D-1", host: "W-1", kind: "door", is_door: true, provenance: null,
      type_ref: "DR-30", width_m: 0.9, height_m: 2.03, sill_m: 0, center_along_m: 5,
      arch_rise_m: 0, flip_hinge: false, flip_swing: false }],
  }));

  const framing = sections.find((section) => section.id === "framing")!;
  const studs = framing.rows.find((row) => row.label === "2x6")!;
  assert(studs.pieces === 2 && Math.abs(studs.quantity - 6 * FEET_PER_METER) < 1e-6,
    "Two 3 m studs bill as 2 pieces and ~19.7 lin ft");
  assert(!framing.rows.some((row) => row.label === "band"),
    "A material-bearing skin band is envelope, not framing lumber");

  const envelope = sections.find((section) => section.id === "envelope")!;
  const sheathing = envelope.rows.find((row) => row.label === "zip-r")!;
  assert(Math.abs(sheathing.quantity - 30 * FEET_PER_METER * FEET_PER_METER) < 1e-6,
    "A 10 m x 3 m wall layer bills ~323 sq ft of face area");

  const concrete = sections.find((section) => section.id === "concrete")!;
  assert(concrete.rows.length === 1 && concrete.rows[0].label === "SLAB-4",
    "Solids bill under their assembly");
  const expectedCuYd = (9 - 1) * 0.1 / (0.9144 ** 3);
  assert(Math.abs(concrete.rows[0].quantity - expectedCuYd) < 1e-9,
    "Solid volume deducts its voids before converting to cubic yards");

  const openings = sections.find((section) => section.id === "openings")!;
  assert(openings.rows.length === 1 && openings.rows[0].pieces === 1,
    "Openings are counted by catalog product type");

  // Empty sections are kept so the reader can say a house has none of something.
  assert(sections.map((section) => section.id).join() ===
    "framing,envelope,concrete,openings,placeables,returns",
    "Every BOM section is emitted, in order, even when empty");
}
