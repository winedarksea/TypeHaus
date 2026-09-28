// The board layout of one plank tile: pure, so the stagger rules are pinned headless.
import { layoutPlankTile, MIN_JOINT_OFFSET_M, MIN_PLANK_STAGGER_M } from "./plankLayout";
import { WOOD_PLANK_STYLES } from "./plankMaterial";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const EPS = 1e-9;
const INCH = 0.0254;

function loopDistance(a: number, b: number, period: number): number {
  const d = Math.abs(a - b) % period;
  return Math.min(d, period - d);
}

export function runPlankLayoutTests() {
  for (const key of ["strip-floor", "plank-floor", "lvp-plank", "tg-board", "shiplap"]) {
    const style = WOOD_PLANK_STYLES[key];
    const lanes = layoutPlankTile(style);
    assert(lanes.length === style.boardsPerTile, `${key}: one lane per board across the tile`);

    // Every lane closes the loop exactly, or the tile seams where it repeats.
    for (const lane of lanes) {
      const total = lane.reduce((sum, b) => sum + (b.v1 - b.v0), 0);
      assert(Math.abs(total - style.tileAlongM) < 1e-6, `${key}: a lane sums to the tile length`);
      assert(lane.every((b) => b.v0 >= -EPS && b.v0 < style.tileAlongM),
        `${key}: every board starts inside the tile`);
    }

    // Same recipe, same floor: no Math.random anywhere.
    assert(JSON.stringify(layoutPlankTile(style)) === JSON.stringify(lanes),
      `${key}: the layout is deterministic`);

    const { lengths } = style;
    if (lengths.kind === "continuous") continue;
    if (lengths.kind === "random") {
      for (const b of lanes.flat()) {
        const len = b.v1 - b.v0;
        assert(len >= lengths.minM - 1e-6 && len <= lengths.maxM + 1e-6,
          `${key}: a random board (${(len / INCH).toFixed(1)}in) stays inside the milled range`);
      }
    }
    // No H-joints: adjacent lanes' end joints stay apart, and the tile wraps ACROSS too, so
    // the last lane is judged against the first.
    const gap = lengths.kind === "fixed" ? MIN_PLANK_STAGGER_M : MIN_JOINT_OFFSET_M;
    for (let i = 0; i < lanes.length; i++) {
      const next = lanes[(i + 1) % lanes.length];
      for (const a of lanes[i]) {
        for (const b of next) {
          assert(loopDistance(a.v0, b.v0, style.tileAlongM) >= gap - 1e-6,
            `${key}: lanes ${i}/${(i + 1) % lanes.length} put end joints `
            + `${(loopDistance(a.v0, b.v0, style.tileAlongM) / INCH).toFixed(1)}in apart`);
        }
      }
    }
  }

  // Real wood is every board its own; a printed plank cycles a handful of visuals.
  const plank = layoutPlankTile(WOOD_PLANK_STYLES["plank-floor"]).flat();
  assert(new Set(plank.map((b) => b.printId)).size === plank.length,
    "owner-milled oak: every board is its own wood");
  const lvp = layoutPlankTile(WOOD_PLANK_STYLES["lvp-plank"]).flat();
  assert(lvp.every((b) => Math.abs(b.v1 - b.v0 - 48 * INCH) < 1e-6), "every LVP plank is 48in");
  assert(new Set(lvp.map((b) => b.printId)).size <= 6, "the LVP print repeats every 6 boards");
  assert(new Set(lvp.map((b) => b.printId)).size < lvp.length,
    "…and does repeat within one tile, which is the tell");

  // The three floors differ in format, not just in name.
  const [strip, oak, vinyl] = ["strip-floor", "plank-floor", "lvp-plank"]
    .map((k) => WOOD_PLANK_STYLES[k]);
  assert(Math.abs(oak.faceWidthM - 3.125 * INCH) < 1e-9, "the milled face is 3 1/8in");
  assert(Math.abs(vinyl.faceWidthM - 7 * INCH) < 1e-9, "the LVP face is 7in");
  assert(strip.faceWidthM < oak.faceWidthM && oak.faceWidthM < vinyl.faceWidthM,
    "strip, milled plank and LVP read as three widths");
  assert(vinyl.jointProfile === "bevel" && oak.jointProfile === "butt",
    "LVP is micro-bevelled; a site-finished floor is sanded flush");

  console.log("Plank layout tests passed.");
}
