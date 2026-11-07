import type { TileStyle } from "./tilePixels";
import { tilePhotoRecipe, TILE_PHOTO_FACE_PIXELS } from "./tilePhotoCatalog";

// Keep the original product photos bundled: Vite fingerprints them and the PWA caches them.
/** Product faces and rotated repeats; not a reconstruction of every manufactured print. */
export async function buildTilePhotoCanvas(style: TileStyle): Promise<HTMLCanvasElement> {
  if (!style.photo) throw new Error("A tile photo recipe is required");
  const recipe = tilePhotoRecipe(style.photo);
  const images = await Promise.all(recipe.sources.map(async url => {
    const image = new Image();
    image.src = url;
    await image.decode();
    return image;
  }));
  const [cols, rows] = style.repeat ?? [2, 2];
  const [width, height] = TILE_PHOTO_FACE_PIXELS;
  const canvas = document.createElement("canvas");
  canvas.width = width * cols; canvas.height = height * rows;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("2D canvas unavailable for product tile photography");
  context.fillStyle = `rgb(${style.grout.join(",")})`;
  context.fillRect(0, 0, canvas.width, canvas.height);
  const jointX = style.jointM / (style.sizeM[0] + style.jointM) * width;
  const jointY = style.jointM / (style.sizeM[1] + style.jointM) * height;
  for (let cell = 0; cell < cols * rows; cell++) {
    const face = recipe.faces[cell % recipe.faces.length];
    context.save();
    context.translate((cell % cols + 0.5) * width, (Math.floor(cell / cols) + 0.5) * height);
    // Source orientation varies; the house lays the long axis along plan Y.
    context.rotate((face.landscape ? Math.PI / 2 : 0) + (face.rotated ? Math.PI : 0));
    const [sourceX, sourceY, sourceWidth, sourceHeight] = face.crop;
    const targetWidth = face.landscape ? height - jointY : width - jointX;
    const targetHeight = face.landscape ? width - jointX : height - jointY;
    context.drawImage(images[face.source], sourceX, sourceY, sourceWidth, sourceHeight,
      -targetWidth / 2, -targetHeight / 2, targetWidth, targetHeight);
    context.restore();
  }
  return canvas;
}
