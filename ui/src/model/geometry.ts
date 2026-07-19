// Geometry & unit helpers. The UI never re-measures the design (→ 21b) — these operate
// only on presentation concerns: mapping SI meters to screen pixels, formatting lengths
// for display, and deriving *view-only* aggregates (the node graph for hit-testing, the
// bounding extents for the HUD readout) from the numbers model.json already resolved.

import type { Model, Vec2, Wall } from "./types";

export const M_PER_FT = 0.3048;

export function metersToFeet(m: number): number {
  return m / M_PER_FT;
}

// Format meters as ft-in to the nearest 1/16", the drafting default (→ 21 ft-in keypad).
export function formatFtIn(meters: number): string {
  const totalInches = (meters / M_PER_FT) * 12;
  const sign = totalInches < 0 ? "-" : "";
  let inches = Math.abs(totalInches);
  const feet = Math.floor(inches / 12);
  inches -= feet * 12;
  const whole = Math.floor(inches);
  const frac = inches - whole;
  const sixteenths = Math.round(frac * 16);
  let w = whole;
  let ft = feet;
  let s = sixteenths;
  if (s === 16) {
    s = 0;
    w += 1;
  }
  if (w === 12) {
    w = 0;
    ft += 1;
  }
  let fracStr = "";
  if (s > 0) {
    let num = s;
    let den = 16;
    while (num % 2 === 0) {
      num /= 2;
      den /= 2;
    }
    fracStr = ` ${num}/${den}`;
  }
  return `${sign}${ft}'-${w}${fracStr}"`;
}

// Parse a ft-in string ("12'-6\"", "12' 6 1/2\"", "6\"", "13'") back to meters. Returns
// null on an unparseable string so the keypad can reject rather than silently guess.
export function parseFtIn(text: string): number | null {
  const t = text.trim();
  if (t === "") return null;
  const m = t.match(
    /^(-)?\s*(?:(\d+(?:\.\d+)?)\s*'?\s*[-\s]?)?\s*(?:(\d+(?:\.\d+)?)\s*(?:\s+(\d+)\s*\/\s*(\d+))?\s*"?)?\s*$/,
  );
  if (!m) return null;
  const [, neg, ftS, inS, numS, denS] = m;
  if (ftS === undefined && inS === undefined) return null;
  const ft = ftS ? parseFloat(ftS) : 0;
  let inch = inS ? parseFloat(inS) : 0;
  if (numS && denS) inch += parseFloat(numS) / parseFloat(denS);
  const total = ft + inch / 12;
  const meters = total * M_PER_FT * (neg ? -1 : 1);
  return meters;
}

export interface Node {
  id: string; // quantized "x,y" key
  p: Vec2;
  walls: string[]; // wall uids meeting here
}

const QUANT = 1e-4; // ~0.1 mm node coincidence tolerance

export function nodeKey(p: Vec2): string {
  return `${Math.round(p[0] / QUANT)},${Math.round(p[1] / QUANT)}`;
}

// Derive the node graph from wall axes for hit-testing and open-end detection. This is a
// view convenience only; the authoritative topology lives server-side.
export function deriveNodes(walls: Wall[]): Map<string, Node> {
  const nodes = new Map<string, Node>();
  for (const w of walls) {
    for (const p of w.axis) {
      const k = nodeKey(p);
      let n = nodes.get(k);
      if (!n) {
        n = { id: k, p, walls: [] };
        nodes.set(k, n);
      }
      n.walls.push(w.uid);
    }
  }
  return nodes;
}

export interface Extents {
  min: Vec2;
  max: Vec2;
  width_m: number;
  depth_m: number;
}

export function structuralExtents(model: Model): Extents | null {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  const acc = (p: Vec2) => {
    minX = Math.min(minX, p[0]);
    minY = Math.min(minY, p[1]);
    maxX = Math.max(maxX, p[0]);
    maxY = Math.max(maxY, p[1]);
  };
  for (const w of model.walls) for (const ly of w.layers) for (const p of ly.polygon) acc(p);
  if (!isFinite(minX)) {
    for (const w of model.walls) for (const p of w.axis) acc(p);
  }
  if (!isFinite(minX)) return null;
  return {
    min: [minX, minY],
    max: [maxX, maxY],
    width_m: maxX - minX,
    depth_m: maxY - minY,
  };
}

export function interiorExtents(model: Model): Extents | null {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const r of model.rooms)
    for (const p of r.clear_face) {
      minX = Math.min(minX, p[0]);
      minY = Math.min(minY, p[1]);
      maxX = Math.max(maxX, p[0]);
      maxY = Math.max(maxY, p[1]);
    }
  if (!isFinite(minX)) return null;
  return { min: [minX, minY], max: [maxX, maxY], width_m: maxX - minX, depth_m: maxY - minY };
}

