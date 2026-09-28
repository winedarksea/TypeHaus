// ── Wood planks: the board layout of one repeat tile, and each board's figure ──────────────
// Split from plankMaterial.ts, which owns the recipes and the THREE side. `layoutPlankTile` is
// pure (no canvas), so the stagger rules are testable headless; `drawBoardFigure` paints
// luminance only, so `material.color` stays the species colour.

/** How a style's boards end along the run. */
export type PlankLengths =
  | { readonly kind: "continuous" } // paneling: no end joints drawn
  | { readonly kind: "random"; readonly minM: number; readonly maxM: number } // milled stock
  | { readonly kind: "fixed"; readonly lenM: number }; // a manufactured plank

/**
 * The recipe for one wood finish. `key` seeds the map cache so distinct styles never collide.
 * A tile is `boardsPerTile` lanes across and `tileAlongM` along; every lane's boards sum to
 * `tileAlongM`, so the tile wraps without a seam.
 */
export interface PlankStyle {
  readonly key: string;
  readonly faceWidthM: number; // exposed face of one board, across the run
  readonly boardsPerTile: number;
  readonly lengths: PlankLengths;
  readonly tileAlongM: number;
  readonly pxPerM: number; // canvas resolution; non-square tiles are fine (WebGL2 NPOT)
  readonly jointFraction: number; // joint width ÷ face width
  // `vee` a T&G groove, `butt` a sanded-flush seam, `bevel` a factory micro-bevel on all
  // four edges — darker and deeper than a butt, and the first thing that reads as LVP.
  readonly jointProfile: "vee" | "butt" | "bevel";
  // Per-board tone spread, as a fraction of full brightness. LIGHTNESS ONLY: the maps are
  // luminance, so hue cannot vary per board — and keeping the map neutral is what lets
  // `material.color` stay the species colour.
  readonly jitter: number;
  readonly grain: number; // figure contrast, 0..1
  readonly figure: "streak" | "oak";
  // 0: every board is its own wood. N: only N board visuals, cycled — a printed plank's tell.
  readonly printRepeat: number;
  readonly reliefScale: number; // normal-map strength
}

export interface PlankBoard {
  readonly v0: number; // metres along the tile; in [0, tileAlongM)
  readonly v1: number; // may pass tileAlongM — the board wraps to the tile's start
  readonly boardId: number;
  readonly printId: number; // boards sharing one look alike
}

// Minimum end-joint offset between adjacent lanes: 6" for milled stock (the H-joint rule),
// 8" for click-lock planks (the manufacturers' minimum stagger).
export const MIN_JOINT_OFFSET_M = 0.1524;
export const MIN_PLANK_STAGGER_M = 0.2032;

/** Deterministic hash in [0, 1) — no Math.random, so the maps reproduce across reloads. */
export function hashBoard(row: number, board: number): number {
  const h = Math.sin(row * 12.9898 + board * 78.233) * 43758.5453;
  return h - Math.floor(h);
}

/** Circular distance between two positions on a loop of length `period`. */
function loopDistance(a: number, b: number, period: number): number {
  const d = Math.abs(a - b) % period;
  return Math.min(d, period - d);
}

function clearance(cut: number, others: readonly number[], period: number): number {
  let best = Infinity;
  for (const other of others) best = Math.min(best, loopDistance(cut, other, period));
  return best;
}

/**
 * Pick a position in [lo, hi] near `wanted` that clears every `others` cut by `gap` on a loop
 * of length `period`. Scans outward from `wanted`; if nothing clears, the best-clearing one.
 */
function clearCut(wanted: number, lo: number, hi: number, others: readonly number[],
  gap: number, period: number): number {
  const steps = 48;
  let best = wanted;
  let bestClear = clearance(wanted, others, period);
  if (bestClear >= gap) return wanted;
  for (let k = 1; k <= steps; k++) {
    for (const sign of [1, -1]) {
      const candidate = wanted + sign * (k / steps) * (hi - lo);
      if (candidate < lo || candidate > hi) continue;
      const c = clearance(candidate, others, period);
      if (c >= gap) return candidate;
      if (c > bestClear) { bestClear = c; best = candidate; }
    }
  }
  return best;
}

