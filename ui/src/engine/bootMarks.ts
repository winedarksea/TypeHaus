// `window.__haus.boot`: one boot timeline both engines write, read by `perf-check` and
// `measure-first-house`. Each entry is a step's duration and when it ended, in page ms. First
// landing only — a later edit's rebuild is not boot.
//
// Client marks (same names in both modes): modelFetch, modelParse, panel3dChunk, shellVisible,
// sceneComplete, firstFrame. Engine marks (the worker's steps) arrive with an epoch `at`.

export interface BootEntry {
  ms: number;
  at: number;
}

function bootTable(): Record<string, BootEntry> | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { __haus?: Record<string, unknown> };
  const haus = (w.__haus ??= {});
  return (haus.boot ??= {}) as Record<string, BootEntry>;
}

// Record `name` as ending now (or at epoch `atEpoch`), having taken `ms`.
export function bootMark(name: string, ms: number, atEpoch?: number): void {
  const boot = bootTable();
  if (!boot) return;
  const at = atEpoch === undefined ? performance.now() : atEpoch - performance.timeOrigin;
  boot[name] ??= { ms, at };
}

// Time `fn` (sync or async) as boot step `name`.
export async function bootTimed<T>(name: string, fn: () => Promise<T> | T): Promise<T> {
  const t0 = performance.now();
  const out = await fn();
  bootMark(name, performance.now() - t0);
  return out;
}
