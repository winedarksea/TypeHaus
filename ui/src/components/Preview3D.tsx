import { useStore } from "../state/store";
import { Panel3D } from "./Panel3DLazy";
import { Icon } from "../icons/Icon";

// Floating synchronized 3D preview (Phase 10): a small 3D window over the 2D plan — the
// recommended everyday mode. Selection, hover, level, and visibility already sync through the
// shared store, so the reused Panel3D stays in lock-step with the plan automatically.
export function Preview3D() {
  const viewMode = useStore((s) => s.viewMode);
  const open = useStore((s) => s.preview3DOpen);
  const setOpen = useStore((s) => s.setPreview3DOpen);

  // Only meaningful as an overlay when the main stage is the 2D plan.
  if (viewMode !== "2d") return null;

  if (!open) {
    return (
      <button className="preview3d-toggle" onClick={() => setOpen(true)} title="Show 3D preview">
        3D <Icon name="chevron-right" size={14} />
      </button>
    );
  }

  return (
    <div className="preview3d">
      <div className="preview3d-head">
        <span>3D preview</span>
        <button className="btn icon-btn" onClick={() => setOpen(false)} title="Hide 3D preview"><Icon name="close" size={16} /></button>
      </div>
      <div className="preview3d-body">
        <Panel3D compact />
      </div>
    </div>
  );
}