// Point along a wall axis at parameter t in meters from the a-node (for opening centers).
export function pointAlong(w: Wall, alongM: number): Vec2 {
  const [a, b] = w.axis;
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy) || 1;
  return [a[0] + (dx / len) * alongM, a[1] + (dy / len) * alongM];
}

export function wallLength(w: Wall): number {
  const [a, b] = w.axis;
  return Math.hypot(b[0] - a[0], b[1] - a[1]);
}

// --- Authoring hit-tests (view-only; the server re-derives authoritative geometry). ------

export interface WallHit {
  wall: Wall;
  along_m: number; // distance from the a-node along the axis
  point: Vec2; // the projected point on the axis
  dist_m: number; // perpendicular distance from `world` to the axis
}

// Closest wall axis to a world point, clamped to the segment. Used by the opening and
// dimension tools to resolve which wall a tap landed on without an element onClick.
export function nearestWallHit(walls: Wall[], world: Vec2): WallHit | null {
  let best: WallHit | null = null;
  for (const wall of walls) {
    const [a, b] = wall.axis;
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const len2 = dx * dx + dy * dy;
    if (len2 === 0) continue;
    let t = ((world[0] - a[0]) * dx + (world[1] - a[1]) * dy) / len2;
    t = Math.max(0, Math.min(1, t));
    const point: Vec2 = [a[0] + t * dx, a[1] + t * dy];
    const dist_m = Math.hypot(world[0] - point[0], world[1] - point[1]);
    if (!best || dist_m < best.dist_m) {
      best = { wall, along_m: t * Math.sqrt(len2), point, dist_m };
    }
  }
  return best;
}

// Snap a world point to the nearest existing node within `tol_m`, else to a `grid_m` grid,
// else leave it free. Returns the snapped point and the node id when a node was hit.
export interface Snap {
  point: Vec2;
  nodeId: string | null;
}

export function snapWorld(
  world: Vec2,
  nodes: Map<string, Node>,
  tol_m: number,
  grid_m: number | null,
): Snap {
  let bestNode: Node | null = null;
  let bestDist = tol_m;
  for (const n of nodes.values()) {
    const d = Math.hypot(world[0] - n.p[0], world[1] - n.p[1]);
    if (d <= bestDist) {
      bestDist = d;
      bestNode = n;
    }
  }
  if (bestNode) return { point: bestNode.p, nodeId: bestNode.id };
  if (grid_m && grid_m > 0) {
    return {
      point: [Math.round(world[0] / grid_m) * grid_m, Math.round(world[1] / grid_m) * grid_m],
      nodeId: null,
    };
  }
  return { point: world, nodeId: null };
}

// Ortho-lock a point to the horizontal/vertical from an anchor (whichever axis is dominant).
export function orthoLock(anchor: Vec2, p: Vec2): Vec2 {
  return Math.abs(p[0] - anchor[0]) >= Math.abs(p[1] - anchor[1])
    ? [p[0], anchor[1]]
    : [anchor[0], p[1]];
}
