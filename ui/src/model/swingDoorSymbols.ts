/** Hinged plan geometry, mirroring emit/draw/door_symbols.py in screen coordinates. */
import type { DoorPlanDimensions, Opening, Vec2 } from "./types";
import { doorSymbolPoint } from "./doorSymbols";

// Existing cased-door schematic defaults, used for older offline model snapshots only.
const SCHEMATIC_JAMB_THICKNESS_M = 0.01905;
const SCHEMATIC_LEAF_THICKNESS_M = 0.045;

export interface SwingDoorArc {
  hinge: Vec2;
  closedTip: Vec2;
  openTip: Vec2;
  radius: number;
  sweepFlag: 0 | 1;
}

export interface SwingDoorGeometry {
  leaves: Vec2[][];
  jambs: Vec2[][];
  arcs: SwingDoorArc[];
}

export function swingDoorDimensions(opening: Opening, wallThicknessM: number): DoorPlanDimensions {
  if (opening.door_plan_dimensions) return opening.door_plan_dimensions;
  const sizing = opening.sizing;
  const product = opening.cased_product;
  const placement = opening.doorway?.exterior_placement;
  const faces = placement
    ? [placement.frame_inner_m, placement.frame_outer_m]
    : product?.finish_faces_m ?? [-wallThicknessM / 2, wallThicknessM / 2];
  return {
    hinge_half_m: sizing ? sizing.rough_w_m / 2 - sizing.jamb_allowance_m : opening.width_m / 2,
    leaf_width_m: sizing?.leaf_w_m ?? opening.width_m,
    leaf_thickness_m: product?.leaf_thickness_m ?? SCHEMATIC_LEAF_THICKNESS_M,
    jamb_thickness_m: product?.jamb_thickness_m ?? Math.min(SCHEMATIC_JAMB_THICKNESS_M,
      sizing?.jamb_allowance_m ?? SCHEMATIC_JAMB_THICKNESS_M),
    frame_normal_low_m: Math.min(...faces),
    frame_normal_high_m: Math.max(...faces),
    leaf_normal_m: placement?.leaf_normal_m ?? 0,
  };
}

export function swingDoorGeometry(input: {
  center: Vec2;
  angleRadians: number;
  operatingSign: number;
  hingeSign: number;
  doubleSwing: boolean;
  maximumOpeningDegrees: number;
  dimensions: DoorPlanDimensions;
  pixelsPerMeter: number;
}): SwingDoorGeometry {
  const { dimensions: d, pixelsPerMeter: scale, angleRadians: angle, operatingSign: swing } = input;
  const at = (along: number, normal: number): Vec2 =>
    doorSymbolPoint(input.center, angle, 1, along * scale, normal * scale);
  const jambs = [-1, 1].map(side => [
    at(side * d.hinge_half_m, d.frame_normal_low_m),
    at(side * (d.hinge_half_m + d.jamb_thickness_m), d.frame_normal_low_m),
    at(side * (d.hinge_half_m + d.jamb_thickness_m), d.frame_normal_high_m),
    at(side * d.hinge_half_m, d.frame_normal_high_m),
    at(side * d.hinge_half_m, d.frame_normal_low_m),
  ]);
  const leaves: Vec2[][] = [];
  const arcs: SwingDoorArc[] = [];
  const length = d.leaf_width_m * scale / (input.doubleSwing ? 2 : 1);
  const openingAngle = input.maximumOpeningDegrees * Math.PI / 180;
  for (const side of input.doubleSwing ? [-1, 1] : [input.hingeSign]) {
    const hinge = at(side * d.hinge_half_m, d.leaf_normal_m);
    const closedTip: Vec2 = [hinge[0] - side * Math.cos(angle) * length,
      hinge[1] - side * Math.sin(angle) * length];
    const along = -side * Math.cos(openingAngle);
    const normal = swing * Math.sin(openingAngle);
    const direction: Vec2 = [Math.cos(angle) * along + Math.sin(angle) * normal,
      Math.sin(angle) * along - Math.cos(angle) * normal];
    const openTip: Vec2 = [hinge[0] + direction[0] * length, hinge[1] + direction[1] * length];
    // SVG y is inverted: mirror the Python leaf's thickness toward the shut position.
    const thickness = d.leaf_thickness_m * scale;
    const offset: Vec2 = [direction[1] * side * swing * thickness,
      -direction[0] * side * swing * thickness];
    leaves.push([hinge, openTip, [openTip[0] + offset[0], openTip[1] + offset[1]],
      [hinge[0] + offset[0], hinge[1] + offset[1]], hinge]);
    // Handing remains unambiguous at 180°, when a cross-product test degenerates.
    arcs.push({ hinge, closedTip, openTip, radius: length,
      sweepFlag: side * swing > 0 ? 1 : 0 });
  }
  return { leaves, jambs, arcs };
}
