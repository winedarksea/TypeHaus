import {
  BRICK_UNIT_M,
  CMU_UNIT_M,
  isCmu,
  isMasonry,
  masonryStyleFor,
  masonryTileSizeM,
  MASONRY_TILE_SIZE_M,
} from "./materials";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// Pure (no-canvas) assertions for the masonry finish selection. The procedural map generation
// itself needs a 2D canvas and is exercised in the browser; here we lock the module geometry
// and finish routing that the map builder and wall UVs consume.
export function runMaterialGeometryTests() {
  // Family membership: brick, CMU and stone are all masonry; CMU is specifically block.
  assert(isMasonry("brick-red") && isMasonry("cmu-8") && isMasonry("stone-veneer"),
    "brick / CMU / stone all resolve to the masonry family");
  assert(isCmu("cmu-8in") && isCmu("block-8") && !isCmu("brick-red")
    && !isCmu("standing-seam"), "isCmu picks out block/CMU material refs only");

  // CMU renders with the big 16"×8" face module, visually distinct from the 8"×2⅔" brick.
  const cmu = masonryStyleFor("cmu-8in");
  assert(cmu.unitM === CMU_UNIT_M, "CMU uses the 16in x 8in face module");
  assert(Math.abs(cmu.unitM[0] - 0.4064) < 1e-6 && Math.abs(cmu.unitM[1] - 0.2032) < 1e-6,
    "CMU face module is 16in x 8in in meters");
  assert(cmu.unitM[0] > BRICK_UNIT_M[0] * 1.9 && cmu.unitM[1] > BRICK_UNIT_M[1] * 2.9,
    "The CMU unit is markedly larger than a brick, so it never reads as brick");
  assert(cmu.base !== null, "CMU carries its own fixed grey unit colour, not the brick-red family colour");

  // White brick: brick module, but a light unit over grey mortar — the distinguishing option.
  const white = masonryStyleFor("white-brick");
  assert(white.unitM === BRICK_UNIT_M, "White brick keeps the brick module");
  assert(white.base !== null && white.base.toLowerCase() !== "#cfc8ba", "White brick has a light fixed unit colour");
  const defaultBrick = masonryStyleFor("brick-red");
  assert(defaultBrick.mortar === "#cfc8ba", "Default brick keeps its tan mortar");
  assert(white.mortar !== defaultBrick.mortar, "White brick swaps in grey mortar, distinct from the tan default");
  assert(defaultBrick.base === null, "Default brick takes its unit colour from the palette family (unchanged)");

  // Selection precedence: CMU beats the white-brick check even if both tokens appear.
  assert(masonryStyleFor("white-cmu-block").key === "cmu",
    "A block material stays CMU even when it also mentions white");

  // Repeat-tile sizing feeds the world-scaled wall UVs; brick default is unchanged.
  const brickTile = masonryTileSizeM(defaultBrick);
  assert(Math.abs(brickTile[0] - MASONRY_TILE_SIZE_M[0]) < 1e-9
    && Math.abs(brickTile[1] - MASONRY_TILE_SIZE_M[1]) < 1e-9,
    "Default brick tile size matches the exported constant (no regression)");
  const cmuTile = masonryTileSizeM(cmu);
  assert(cmuTile[0] > brickTile[0] && cmuTile[1] > brickTile[1],
    "The CMU repeat tile is larger in both directions than the brick tile");
}
