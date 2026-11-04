import { lazy, Suspense } from "react";
import { bootTimed } from "../engine/bootMarks";
import { Loading3D } from "./Loading3D";

// The 3D panel, code-split away from the first paint.
//
// three.js is ~670 KB minified before GLTFLoader and RoomEnvironment; without this split it
// would sit in the entry chunk even for a user who never leaves 2D, where App unmounts Panel3D
// entirely. Splitting it here rather than at each call site keeps the two mount points (the
// full pane in App, the floating preview) importing one thing.
//
// The fallback is the same overlay the scene build shows (→ Loading3D): on a cold cache or a
// slow link the chunk is seconds, not a flash, and an empty pane reads as broken.
let chunk: Promise<typeof import("./Panel3D")> | null = null;
/** Start the chunk fetch early (App does so at init or once the first model lands); idempotent. */
export function preloadPanel3D() {
  chunk ??= bootTimed("panel3dChunk", () => import("./Panel3D"));
  return chunk;
}

/** The same, in idle time — then warm the procedural texture maps the first build would
 *  otherwise pay for. Returns a cancel. */
export function preloadPanel3DWhenIdle(): () => void {
  const idle = (run: () => void): (() => void) => {
    if (typeof requestIdleCallback === "function") {
      const handle = requestIdleCallback(run, { timeout: 2000 });
      return () => cancelIdleCallback(handle);
    }
    const handle = setTimeout(run, 200);
    return () => clearTimeout(handle);
  };
  let cancelWarm: (() => void) | null = null;
  let cancelled = false;
  const cancelLoad = idle(() => {
    preloadPanel3D().then((module) => {
      if (!cancelled) cancelWarm = module.warmProceduralTextures(idle);
    }).catch(() => { /* the pane's own lazy() surfaces a failed chunk */ });
  });
  return () => { cancelled = true; cancelLoad(); cancelWarm?.(); };
}

const Panel3DImpl = lazy(() =>
  preloadPanel3D().then((module) => ({ default: module.Panel3D })));

export function Panel3D({ compact = false }: { compact?: boolean }) {
  return (
    <Suspense fallback={<Loading3D />}>
      <Panel3DImpl compact={compact} />
    </Suspense>
  );
}
