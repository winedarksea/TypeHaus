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
  "lifeproof-limestone": {
    sources: [new URL("../assets/tiles/lifeproof-limestone-face.jpg", import.meta.url).href],
    photographedFaces: 5,
    // Swatch faces are 2:1 landscape, strictly inside the grout (measured from pixels): top right,
    // row 2 centre, row 3 centre, row 4 left and right. The badge-covered top-left face is excluded.
    // Ten cells: five faces, then their rotations shifted two columns so none sits beside its own.
    faces: [
      { source: 0, crop: [506, 21, 472, 229], landscape: true },
      { source: 0, crop: [341, 262, 479, 234], landscape: true },
      { source: 0, crop: [177, 508, 481, 234], landscape: true },
      { source: 0, crop: [21, 755, 470, 222], landscape: true },
      { source: 0, crop: [503, 755, 474, 222], landscape: true },
      { source: 0, crop: [177, 508, 481, 234], landscape: true, rotated: true },
      { source: 0, crop: [21, 755, 470, 222], landscape: true, rotated: true },
      { source: 0, crop: [503, 755, 474, 222], landscape: true, rotated: true },
      { source: 0, crop: [506, 21, 472, 229], landscape: true, rotated: true },
      { source: 0, crop: [341, 262, 479, 234], landscape: true, rotated: true },
    ],
  },
} as const satisfies Record<string, TilePhotoRecipe>;
export type TilePhotoKey = keyof typeof TILE_PHOTO_CATALOG;

export function tilePhotoRecipe(key: TilePhotoKey): TilePhotoRecipe {
  return TILE_PHOTO_CATALOG[key];
}
