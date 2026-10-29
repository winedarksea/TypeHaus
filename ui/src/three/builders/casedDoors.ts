// Shapes consume engine-resolved dimensions; mirrors geometry_cased_doors.py.
import type { CasedDoorSpec } from "../../model/types";
import type { AddBox } from "./doorProducts";
import { buildLeverSet } from "./doorProducts";

export function buildCasedDoor(s: CasedDoorSpec, hinge: number, swing: number,
  add: { liner: AddBox; leaf: AddBox; stop: AddBox; hardware: AddBox }) {
  const [lo, hi] = s.finish_faces_m;
  const inner = s.width_m / 2 - s.jamb_allowance_m;
  const jamb = s.jamb_thickness_m, head = s.head_z_m - s.jamb_allowance_m;
  const base = s.base_z_m, height = head - base;
  const pocket = s.operation === "pocket";
  const slot = s.leaf_thickness_m + 2 * s.pocket_slot_gap_m;
  const liner = (side: number, n0: number, n1: number) => {
    if (n1 > n0) add.liner(jamb, height, n1 - n0, side * (inner + jamb / 2),
      base + height / 2, (n0 + n1) / 2);
  };
  for (const side of [-1, 1]) {
    if (pocket && side === s.pocket_sign) {
      liner(side, lo, -slot / 2); liner(side, slot / 2, hi);
    } else liner(side, lo, hi);
  }
  const headRanges = pocket ? [[lo, -slot / 2], [slot / 2, hi]] : [[lo, hi]];
  for (const [n0, n1] of headRanges) {
    const headCover = pocket ? s.track_height_m : 0;
    if (n1 > n0) add.liner(2 * inner, jamb + headCover, n1 - n0, 0,
      head + (jamb - headCover) / 2, (n0 + n1) / 2);
  }
  const leafWidth = s.leaf_width_m || 2 * (inner - s.leaf_gap_m);
  // A pocket leaf closes on the latch jamb and runs on into its slot; a swing is centred.
  const leafAlong = pocket ? s.pocket_sign * (leafWidth / 2 - (inner - s.leaf_gap_m)) : 0;
  add.leaf(leafWidth, s.leaf_top_z_m - s.leaf_bottom_z_m, s.leaf_thickness_m,
    leafAlong, (s.leaf_top_z_m + s.leaf_bottom_z_m) / 2, s.leaf_normal_m);
  if (pocket) {
    add.hardware(2 * inner, s.track_height_m, s.track_depth_m, 0, head - s.track_height_m / 2, 0);
  } else {
    const stopNormal = s.leaf_normal_m - swing * (s.leaf_thickness_m + s.stop_depth_m) / 2;
    const projection = s.stop_projection_m;
    for (const side of [-1, 1]) add.stop(projection, height, s.stop_depth_m,
      side * (inner - projection / 2), base + height / 2, stopNormal);
    add.stop(2 * (inner - projection), projection, s.stop_depth_m, 0, head - projection / 2, stopNormal);
    buildLeverSet(add.hardware, -hinge * leafWidth / 2, hinge,
      [s.leaf_normal_m - s.leaf_thickness_m / 2, s.leaf_normal_m + s.leaf_thickness_m / 2],
      Math.max(...s.finished_floor_z_m));
  }
}
