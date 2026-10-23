import * as THREE from "three";
import { TILE_STYLES, TILE_RENDER_SETTINGS, tileStyleOrNull, tileRepeatSizeM,
  sampleTile, applyTileUv, buildTileMaps, createTileMaterial, disposeTileTextures } from "./tileMaterial";

function assert(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}
const close = (a: number, b: number) => Math.abs(a - b) < 1e-7;

export function runTileMaterialTests() {
  assert(tileStyleOrNull("porcelain-tile") === null && tileStyleOrNull(null) === null,
    "Generic floors retain their existing rendering");
  const hex = TILE_STYLES["tile-calacatta-gold-hex"];
  const brick = TILE_STYLES["tile-kaleo-running-bond"];
  const carrara = TILE_STYLES["tile-carrara-grid"];
  assert(close(hex.sizeM[0], 2.86 * 0.0254), "Hex chip uses the selected product's actual size");
  assert(close(brick.sizeM[0], 14.17 * 0.0254), "Brick length follows the product");
  assert(close(carrara.sizeM[0], 24 * 0.0254) && close(carrara.sizeM[1], 12 * 0.0254),
    "Economy Carrara is 12 by 24 inches");
  assert(close(carrara.jointM, 1 / 8 * 0.0254), "Carrara joint follows manufacturer recommendation");
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
  // Geometry tests run without a DOM; browser review exercises actual cached canvas maps.
  assert(buildTileMaps(hex) === null, "Headless sampling requires no DOM or external assets");
  disposeTileTextures();
}
