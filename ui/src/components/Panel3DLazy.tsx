import { lazy, Suspense } from "react";

// The 3D panel, code-split away from the first paint.
//
// three.js is ~670 KB minified before GLTFLoader and RoomEnvironment, and it was sitting in the
// single entry chunk even for a user who never leaves 2D — where App unmounts Panel3D entirely.
// Splitting it here rather than at each call site keeps the two mount points (the full pane in
// App, the floating preview) importing one thing.
//
// The fallback is deliberately nothing: the pane is an empty box until the WebGL context and the
// scene exist anyway, so a spinner would only add a flash of chrome to a load that is a local
// chunk fetch.
const Panel3DImpl = lazy(() =>
  import("./Panel3D").then((module) => ({ default: module.Panel3D })));

export function Panel3D({ compact = false }: { compact?: boolean }) {
  return (
    <Suspense fallback={null}>
      <Panel3DImpl compact={compact} />
    </Suspense>
  );
}
