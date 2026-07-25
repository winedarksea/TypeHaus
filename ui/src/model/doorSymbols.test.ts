import {
  BIFOLD_LEADING_EDGE_FRACTION,
  SLIDING_PANEL_CLEARANCE_M,
  bifoldDoorStrokes,
  bifoldFoldOffset,
  doorStrokeGlyph,
  hostWallThicknessM,
  overheadDoorStrokes,
  pocketDoorStrokes,
  slidingDoorStrokes,
} from "./doorSymbols";
import type { DoorOperation, Vec2 } from "./types";

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

  checkSlidingPanelBypassesTheWall(width);
  checkPocketPanelRecedesIntoTheWall(width);
  checkStrokeGlyphDispatch();
  checkHostWallThickness();
}

/**
 * A slider is a panel standing off the wall face that parks a leaf width past one jamb.
 * Both facts are load-bearing: without the standoff it reads as a fixed panel, and without
 * the handed travel it reads as a pocket door.
 */
function checkSlidingPanelBypassesTheWall(width: number) {
  const standoff = 8;
  const strokes = slidingDoorStrokes(CENTER, 0, 1, 1, width, standoff);
  const [panel, parked, strikeTick, stopTick] = strokes;
  if (strokes.length !== 4 || panel.dashed) {
    throw new Error("A slider draws a solid closed panel plus its dashed travel and ticks");
  }
  if (!parked.dashed || !strikeTick.dashed || !stopTick.dashed) {
    throw new Error("The parked panel lies behind the wall it slides over and must be dashed");
  }
  if (Math.abs(distance(panel.points[0], panel.points[1]) - width) > TOLERANCE) {
    throw new Error("The closed sliding panel must span the full rough opening");
  }
  if (panel.points.some(([, y]) => Math.abs(y - (CENTER[1] - standoff)) > TOLERANCE)) {
    throw new Error("The sliding panel must ride at its standoff off the wall face");
  }
  if (Math.abs(distance(parked.points[0], parked.points[1]) - width) > TOLERANCE) {
    throw new Error("A slider parks one leaf width past its jamb");
  }
  // Travel is handed: it must run past one jamb only, and mirror when the handing flips.
  const travelEnd = Math.max(...strokes.flatMap((stroke) => stroke.points.map(([x]) => x)));
  if (Math.abs(travelEnd - (CENTER[0] + width / 2 + width)) > TOLERANCE) {
    throw new Error("The slider's travel must end a leaf width past the park jamb");
  }
  const flipped = slidingDoorStrokes(CENTER, 0, 1, -1, width, standoff);
  const flippedEnd = Math.min(...flipped.flatMap((stroke) => stroke.points.map(([x]) => x)));
  if (Math.abs(flippedEnd - (CENTER[0] - width / 2 - width)) > TOLERANCE) {
    throw new Error("Flipping the park jamb must mirror the slider's travel");
  }
  if (strokes.some((stroke) => stroke.points.some(([, y]) => y > CENTER[1] + TOLERANCE))) {
    throw new Error("A slider must stay on its handed operating side of the wall");
  }
}

/** A pocket panel stays on the wall axis and disappears one leaf width past the jamb. */
function checkPocketPanelRecedesIntoTheWall(width: number) {
  const stopHalf = 4;
  const strokes = pocketDoorStrokes(CENTER, 0, 1, 1, width, stopHalf);
  const [panel, receded, stop] = strokes;
  if (strokes.length !== 3 || panel.dashed) {
    throw new Error("A pocket door draws a solid closed panel, a dashed run and a dashed stop");
  }
  if (!receded.dashed || !stop.dashed) {
    throw new Error("Everything inside the pocket is concealed and must be dashed");
  }
  if (panel.points.concat(receded.points).some(([, y]) => Math.abs(y - CENTER[1]) > TOLERANCE)) {
    throw new Error("A pocket panel runs along the wall axis, with no standoff");
  }
  if (Math.abs(distance(receded.points[0], receded.points[1]) - width) > TOLERANCE) {
    throw new Error("The concealed run is the panel itself: one leaf width");
  }
  const pocketEnd = CENTER[0] + width / 2 + width;
  if (Math.abs(stop.points[0][0] - pocketEnd) > TOLERANCE
    || Math.abs(distance(stop.points[0], stop.points[1]) - 2 * stopHalf) > TOLERANCE) {
    throw new Error("The pocket stop must close the far end of the cavity, across the wall");
  }
}

/**
 * The dispatcher is what keeps the canvas from re-deriving a glyph per operation: the
 * hinged operations opt out (they draw a leaf plus an arc), and the absolute dimensions
 * scale from metres so a wider door does not get a deeper standoff.
 */
function checkStrokeGlyphDispatch() {
  const hostWallThicknessM = 0.1651; // 2x6 studs with 1/2" board each side
  const pixelsPerMeter = 40;
  const glyph = (operation: DoorOperation) => doorStrokeGlyph({
    operation, center: CENTER, angleRadians: 0, operatingSign: 1, parkJambSign: 1,
    widthM: 1.5, heightM: 2.03, hostWallThicknessM, pixelsPerMeter,
  });
  if (glyph("swing") !== null || glyph("double_swing") !== null) {
    throw new Error("Hinged operations draw a leaf and an arc, not a stroke glyph");
  }
  const counts: [DoorOperation, number][] =
    [["overhead", 4], ["bifold", 2], ["slide", 4], ["pocket", 3]];
  for (const [operation, expected] of counts) {
    if (glyph(operation)?.length !== expected) {
      throw new Error(`${operation} must resolve to ${expected} strokes`);
    }
  }
  // Both absolute sizes come from the wall, not the opening: a slider hangs clear of the
  // wall face, and the pocket stop spans the cavity the panel hides in.
  const halfWallPx = (hostWallThicknessM / 2) * pixelsPerMeter;
  const [slidingPanel] = glyph("slide")!;
  const standoffPx = CENTER[1] - slidingPanel.points[0][1];
  if (Math.abs(standoffPx - (halfWallPx + SLIDING_PANEL_CLEARANCE_M * pixelsPerMeter)) > TOLERANCE) {
    throw new Error("The sliding panel must stand clear of the wall face, not inside it");
  }
  const stop = glyph("pocket")![2];
  if (Math.abs(distance(stop.points[0], stop.points[1]) - 2 * halfWallPx) > TOLERANCE) {
    throw new Error("The pocket stop must span the wall the panel hides in");
  }
}

/** Both mirrors of the engine must agree that a bare wall list sums to the wall depth. */
function checkHostWallThickness() {
  const layers = [
    { thickness_m: 0.0127 },
    { thickness_m: 0.14, is_cavity: false },
    { thickness_m: 0.14, is_cavity: true }, // batt in the stud bays: adds no depth
  ];
  if (Math.abs(hostWallThicknessM(layers) - 0.1527) > 1e-9) {
    throw new Error("Cavity layers share their host's slice and must not add wall depth");
  }
}
