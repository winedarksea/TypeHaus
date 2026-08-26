import * as THREE from "three";
import {
  applyMasonryWallUv,
  BRICK_UNIT_M,
  CMU_UNIT_M,
  isCmu,
  isMasonry,
  masonryStyleFor,
  masonryTileSizeM,
  MASONRY_TILE_SIZE_M,
  metalPanelProfileForFinish,
  panelTileSizeM,
  isStandingSeam,
  RIBBED_PANEL_PROFILE,
  RIBBED_PANEL_PITCH_M,
  SEAM_PAN_WIDTH_M,
  SEAM_PROFILE,
  SEAM_TILE_SIZE_M,
} from "./materials";
import {
  authoredAppearance, familyOf, materialColor, RESOLVED_NORDIC_PALETTE, statesOwnColor,
} from "../nordic/palette";
import { CATEGORY_FALLBACK, categoryColor, isSeamMember, memberColor } from "./members";
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

  // ── Metal panel profiles (2026-08-26) ────────────────────────────────────────────────
  // The house walls went from a snap-lock seam to an exposed-fastener PBR panel, and the
  // dispatch had to stop being a substring test to survive it. `pbr-panel-26` has no "seam"
  // in its tag ON PURPOSE, so `isStandingSeam` cannot see it — this is exactly the case that
  // Material.finish exists for, the same argument the Ishtar bricks below make.
  assert(!isStandingSeam("pbr-panel-26"),
    "The substring test cannot reach the PBR panel — which is why the finish dispatch exists");
  assert(isStandingSeam("standing-seam-snaplock") && isStandingSeam("standing-seam-nailstrip-26"),
    "The four seam-profile tags still match the substring fallback (the roofs keep it)");
  assert(metalPanelProfileForFinish("ribbed-panel") === RIBBED_PANEL_PROFILE,
    "An authored finish of 'ribbed-panel' selects the ribbed profile");
  assert(metalPanelProfileForFinish("standing-seam") === SEAM_PROFILE,
    "An authored finish of 'standing-seam' selects the seam profile");
  assert(metalPanelProfileForFinish(null) === null
    && metalPanelProfileForFinish("no-such-finish") === null,
    "No (or unknown) finish declares nothing, leaving the substring fallback in charge");

  // The two profiles are genuinely different geometry, not one recipe with a new name.
  assert(Math.abs(SEAM_PROFILE.moduleM - SEAM_PAN_WIDTH_M) < 1e-9
    && Math.abs(RIBBED_PANEL_PROFILE.moduleM - RIBBED_PANEL_PITCH_M) < 1e-9,
    "Seam pans are 16in and PBR ribs are 12in o.c.");
  assert(RIBBED_PANEL_PROFILE.moduleM < SEAM_PROFILE.moduleM,
    "The PBR rib module is tighter than the seam pan module");
  assert(RIBBED_PANEL_PROFILE.squareness > SEAM_PROFILE.squareness,
    "A roll-formed rib has a flatter crown than a folded seam");
  assert(RIBBED_PANEL_PROFILE.ribHalfWidth > SEAM_PROFILE.ribHalfWidth,
    "A PBR major rib is wider across than a snap-lock upstand");
  // A screwed panel is pulled tight to its girts every 24"; a clipped one floats between
  // clips and is free to wander. Less oil canning is the physical claim, not a style choice.
  assert(RIBBED_PANEL_PROFILE.oilCanning < SEAM_PROFILE.oilCanning,
    "A face-fastened panel oil-cans less than a floating clipped one");

  // Tile size follows the module, so both profiles sit at true scale under the same wall UVs.
  assert(Math.abs(panelTileSizeM(SEAM_PROFILE) - SEAM_TILE_SIZE_M) < 1e-9,
    "The seam profile's tile size is the exported constant (no regression)");
  assert(panelTileSizeM(RIBBED_PANEL_PROFILE) < panelTileSizeM(SEAM_PROFILE),
    "The ribbed tile spans the same 4 modules, so a tighter module means a smaller tile");
  assert(Math.abs(panelTileSizeM() - SEAM_TILE_SIZE_M) < 1e-9,
    "Called with no profile it still answers for the seam, so old call sites are unchanged");

  // The Ishtar scheme (2026-08-20): three more brick faces on the sunken garden's wythe.
  // Every one of them is a tag substring inference CANNOT reach — "glazed-lapis-brick" and
  // "brown-brick" say nothing the old CMU/white/red ladder recognises, so all three would
  // fall through to red brick without their authored finish. That is the whole case for
  // Material.finish and it is what these pin.
  const lapis = masonryStyleFor("glazed-lapis-brick", "glazed-lapis-brick");
  const gold = masonryStyleFor("glazed-gold-brick", "glazed-gold-brick");
  const brown = masonryStyleFor("brown-brick", "brown-brick");
  assert(lapis.unitM === BRICK_UNIT_M && gold.unitM === BRICK_UNIT_M && brown.unitM === BRICK_UNIT_M,
    "The Ishtar faces are all brick, so all three keep the brick module");
  assert(lapis.base !== null && gold.base !== null && brown.base !== null,
    "A glaze is a ceramic coat and brown clay is not red clay — none may take the family colour");
  assert(lapis.mortar === gold.mortar,
    "The gold registers sit inside the lapis field, so they share its joint colour");
  assert(brown.mortar === defaultBrick.mortar,
    "The unglazed plinth keeps the tan mortar of ordinary brick");
  // The plinth is specified as ONE light brick, not a blend (2026-08-21). It was authored the
  // other way — full red-brick jitter, on the argument that variegation is what makes the
  // glaze above it read as a glaze — and on the wall that came out as mixed pallets with
  // near-black units through it. This pins the correction, since the jitter is invisible in
  // any test that only checks the base colour.
  assert(brown.jitterHSL.every((amount, index) => amount <= defaultBrick.jitterHSL[index] / 3),
    "The plinth is one light brick: nowhere near the red brick's blend");
  assert(brown.jitterHSL[2] <= 0.05,
    "Lightness jitter is what showed as mixed pallets, so it stays at the glazes' near-zero");
  assert(masonryStyleFor("glazed-lapis-brick").key === "brick",
    "Without the authored finish the ref alone still cannot tell lapis from red — hence Material.finish");

  assertCoursingStartsAtTheWallBase();
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

