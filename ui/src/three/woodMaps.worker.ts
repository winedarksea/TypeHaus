// Renders wood maps off the main thread (→ woodMaps.ts); buffers go back as transferables.
import { renderWoodPixels, type WoodPixelJob } from "./woodPixels";

self.onmessage = (event: MessageEvent<{ id: number; job: WoodPixelJob }>) => {
  const { id, job } = event.data;
  try {
    const pixels = renderWoodPixels(job);
    (self as unknown as Worker).postMessage({ id, pixels },
      [pixels.color.buffer, pixels.normal.buffer, pixels.roughness.buffer]);
  } catch (error) {
    (self as unknown as Worker).postMessage({ id, error: String(error) });
  }
};
