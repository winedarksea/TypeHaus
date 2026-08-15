import { crossWidth, isVerticalMember, memberFootprint } from "./memberFootprint";
import type { Member, Vec2 } from "./types";

// Minimal member stubs: only the fields memberFootprint reads are worth stating, and stating
// the rest would hide which ones the geometry actually depends on.
function member(fields: Partial<Member>): Member {
  return {
    category: "stud", p0: [0, 0], p1: [0, 0], width_m: 0.0381, depth_m: 0.1397,
    // z0_m..z1_m is what says which way the member was laid, so a stub that omits it says
    // nothing: default to standing on edge (depth_m tall) and let a flat case state its own.
    z0_m: 0, z1_m: 0.1397,
    orient: null, plan_outline: null, ...fields,
  } as unknown as Member;
}

const extent = (ring: Vec2[], axis: 0 | 1) =>
  Math.max(...ring.map((p) => p[axis])) - Math.min(...ring.map((p) => p[axis]));

const near = (a: number, b: number) => Math.abs(a - b) < 1e-9;

export function runMemberFootprintTests() {
  // A resolver-cut outline is the authority — never re-derived from p0/p1.
  const cut: Vec2[] = [[0, 0], [1, 0], [1, 1]];
  if (memberFootprint(member({ plan_outline: cut, p1: [3, 0] })) !== cut) {
    throw new Error("memberFootprint must pass a resolved plan_outline through unchanged");
  }
  // Fewer than 3 points is not a polygon; fall back rather than emit a degenerate ring.
  if (memberFootprint(member({ plan_outline: [[0, 0], [1, 0]], p1: [2, 0] })).length !== 4) {
    throw new Error("A plan_outline with under 3 points must fall back to the derived footprint");
  }

  // A stud seen end-on: p0 == p1, so it has no plan run and its mark is a rectangle, not a
  // point. `orient` is the *thickness* axis (along the wall), so the 5.5" depth face must
  // come out perpendicular to it — a stud drawn the other way round reads as a smear across
  // the wall instead of a 1.5" end-cut. Mirrors resolve/framing/footprint.py.
  const stud = member({ orient: [1, 0] });
  if (!isVerticalMember(stud)) throw new Error("p0 == p1 must read as a vertical member");
  const studRing = memberFootprint(stud);
  if (studRing.length !== 4 || !near(extent(studRing, 0), 0.0381) || !near(extent(studRing, 1), 0.1397)) {
    throw new Error("A vertical member must draw width_m along orient and depth_m across it");
  }
  // Rotating the wall rotates the stud with it: the same rectangle, axes swapped.
  const turned = memberFootprint(member({ orient: [0, 1] }));
  if (!near(extent(turned, 0), 0.1397) || !near(extent(turned, 1), 0.0381)) {
    throw new Error("A vertical member's rectangle must follow its orient axis");
  }
  // A 45° wall: neither axis-aligned extent is width or depth, but the ring stays centred
  // on p0 and keeps its area — the check that the two axes were not silently swapped.
  const s = Math.SQRT1_2;
  const diagonal = memberFootprint(member({ p0: [2, 3], p1: [2, 3], orient: [s, s] }));
  const expectedDiagonalExtent = (0.0381 + 0.1397) * s;
  if (!near(extent(diagonal, 0), expectedDiagonalExtent) || !near(extent(diagonal, 1), expectedDiagonalExtent)) {
    throw new Error("A vertical member on a skewed wall must stay an oriented width x depth rect");
  }
  if (!near(diagonal.reduce((sum, p) => sum + p[0], 0) / 4, 2)
    || !near(diagonal.reduce((sum, p) => sum + p[1], 0) / 4, 3)) {
    throw new Error("A vertical member's rectangle must stay centred on p0");
  }
  // No orient to align to (the resolver left it null): axis-aligned, still centred on p0.
  const unoriented = memberFootprint(member({ p0: [1, 1], p1: [1, 1] }));
  if (!near(extent(unoriented, 0), 0.0381) || !near(extent(unoriented, 1), 0.1397)) {
    throw new Error("A vertical member without orient must fall back to an axis-aligned rect");
  }

  // Horizontal members: a band along the run, of the face they actually show in plan. A
  // plate lies flat, so that is depth_m — the plate rule three/memberBox.ts builds boxes by.
  const joist = member({ category: "joist", p0: [0, 0], p1: [0, 2] });
  const joistRing = memberFootprint(joist);
  if (crossWidth(joist) !== 0.0381 || joistRing.length !== 4
    || !near(extent(joistRing, 0), 0.0381) || !near(extent(joistRing, 1), 2)) {
    throw new Error("An on-edge horizontal member must draw a width_m band along its run");
  }
  const flat = { p0: [0, 0] as Vec2, p1: [4, 0] as Vec2, z0_m: 0, z1_m: 0.0381 };
  const plate = member({ category: "plate", ...flat });
  const plateRing = memberFootprint(plate);
  if (crossWidth(plate) !== 0.1397 || !near(extent(plateRing, 1), 0.1397)
    || !near(extent(plateRing, 0), 4)) {
    throw new Error("A plate lies flat, so its plan band must be depth_m wide, not width_m");
  }
  // The rule is the member's own z-extent, not its category name. Blocking courses and rough
  // sills lie just as flat as a plate and used to fall through to width_m — a 1.5" ribbon down
  // the middle of a 5.5" wall, running past the rough-opening mask at every jamb.
  for (const category of ["raked_plate", "blocking", "sill", "partition", "brand_new_category"]) {
    if (crossWidth(member({ category, ...flat })) !== 0.1397) {
      throw new Error(`A flat-laid ${category} must draw its depth_m face, whatever it is called`);
    }
  }
  // ...and a category that *can* lie either way is read each time, not remembered.
  if (crossWidth(member({ category: "blocking", p0: [0, 0], p1: [4, 0] })) !== 0.0381) {
    throw new Error("Blocking standing on edge must still draw its width_m face");
  }
  // A raked member climbs meters end to end; only the extent at one station names the lay.
  const rafter = member({
    category: "rafter", p0: [0, 0], p1: [0, 4], z0_end_m: 2, z1_end_m: 2 + 0.1397,
  });
  if (crossWidth(rafter) !== 0.0381) {
    throw new Error("A raked member's lay must read from z1_m - z0_m, not its end-to-end rise");
  }
}
