import * as THREE from "three";
import { ONYX_PRINTS, hexRgb, renderOnyxFacePixels } from "./onyxPixels";
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
  for (const [key, print] of [["tile-onyx-opera-blue-grid", "opera-blue"], ["tile-onyx-agua-linda-grid", "agua-linda"]] as const) {
    const onyx = TILE_STYLES[key];
    const [ow, oh] = tileRepeatSizeM(onyx);
    assert(close(ow, 4 * (24 + 1 / 16) * IN) && close(oh, 2 * (48 + 1 / 16) * IN), `${key}: true-scale repeat`);
    assert(onyx.print === print && onyx.jointM === IN / 16, `${key}: names its print`);
    const job = { print, face: 0, pitchM: [(24 + 1 / 16) * IN, (48 + 1 / 16) * IN] as const, jointM: IN / 16,
      grout: onyx.grout, width: 64, height: 128 };
    const a = renderOnyxFacePixels(job), b = renderOnyxFacePixels(job);
    assert(a.color.every((c, i) => c === b.color[i]) && a.orm.every((c, i) => c === b.orm[i]),
      `${key}: pixels are deterministic`);
    const other = renderOnyxFacePixels({ ...job, face: 1 });
    let diff = 0, count = 0;
    for (let i = 0; i < a.color.length; i += 4) for (let c = 0; c < 3; c++) { diff += Math.abs(a.color[i + c] - other.color[i + c]); count++; }
    assert(diff / count > 8, `${key}: faces differ`);
    const mean = hexRgb(ONYX_PRINTS[print].faceMean);
    for (let face = 0; face < ONYX_PRINTS[print].faces; face++) {
      const p = face === 0 ? a : renderOnyxFacePixels({ ...job, face });
      const m = [0, 0, 0];
      for (let i = 0; i < p.color.length; i += 4) for (let c = 0; c < 3; c++) m[c] += p.color[i + c] / (p.color.length / 4);
      assert(m.every((v, c) => Math.abs(v - mean[c]) < 12), `${key}: face ${face} mean is near the authored colour`);
    }
  }
  const distance = (print: "opera-blue" | "agua-linda") => hexRgb(ONYX_PRINTS[print].faceMean);
  const [m1, m2] = [distance("opera-blue"), distance("agua-linda")];
  assert(Math.hypot(m1[0] - m2[0], m1[1] - m2[1], m1[2] - m2[2]) > 10, "The two prints are different blues");
  // Geometry tests run without a DOM; browser review exercises actual cached canvas maps.
  assert(buildTileMaps(carrara) === null, "Headless sampling requires no DOM or external assets");
  disposeTileTextures();
}
