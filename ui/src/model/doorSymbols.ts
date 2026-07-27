// Door plan-symbol geometry for the 2D canvas.
//
// This mirrors `packages/engine/src/typehaus/emit/draw/door_symbols.py`: the canvas, the
// PDF and the DXF must draw the same glyph for the same door, so the constants and the
// construction below are the shared definition and the two files change together. As
// everywhere in the UI, nothing here re-measures the design — it only lays out a symbol
// around an opening the engine already placed.

import type { DoorOperation, Vec2, WindowOperation } from "./types";

// A sectional door parks its panels on horizontal track running back into the garage by
// roughly the door height; drawing that band dashed says the swept volume is ceiling
// space, which a swing arc actively mis-states.
export const OVERHEAD_TRACK_DEPTH_PER_DOOR_HEIGHT = 1;

// The bifold glyph draws the leaves part-open, otherwise the pair reads as a plain panel
// line. Fixing the leading edge at this fraction of the half-opening makes the folded
// knuckle offset exact rather than an eyeballed chevron depth.
export const BIFOLD_LEADING_EDGE_FRACTION = 0.6;

// A surface-mounted slider hangs clear of the wall face on rollers instead of filling the
// opening, so its panel draws *outside* the wall depth — half the host thickness plus this
// hardware clearance (2", mirroring `SLIDING_PANEL_CLEARANCE_IN` on the engine side).
export const SLIDING_PANEL_CLEARANCE_M = 0.0508;

export interface DoorSymbolStroke {
  points: Vec2[];
  dashed: boolean;
}

/**
 * A point in the symbol's local frame, in screen pixels: `along` runs down the wall from
 * `origin`, `across` is the handed operating side. Screen y is inverted from plan y, so
 * the +90 degree normal is [sin, -cos] — the same handedness the drawing IR uses.
 */
export function doorSymbolPoint(
  origin: Vec2,
  angleRadians: number,
  operatingSign: number,
  along: number,
  across: number,
): Vec2 {
  return [
    origin[0] + Math.cos(angleRadians) * along + Math.sin(angleRadians) * operatingSign * across,
    origin[1] + Math.sin(angleRadians) * along - Math.cos(angleRadians) * operatingSign * across,
  ];
}

/**
 * Perpendicular projection of a folded bifold knuckle, from rigid-leaf geometry: each half
 * of a pair is two leaves of a quarter-opening, and folded symmetrically the knuckle is the
 * apex of an isoceles triangle over the leading edge run.
 */
export function bifoldFoldOffset(widthPx: number, leafRunPx: number): number {
  const leafLength = widthPx / 4;
  const halfRun = leafRunPx / 2;
  return Math.sqrt(Math.max(leafLength * leafLength - halfRun * halfRun, 0));
}

/**
 * Sectional overhead door: the closed panel across the opening plus the jamb track legs and
 * the parked panel band. Everything but the closed panel is dashed — it is above the plan
 * cut — and there is deliberately no swing arc.
 */
export function overheadDoorStrokes(
  center: Vec2,
  angleRadians: number,
  operatingSign: number,
  widthPx: number,
  trackDepthPx: number,
): DoorSymbolStroke[] {
  const at = (along: number, across: number) =>
    doorSymbolPoint(center, angleRadians, operatingSign, along, across);
  const half = widthPx / 2;
  return [
    { points: [at(-half, 0), at(half, 0)], dashed: false },
    { points: [at(-half, 0), at(-half, trackDepthPx)], dashed: true },
    { points: [at(half, 0), at(half, trackDepthPx)], dashed: true },
    { points: [at(-half, trackDepthPx), at(half, trackDepthPx)], dashed: true },
  ];
}

/** Bifold pair: two folded leaf runs chevroned back from the jambs, with no swing arc. */
export function bifoldDoorStrokes(
  center: Vec2,
  angleRadians: number,
  operatingSign: number,
  widthPx: number,
): DoorSymbolStroke[] {
  const at = (along: number, across: number) =>
    doorSymbolPoint(center, angleRadians, operatingSign, along, across);
  const half = widthPx / 2;
  const leafRun = half * BIFOLD_LEADING_EDGE_FRACTION;
  const foldOffset = bifoldFoldOffset(widthPx, leafRun);
  return [-1, 1].map((side) => ({
    points: [
      at(side * half, 0),
      at(side * (half - leafRun / 2), foldOffset),
      at(side * (half - leafRun), 0),
    ],
    dashed: false,
  }));
}

