// The tile styles and their pure, three-free sampling — shared by the main thread and the
// tile-map worker (→ tileMaps.worker.ts), which renders the 1024² maps off the main thread.
import { writeHeightNormals } from "./heightNormals";
import { latticeHash, tiledFbm } from "./valueNoise";
import type { TilePhotoKey } from "./tilePhotoCatalog";
import { sampleGatsbyPrint } from "./gatsbyPrint";

const INCH = 0.0254;
export const TILE_RENDER_SETTINGS = {
  pixels: 1024, groutDepthM: 0.0006, bevelM: 0.0007, groutRoughness: 0.85,
  anisotropy: 4, photoAnisotropy: 8,
} as const;

export interface TileStyle {
  readonly pattern: "running-bond" | "grid";
  readonly sizeM: readonly [number, number];
  readonly jointM: number;
  readonly color: readonly [number, number, number];
  readonly grout: readonly [number, number, number];
  readonly roughness: number;
  /** Per-tile shade: fired-clay batches, faint porcelain lots (default), or none. */
  readonly variation?: "terracotta" | "subtle" | "none";
  /** Strength of the printed vein; 0 (default) is an unveined face. */
  readonly veinWeight?: number;
  /** Joint roughness when the "joint" is the panel's own relief, not grout. */
  readonly jointRoughness?: number;
  /** Printed sheet joints have no physical grout recess. */
  readonly jointDepthM?: number;
  readonly inlay?: "gatsby";
  /** Tiles per repeat, [cols, rows]; default [2, 2]. */
  readonly repeat?: readonly [number, number];
  /** Bundled product photography; joints remain metric, independent of the image. */
  readonly photo?: TilePhotoKey;
}

export const TILE_STYLES: Readonly<Record<string, TileStyle>> = {
  "tile-kaleo-running-bond": {
    pattern: "running-bond", sizeM: [14.17 * INCH, 7.08 * INCH], jointM: INCH / 8,
    color: [187, 115, 83], grout: [232, 218, 180], roughness: 0.82, variation: "terracotta",
  },
  "tile-carrara-grid": {
    pattern: "grid", sizeM: [24 * INCH, 12 * INCH], jointM: INCH / 8,
    color: [244, 246, 246], grout: [250, 249, 245], roughness: 0.58, veinWeight: 0.42,
  },
  // Printed marble, alternating black corner diamonds and paired diagonal gold pinstripes.
  "tile-gatsby-grid": {
    pattern: "grid", sizeM: [9 * INCH, 9 * INCH], jointM: INCH / 16,
    color: [245, 245, 245], grout: [176, 177, 175], roughness: 0.4,
    inlay: "gatsby", jointDepthM: 0, jointRoughness: 0.4, variation: "none",
  },
  // Swanstone Modern Subway: a 6x24 relief moulded into one gloss panel, so the "grout" is
  // the body colour and only the recess reads.
  "tile-swanstone-modern-subway": {
    pattern: "running-bond", sizeM: [24 * INCH, 6 * INCH], jointM: INCH / 8,
    color: [244, 244, 242], grout: [244, 244, 242], roughness: 0.35, variation: "none",
    jointRoughness: 0.45,
  },
  // Photographed onyx-look polished porcelain; grout is platinum.
  "tile-onyx-opera-blue-grid": {
    pattern: "grid", sizeM: [24 * INCH, 48 * INCH], jointM: INCH / 16, repeat: [3, 2],
    color: [197, 198, 204], grout: [200, 201, 200], roughness: 0.16, variation: "none", photo: "opera-blue",
  },
  "tile-onyx-jume-blue-grid": {
    pattern: "grid", sizeM: [23.62 * INCH, 47.24 * INCH], jointM: INCH / 16, repeat: [2, 2],
    color: [120, 148, 169], grout: [200, 201, 200], roughness: 0.16,
    variation: "none", photo: "jume-onyx-blue",
  },
};

export function tileStyleOrNull(finish: string | null | undefined): TileStyle | null {
  return finish ? TILE_STYLES[finish] ?? null : null;
}

/** Rectangular repeat contains whole staggered rows, including joints. */
export function tileRepeatSizeM(style: TileStyle): readonly [number, number] {
  const [w, h] = style.sizeM;
  const [cols, rows] = style.repeat ?? [2, 2];
  return [(w + style.jointM) * cols, (h + style.jointM) * rows];
}

const wrap = (x: number, period: number) => ((x % period) + period) % period;
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const VEIN_COLOR = [139, 151, 160] as const;
const noiseOctaves: ReadonlyArray<readonly [number, number]> = [[4, 0.8], [13, 0.3], [37, 0.12]];

interface TileSample {
  readonly color: readonly number[];
  readonly heightM: number;
  readonly roughness: number;
}

