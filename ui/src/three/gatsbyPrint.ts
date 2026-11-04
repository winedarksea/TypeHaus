/** Windsor Gatsby 87061, reconstructed from the product swatch:
 * https://www.diamondw.com/wp-content/uploads/2023/05/First-Class-Web-Swatch-Windsor-Gatsby.jpg
 * Two diagonal black corners per square alternate direction; four corners form a diamond.
 */
import { tiledFbm } from "./valueNoise";

export const GATSBY_PRINT_SETTINGS = {
  blackCornerFraction: 0.29,
  goldDiagonalOffsets: [0.75, 1.25],
  goldLineWidthM: 0.0254 / 16,
  black: [37, 38, 39], whiteVein: [155, 158, 160], gold: [171, 146, 68],
  whiteCloudStrength: 30, whiteVeinStrength: 42, blackVeinStrength: 0.35,
  blackCloudStrength: 12, veinFrequency: [18, 11], veinWarp: 5, veinExponent: 8,
  cloudOctaves: [[4, 0.8], [13, 0.3], [37, 0.12]],
} as const;

/** Cell coordinates span [0,1]; repeat coordinates keep the marble noise tileable. */
export function sampleGatsbyPrint(
  u: number, v: number, cellX: number, cellY: number, column: number, row: number,
  cellWidthM: number, white: readonly number[],
): readonly number[] {
  const settings = GATSBY_PRINT_SETTINGS;
  const diagonal = ((column + row) % 2 === 0 ? cellX : 1 - cellX) + cellY;
  const cloud = tiledFbm(u, v, settings.cloudOctaves);
  const vein = Math.pow(1 - Math.abs(Math.sin(
    settings.veinFrequency[0] * u + settings.veinFrequency[1] * v + cloud * settings.veinWarp,
  )), settings.veinExponent);
  if (diagonal < settings.blackCornerFraction || diagonal > 2 - settings.blackCornerFraction) {
    return settings.black.map((channel, index) => channel + cloud * settings.blackCloudStrength
      + (settings.whiteVein[index] - channel) * vein * settings.blackVeinStrength);
  }
  const goldDistanceM = Math.min(...settings.goldDiagonalOffsets.map(offset =>
    Math.abs(diagonal - offset))) * cellWidthM / Math.SQRT2;
  if (goldDistanceM < settings.goldLineWidthM / 2) return settings.gold;
  return white.map(channel => channel + cloud * settings.whiteCloudStrength
    - vein * settings.whiteVeinStrength);
}