/** One lane of random-length boards: the cut positions around the tile's loop. */
function randomLaneCuts(lane: number, minM: number, maxM: number, period: number,
  neighbours: readonly number[]): number[] {
  const first = clearCut(hashBoard(lane, 0) * period, 0, period, neighbours,
    MIN_JOINT_OFFSET_M, period);
  const cuts = [first];
  let pos = first;
  let remaining = period;
  for (let n = 1; remaining > maxM; n++) {
    // Leave at least `minM` for the board that closes the loop.
    const lo = minM;
    const hi = Math.min(maxM, remaining - minM);
    if (hi < lo) break;
    const wanted = pos + lo + hashBoard(lane, n) * (hi - lo);
    const cut = clearCut(wanted, pos + lo, pos + hi, neighbours, MIN_JOINT_OFFSET_M, period);
    remaining -= cut - pos;
    pos = cut;
    cuts.push(cut);
  }
  return cuts;
}

/** One lane of fixed-length planks: a hashed offset clear of the neighbouring lanes. */
function fixedLaneCuts(lane: number, lenM: number, period: number,
  neighbours: readonly number[]): number[] {
  // Stagger is judged modulo one plank: every cut in a lane repeats at `lenM`.
  const offset = clearCut(hashBoard(lane, 0) * lenM, 0, lenM,
    neighbours.map((c) => c % lenM), MIN_PLANK_STAGGER_M, lenM);
  const cuts: number[] = [];
  for (let v = offset; v < period - 1e-9; v += lenM) cuts.push(v);
  return cuts;
}

/**
 * The boards of one repeat tile, lane by lane. Each lane's boards sum exactly to
 * `tileAlongM`; the tile also wraps ACROSS, so the last lane is staggered against the first.
 */
export function layoutPlankTile(style: PlankStyle): PlankBoard[][] {
  const period = style.tileAlongM;
  const lanes: number[][] = [];
  for (let lane = 0; lane < style.boardsPerTile; lane++) {
    const neighbours = [
      ...(lanes[lane - 1] ?? []),
      ...(lane === style.boardsPerTile - 1 && lane > 1 ? lanes[0] : []),
    ];
    const { lengths } = style;
    lanes.push(
      lengths.kind === "random"
        ? randomLaneCuts(lane, lengths.minM, lengths.maxM, period, neighbours)
        : lengths.kind === "fixed"
        ? fixedLaneCuts(lane, lengths.lenM, period, neighbours)
        : [0],
    );
  }
  let boardId = 0;
  return lanes.map((cuts) => {
    const sorted = [...cuts].map((c) => ((c % period) + period) % period).sort((a, b) => a - b);
    return sorted.map((v0, i) => {
      const next = i + 1 < sorted.length ? sorted[i + 1] : sorted[0] + period;
      const id = boardId++;
      return {
        v0, v1: next, boardId: id,
        printId: style.printRepeat > 0 ? id % style.printRepeat : id,
      };
    });
  });
}

/** A board's tone, centred on 1.0 so the tinted floor averages to the authored colour. */
export function boardShade(seed: number, style: PlankStyle): number {
  return 1 - style.jitter / 2 + hashBoard(seed, 1) * style.jitter;
}

export interface BoardRect { readonly x: number; readonly y: number; readonly w: number; readonly h: number }

/** A multiplicative darken at `alpha`, over a luminance map. */
function ink(alpha: number): string {
  return `rgba(0,0,0,${Math.max(0, Math.min(1, alpha)).toFixed(3)})`;
}

// Paneling: a few flat streaks along the board. Unchanged from the original recipe.
function drawStreaks(ctx: CanvasRenderingContext2D, r: BoardRect, seed: number, grain: number) {
  for (let streak = 0; streak < 3; streak++) {
    const g = hashBoard(seed * 31 + streak, 17);
    ctx.fillStyle = ink(0.09 * grain * (0.4 + g));
    ctx.fillRect(r.x + g * r.w, r.y, Math.max(1, r.w * 0.06), r.h);
  }
}

