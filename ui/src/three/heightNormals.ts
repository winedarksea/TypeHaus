// A tangent-space normal map from a wrapped height field, in scalar math: the per-pixel
// `new Vector3(...).normalize()` this replaces was most of a procedural map's build time.

/** Central differences of `heights` (w×h, wrapping), scaled by `scaleX`/`scaleY`, into the RGB
 *  of `out` (RGBA, alpha left alone). */
export function writeHeightNormals(
  heights: Float32Array, w: number, h: number, scaleX: number, scaleY: number,
  out: Uint8ClampedArray | Uint8Array,
): void {
  const round = out instanceof Uint8Array;
  for (let y = 0; y < h; y++) {
    const up = ((y + 1) % h) * w, down = ((y - 1 + h) % h) * w, row = y * w;
    for (let x = 0; x < w; x++) {
      const right = (x + 1) % w, left = (x - 1 + w) % w;
      const nx = -(heights[row + right] - heights[row + left]) * scaleX;
      const ny = -(heights[up + x] - heights[down + x]) * scaleY;
      const inv = 1 / Math.sqrt(nx * nx + ny * ny + 1);
      const offset = (row + x) * 4;
      const r = (nx * inv * 0.5 + 0.5) * 255, g = (ny * inv * 0.5 + 0.5) * 255, b = (inv * 0.5 + 0.5) * 255;
      // A plain byte array truncates; the canvas's clamped array rounds. Keep each caller's.
      out[offset] = round ? Math.round(r) : r;
      out[offset + 1] = round ? Math.round(g) : g;
      out[offset + 2] = round ? Math.round(b) : b;
    }
  }
}
