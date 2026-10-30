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

/** Integer-lattice hash in [0, 1); fast and seedable, for untiled kernels (onyx faces). */
export function hashNoise2(ix: number, iy: number, seed = 0): number {
  let h = Math.imul(ix, 374761393) + Math.imul(iy, 668265263) + Math.imul(seed + 1, 1274126177);
  h = Math.imul(h ^ (h >>> 13), 1103515245);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Untiled smooth value noise in [0, 1) at lattice coordinates. */
export function valueNoise2(x: number, y: number, seed = 0): number {
  const x0 = Math.floor(x), y0 = Math.floor(y);
  const tx = x - x0, ty = y - y0;
  const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
  const a = hashNoise2(x0, y0, seed), b = hashNoise2(x0 + 1, y0, seed);
  const c = hashNoise2(x0, y0 + 1, seed), d = hashNoise2(x0 + 1, y0 + 1, seed);
  return a + (b - a) * sx + (c - a + (a - b - c + d) * sx) * sy;
}

/**
 * Untiled fbm centred on 0.5. `baseFreq` is the first octave's cycles per metre and `nyquist`
 * the cycles per metre the target raster resolves: octaves beyond it fade out gaussian-wise.
 */
export function fbm2(x: number, y: number, octaves: number, seed = 0,
  baseFreq = 1, nyquist = Infinity): number {
  let sum = 0, gain = 0.5, total = 0, freq = 1;
  for (let i = 0; i < octaves; i++, freq *= 2, gain *= 0.5) {
    const f = baseFreq * freq / nyquist;
    total += gain;
    if (f < 3) sum += gain * Math.exp(-0.5 * f * f) * (valueNoise2(x * freq, y * freq, seed + i * 31) - 0.5);
  }
  return 0.5 + sum / total;
}
