// Deterministic, tileable value noise for the procedural finish maps (mineral wash, veined
// marble). No Math.random, so a tile is identical across reloads. Coordinates are in TILE
// units: `u, v` in [0, 1) span one repeat, and every lattice wraps at its own frequency, so
// any integer frequency is seamless across the tile edge.

/** A stable pseudo-random value in [0, 1) for an integer lattice point. */
export function latticeHash(x: number, y: number): number {
  const h = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return h - Math.floor(h);
}

/** Smoothstep-bilinear value noise in [0, 1) at integer `frequency`, wrapping over the tile. */
export function tiledValueNoise(u: number, v: number, frequency: number): number {
  const fx = u * frequency;
  const fy = v * frequency;
  const x0 = Math.floor(fx);
  const y0 = Math.floor(fy);
  const tx = fx - x0;
  const ty = fy - y0;
  const sx = tx * tx * (3 - 2 * tx);
  const sy = ty * ty * (3 - 2 * ty);
  const wrap = (n: number) => ((n % frequency) + frequency) % frequency;
  const n00 = latticeHash(wrap(x0), wrap(y0));
  const n10 = latticeHash(wrap(x0 + 1), wrap(y0));
  const n01 = latticeHash(wrap(x0), wrap(y0 + 1));
  const n11 = latticeHash(wrap(x0 + 1), wrap(y0 + 1));
  const top = n00 + (n10 - n00) * sx;
  const bottom = n01 + (n11 - n01) * sx;
  return top + (bottom - top) * sy;
}

/** Summed octaves, each `[frequency, amplitude]`, centred on zero. */
export function tiledFbm(u: number, v: number,
  octaves: readonly (readonly [number, number])[]): number {
  let value = 0;
  for (const [frequency, amplitude] of octaves) {
    value += (tiledValueNoise(u, v, frequency) - 0.5) * amplitude;
  }
  return value;
}
