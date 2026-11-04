// Renders tile maps off the main thread (→ tileMaps.ts); buffers go back as transferables.
import { renderTilePixels, type TileStyle } from "./tilePixels";

self.onmessage = (event: MessageEvent<{ id: number; style: TileStyle }>) => {
  const { id, style } = event.data;
  try {
    const pixels = renderTilePixels(style);
    (self as unknown as Worker).postMessage({ id, pixels },
      [pixels.color.buffer, pixels.normal.buffer, pixels.roughness.buffer]);
  } catch (error) {
    (self as unknown as Worker).postMessage({ id, error: String(error) });
  }
};
