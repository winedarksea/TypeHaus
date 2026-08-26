import * as THREE from "three";
import {
  applyPlankPlaneUv,
  applyPlankWallUv,
  isWoodPlank,
  planLongAxis,
  plankStyleFor,
  plankTileSizeM,
  WOOD_PLANK_STYLES,
} from "./plankMaterial";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// Pure (no-canvas) assertions for the wood-plank finish selection and UV framing. The
// procedural map generation needs a 2D canvas and is exercised in the browser; here we lock
// the board module, the recipe routing and the UV frames the map builder consumes.
export function runPlankMaterialTests() {
  // --- what counts as a board surface -------------------------------------------------
  assert(isWoodPlank("sauna-tg") && isWoodPlank("walnut-tg") && isWoodPlank("cedar-tg"),
    "the library's `<species>-tg` paneling refs are all board surfaces");
  assert(isWoodPlank("oak") && isWoodPlank("lvp"),
    "the plank floor finishes are board surfaces");
  assert(!isWoodPlank("gwb") && !isWoodPlank("tile") && !isWoodPlank("carpet")
    && !isWoodPlank("sealed-concrete") && !isWoodPlank(null) && !isWoodPlank(undefined),
    "sheet and monolithic finishes are not board surfaces");
  // The sauna's plywood furring sits directly behind the T&G and must not itself be boarded.
  assert(!isWoodPlank("struct-1-plywood") && !isWoodPlank("plywood-subfloor"),
    "sheet goods are not boards, however wooden they are");

  // --- recipe routing -----------------------------------------------------------------
  // An authored `Material.finish` is definitive; `oak` carries "strip-floor".
  assert(plankStyleFor("oak", "strip-floor").key === "strip-floor",
    "an authored finish selects the recipe");
  // Inference covers the refs that author nothing usable. `walnut-tg` spends its single
  // `finish` slot on "clear-satin-hardwax-oil", which names no recipe — it must fall through
  // to inference rather than to a default that is not paneling.
  assert(plankStyleFor("walnut-tg", "clear-satin-hardwax-oil").key === "tg-board",
    "a finish naming no known recipe falls through to inference, not to an error");
  assert(plankStyleFor("sauna-tg").key === "tg-board",
    "a `-tg` ref infers tongue-and-groove paneling");
  assert(plankStyleFor("oak").key === "strip-floor",
    "a flooring ref infers strip flooring even with no authored finish");

  const tg = WOOD_PLANK_STYLES["tg-board"];
  const strip = WOOD_PLANK_STYLES["strip-floor"];
  // The two recipes must stay visibly different products, not two names for one board.
  assert(tg.faceWidthM > strip.faceWidthM * 1.4,
    "a paneling board shows a markedly wider face than a floor strip");
  assert(Math.abs(tg.faceWidthM - 0.0889) < 1e-6, "the T&G face is 3 1/2in in meters");
  assert(Math.abs(strip.faceWidthM - 0.0572) < 1e-6, "the strip face is 2 1/4in in meters");
  assert(tg.boardLenM === 0 && strip.boardLenM > 0,
    "paneling runs continuous; a strip floor has staggered end joints");
  assert(tg.jointProfile === "vee" && strip.jointProfile === "butt",
    "a T&G joint is a groove; a sanded floor joint is a butt seam");

  // A repeat tile spans whole boards in both directions, or the module drifts across a wall.
  for (const style of [tg, strip]) {
    const [across, along] = plankTileSizeM(style);
    assert(Math.abs(across - style.faceWidthM * style.boardsPerTile) < 1e-9,
      `${style.key} tile is a whole number of boards across`);
    assert(along > 0, `${style.key} tile has a positive extent along the boards`);
  }

  // --- wall UVs -----------------------------------------------------------------------
  // A 4 m long, 2 m tall quad on the x-axis, wall base at z = 0. Scene coords are
  // (x, elevation, -y), which is what projectScenePointToPlan undoes.
  const axis = [[0, 0], [4, 0]] as const;
  const quad = () => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array([
      0, 0, 0, 4, 0, 0, 4, 2, 0, 0, 2, 0,
    ]), 3));
    return g;
  };
  const tile = plankTileSizeM(tg);

  const vertical = quad();
  applyPlankWallUv(vertical, axis, [0, 0], tile, 0, "vertical");
  const vu = vertical.getAttribute("uv");
  // Boards vertical: the across-boards axis (u) runs ALONG the wall, so u spans the 4 m run.
  assert(Math.abs(vu.getX(1) - 4 / tile[0]) < 1e-6,
    "vertical boards lay the board module along the wall run");
  assert(Math.abs(vu.getY(1)) < 1e-9,
    "vertical boards put no along-board travel at the wall base");

  const horizontal = quad();
  applyPlankWallUv(horizontal, axis, [0, 0], tile, 0, "horizontal");
  const hu = horizontal.getAttribute("uv");
  // Boards horizontal: the across-boards axis runs UP the wall instead — the quarter turn.
  assert(Math.abs(hu.getX(1)) < 1e-9,
    "horizontal boards put no across-board travel along the wall run");
  assert(Math.abs(hu.getX(2) - 2 / tile[0]) < 1e-6,
    "horizontal boards course the board module up the wall");

  // The board module starts at the wall's own base, not at project zero — the same argument
  // applyMasonryWallUv makes. A wall founded 3 m down must still start on a whole board.
  const founded = quad();
  applyPlankWallUv(founded, axis, [0, 0], tile, -3, "horizontal");
  assert(Math.abs(founded.getAttribute("uv").getX(0) - 3 / tile[0]) < 1e-6,
    "coursing is measured from the wall base, so `baseZM` offsets it");

  // An unstated direction must still produce a usable frame rather than NaN: `board_run` is
  // null wherever the engine cannot derive one, and that is most wood in the model.
  const unstated = quad();
  applyPlankWallUv(unstated, axis, [0, 0], tile, 0, null);
  const uu = unstated.getAttribute("uv");
  for (let i = 0; i < uu.count * 2; i++) {
    assert(Number.isFinite(uu.array[i]), "a null board_run still yields finite UVs");
  }

  // A degenerate axis must not write NaN UVs into the buffer.
  const degenerate = quad();
  applyPlankWallUv(degenerate, [[1, 1], [1, 1]], [0, 0], tile, 0, "vertical");
  assert(degenerate.getAttribute("uv") === undefined
    || Array.from(degenerate.getAttribute("uv").array).every(Number.isFinite),
    "a zero-length wall axis is refused rather than writing NaN");

  // --- plane UVs and the long axis ----------------------------------------------------
  // Boards are laid the long way, so a 14 x 11 room runs its boards along the 14.
  assert(Math.abs(Math.abs(planLongAxis([[0, 0], [14, 0], [14, 11], [0, 11]])[0]) - 1) < 1e-9,
    "a wider-than-deep room runs its boards east-west");
  assert(Math.abs(Math.abs(planLongAxis([[0, 0], [11, 0], [11, 14], [0, 14]])[1]) - 1) < 1e-9,
    "a deeper-than-wide room runs its boards north-south");
  // The longest EDGE, not the bounding box: an L keeps to its own geometry.
  const ell = planLongAxis([[0, 0], [20, 0], [20, 4], [8, 4], [8, 12], [0, 12]]);
  assert(Math.abs(Math.abs(ell[0]) - 1) < 1e-9,
    "an L-shaped room follows its longest edge, not the box around it");

  const floor = new THREE.BufferGeometry();
  floor.setAttribute("position", new THREE.BufferAttribute(new Float32Array([
    0, 0, 0, 4, 0, 0, 4, 0, -2, 0, 0, -2,
  ]), 3));
  const stripTile = plankTileSizeM(strip);
  applyPlankPlaneUv(floor, [0, 0], [1, 0], stripTile);
  const fu = floor.getAttribute("uv");
  // Boards running +x: travel along +x is along-board (v), travel in +y is across (u).
  assert(Math.abs(fu.getY(1) - 4 / stripTile[1]) < 1e-6,
    "travel along the board run advances the along-board axis");
  assert(Math.abs(fu.getX(1)) < 1e-9,
    "travel along the board run does not cross boards");
  assert(Math.abs(fu.getX(2) - 2 / stripTile[0]) < 1e-6,
    "travel across the run crosses whole boards");

  console.log("Wood plank material tests passed.");
}
