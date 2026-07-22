import { useState } from "react";
import { useStore } from "../state/store";
import type { Model, Wall } from "../model/types";
import { BuildingScienceDashboard } from "./BuildingScienceDashboard";
import { SpaceDashboard } from "./SpaceDashboard";
import { RoofDesigner } from "./RoofDesigner";
import { DetailViewer } from "./DetailViewer";
import { DetailsNavigator } from "./DetailsNavigator";

// Left project drawer (Phase 3 relocation; Phase 6 grows the object hierarchy + Views).
// Houses the always-on dashboards evicted from the strict inspector. Opens as one of the
// two large side panels; toggled from the top bar.
export function ProjectDrawer() {
  const model = useStore((s) => s.model);
  const open = useStore((s) => s.projectDrawerOpen);
  const setOpen = useStore((s) => s.setProjectDrawerOpen);
  const setWorkbench = useStore((s) => s.setWorkbench);
  const [showDetails, setShowDetails] = useState(false);

  if (!open || !model) return null;

  return (
    <aside className="project-drawer">
      <div className="drawer-header">
        <h3 style={{ margin: 0 }}>Project</h3>
        <button className="btn" onClick={() => setOpen(false)} title="Close project drawer">
          ✕
        </button>
      </div>
      <Hierarchy model={model} />
      <div style={{ marginTop: 12 }}>
        <button className="btn" onClick={() => setShowDetails(true)}>Transition details…</button>
      </div>
      <AssemblyPicker model={model} onEdit={() => setWorkbench("assembly")} />
      <div style={{ marginTop: 8 }}>
        <button className="btn" onClick={() => setWorkbench("stair")}>Stair workbench…</button>
      </div>
      <BuildingScienceDashboard science={model.building_science} />
      <SpaceDashboard summary={model.space_summary} buildingHeight={model.building_height_summary} />
      <RoofDesigner model={model} />
      <DetailsNavigator />
      {showDetails && <DetailViewer onClose={() => setShowDetails(false)} />}
    </aside>
  );
}

// Object hierarchy (Phase 6): an indexed view over the model graph. Selecting a level sets
// the active storey; the counts orient the user without cramming the strict inspector.
function Hierarchy({ model }: { model: Model }) {
  const activeStorey = useStore((s) => s.activeStorey);
  const setActiveStorey = useStore((s) => s.setActiveStorey);
  const counts: [string, number][] = [
    ["Walls", model.walls.length],
    ["Openings", model.openings.length],
    ["Rooms", model.rooms.length],
    ["Stairs", (model.stairs ?? []).length],
    ["Roofs", (model.roofs ?? []).length],
    ["Components", (model.canvas_objects ?? []).length],
  ];
  return (
    <div>
      <h3>{model.project.name}</h3>
      <div className="hierarchy-levels">
        {model.storeys.map((s) => (
          <button
            key={s.tag}
            className={`hierarchy-level${activeStorey === s.tag ? " active" : ""}`}
            onClick={() => setActiveStorey(s.tag)}
          >
            {s.tag}
          </button>
        ))}
      </div>
      <div className="kv" style={{ marginTop: 8 }}>
        {counts.map(([label, n]) => (
          <span key={label} style={{ display: "contents" }}>
            <span className="k">{label}</span>
            <span className="num">{n}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function AssemblyPicker({ model, onEdit }: { model: Model; onEdit: () => void }) {
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  const byAssembly = new Map<string, Wall[]>();
  for (const w of model.walls) {
    const key = w.assembly || "UNCONFIGURED";
    (byAssembly.get(key) ?? byAssembly.set(key, []).get(key)!).push(w);
  }
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Assemblies</h3>
        <button className="btn" onClick={onEdit}>Edit</button>
      </div>
      {[...byAssembly.entries()].map(([name, walls]) => (
        <div
          key={name}
          className="finding info"
          onClick={() => select("wall", walls[0].uid)}
          style={{
            outline:
              selection.kind === "wall" && walls.some((w) => w.uid === selection.uid)
                ? "2px solid var(--accent)"
                : "none",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>{name}</span>
            <span className="muted">×{walls.length}</span>
          </div>
          <span className="muted">{walls[0].layers.length} layers</span>
        </div>
      ))}
    </div>
  );
}
