// The 2D outline of one wall layer band — the rectangle its extrusion sweeps, with the
// openings taken out of it — and the arch soffits that outline carries.
//
// Split out of builders/walls.ts on 2026-08-21 to fix the thin bright band that ran across
// every opening at a brick colour change. The band used to be built as one rectangle with a
// THREE.Path *hole* per opening, each hole clamped into the band. That is right only while an
// opening sits strictly inside the band. The instant it reaches an edge — which it does at
// every band a tall opening passes through, and W-B-BRICK's door passes through four — the
// clamp lays the hole's head (or sill) exactly on the band's own edge, and ExtrudeGeometry
// sweeps it: a lit, normal-bearing strip spanning the opening, back to back with the band
// cap it is coincident with, and with the neighbouring band's clamped edge as well. Two or
// three surfaces fighting for the same pixels, most visible where nothing else is behind
// them — across the openings.
//
// So a clamped edge is not a hole here. An opening that reaches the band's bottom or top is a
// NOTCH in the outer ring; one that spans the band's full height SPLITS it into separate
// shapes; only an opening strictly inside the band stays a hole. Nothing is then coincident
// with anything, because nothing is drawn at the clamp line at all.
import * as THREE from "three";
import type { Opening, Wall } from "../../model/types";
import { archSoffitCircle, archSoffitSample, archSoffitSegmentCount, baseRefZ } from "./wallFrame";

// `circleCenterM` is the soffit circle's centre elevation — the springline for a semicircle,
// and `depthM` below it for a segmental arch.
export interface ArchSoffitCylinder {
  centerAlongM: number; circleCenterM: number; radiusM: number;
}

/** The band being built, in the wall's local frame: its extent along, and its elevations. */
export interface WallBand {
  minAlong: number; maxAlong: number; bandBottom: number; bandTop: number;
}

const EPS = 1e-9;

type Point = [number, number];

/**
 * One opening as this band sees it: the void's sill, its head profile left to right (the arch
 * curve, or the two corners of a square head), and which of the band's edges it runs out to.
 * Every elevation is already clamped into the band, so `touchesBottom`/`touchesTop` are simply
 * whether that clamp bit.
 */
interface BandCut {
  start: number; end: number; bottom: number;
  head: Point[];
  touchesBottom: boolean; touchesTop: boolean;
}

// Consecutive coincident points are a triangulator's worst input, and the clamp makes them
// freely: a head clipped flat turns a run of arch samples into the same point over and over.
function withoutRepeats(points: readonly Point[]): Point[] {
  const kept: Point[] = [];
  for (const point of points) {
    const last = kept[kept.length - 1];
    if (!last || Math.hypot(point[0] - last[0], point[1] - last[1]) > 1e-12) kept.push(point);
  }
  return kept;
}

function bandCuts(
  band: WallBand, wall: Wall, openings: readonly Opening[], soffits: ArchSoffitCylinder[],
): BandCut[] {
  const { minAlong, maxAlong, bandBottom, bandTop } = band;
  const clampY = (elevation: number) => Math.min(bandTop, Math.max(bandBottom, elevation));
  const cuts: BandCut[] = [];
  for (const opening of openings) {
    const start = Math.max(minAlong, opening.center_along_m - opening.width_m / 2);
    const end = Math.min(maxAlong, opening.center_along_m + opening.width_m / 2);
    // The threshold is where the opening's height is measured *from*, and it can sit below
    // the wall that hosts it — the garage overhead door lands on the slab, one stem reveal
    // under W-G-E's base. Only the cut is clamped to the wall body; measuring the head off
    // the clamped value instead would make the hole as much too tall as the sill is
    // negative, and disagree with the wall solids (resolve/geometry_walls.py, and
    // wallLayerPieces, which both measure from the threshold).
    const threshold = baseRefZ(wall) + opening.sill_m;
    const bottom = clampY(threshold);
    // An opening that misses this band entirely cuts nothing from it: the plinth course
    // under a door's threshold is solid brick, and so is the field above its arch.
    if (end - start <= EPS || bottom >= bandTop - EPS ||
        threshold + opening.height_m <= bandBottom + EPS) continue;
    const archRise = opening.arch_rise_m ?? 0;
    let head: Point[];
    if (archRise <= EPS) {
      const top = clampY(threshold + opening.height_m);
      head = [[start, top], [end, top]];
    } else {
      const { radiusM, halfAngleRad, depthM } = archSoffitCircle(opening.width_m / 2, archRise);
      const springlineM = threshold + Math.max(0, opening.height_m - archRise);
      const segmentCount = archSoffitSegmentCount(radiusM, halfAngleRad);
      head = [[start, clampY(springlineM)]];
      for (let segment = 0; segment <= segmentCount; segment++) {
        const { offsetM, heightM } = archSoffitSample(segment, segmentCount, radiusM, halfAngleRad);
        head.push([opening.center_along_m + offsetM, clampY(springlineM + heightM)]);
      }
      soffits.push({
        centerAlongM: opening.center_along_m, circleCenterM: springlineM - depthM, radiusM,
      });
    }
    head = withoutRepeats(head);
    cuts.push({
      start, end, bottom, head,
      touchesBottom: bottom <= bandBottom + EPS,
      touchesTop: head.some(([, elevation]) => elevation >= bandTop - EPS),
    });
  }
  return cuts;
}

