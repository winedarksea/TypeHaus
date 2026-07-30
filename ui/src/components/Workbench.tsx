import { useStore } from "../state/store";
import { AssemblyEditor } from "./AssemblyEditor";
import { StairDesigner } from "./StairDesigner";
import { Icon } from "../icons/Icon";

// Workbench (Phase 7): complex edits temporarily take over the UI in focus mode — the canvas
// dims behind a breadcrumb back, instead of cramming the strict inspector or firing modals.
// The assembly + stair editors are hosted here; window/door detail stays in its popover.
export function Workbench() {
  const workbench = useStore((s) => s.workbench);
  const setWorkbench = useStore((s) => s.setWorkbench);
  const model = useStore((s) => s.model);
  const close = () => setWorkbench(null);

  if (!workbench) return null;

  const title = workbench === "assembly" ? "Wall-assembly workbench" : "Stair workbench";

  return (
    <div className="workbench-backdrop">
      <div className="workbench">
        <div className="workbench-bread">
          <button className="btn" onClick={close} title="Back to canvas"><Icon name="arrow-left" size={18} /> Back</button>
          <span className="workbench-title">{title}</span>
        </div>
        <div className="workbench-body">
          {workbench === "assembly" && <AssemblyEditor onClose={close} embedded />}
          {workbench === "stair" && model && <StairDesigner model={model} />}
        </div>
      </div>
    </div>
  );
}
