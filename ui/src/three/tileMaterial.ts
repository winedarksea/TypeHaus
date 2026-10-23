/** Product-sized bathroom finishes. Joint widths are visual allowances unless noted. */
import * as THREE from "three";
import { projectScenePointToPlan, type PlanCenter } from "./planGeometry";
import { latticeHash, tiledFbm } from "./valueNoise";

const INCH = 0.0254;
const SQRT3 = Math.sqrt(3);
export const TILE_RENDER_SETTINGS = {
  pixels: 1024, groutDepthM: 0.0006, bevelM: 0.0007, groutRoughness: 0.85,
  anisotropy: 4,
} as const;

export interface TileStyle {
  readonly pattern: "hex" | "running-bond" | "flower" | "grid";
  readonly sizeM: readonly [number, number];
  readonly jointM: number;
  readonly color: readonly [number, number, number];
  readonly grout: readonly [number, number, number];
  readonly roughness: number;
}

export const TILE_STYLES: Readonly<Record<string, TileStyle>> = {
  "tile-calacatta-gold-hex": {
    pattern: "hex", sizeM: [2.86 * INCH, 2.86 * INCH], jointM: INCH / 8,
    color: [247, 245, 239], grout: [249, 248, 244], roughness: 0.72,
  },
  "tile-kaleo-running-bond": {
    pattern: "running-bond", sizeM: [14.17 * INCH, 7.08 * INCH], jointM: INCH / 8,
    color: [187, 115, 83], grout: [232, 218, 180], roughness: 0.82,
  },
  "tile-flower-blue": {
    pattern: "flower", sizeM: [11.12 * INCH, 11.44 * INCH], jointM: INCH / 16,
    color: [244, 245, 242], grout: [211, 215, 215], roughness: 0.22,
  },
  "tile-carrara-grid": {
    pattern: "grid", sizeM: [24 * INCH, 12 * INCH], jointM: INCH / 8,
    color: [244, 246, 246], grout: [250, 249, 245], roughness: 0.58,
  },
};

export function tileStyleOrNull(finish: string | null | undefined): TileStyle | null {
  return finish ? TILE_STYLES[finish] ?? null : null;
}

/** Rectangular repeat contains whole staggered rows / hex columns, including joints. */
export function tileRepeatSizeM(style: TileStyle): readonly [number, number] {
  const [w, h] = style.sizeM;
  if (style.pattern === "hex") {
    const pitch = w + style.jointM;
    return [2 * SQRT3 * pitch, 2 * pitch];
  }
  if (style.pattern === "flower") return [w, h];
  return [(w + style.jointM) * 2, (h + style.jointM) * 2];
}

const wrap = (x: number, period: number) => ((x % period) + period) % period;
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const noiseOctaves: ReadonlyArray<readonly [number, number]> = [[4, 0.8], [13, 0.3], [37, 0.12]];
const BLUE_COLORS = [[235, 240, 240], [181, 207, 218], [119, 159, 180], [82, 113, 139],
  [240, 241, 237], [213, 221, 224]] as const;

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
  let distance = 0, id = 0, localX = x, localY = y;
  let base: readonly number[] = style.color;
  if (style.pattern === "hex") {
    const pitch = style.sizeM[0] + style.jointM;
    const columnPitch = SQRT3 * pitch / 2;
    let best = -Infinity;
    const column = Math.round(x / columnPitch);
    for (let c = column - 1; c <= column + 1; c++) {
      const row = Math.round(y / pitch - c / 2);
      const dx = x - c * columnPitch, dy = y - (row + c / 2) * pitch;
      const edge = Math.max(Math.abs(dy), SQRT3 / 2 * Math.abs(dx) + Math.abs(dy) / 2);
      const inside = style.sizeM[0] / 2 - edge;
      if (inside > best) {
        best = inside; localX = dx; localY = dy;
        id = latticeHash(wrap(c, 4), wrap(row + Math.floor(c / 2), 2));
      }
    }
    distance = best;
  } else if (style.pattern === "flower") {
    // Marquise glass pieces follow a periodic swirl, with white glass infill. The
    // mesh-sheet dimensions set the repeat; these are shaped chips, not a floral print.
    const cells = 8;
    const cellX = repeatX / cells, cellY = repeatY / cells;
    const column = Math.floor(x / cellX), row = Math.floor(y / cellY);
    let closestEdge = -Infinity, selectedColor: readonly number[] = style.color;
    for (let c = column - 1; c <= column + 1; c++) {
      for (let r = row - 1; r <= row + 1; r++) {
        const phaseX = (wrap(c, cells) + 0.5) / cells * Math.PI * 2;
        const phaseY = (wrap(r, cells) + 0.5) / cells * Math.PI * 2;
        const centerX = (c + 0.5 + 0.12 * Math.sin(phaseY)) * cellX;
        const centerY = (r + 0.5 + 0.12 * Math.sin(phaseX)) * cellY;
        const angle = Math.atan2(Math.sin(phaseY), Math.sin(phaseX)) + 0.65;
        const dx = x - centerX, dy = y - centerY;
        const along = dx * Math.cos(angle) + dy * Math.sin(angle);
        const across = -dx * Math.sin(angle) + dy * Math.cos(angle);
        const halfLength = cellX * 0.65, halfWidth = cellY * 0.28;
        const edge = Math.min(halfLength - Math.abs(along),
          halfWidth * (1 - (along / halfLength) ** 2) - Math.abs(across));
        if (edge > closestEdge) {
          closestEdge = edge; localX = along; localY = across;
          id = latticeHash(wrap(c, cells), wrap(r, cells));
          selectedColor = BLUE_COLORS[Math.floor(id * BLUE_COLORS.length)];
        }
      }
    }
    base = closestEdge > 0 ? selectedColor : style.color;
    distance = Math.abs(closestEdge) - style.jointM / 2;
  } else {
    const px = style.sizeM[0] + style.jointM, py = style.sizeM[1] + style.jointM;
    const row = Math.floor(y / py);
    const shiftedX = x + (style.pattern === "running-bond" ? (row % 2) * px / 2 : 0);
    const col = Math.floor(shiftedX / px);
    localX = wrap(shiftedX, px); localY = wrap(y, py);
    distance = Math.min(localX, px - localX, localY, py - localY) - style.jointM / 2;
    id = latticeHash(wrap(col, 2), wrap(row, 2));
  }
  const tileFraction = clamp(distance / TILE_RENDER_SETTINGS.bevelM);
  const cloud = tiledFbm(u, v, noiseOctaves);
  const primary = Math.pow(1 - Math.abs(Math.sin(26 * localX + 17 * localY + 4 * cloud + id * 8)), 38);
  const secondary = Math.pow(1 - Math.abs(Math.sin(43 * localX - 31 * localY + 5 * cloud + id * 13)), 65);
  const vein = Math.max(primary, secondary * 0.45);
  const terracotta = style.pattern === "running-bond";
  const variation = terracotta ? 0.90 + id * 0.18 + cloud * 0.10 : 0.98 + id * 0.025;
  const veinColor = style.pattern === "hex" ? [178, 146, 93] : [139, 151, 160];
  const veinAmount = terracotta ? 0 : vein * (style.pattern === "flower" ? 0.18 : 0.42);
  const color = base.map((channel, i) => {
    const tile = channel * variation * (1 - veinAmount) + veinColor[i] * veinAmount;
    // Baked contact shading makes white recessed joints readable without changing grout hue.
    return style.grout[i] * 0.90 * (1 - tileFraction) + tile * tileFraction;
  });
  return {
    color, heightM: tileFraction * TILE_RENDER_SETTINGS.groutDepthM,
    roughness: TILE_RENDER_SETTINGS.groutRoughness * (1 - tileFraction)
      + style.roughness * tileFraction,
  };
}