// A brick wall is laid from the bottom up: the bricklayer starts on a full course at the base
// and only ever cuts at the top. The UV course line used to be measured from project zero, so
// every wall in the house started mid-brick — the sunken garden veneer, founded at -101",
// rendered its bottom course as a third of a brick and cut every register band above it too.
function assertCoursingStartsAtTheWallBase() {
  const tile = masonryTileSizeM(masonryStyleFor("brick-red"));
  const baseZ = -2.5654; // -101", the Ishtar wall's base: deliberately NOT a whole tile.
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(
    [0, baseZ, 0, 1, baseZ, 0, 1, baseZ + tile[1], 0], 3));
  applyMasonryWallUv(geometry, [[0, 0], [6, 0]], [0, 0], tile, baseZ);
  const uv = geometry.getAttribute("uv");
  assert(Math.abs(uv.getY(0)) < 1e-6 && Math.abs(uv.getY(1)) < 1e-6,
    "The wall's base sits exactly on a bed joint, so the bottom course is a whole brick");
  assert(Math.abs(uv.getY(2) - 1) < 1e-6, "One tile up the wall is exactly one tile up the map");

  const fromZero = new THREE.BufferGeometry();
  fromZero.setAttribute("position", new THREE.Float32BufferAttribute([0, baseZ, 0], 3));
  applyMasonryWallUv(fromZero, [[0, 0], [6, 0]], [0, 0], tile);
  assert(Math.abs(fromZero.getAttribute("uv").getY(0) % 1) > 1e-3,
    "Measuring from project zero is what cut the bottom course — the regression this pins");
}

