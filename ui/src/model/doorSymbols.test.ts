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
  windowStrokeGlyph,
  WINDOW_SASH_PROJECTION_FRACTION,
  WINDOW_TRACK_OFFSET_FRACTION,
} from "./doorSymbols";
import { WINDOW_OPERATION_LABELS } from "../components/WindowSettingsPopover";
import { doorTypeLabel } from "../components/DoorSettingsPopover";
import type { DoorOperation, Vec2, WindowOperation } from "./types";

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

/**
 * Window sash glyphs and the two picker label maps. Grouped with the door symbols because
 * they are the same construction and the same claim: the plan symbol and the picker label
 * must both make a fixed (picture) unit distinguishable from an operable one of equal size,
 * which is the only thing separating them once they are cut into the same rough opening.
 */
export function runWindowSymbolTests() {
  // Same wall as above: running left→right on screen, sash operating toward the bottom.
  const input = {
    center: CENTER, angleRadians: 0, operatingSign: 1, parkJambSign: 1,
    widthM: 1, pixelsPerMeter: 80,
  };
  const widthPx = 80;
  const glyph = (operation: WindowOperation | undefined) =>
    windowStrokeGlyph({ ...input, operation });

  if (glyph("fixed").length !== 0) {
    throw new Error("A fixed picture window has no sash and must draw no hardware");
  }
  if (glyph(undefined).length !== 0) {
    throw new Error("An unknown operation must draw nothing rather than invent hardware");
  }

  const [casement] = glyph("casement");
  if (glyph("casement").length !== 1 || casement.dashed) {
    throw new Error("A casement is one solid tick from its hinge jamb");
  }
  const [hinge, freeStile] = casement.points;
  if (Math.abs(hinge[0] - (CENTER[0] + widthPx / 2)) > TOLERANCE || Math.abs(hinge[1] - CENTER[1]) > TOLERANCE) {
    throw new Error("The casement tick must start on the wall line at the handed hinge jamb");
  }
  if (freeStile[1] >= CENTER[1]) {
    throw new Error("The casement sash must project to the handed operating side");
  }
  const flippedHinge = windowStrokeGlyph({ ...input, operation: "casement", parkJambSign: -1 })[0].points[0];
  if (Math.abs(flippedHinge[0] - (CENTER[0] - widthPx / 2)) > TOLERANCE) {
    throw new Error("Flipping the handed jamb must move the casement hinge to the other jamb");
  }
  const flippedSide = windowStrokeGlyph({ ...input, operation: "casement", operatingSign: -1 })[0].points[1];
  if (flippedSide[1] <= CENTER[1]) {
    throw new Error("Flipping the operating side must swing the casement tick across the wall");
  }

  const [awning] = glyph("awning");
  const [left, apex, right] = awning.points;
  if (Math.abs(left[0] - (CENTER[0] - widthPx / 2)) > TOLERANCE
    || Math.abs(right[0] - (CENTER[0] + widthPx / 2)) > TOLERANCE) {
    throw new Error("The awning chevron must span jamb to jamb");
  }
  if (Math.abs(apex[0] - CENTER[0]) > TOLERANCE || apex[1] >= CENTER[1]) {
    throw new Error("A top-hinged awning apexes at the centre, on the operating side");
  }
  if (Math.abs(CENTER[1] - apex[1] - widthPx * WINDOW_SASH_PROJECTION_FRACTION) > TOLERANCE) {
    throw new Error("The sash projection must be the published width fraction");
  }

  // The two non-projecting operations ride in the frame: their glyph is track, offset off
  // the wall line by less than a sash projects, so they never read as an opening leaf.
  const hung = glyph("double_hung");
  if (hung.length !== 1 || !hung[0].dashed) {
    throw new Error("A double-hung check rail is concealed track and must be dashed");
  }
  const trackOffset = CENTER[1] - hung[0].points[0][1];
  if (Math.abs(trackOffset - widthPx * WINDOW_TRACK_OFFSET_FRACTION) > TOLERANCE) {
    throw new Error("The track offset must be the published width fraction");
  }
  if (trackOffset >= widthPx * WINDOW_SASH_PROJECTION_FRACTION) {
    throw new Error("Track must sit closer to the wall than a projecting sash does");
  }
  const slider = glyph("slider");
  if (slider.length !== 2 || slider[0].dashed || !slider[1].dashed) {
    throw new Error("A slider draws its moving leaf solid and the half it crosses dashed");
  }
  if (slider[0].points[0][0] >= slider[1].points[1][0]) {
    throw new Error("The slider leaf must travel toward the handed park jamb");
  }

  // Every member of each vocabulary is labelled: a picker that falls through to a raw enum
  // value is the failure this map exists to prevent.
  const operations: WindowOperation[] = ["fixed", "casement", "double_hung", "slider", "awning"];
  for (const operation of operations) {
    if (!WINDOW_OPERATION_LABELS[operation]) {
      throw new Error(`Window operation ${operation} has no trade label`);
    }
  }
  if (!WINDOW_OPERATION_LABELS.fixed.includes("picture")) {
    throw new Error("The fixed label must say 'picture' — it is the one a client mis-picks");
  }

  // Every picker label carries leaf makeup; exterior French pairs and sliders must be
  // distinguishable without relying on their tags.
  const interior = { operation: "swing" as DoorOperation, exterior: false, glazed: false };
  if (doorTypeLabel(interior) !== "swing · solid") {
    throw new Error("An interior door label must state its leaf makeup");
  }
  if (doorTypeLabel({ ...interior, glazed: true }) !== "swing · glazed") {
    throw new Error("A glazed interior leaf must be labelled as such");
  }
  if (doorTypeLabel({ operation: "slide", exterior: true, glazed: true }) !== "sliding · glazed") {
    throw new Error("An exterior door label must state its glazing");
  }
}
