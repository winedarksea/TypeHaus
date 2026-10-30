// Renders onyx faces off the main thread (→ onyxMaps.ts); buffers go back as transferables.
import { renderOnyxFacePixels, type OnyxPixelJob } from "./onyxPixels";

self.onmessage = (event: MessageEvent<{ id: number; job: OnyxPixelJob }>) => {
  const { id, job } = event.data;
  try {
    const pixels = renderOnyxFacePixels(job);
    (self as unknown as Worker).postMessage({ id, pixels },
      [pixels.color.buffer, pixels.normal.buffer, pixels.orm.buffer]);
  } catch (error) {
    (self as unknown as Worker).postMessage({ id, error: String(error) });
  }
};