interface TileMaps { color: THREE.Texture; normal: THREE.Texture; roughness: THREE.Texture }
const tileMaps = new Map<TileStyle, TileMaps>();

export function buildTileMaps(style: TileStyle): TileMaps | null {
  if (tileMaps.has(style)) return tileMaps.get(style)!;
  if (typeof document === "undefined") return null;
  const size = TILE_RENDER_SETTINGS.pixels;
  const canvases = Array.from({ length: 3 }, () => {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    return canvas;
  });
  const contexts = canvases.map(canvas => canvas.getContext("2d"));
  if (contexts.some(context => !context)) throw new Error("2D canvas unavailable for tile maps");
  const images = contexts.map(context => context!.createImageData(size, size));
  const heights = new Float32Array(size * size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const sample = sampleTile(style, x / size, y / size);
    const offset = (y * size + x) * 4;
    for (let c = 0; c < 3; c++) {
      images[0].data[offset + c] = Math.max(0, Math.min(255, Math.round(sample.color[c])));
      images[2].data[offset + c] = Math.round(sample.roughness * 255);
    }
    heights[y * size + x] = sample.heightM;
    for (const image of images) image.data[offset + 3] = 255;
  }
  const [widthM, heightM] = tileRepeatSizeM(style);
  const height = (x: number, y: number) => heights[wrap(y, size) * size + wrap(x, size)];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const dx = (height(x + 1, y) - height(x - 1, y)) * size / (2 * widthM);
    const dy = (height(x, y + 1) - height(x, y - 1)) * size / (2 * heightM);
    const n = new THREE.Vector3(-dx, -dy, 1).normalize();
    const offset = (y * size + x) * 4;
    [n.x, n.y, n.z].forEach((value, i) => { images[1].data[offset + i] = (value * 0.5 + 0.5) * 255; });
  }
  const textures = canvases.map((canvas, index) => {
    contexts[index]!.putImageData(images[index], 0, 0);
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.colorSpace = index === 0 ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    texture.anisotropy = TILE_RENDER_SETTINGS.anisotropy;
    return texture;
  });
  const maps = { color: textures[0], normal: textures[1], roughness: textures[2] };
  tileMaps.set(style, maps);
  return maps;
}

export function createTileMaterial(mode: "nordic" | "schematic", style: TileStyle,
  schematicColor: THREE.ColorRepresentation): THREE.MeshStandardMaterial {
  const maps = mode === "nordic" ? buildTileMaps(style) : null;
  return new THREE.MeshStandardMaterial({
    color: maps ? 0xffffff : schematicColor, metalness: 0,
    roughness: mode === "schematic" ? 1 : maps ? 1 : style.roughness,
    map: maps?.color ?? null, normalMap: maps?.normal ?? null, roughnessMap: maps?.roughness ?? null,
    flatShading: mode === "schematic",
  });
}

/** Project coordinates keep phase through clipped room parts and independent of camera. */
export function applyTileUv(geometry: THREE.BufferGeometry, center: PlanCenter, style: TileStyle): void {
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  const [width, height] = tileRepeatSizeM(style);
  for (let i = 0; i < positions.count; i++) {
    const [x, y] = projectScenePointToPlan(positions.getX(i), positions.getZ(i), center);
    uv[i * 2] = x / width; uv[i * 2 + 1] = y / height;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

export function disposeTileTextures(): void {
  for (const maps of tileMaps.values()) Object.values(maps).forEach(map => map.dispose());
  tileMaps.clear();
}
