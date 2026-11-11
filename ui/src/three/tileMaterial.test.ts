import * as THREE from "three";
import { tilePhotoRecipe } from "./tilePhotoCatalog";
import { TILE_STYLES, TILE_RENDER_SETTINGS, tileStyleOrNull, tileRepeatSizeM,
  sampleTile, applyTileUv, buildTileMaps, createTileMaterial, disposeTileTextures } from "./tileMaterial";

function assert(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}
const close = (a: number, b: number) => Math.abs(a - b) < 1e-7;

export function runTileMaterialTests() {
  assert(tileStyleOrNull("porcelain-tile") === null && tileStyleOrNull(null) === null,
    "Generic floors retain their existing rendering");
  const brick = TILE_STYLES["tile-kaleo-running-bond"];
  const carrara = TILE_STYLES["tile-carrara-grid"];
  const subway = TILE_STYLES["tile-swanstone-modern-subway"];
  assert(close(subway.sizeM[0], 24 * 0.0254) && close(subway.sizeM[1], 6 * 0.0254),
    "Modern Subway relief is 6 by 24 inches");
  const face = sampleTile(subway, 0.1, 0.25), other = sampleTile(subway, 0.6, 0.75);
  assert(face.color.every((c, i) => close(c, other.color[i])), "The white panel has no shade or vein");
  assert(close(brick.sizeM[0], 14.17 * 0.0254), "Brick length follows the product");
  assert(close(carrara.sizeM[0], 24 * 0.0254) && close(carrara.sizeM[1], 12 * 0.0254),
    "Economy Carrara is 12 by 24 inches");
  assert(close(carrara.jointM, 1 / 8 * 0.0254), "Carrara joint follows manufacturer recommendation");
  const gatsby = TILE_STYLES["tile-gatsby-grid"];
  assert(close(gatsby.sizeM[0], 9 * 0.0254) && close(gatsby.sizeM[1], 9 * 0.0254),
    "Gatsby keeps the 9-inch printed squares");
  // Probe all four quarters of a diamond, including across the repeat boundary.
  for (const vertex of [0, 0.5, 1]) {
    for (const dx of [-0.025, 0.025]) for (const dy of [-0.025, 0.025]) {
      assert(sampleTile(gatsby, vertex + dx, vertex + dy).color.every(channel => channel < 90),
        "Black marble quarters meet into diamonds at alternating grid intersections");
    }
  }
  assert(sampleTile(gatsby, 0.025, 0.475).color.every(channel => channel > 190),
    "The other grid intersections remain white marble");
  for (const [u, v] of [[0.1875, 0.1875], [0.3125, 0.3125], [0.8125, 0.1875]]) {
    const gold = sampleTile(gatsby, u, v).color;
    assert(gold[0] > gold[1] && gold[1] > gold[2] * 1.5,
      "Paired gold diagonals mirror in adjacent squares");
  }
  let dark = 0, gold = 0;
  const samplesPerAxis = 128;
  for (let y = 0; y < samplesPerAxis; y++) for (let x = 0; x < samplesPerAxis; x++) {
    const sample = sampleTile(gatsby, (x + 0.5) / samplesPerAxis, (y + 0.5) / samplesPerAxis);
    if (sample.color.every(channel => channel < 90)) dark++;
    if (sample.color[0] > sample.color[1] && sample.color[1] > sample.color[2] * 1.5) gold++;
    assert(sample.heightM === 0 && sample.roughness === gatsby.roughness,
      "Printed joints and inlays stay on the same vinyl surface");
  }
  assert(dark / samplesPerAxis ** 2 > 0.06 && dark / samplesPerAxis ** 2 < 0.10,
    "Black diamonds occupy the swatch's approximate area, keeping them visible at room scale");
  assert(gold / samplesPerAxis ** 2 > 0.01 && gold / samplesPerAxis ** 2 < 0.03,
    "The gold remains a pinstripe across the repeat");
  for (const [key, style] of Object.entries(TILE_STYLES)) {
    assert(tileStyleOrNull(key) === style, "Declared recipe selects its configuration");
    for (const [u, v] of [[0.13, 0.27], [0.89, 0.61], [-0.27, 0.91]]) {
      const a = sampleTile(style, u, v), b = sampleTile(style, u + 1, v - 1);
      assert(a.color.every((c, i) => close(c, b.color[i])) && close(a.heightM, b.heightM),
        "Sampling repeats in both axes, including negative world positions");
      assert(a.color.every(Number.isFinite) && Number.isFinite(a.roughness), "All map channels are finite");
    }
    const [width, height] = tileRepeatSizeM(style);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute([0, 4, 0, width, 4, height], 3));
    applyTileUv(geometry, [0, 0], style);
    const uv = geometry.getAttribute("uv");
    assert(close(Math.abs(uv.getX(1) - uv.getX(0)), 1)
      && close(Math.abs(uv.getY(1) - uv.getY(0)), 1), "World distances produce one repeat");
    const schematic = createTileMaterial("schematic", style, "#abcdef");
    assert(!schematic.map && schematic.color.getHexString() === "abcdef", "Schematic keeps authored flat color");
    schematic.dispose(); geometry.dispose();
  }
  const boundary = sampleTile(carrara, 0, 0);
  const center = sampleTile(carrara, 0.25, 0.25);
  assert(boundary.heightM === 0 && center.heightM === TILE_RENDER_SETTINGS.groutDepthM,
    "Grout is recessed below the tile face");
  assert(boundary.roughness > center.roughness, "Grout is rougher than matte porcelain");
  const [w, h] = tileRepeatSizeM(brick);
  const a = sampleTile(brick, 0, (brick.sizeM[1] + brick.jointM) / h / 2);
  const b = sampleTile(brick, 0, (brick.sizeM[1] + brick.jointM) / h * 1.5);
  assert(a.heightM === 0 && b.heightM > 0, "Running bond staggers vertical joints by half a tile");
  assert(w > 0, "Repeat is positive");
  const IN = 0.0254;
  const jume = TILE_STYLES["tile-onyx-jume-blue-grid"];
  assert(jume.photo === "jume-onyx-blue", "Jume uses bundled product photography");
  assert(close(jume.sizeM[0], 23.62 * IN) && close(jume.sizeM[1], 47.24 * IN)
    && close(jume.jointM, IN / 16), "Jume uses actual face dimensions and 1/16-inch joints");
  const [jw, jh] = tileRepeatSizeM(jume);
  assert(close(jw, 2 * (23.62 + 1 / 16) * IN) && close(jh, 2 * (47.24 + 1 / 16) * IN),
    "Photo atlas keeps tile scale through its 2x2 repeat");
  assert(sampleTile(jume, 0.2, 0.2).heightM === sampleTile(jume, 0.3, 0.3).heightM,
    "Printed veining adds no physical relief");
  const lime = TILE_STYLES["tile-limestone-grid"];
  assert(lime.photo === "lifeproof-limestone", "Limestone uses bundled product photography");
  assert(close(lime.sizeM[0], 12 * IN) && close(lime.sizeM[1], 24 * IN) && close(lime.jointM, 3 / 16 * IN),
    "Limestone is 12x24 with the long axis along plan Y and 3/16-inch joints");
  const [lw, lh] = tileRepeatSizeM(lime);
  assert(close(lw, 5 * (12 + 3 / 16) * IN) && close(lh, 2 * (24 + 3 / 16) * IN),
    "Limestone's ten-cell atlas preserves the 12x24 tile and joint scale");
  const recipe = tilePhotoRecipe(lime.photo);
  assert(recipe.photographedFaces === 5 && recipe.faces.length === 10,
    "Limestone uses five photographed faces and their rotations");
  assert(recipe.faces.every(face => face.crop[2] > 0 && face.crop[3] > 0),
    "Every source face has a valid crop");
  const [cols, rows] = lime.repeat!;
  const neighbours = recipe.faces.every((face, i) => {
    const c = i % cols, r = Math.floor(i / cols);
    return [(r * cols) + (c + 1) % cols, ((r + 1) % rows) * cols + c]
      .every(n => `${recipe.faces[n].crop}` !== `${face.crop}`);
  });
  assert(neighbours, "No limestone face sits beside, or above, its own rotation, wrapping included");
  assert(lime.clearcoat === 0 && lime.roughness > 0.5, "Limestone is matte, not glazed");
  assert(lime.color[0] > lime.color[2] + 20 && lime.grout[0] > lime.grout[2] + 20, "Limestone and Biscuit grout are warm");
  assert(sampleTile(lime, 0.1, 0.25).heightM === sampleTile(lime, 0.3, 0.75).heightM,
    "The printed stone adds no physical relief");
  assert(Math.hypot(lime.color[0] - jume.color[0], lime.color[1] - jume.color[1], lime.color[2] - jume.color[2]) > 10,
    "Limestone and Jume are different prints");
  // Geometry tests run without a DOM; browser review exercises actual cached canvas maps.
  assert(buildTileMaps(carrara) === null, "Headless sampling requires no DOM or external assets");
  disposeTileTextures();
}
