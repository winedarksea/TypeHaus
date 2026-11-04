// What procedural texture generation cost since the last read (→ Panel3D publishPerf,
// perf-check). The maps are module-cached, so a rebuild that finds them warm reports nothing.
const textureMs: Record<string, number> = {};

/** Start timing one generator run; call the returned function when the map is built. */
export function textureTimer(name: string): () => void {
  const t0 = performance.now();
  return () => { textureMs[name] = (textureMs[name] ?? 0) + performance.now() - t0; };
}

/** The texture cost accumulated since the last call, then reset. */
export function takeTextureMs(): Record<string, number> {
  const out = { ...textureMs };
  for (const name of Object.keys(textureMs)) delete textureMs[name];
  return out;
}
