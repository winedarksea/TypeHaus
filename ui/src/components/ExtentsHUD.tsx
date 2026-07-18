import { useStore } from "../state/store";
import { formatFtIn, interiorExtents, structuralExtents } from "../model/geometry";

// Extents & dimensions HUD (WP2.4, → 21b feature 1): overall structural envelope vs.
// open interior space. Every number derives from model.json — the UI never re-measures.
export function ExtentsHUD() {
  const model = useStore((s) => s.model);
  if (!model) return null;
  const struct = structuralExtents(model);
  const interior = interiorExtents(model);
  if (!struct) return null;

  return (
    <div className="hud">
      <div className="row">
        <span className="k">Structural</span>
        <span>
          {formatFtIn(struct.width_m)} × {formatFtIn(struct.depth_m)}
        </span>
      </div>
      {interior && (
        <div className="row">
          <span className="k">Open space</span>
          <span>
            {formatFtIn(interior.width_m)} × {formatFtIn(interior.depth_m)}
          </span>
        </div>
      )}
      <div className="row">
        <span className="k">Storeys</span>
        <span>{model.storeys.length}</span>
      </div>
    </div>
  );
}