/** Pure sampling also supports numerical seam and true-scale tests without a canvas. */
export function sampleTile(style: TileStyle, u: number, v: number): TileSample {
  u = wrap(u, 1); v = wrap(v, 1);
  const [repeatX, repeatY] = tileRepeatSizeM(style);
  const x = u * repeatX, y = v * repeatY;
  const px = style.sizeM[0] + style.jointM, py = style.sizeM[1] + style.jointM;
  const row = Math.floor(y / py);
  const shiftedX = x + (style.pattern === "running-bond" ? (row % 2) * px / 2 : 0);
  const col = Math.floor(shiftedX / px);
  const localX = wrap(shiftedX, px), localY = wrap(y, py);
  const distance = Math.min(localX, px - localX, localY, py - localY) - style.jointM / 2;
  const [cols, rows] = style.repeat ?? [2, 2];
  const id = latticeHash(wrap(col, cols), wrap(row, rows));
  const tileFraction = clamp(distance / TILE_RENDER_SETTINGS.bevelM);
  if (style.inlay === "gatsby") {
    const face = sampleGatsbyPrint(u, v, localX / px, localY / py, col, row, px, style.color);
    return {
      color: style.grout.map((channel, i) => channel * (1 - tileFraction) + face[i] * tileFraction),
      heightM: tileFraction * (style.jointDepthM ?? TILE_RENDER_SETTINGS.groutDepthM),
      roughness: (style.jointRoughness ?? TILE_RENDER_SETTINGS.groutRoughness) * (1 - tileFraction)
        + style.roughness * tileFraction,
    };
  }
  if (style.photo) return {
    color: style.grout.map((channel, i) => channel * (1 - tileFraction) + style.color[i] * tileFraction),
    heightM: tileFraction * TILE_RENDER_SETTINGS.groutDepthM,
    roughness: TILE_RENDER_SETTINGS.groutRoughness * (1 - tileFraction)
      + style.roughness * tileFraction,
  };
  const cloud = tiledFbm(u, v, noiseOctaves);
  const primary = Math.pow(1 - Math.abs(Math.sin(26 * localX + 17 * localY + 4 * cloud + id * 8)), 38);
  const secondary = Math.pow(1 - Math.abs(Math.sin(43 * localX - 31 * localY + 5 * cloud + id * 13)), 65);
  const vein = Math.max(primary, secondary * 0.45);
  const shade = style.variation ?? "subtle";
  const variation = shade === "terracotta" ? 0.90 + id * 0.18 + cloud * 0.10
    : shade === "subtle" ? 0.98 + id * 0.025 : 1;
  const veinAmount = vein * (style.veinWeight ?? 0);
  const color = style.color.map((channel, i) => {
    const tile = channel * variation * (1 - veinAmount) + VEIN_COLOR[i] * veinAmount;
    // Baked contact shading makes white recessed joints readable without changing grout hue.
    return style.grout[i] * 0.90 * (1 - tileFraction) + tile * tileFraction;
  });
  return {
    color, heightM: tileFraction * (style.jointDepthM ?? TILE_RENDER_SETTINGS.groutDepthM),
    roughness: (style.jointRoughness ?? TILE_RENDER_SETTINGS.groutRoughness) * (1 - tileFraction)
      + style.roughness * tileFraction,
  };
}

export interface TilePixels {
  readonly size: number;
  readonly color: Uint8ClampedArray<ArrayBuffer>;
  readonly normal: Uint8ClampedArray<ArrayBuffer>;
  readonly roughness: Uint8ClampedArray<ArrayBuffer>;
}

/** The colour, normal and roughness rasters of one style's repeat (RGBA). */
export function renderTilePixels(style: TileStyle): TilePixels {
  const size = TILE_RENDER_SETTINGS.pixels;
  const images = [0, 1, 2].map(() => new Uint8ClampedArray(size * size * 4));
  const heights = new Float32Array(size * size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const sample = sampleTile(style, x / size, y / size);
    const offset = (y * size + x) * 4;
    for (let c = 0; c < 3; c++) {
      images[0][offset + c] = Math.max(0, Math.min(255, Math.round(sample.color[c])));
      images[2][offset + c] = Math.round(sample.roughness * 255);
    }
    // Physical materials read clearcoat from R and roughness from G; grout has no glaze.
    if (style.photo) images[2][offset] = Math.round(
      sample.heightM / TILE_RENDER_SETTINGS.groutDepthM * 255);
    heights[y * size + x] = sample.heightM;
    for (const image of images) image[offset + 3] = 255;
  }
  const [widthM, heightM] = tileRepeatSizeM(style);
  writeHeightNormals(heights, size, size, size / (2 * widthM), size / (2 * heightM), images[1]);
  return { size, color: images[0], normal: images[1], roughness: images[2] };
}
