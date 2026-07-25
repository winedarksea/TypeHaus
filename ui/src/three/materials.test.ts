import {
  BRICK_UNIT_M,
  CMU_UNIT_M,
  isCmu,
  isMasonry,
  masonryStyleFor,
  masonryTileSizeM,
  MASONRY_TILE_SIZE_M,
} from "./materials";
import { authoredAppearance, familyOf, materialColor, RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { CATEGORY_FALLBACK, categoryColor, memberColor } from "./members";
import type { Member } from "../model/types";

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

  // An authored finish is definitive: a material tagged plainly "brick" still renders as white
  // brick when the catalog says so. This is the case substring inference cannot express, and
  // the reason the engine ships Material.finish (server/model_json.py catalog.materials).
  assert(masonryStyleFor("brick", "white-brick").key === "white-brick",
    "An authored finish outranks the tag — a plain 'brick' ref can be white brick");
  assert(masonryStyleFor("white-brick", "cmu").key === "cmu",
    "An authored finish outranks the tag in the other direction too");
  assert(masonryStyleFor("brick", null).key === "brick"
    && masonryStyleFor("brick", "no-such-finish").key === "brick",
    "No (or unknown) authored finish falls back to inferring from the ref");

  // The authored colour reaches the fill: white brick must not read as the masonry family red.
  const catalog = [
    { tag: "white-brick", color: "#e9e6df", finish: "white-brick" },
    { tag: "brick", color: "#9c5a4a", finish: "brick" },
    { tag: "spf-stud" },
  ];
  const light = RESOLVED_NORDIC_PALETTE.light;
  assert(materialColor("white-brick", light, catalog) === "#e9e6df",
    "Authored material colour wins over the inferred masonry family colour");
  assert(materialColor("white-brick", light) === light.material.masonry,
    "Without a catalog the same ref still falls back to the masonry family colour");
  assert(materialColor("spf-stud", light, catalog) === light.material.lumber,
    "A catalog material with no authored colour falls back to its inferred family");
  assert(authoredAppearance("white-brick", catalog)?.finish === "white-brick"
    && authoredAppearance("missing", catalog) === undefined,
    "authoredAppearance finds a catalog entry by tag and reports absence as undefined");
}

// --- member colour: no category the engine emits may reach the grey fallback --------------
// `memberColor` routes a member by material when it names one and by category otherwise, and
// both routes leaked: ~470 framing members (rafters, blocking, outlookers, barge rafters, the
// whole truss vocabulary) had no CATEGORY_COLOR entry, and the derived PVC trim had no
// material family. The key-level parity between this table and the engine's _PALETTE is
// asserted engine-side (packages/engine/tests/test_palette_parity.py, which reads this file);
// here we pin the behaviour those keys exist for.
function member(category: string, material: string | null = null): Member {
  return { category, material } as Member;
}

export function runMemberColorTests() {
  const palette = RESOLVED_NORDIC_PALETTE.light;
  // Roof sticks + truss vocabulary: lumber, not the neutral fallback.
  for (const category of [
    "rafter", "blocking", "outlooker", "barge_rafter",
    "top_chord", "bottom_chord", "truss_web", "truss_heel", "seat_cut",
    "king", "jack", "cripple", "sill", "bearing_stiffener",
  ]) {
    assert(categoryColor(category) !== CATEGORY_FALLBACK,
      `${category} has its own colour rather than the grey fallback`);
    assert(memberColor(member(category), palette) === categoryColor(category),
      `${category} with no material colours by category`);
  }

  // Layer-function categories, for a derived skin band that names no material.
  for (const category of ["cladding", "sheathing", "insulation", "membrane", "furring",
    "lining", "finish", "structure", "fascia", "soffit"]) {
    assert(categoryColor(category) !== CATEGORY_FALLBACK,
      `layer-function category ${category} has a colour of its own`);
  }

  // An unknown category still falls back rather than throwing — the fallback stays reachable.
  assert(categoryColor("no-such-category") === CATEGORY_FALLBACK,
    "An unmapped category returns the neutral fallback");

  // Material route: cellular-PVC trim reads as painted siding, not as the neutral fallback.
  assert(familyOf("pvc-cellular") === "siding",
    "Cellular PVC trim resolves to the siding family");
  assert(familyOf("air-barrier") === "membrane",
    "An air barrier resolves to the membrane family");
  const light = RESOLVED_NORDIC_PALETTE.light;
  assert(materialColor("pvc-cellular", light) === light.material.siding,
    "A pvc-cellular fascia/soffit member takes the siding tone, not the fallback");
  assert(materialColor("air-barrier", light) === light.material.membrane,
    "An air-barrier membrane member takes the membrane tone, not the fallback");
  for (const [category, material] of [["fascia", "pvc-cellular"], ["soffit", "pvc-cellular"],
    ["membrane", "air-barrier"]] as const) {
    assert(materialColor(material, light) !== light.material.fallback,
      `${category} (${material}) no longer renders as the #cfc9bd fallback`);
  }

  // The palette path: memberColor always resolves against a ResolvedNordicPalette, so a skin
  // member's colour is a concrete hex value that THREE.Color can parse. Before the palette was
  // threaded through, memberColor called materialColor without one, and the CSS custom-property
  // fallback ("var(--material-…)") reached THREE.Color, which logged an "unknown color" warning
  // for every skin member on every scene rebuild.
  for (const [materialRef, expected] of [
    ["pvc-cellular", light.material.siding],
    ["standing-seam", light.material.metal],
    ["air-barrier", light.material.membrane],
    ["no-such-material", light.material.fallback],
  ] as const) {
    const resolved = memberColor(member("cladding", materialRef), light);
    assert(resolved === expected,
      `A ${materialRef} skin member resolves through the palette to ${expected}`);
    assert(typeof resolved === "string" && !resolved.includes("var("),
      `memberColor(${materialRef}) never hands THREE.Color a CSS var() string`);
  }
  for (const [theme, themed] of Object.entries(RESOLVED_NORDIC_PALETTE)) {
    assert(memberColor(member("cladding", "standing-seam"), themed) === themed.material.metal,
      `The ${theme} palette's metal tone reaches a standing-seam member`);
  }
}