// White oak: fine wavy long grain, cathedral arches on plainsawn boards, and the lighter ray
// flecks of rift/quartersawn stock — white oak's signature, which red oak lacks.
function drawOakFigure(ctx: CanvasRenderingContext2D, r: BoardRect, seed: number,
  style: PlankStyle) {
  const h = (k: number) => hashBoard(seed * 7 + 3, k);
  const g = style.grain;
  const widthScale = Math.max(0.7, style.faceWidthM / 0.08);
  const lines = Math.round((12 + 8 * h(1)) * widthScale);
  const step = 6;
  for (let i = 0; i < lines; i++) {
    const x0 = r.x + ((i + 0.5 + (h(10 + i) - 0.5) * 0.8) / lines) * r.w;
    const amp = (0.3 + h(40 + i) * 1.2) * (r.w / 60);
    const freq = (2 * Math.PI) / (120 + h(70 + i) * 400);
    const phase = h(100 + i) * 6.283;
    ctx.strokeStyle = ink((0.03 + 0.07 * h(130 + i)) * g);
    ctx.lineWidth = 0.5 + h(160 + i) * 1.5;
    ctx.beginPath();
    for (let y = r.y; y <= r.y + r.h + step; y += step) {
      const x = x0 + amp * Math.sin(y * freq + phase);
      if (y === r.y) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  const cut = h(200);
  if (cut < 0.5) {
    // Plainsawn: 2–4 nested parabolic arches, arms continuing as straight grain.
    const arches = 2 + Math.floor(h(201) * 3);
    const cx = r.x + (0.3 + h(202) * 0.4) * r.w;
    const apex = r.y + h(203) * r.h * 0.6;
    const tall = Math.min(r.h * 0.5, (0.15 + h(204) * 0.25) * style.pxPerM);
    for (let j = 0; j < arches; j++) {
      const a = (0.1 + 0.1 * j) * r.w;
      const len = tall * (1 + 0.35 * j);
      ctx.strokeStyle = ink((0.09 + 0.04 * h(210 + j)) * g);
      ctx.lineWidth = 1 + h(220 + j) * 1.5;
      ctx.beginPath();
      ctx.moveTo(cx - a, r.y + r.h);
      ctx.lineTo(cx - a, apex + len);
      for (let s = -1; s <= 1.0001; s += 0.05) ctx.lineTo(cx + a * s, apex + j * 8 + len * s * s);
      ctx.lineTo(cx + a, r.y + r.h);
      ctx.stroke();
    }
  } else if (cut < 0.83) {
    // Rift/quarter: short lens-shaped flecks, lighter, lying with the grain.
    // Near-white luminance cannot be lightened, so the field drops a touch and the flecks
    // sit just above the board's own tone.
    ctx.fillStyle = ink(0.07);
    ctx.fillRect(r.x, r.y, r.w, r.h);
    const fleck = Math.round(Math.min(1, boardShade(seed, style) + 0.02) * 255);
    const flecks = 8 + Math.floor(h(300) * 12 * widthScale);
    ctx.fillStyle = `rgba(${fleck},${fleck},${fleck},${(0.5 + 0.5 * g).toFixed(3)})`;
    for (let k = 0; k < flecks; k++) {
      const fx = r.x + h(310 + k) * r.w;
      const fy = r.y + h(340 + k) * r.h;
      const len = 6 + h(370 + k) * 30;
      ctx.beginPath();
      ctx.ellipse(fx, fy, 0.8 + h(400 + k) * 1.8, len / 2, (h(430 + k) - 0.5) * 0.3, 0, 6.283);
      ctx.fill();
    }
  }
}

/**
 * Paint one board's figure into `r` (luminance, over its already-filled face). Clipped to the
 * board. Boards sharing a `seed` share a figure — which is exactly what an LVP print does.
 */
export function drawBoardFigure(ctx: CanvasRenderingContext2D, r: BoardRect, seed: number,
  style: PlankStyle) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(r.x, r.y, r.w, r.h);
  ctx.clip();
  if (style.figure === "oak") drawOakFigure(ctx, r, seed, style);
  else drawStreaks(ctx, r, seed, style.grain);
  ctx.restore();
}