/**
 * The detour an opening that reaches the band's top makes in the outer ring, walked RIGHT TO
 * LEFT with the rest of the top edge: in at the rightmost point where the head meets the top,
 * down the head's right shoulder, round the sill, and back up the left shoulder to the
 * leftmost such point. The spandrel outboard of each shoulder — real material, below the top
 * edge and above the curve — stays enclosed by that walk.
 */
function topBay(cut: BandCut, bandTop: number): Point[] {
  const { head } = cut;
  const first = head.findIndex(([, elevation]) => elevation >= bandTop - EPS);
  let last = first;
  for (let index = head.length - 1; index > first; index--) {
    if (head[index][1] >= bandTop - EPS) { last = index; break; }
  }
  return [
    ...head.slice(last),
    [cut.end, cut.bottom], [cut.start, cut.bottom],
    ...head.slice(0, first + 1),
  ];
}

// One shape: the rectangle from `left` to `right`, notched along the bottom and top edges by
// the cuts that run out to them, and holed by the ones that do not.
function segmentShape(
  left: number, right: number, bandBottom: number, bandTop: number, cuts: readonly BandCut[],
): THREE.Shape | null {
  if (right - left <= EPS) return null;
  const points: Point[] = [[left, bandBottom]];
  for (const cut of cuts.filter((c) => c.touchesBottom).sort((a, b) => a.start - b.start)) {
    points.push([cut.start, cut.bottom], ...cut.head, [cut.end, cut.bottom]);
  }
  points.push([right, bandBottom], [right, bandTop]);
  for (const cut of cuts.filter((c) => c.touchesTop).sort((a, b) => b.start - a.start)) {
    points.push(...topBay(cut, bandTop));
  }
  points.push([left, bandTop]);

  const shape = new THREE.Shape();
  const ring = withoutRepeats(points);
  shape.moveTo(ring[0][0], ring[0][1]);
  for (const [along, elevation] of ring.slice(1)) shape.lineTo(along, elevation);
  shape.closePath();
  for (const cut of cuts.filter((c) => !c.touchesBottom && !c.touchesTop)) {
    const hole = new THREE.Path();
    hole.moveTo(cut.start, cut.bottom);
    for (const [along, elevation] of cut.head) hole.lineTo(along, elevation);
    hole.lineTo(cut.end, cut.bottom);
    hole.closePath();
    shape.holes.push(hole);
  }
  return shape;
}

/**
 * The shapes to extrude for one wall layer band, and the soffit cylinders their arch heads
 * ride on. More than one shape when an opening runs the band's whole height and parts it —
 * the door leaves the 5⅓" gold register as two separate pieces, which is what it physically
 * does to the wall.
 */
export function wallBandShapes(
  band: WallBand, wall: Wall, openings: readonly Opening[],
): { shapes: THREE.Shape[]; soffits: ArchSoffitCylinder[] } {
  const soffits: ArchSoffitCylinder[] = [];
  const cuts = bandCuts(band, wall, openings, soffits);
  const parting = cuts.filter((c) => c.touchesBottom && c.touchesTop)
    .sort((a, b) => a.start - b.start);
  const shapes: THREE.Shape[] = [];
  let left = band.minAlong;
  for (const cut of [...parting, null]) {
    const right = cut ? cut.start : band.maxAlong;
    const inside = cuts.filter((c) => !(c.touchesBottom && c.touchesTop) &&
      c.start >= left - EPS && c.end <= right + EPS);
    const shape = segmentShape(left, right, band.bandBottom, band.bandTop, inside);
    if (shape) shapes.push(shape);
    if (cut) left = cut.end;
  }
  return { shapes, soffits };
}
