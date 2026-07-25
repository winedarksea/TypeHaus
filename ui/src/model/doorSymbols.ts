// Door plan-symbol geometry for the 2D canvas.
//
// This mirrors `packages/engine/src/typehaus/emit/draw/door_symbols.py`: the canvas, the
// PDF and the DXF must draw the same glyph for the same door, so the constants and the
// construction below are the shared definition and the two files change together. As
// everywhere in the UI, nothing here re-measures the design — it only lays out a symbol
// around an opening the engine already placed.

import type { Vec2 } from "./types";

// A sectional door parks its panels on horizontal track running back into the garage by
// roughly the door height; drawing that band dashed says the swept volume is ceiling
// space, which a swing arc actively mis-states.
export const OVERHEAD_TRACK_DEPTH_PER_DOOR_HEIGHT = 1;

// The bifold glyph draws the leaves part-open, otherwise the pair reads as a plain panel
// line. Fixing the leading edge at this fraction of the half-opening makes the folded
// knuckle offset exact rather than an eyeballed chevron depth.
export const BIFOLD_LEADING_EDGE_FRACTION = 0.6;

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
