import type { BuildProgress } from "../three/builders/sceneStages";

// The one "the 3D view is on its way" overlay, in both engine modes: while the model loads
// (App), while the three.js chunk loads (Panel3DLazy), and while the scene builds (Panel3D).
export function Loading3D({ label = "Loading 3D view…", progress }: {
  label?: string;
  progress?: BuildProgress | null;
}) {
  return (
    <div className="loading-3d" role="status" aria-live="polite">
      <span>{label}</span>
      {progress && progress.total > 0 && (
        <span className="muted">{progress.phase} · {progress.done}/{progress.total}</span>
      )}
    </div>
  );
}
