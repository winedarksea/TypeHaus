import { orthoLock, snapWorld, type Node } from "../../model/geometry";
import type { Vec2 } from "../../model/types";

// Both preview and taps resolve here so a click fixes exactly the point shown by the tape.
export function resolveMeasurementPoint(
  world: Vec2,
  options: {
    snappingEnabled: boolean;
    nodes: Map<string, Node>;
    toleranceM: number;
    gridM: number | null;
    start: Vec2 | null;
    shiftPressed: boolean;
  },
): Vec2 {
  const point = options.snappingEnabled
    ? snapWorld(world, options.nodes, options.toleranceM, options.gridM).point
    : world;
  return options.start && options.shiftPressed ? orthoLock(options.start, point) : point;
}
