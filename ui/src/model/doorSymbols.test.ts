import {
  BIFOLD_LEADING_EDGE_FRACTION,
  bifoldDoorStrokes,
  bifoldFoldOffset,
  overheadDoorStrokes,
} from "./doorSymbols";
import type { Vec2 } from "./types";

const CENTER: Vec2 = [100, 50];
const TOLERANCE = 1e-9;

function distance(a: Vec2, b: Vec2): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

export function runDoorSymbolTests() {
  // A wall running left→right on screen, door operating toward the bottom of the screen.
  const width = 80;
  const overhead = overheadDoorStrokes(CENTER, 0, 1, width, 60);
  const [panel, leftTrack, rightTrack, parked] = overhead;
  if (overhead.length !== 4 || panel.dashed) {
    throw new Error("An overhead door draws a solid closed panel plus three dashed track lines");
  }
  if (!leftTrack.dashed || !rightTrack.dashed || !parked.dashed) {
    throw new Error("Overhead track and the parked panel are above the cut plane and must be dashed");
  }
  if (Math.abs(distance(panel.points[0], panel.points[1]) - width) > TOLERANCE) {
    throw new Error("The closed overhead panel must span the full rough opening");
  }
  if (overhead.some((stroke) => stroke.points.some(([, y]) => y > CENTER[1] + TOLERANCE))) {
    throw new Error("Overhead track must project to the handed operating side only");
  }

  // Handing flips the whole glyph to the other side of the wall, as the swing arc does.
  const flipped = overheadDoorStrokes(CENTER, 0, -1, width, 60);
  if (flipped.some((stroke) => stroke.points.some(([, y]) => y < CENTER[1] - TOLERANCE))) {
    throw new Error("A flipped overhead door must project its track to the opposite side");
  }

  // Rigid leaves: both segments of a folded half are exactly a quarter of the opening.
  const [leftHalf] = bifoldDoorStrokes(CENTER, 0, 1, width);
  const leafLength = width / 4;
  const [jamb, knuckle, leadingEdge] = leftHalf.points;
  if (Math.abs(distance(jamb, knuckle) - leafLength) > 1e-9
    || Math.abs(distance(knuckle, leadingEdge) - leafLength) > 1e-9) {
    throw new Error("Bifold leaves must be drawn at their real quarter-opening length");
  }
  if (knuckle[1] >= jamb[1]) {
    throw new Error("The bifold knuckle must fold toward the handed operating side");
  }
  const expectedRun = (width / 2) * BIFOLD_LEADING_EDGE_FRACTION;
  if (Math.abs(bifoldFoldOffset(width, expectedRun) - (CENTER[1] - knuckle[1])) > 1e-9) {
    throw new Error("The drawn fold offset must match the published isoceles solution");
  }
  if (bifoldDoorStrokes(CENTER, 0, 1, width).length !== 2) {
    throw new Error("A bifold pair draws one folded run per half of the opening");
  }
}