/**
 * Bypass slider: the panel offset off the wall face, parking one leaf width past the jamb
 * it slides to. The parked panel is dashed — it lies behind the wall it slides over — and
 * the two short ticks close the travel so the standoff reads as track, not a second wall.
 * `parkJambSign` is the handed jamb (+1 along the wall), the same handing a hinge uses.
 */
export function slidingDoorStrokes(
  center: Vec2,
  angleRadians: number,
  operatingSign: number,
  parkJambSign: number,
  widthPx: number,
  panelStandoffPx: number,
): DoorSymbolStroke[] {
  const at = (along: number, across: number) =>
    doorSymbolPoint(center, angleRadians, operatingSign, along, across);
  const half = widthPx / 2;
  // The panel is its own travel: it parks one leaf width past the jamb it slides to.
  const parkedEnd = parkJambSign * (half + widthPx);
  return [
    { points: [at(-half, panelStandoffPx), at(half, panelStandoffPx)], dashed: false },
    { points: [at(parkJambSign * half, panelStandoffPx), at(parkedEnd, panelStandoffPx)], dashed: true },
    { points: [at(-parkJambSign * half, 0), at(-parkJambSign * half, panelStandoffPx)], dashed: true },
    { points: [at(parkedEnd, 0), at(parkedEnd, panelStandoffPx)], dashed: true },
  ];
}

/**
 * Pocket door: the panel receding along the wall axis into its cavity, dashed because it
 * is concealed inside the wall, stopped by the dashed stud at the back of the pocket.
 * Nothing stands off the wall — that is what distinguishes it from the surface slider.
 */
export function pocketDoorStrokes(
  center: Vec2,
  angleRadians: number,
  operatingSign: number,
  parkJambSign: number,
  widthPx: number,
  stopHalfLengthPx: number,
): DoorSymbolStroke[] {
  const at = (along: number, across: number) =>
    doorSymbolPoint(center, angleRadians, operatingSign, along, across);
  const half = widthPx / 2;
  const pocketEnd = parkJambSign * (half + widthPx);
  return [
    { points: [at(-half, 0), at(half, 0)], dashed: false },
    { points: [at(parkJambSign * half, 0), at(pocketEnd, 0)], dashed: true },
    { points: [at(pocketEnd, -stopHalfLengthPx), at(pocketEnd, stopHalfLengthPx)], dashed: true },
  ];
}

export interface DoorGlyphInput {
  operation: DoorOperation | undefined;
  /** Opening centre, in screen pixels. */
  center: Vec2;
  angleRadians: number;
  /** Handed operating side: which face of the wall the door works toward. */
  operatingSign: number;
  /** Handed jamb: the hinge, or the jamb a sliding/pocket panel parks against. */
  parkJambSign: number;
  widthM: number;
  heightM: number;
  hostWallThicknessM: number;
  pixelsPerMeter: number;
}

/**
 * Total depth of the wall a door sits in, mirroring `ResolvedWall.thickness_m`: cavity
 * layers share their host's slice and add nothing. A slider stands off this, and a pocket
 * panel hides inside it, so the glyph cannot be placed from the opening alone.
 */
export function hostWallThicknessM(layers: readonly { thickness_m: number; is_cavity?: boolean }[]): number {
  return layers.reduce((sum, layer) => sum + (layer.is_cavity ? 0 : layer.thickness_m), 0);
}

/**
 * The stroke-only glyph for an operation that does not swing, or null for the hinged
 * operations the canvas draws as a leaf plus an arc (see `swingArcSweepFlag`, which owns
 * the arc handedness the engine's `_quarter_swing_arc` mirrors).
 *
 * Dimensions arrive in model metres and are scaled here, so a caller never converts: the
 * sliding standoff and the pocket stop come from the wall, not from the opening width.
 */