export function runMemberColorTests() {
  const palette = RESOLVED_NORDIC_PALETTE.light;
  // Roof sticks + truss vocabulary: lumber, not the neutral fallback.
  for (const category of [
    "rafter", "blocking", "outlooker", "barge_rafter",
    "top_chord", "bottom_chord", "truss_web", "truss_heel", "seat_cut",
    "king", "jack", "cripple", "sill", "bearing_stiffener",
    // Rainscreen/liner strapping: lumber on its own grid, not the grey fallback.
    "strapping",
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

  // Material route: cellular-PVC trim falls to the siding family by substring alone, but its
  // FINISH_BASE entry (factory white, not the family's blue-grey) takes precedence.
  assert(familyOf("pvc-cellular") === "siding",
    "Cellular PVC trim's substring guess is the siding family");
  assert(familyOf("air-barrier") === "membrane",
    "An air barrier resolves to the membrane family");
  const light = RESOLVED_NORDIC_PALETTE.light;
  assert(materialColor("pvc-cellular", light) === "#f4f2ee",
    "A pvc-cellular fascia/soffit member takes its FINISH_BASE white, not the siding family tone");
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
    ["pvc-cellular", "#f4f2ee"],
    ["standing-seam", light.material.metal],
    ["air-barrier", light.material.membrane],
    // A ref the palette cannot place keeps its category tone rather than taking the neutral
    // `material.fallback` — see the kdat assertions below for why that matters.
    ["no-such-material", categoryColor("cladding")],
  ] as const) {
    const resolved = memberColor(member("cladding", materialRef), light);
    assert(resolved === expected,
      `A ${materialRef} skin member resolves through the palette to ${expected}`);
    assert(typeof resolved !== "string" || !resolved.includes("var("),
      `memberColor(${materialRef}) never hands THREE.Color a CSS var() string`);
  }

  // The truss wall's outrigger band (resolve/framing/furring.py + framing/truss_frame.py).
  // Every strapping, ladder-blocking and jamb-filler stick carries material_ref "kdat", which
  // no familyOf needle matches and no FINISH_BASE entry names — so routing a member by its
  // material ref unconditionally painted 590 members of catlin the neutral #cfc9bd, a pale
  // grey band of "lumber" screwed to the frame it is supposed to match. They belong on their
  // category tone, which is what the .glb has always given them.
  assert(familyOf("kdat") === null && !statesOwnColor("kdat"),
    "kdat states no colour a member can see — the precondition this whole case rests on");
  for (const category of ["strapping", "truss_blocking", "truss_filler", "furring"]) {
    const resolved = memberColor(member(category, "kdat"), light);
    assert(resolved === categoryColor(category),
      `A kdat ${category} member reads as its category lumber, not the grey material fallback`);
    assert(categoryColor(category) !== CATEGORY_FALLBACK,
      `${category} has a lumber tone of its own to fall back to`);
  }
  for (const [theme, themed] of Object.entries(RESOLVED_NORDIC_PALETTE)) {
    assert(memberColor(member("cladding", "standing-seam"), themed) === themed.material.metal,
      `The ${theme} palette's metal tone reaches a standing-seam member`);
  }

  // Formed metal trim — the vented ridge cap, the corner trim capping a wrapped edge, the
  // hung gutter — is the same painted stock as the panels it caps and is derived carrying
  // the roofing's own material_ref. It has to reach the seam finish (Regal White) rather
  // than the flat metal fill, or the cap reads dark grey against the white roof under it.
  for (const category of ["cladding", "ridge_cap", "corner_trim", "gutter"]) {
    assert(isSeamMember(member(category, "standing-seam")),
      `A standing-seam ${category} member takes the painted-metal seam finish`);
  }
  // Category alone is not enough: an aluminum gutter is not standing seam, and lumber
  // never is regardless of category.
  assert(!isSeamMember(member("gutter", "aluminum")),
    "An aluminum gutter keeps the flat fill — the seam finish is material-gated");
  assert(!isSeamMember(member("stud", "spf")), "Lumber never takes the seam finish");
  assert(!isSeamMember(member("fascia", "standing-seam")),
    "Only the metal-trim categories opt in — a fascia nailer is framing by trade");
}
