/** Original product imagery and face boundaries, excluding photographed joints/margins. */
interface TilePhotoFace {
  readonly source: number;
  readonly crop: readonly [number, number, number, number];
  readonly landscape: boolean;
  readonly rotated?: boolean;
}
interface TilePhotoRecipe {
  readonly sources: readonly string[];
  readonly faces: readonly TilePhotoFace[];
  readonly photographedFaces: number;
}

export const TILE_PHOTO_FACE_PIXELS = [512, 1024] as const;
export const TILE_PHOTO_CATALOG = {
  "jume-onyx-blue": {
    sources: [
      new URL("../assets/tiles/jume-onyx-blue-pair.jpg", import.meta.url).href,
      new URL("../assets/tiles/jume-onyx-blue-face.jpg", import.meta.url).href,
    ],
    photographedFaces: 3,
    faces: [
      { source: 0, crop: [2, 2, 995, 494], landscape: true },
      { source: 1, crop: [4, 254, 991, 494], landscape: true },
      { source: 0, crop: [2, 504, 995, 494], landscape: true },
      { source: 1, crop: [4, 254, 991, 494], landscape: true, rotated: true },
    ],
  },
  "opera-blue": {
    sources: [
      new URL("../assets/tiles/opera-blue-face.jpg", import.meta.url).href,
      new URL("../assets/tiles/opera-blue-installed.jpg", import.meta.url).href,
      new URL("../assets/tiles/opera-blue-alternate.jpg", import.meta.url).href,
    ],
    photographedFaces: 3,
    // Full faces only: the partial tiles beside the installed centre face are excluded.
    faces: [
      { source: 2, crop: [7, 232, 895, 447], landscape: true },
      { source: 1, crop: [252, 3, 494, 993], landscape: false },
      { source: 0, crop: [10, 383, 1478, 736], landscape: true },
      { source: 1, crop: [252, 3, 494, 993], landscape: false, rotated: true },
      { source: 0, crop: [10, 383, 1478, 736], landscape: true, rotated: true },
      { source: 2, crop: [7, 232, 895, 447], landscape: true, rotated: true },
    ],
  },
} as const satisfies Record<string, TilePhotoRecipe>;
export type TilePhotoKey = keyof typeof TILE_PHOTO_CATALOG;

export function tilePhotoRecipe(key: TilePhotoKey): TilePhotoRecipe {
  return TILE_PHOTO_CATALOG[key];
}