export function doorStrokeGlyph(input: DoorGlyphInput): DoorSymbolStroke[] | null {
  const { operation, center, angleRadians, operatingSign, parkJambSign } = input;
  const widthPx = input.widthM * input.pixelsPerMeter;
  const halfWallPx = (input.hostWallThicknessM / 2) * input.pixelsPerMeter;
  switch (operation) {
    case "overhead":
      return overheadDoorStrokes(center, angleRadians, operatingSign, widthPx,
        input.heightM * OVERHEAD_TRACK_DEPTH_PER_DOOR_HEIGHT * input.pixelsPerMeter);
    case "bifold":
      return bifoldDoorStrokes(center, angleRadians, operatingSign, widthPx);
    case "slide":
      return slidingDoorStrokes(center, angleRadians, operatingSign, parkJambSign, widthPx,
        halfWallPx + SLIDING_PANEL_CLEARANCE_M * input.pixelsPerMeter);
    case "pocket":
      return pocketDoorStrokes(center, angleRadians, operatingSign, parkJambSign, widthPx,
        halfWallPx);
    default:
      return null;
  }
}

// --- window sash glyphs ------------------------------------------------------------------
//
// The same construction as the door glyphs above (`doorSymbolPoint`, handed by
// `operatingSign`), at a smaller scale: a sash projection is a *notation* — a hint at which
// way the unit opens — not the swept volume a door arc has to reserve. Architectural
// convention draws it on the hinge side of the elevation; in plan we settle for a tick that
// is unambiguous at 1/4" scale, which is the only scale the canvas is read at.

/**
 * How far a sash glyph projects off the wall line, as a fraction of the opening width.
 * Small enough that a bank of windows does not read as a row of doors, large enough that a
 * casement is distinguishable from a fixed unit without zooming.
 */
export const WINDOW_SASH_PROJECTION_FRACTION = 0.35;

/** Offset of the double-hung/slider track line off the wall line, likewise width-relative. */
export const WINDOW_TRACK_OFFSET_FRACTION = 0.12;

export interface WindowGlyphInput {
  operation: WindowOperation | undefined;
  /** Opening centre, in screen pixels. */
  center: Vec2;
  angleRadians: number;
  /** Handed operating side: which face of the wall the sash swings/slides toward. */
  operatingSign: number;
  /** Handed jamb: the hinge of a casement, or the jamb a slider's moving leaf parks at. */
  parkJambSign: number;
  widthM: number;
  pixelsPerMeter: number;
}

/**
 * The stroke glyph for a window operation, in the opening's local frame.
 *
 * A `fixed` unit returns no strokes *by construction*, not as a fallback: a picture window
 * has no sash, and the bare sill/head line the canvas already draws is its complete symbol.
 * That is exactly the distinction this whole glyph exists to make visible, so an unknown or
 * missing operation returns the empty set too rather than inventing hardware.
 */
export function windowStrokeGlyph(input: WindowGlyphInput): DoorSymbolStroke[] {
  const { operation, center, angleRadians, operatingSign, parkJambSign } = input;
  const at = (along: number, across: number) =>
    doorSymbolPoint(center, angleRadians, operatingSign, along, across);
  const widthPx = input.widthM * input.pixelsPerMeter;
  const half = widthPx / 2;
  const projection = widthPx * WINDOW_SASH_PROJECTION_FRACTION;
  const trackOffset = widthPx * WINDOW_TRACK_OFFSET_FRACTION;
  switch (operation) {
    case "casement":
      // Side-hinged: one tick from the hinge jamb out to where the free stile ends up.
      // Hinged at `parkJambSign`, so it mirrors with the same handing a door hinge uses.
      return [{ points: [at(parkJambSign * half, 0), at(-parkJambSign * half, projection)],
        dashed: false }];
    case "awning":
      // Top-hinged, projecting out at the bottom: a symmetric chevron apexed at the centre,
      // which is what separates it from the casement's one-sided tick.
      return [{ points: [at(-half, 0), at(0, projection), at(half, 0)], dashed: false }];
    case "double_hung":
      // Nothing projects — the sashes ride in the frame — so the glyph is the check-rail
      // line, drawn dashed because it sits above the plan cut like any concealed track.
      return [{ points: [at(-half, trackOffset), at(half, trackOffset)], dashed: true }];
    case "slider":
      // The moving leaf (solid) over the half it occupies, and dashed over the half it
      // slides across, in the handed direction — the door slider's logic at sash scale.
      return [
        { points: [at(-parkJambSign * half, trackOffset), at(0, trackOffset)], dashed: false },
        { points: [at(0, trackOffset), at(parkJambSign * half, trackOffset)], dashed: true },
      ];
    default:
      return [];
  }
}
