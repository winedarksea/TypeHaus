// The wood figure kernel: plain arrays, no DOM and no three, so the worker can run it.
import { hashBoard, layoutPlankTile, type PlankStyle } from "./plankLayout";
import { woodFigureSampler, WOOD_RENDER_SETTINGS as SETTINGS,
  type WoodSpeciesProfile, type WoodSurface } from "./woodSpecies";

export interface WoodPixelJob {
  readonly style: PlankStyle;
  readonly profile: WoodSpeciesProfile;
  readonly base: readonly [number, number, number]; // sRGB, 0..1
  readonly surface: WoodSurface;
  readonly endGrain: boolean;
}
export interface WoodPixels {
  readonly width: number;
  readonly height: number;
  readonly color: Uint8ClampedArray;
  readonly normal: Uint8ClampedArray;
  readonly roughness: Uint8ClampedArray;
}
// A site-sanded butt joint is flush; a raised normal at each end reads as a factory bevel.
const JOINT_DEPTH_M = { vee: 0.0011, bevel: 0.0007, butt: 0 } as const;
const clamp = (v: number) => Math.max(0, Math.min(1, v));

export function woodTileSize(style: PlankStyle, endGrain: boolean) {
  const acrossM = style.faceWidthM * style.boardsPerTile;
  const alongM = endGrain ? style.faceWidthM : style.tileAlongM;
  const density = Math.min(style.pxPerM, SETTINGS.maximumTextureEdge / Math.max(acrossM, alongM));
  return { acrossM, alongM, density,
    width: Math.max(16, Math.round(acrossM * density)),
    height: Math.max(16, Math.round(alongM * density)) };
}

/** Full-colour maps: the texture carries the authored base plus positive AND negative variation. */
export function renderWoodPixels({ style, profile, base, surface, endGrain }: WoodPixelJob): WoodPixels {
  const { acrossM, alongM, density, width, height } = woodTileSize(style, endGrain);
  const color = new Uint8ClampedArray(width * height * 4);
  const normal = new Uint8ClampedArray(width * height * 4);
  const roughness = new Uint8ClampedArray(width * height * 4);
  const relief = new Float32Array(width * height);
  const lanes = endGrain ? Array.from({ length: style.boardsPerTile }, (_, i) =>
    [{ v0: 0, v1: alongM, printId: i }]) : layoutPlankTile(style);
  const boardSamplers = lanes.map(lane => lane.map(board => ({ ...board,
    sample: woodFigureSampler(board.printId, profile, endGrain, density),
    variation: (hashBoard(board.printId, 7) - 0.5) * profile.variation,
    hue: (hashBoard(board.printId, 11) - 0.5) * profile.variation * 0.35,
    sapwood: hashBoard(board.printId, 12) < profile.sapwood,
  })));
  const pixelWidthM = acrossM / width, pixelHeightM = alongM / height;
  const poreDepth = surface === "unfinished" ? SETTINGS.unfinishedPoreDepthM : SETTINGS.clearPoreDepthM;
  for (let x = 0; x < width; x++) {
    const lane = Math.min(style.boardsPerTile - 1, Math.floor(x / width * style.boardsPerTile));
    const localX = (x + 0.5) * pixelWidthM - lane * style.faceWidthM;
    const edgeX = Math.min(localX, style.faceWidthM - localX);
    for (let y = 0; y < height; y++) {
      const v = (y + 0.5) * pixelHeightM;
      const boards = boardSamplers[lane];
      // A wrapped plank is the SAME board on both sides of the texture boundary.
      const board = boards.find(b => v >= b.v0 && v < b.v1)
        ?? boards[boards.length - 1];
      const localY = (v - board.v0 + alongM) % alongM;
      const figure = board.sample(localX, localY);
      if (!endGrain && style.lengths.kind === "continuous") {
        // Blend only the far end of a continuous tile; no hard figure reset on tall walls.
        const blend = clamp((localY - alongM + 0.25) / 0.25);
        if (blend > 0) {
          const wrapped = board.sample(localX, localY - alongM);
          const smooth = blend * blend * (3 - 2 * blend);
          figure.tone += (wrapped.tone - figure.tone) * smooth;
          figure.pore += (wrapped.pore - figure.pore) * smooth;
        }
      }
      const variation = board.variation;
      const hue = board.hue;
      const sapwoodEdge = board.sapwood
        ? clamp((0.018 - localX + Math.sin(localY * 4) * 0.003) / 0.008) : 0;
      const edgeY = style.lengths.kind === "continuous" || endGrain ? Infinity
        : Math.min(localY, board.v1 - board.v0 - localY);
      const jointWidth = endGrain ? 0 : style.faceWidthM * style.jointFraction;
      const joint = jointWidth > 0 ? clamp(1 - Math.min(edgeX, edgeY) / (jointWidth * 0.7)) : 0;
      const painted = surface === "painted";
      const tone = painted ? 1 : 1 + variation + figure.tone;
      const endShade = endGrain && !painted ? SETTINGS.endGrainDarkening : 1;
      const offset = (y * width + x) * 4;
      for (let channel = 0; channel < 3; channel++) {
        const tint = painted ? base[channel] : base[channel] * (tone + hue * (1 - channel))
          + sapwoodEdge * (SETTINGS.sapwoodSrgb[channel] - base[channel]) * 0.75;
        color[offset + channel] = Math.round(clamp(tint * endShade * (1 - joint * 0.35)) * 255);
        roughness[offset + channel] = Math.round(255 * (1 - SETTINGS.roughnessVariation
          + (painted ? 0 : figure.pore * 0.8 + (0.5 + figure.tone) * SETTINGS.roughnessVariation)));
      }
      color[offset + 3] = roughness[offset + 3] = 255;
      relief[y * width + x] = -joint * JOINT_DEPTH_M[style.jointProfile]
        - (painted ? 0 : figure.pore * poreDepth / 0.06);
    }
  }
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    const at = (a: number, b: number) => relief[((b + height) % height) * width + (a + width) % width];
    const dx = (at(x + 1, y) - at(x - 1, y)) / (2 * pixelWidthM);
    // Canvas y is flipped in a THREE texture: its height derivative has the opposite sign.
    const dy = -(at(x, y + 1) - at(x, y - 1)) / (2 * pixelHeightM);
    const length = Math.hypot(dx, dy, 1), offset = (y * width + x) * 4;
    normal[offset] = Math.round((0.5 - dx / length * 0.5) * 255);
    normal[offset + 1] = Math.round((0.5 - dy / length * 0.5) * 255);
    normal[offset + 2] = Math.round((0.5 + 1 / length * 0.5) * 255);
    normal[offset + 3] = 255;
  }
  return { width, height, color, normal, roughness };
}
