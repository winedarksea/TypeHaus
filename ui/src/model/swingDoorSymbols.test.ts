import fixtures from "./swingDoorFixtures.json";
import { swingDoorDimensions, swingDoorGeometry } from "./swingDoorSymbols";
import type { Opening, Vec2 } from "./types";

function close(actual: number, expected: number, message: string) {
  if (Math.abs(actual - expected) > 1e-7) throw new Error(`${message}: ${actual} != ${expected}`);
}

export function runSwingDoorSymbolTests() {
  for (const fixture of fixtures) {
    const input = { ...fixture.input, center: fixture.input.center as Vec2 };
    const geometry = swingDoorGeometry(input);
    for (const kind of ["leaves", "jambs"] as const) {
      if (geometry[kind].length !== fixture.expected[kind].length) throw new Error(`Missing ${kind}`);
      geometry[kind].forEach((outline, index) => outline.forEach((point, vertex) => {
        const expected = fixture.expected[kind][index][vertex];
        close(point[0], expected[0], `${kind} Python parity x`);
        close(point[1], expected[1], `${kind} Python parity y`);
      }));
    }
    for (const arc of geometry.arcs) {
      close(Math.hypot(arc.openTip[0] - arc.hinge[0], arc.openTip[1] - arc.hinge[1]),
        arc.radius, "The arc ends on the open leaf");
      close(Math.hypot(arc.closedTip[0] - arc.hinge[0], arc.closedTip[1] - arc.hinge[1]),
        arc.radius, "The arc starts at the closed leaf tip");
      const side = geometry.arcs.length === 2 ? (arc === geometry.arcs[0] ? -1 : 1) : input.hingeSign;
      if (arc.sweepFlag !== (side * input.operatingSign > 0 ? 1 : 0)) {
        throw new Error("Arc sweeps toward the authored operating side, including 180 degree stops");
      }
    }
    const shifted = swingDoorGeometry({ ...input,
      dimensions: { ...input.dimensions, leaf_normal_m: input.dimensions.leaf_normal_m + 0.1 } });
    if (JSON.stringify(geometry.jambs) !== JSON.stringify(shifted.jambs)) {
      throw new Error("Moving an exterior leaf must not move its frame");
    }
  }
  // Compatibility for downloaded snapshots predating the resolved glyph dimensions.
  const oldOpening = { width_m: 0.95,
    sizing: { rough_w_m: 0.95, jamb_allowance_m: 0.0254, leaf_w_m: 0.8932 } } as Opening;
  const oldDimensions = swingDoorDimensions(oldOpening, 0.15);
  close(oldDimensions.hinge_half_m, 0.4496, "Held opening hinge face");
  close(oldDimensions.leaf_width_m, 0.8932, "Held leaf width");
  if (oldDimensions.jamb_thickness_m >= oldOpening.sizing!.jamb_allowance_m) {
    throw new Error("Shim allowance must not become visible jamb stock");
  }
  const dimensions = fixtures[0].input.dimensions;
  if (swingDoorDimensions({ ...oldOpening, door_plan_dimensions: dimensions }, 0.15) !== dimensions) {
    throw new Error("Resolved dimensions take precedence over legacy schematic defaults");
  }
}
