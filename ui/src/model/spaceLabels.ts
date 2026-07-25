// Room/area plan labels (→ TODO: "clearly show the name of each room/area (or perhaps unique
// id if name is missing), such that a user can easily vibe code a change to that area with the
// text/id as a reference").
//
// The engine's Room has no free-text name — its human-readable identity is its `occupancy`,
// and its addressable identity is its `tag`. The drawn label therefore carries *both*: the
// occupancy as the name, the tag as the id you paste back into the plan source. When a space is
// too small to hold three lines, the id wins — a name you cannot act on is the line to drop.

import type { Room, Vec2 } from "./types";

export const SQ_FT_PER_SQ_M = 10.763910416709722;

// Line budget. Each label line is one text row; a space narrower/shorter than this cannot hold
// one legibly at the current zoom, so the label degrades rather than overflowing its room.
export const SPACE_LABEL_LINE_HEIGHT_PX = 14;
export const SPACE_LABEL_MIN_WIDTH_PX = 46;

export interface SpaceLabel {
  name: string; // human-readable identity (occupancy), title-cased
  id: string; // the unique tag a plan file addresses this space by
  area: string; // e.g. "324 SF"
}

/** Title-case an occupancy enum value ("half_bath" → "Half Bath"). */
export function humanizeOccupancy(occupancy: string): string {
  return occupancy
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}

export function spaceLabel(room: Pick<Room, "tag" | "occupancy" | "area_m2">): SpaceLabel {
  return {
    name: room.occupancy ? humanizeOccupancy(room.occupancy) : room.tag,
    id: room.tag,
    area: `${Math.round(room.area_m2 * SQ_FT_PER_SQ_M)} SF`,
  };
}

/**
 * How many of the three label lines fit inside a space of this on-screen size, id first.
 * Returns 0 when even the id would overflow — better a bare fill than illegible text.
 */
export function spaceLabelLineBudget(widthPx: number, heightPx: number): number {
  if (widthPx < SPACE_LABEL_MIN_WIDTH_PX) return 0;
  return Math.max(0, Math.min(3, Math.floor(heightPx / SPACE_LABEL_LINE_HEIGHT_PX)));
}

/** Screen-space bounding box of a projected ring, as [widthPx, heightPx]. */
export function projectedExtentPx(ring: readonly Vec2[], project: (p: Vec2) => Vec2): Vec2 {
  if (ring.length === 0) return [0, 0];
  const points = ring.map(project);
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  return [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
}
