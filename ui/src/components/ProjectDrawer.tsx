import { Fragment, useState } from "react";
import { useStore } from "../state/store";
import type { Model, Wall } from "../model/types";
import { BuildingScienceDashboard } from "./BuildingScienceDashboard";
import { SpaceDashboard } from "./SpaceDashboard";
import { RoofDesigner } from "./RoofDesigner";
import { DetailsNavigator } from "./DetailsNavigator";

// Left project drawer (Phase 3 relocation; Phase 6 grows the object hierarchy + Views).
// Houses the always-on dashboards evicted from the strict inspector. Opens as one of the
// two large side panels; toggled from the top bar. The body is organized into collapsible
// DrawerSections so the drawer reads as a single, consistent, scannable outline.
export function ProjectDrawer() {
  const model = useStore((s) => s.model);
  const open = useStore((s) => s.activePanel === "project");
  const setActivePanel = useStore((s) => s.setActivePanel);
  const setWorkbench = useStore((s) => s.setWorkbench);

  if (!open || !model) return null;

  return (
    <aside className="project-drawer">
      <div className="drawer-header">
        <h3 style={{ margin: 0 }}>{model.project.name}</h3>
        <button className="btn" onClick={() => setActivePanel(null)} title="Close project drawer">
          ✕
        </button>
      </div>

      <DrawerSection title="Project" defaultOpen>
        <Hierarchy model={model} />
      </DrawerSection>

      <DrawerSection
        title="Assemblies"
        defaultOpen
        right={<button className="btn" onClick={() => setWorkbench("assembly")}>Edit</button>}
      >
        <AssemblyPicker model={model} />
      </DrawerSection>

      <DrawerSection title="Building science">
        <BuildingScienceDashboard science={model.building_science} />
      </DrawerSection>

      <DrawerSection title="Space">
        <SpaceDashboard summary={model.space_summary} buildingHeight={model.building_height_summary} />
      </DrawerSection>

      <DrawerSection title="Roof">
        <RoofDesigner model={model} />
      </DrawerSection>

      <DrawerSection title="Details">
        <DetailsNavigator />
      </DrawerSection>
    </aside>
  );
}

// Lightweight collapsible section: owns its own open/closed state and renders a header button
// (with a chevron and an optional inline action) over a body. Replaces the ad-hoc per-child
// <h3> + magic-number margins the drawer used to stack.
function DrawerSection({ title, defaultOpen = false, right, children }: {
  title: string;
  defaultOpen?: boolean;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="drawer-section">
      <button className="drawer-section-head" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="chev">{open ? "▾" : "▸"}</span>
        <span className="drawer-section-title">{title}</span>
        {right && (
          <span className="drawer-section-right" onClick={(e) => e.stopPropagation()}>{right}</span>
        )}
      </button>
      {open && <div className="drawer-section-body">{children}</div>}
    </section>
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
          <Fragment key={label}>
            <span className="k">{label}</span>
            <span className="num">{n}</span>
          </Fragment>
        ))}
      </div>
    </div>
  );
}

function AssemblyPicker({ model }: { model: Model }) {
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  const byAssembly = new Map<string, Wall[]>();
  for (const w of model.walls) {
    const key = w.assembly || "UNCONFIGURED";
    (byAssembly.get(key) ?? byAssembly.set(key, []).get(key)!).push(w);
  }
  return (
    <div>
      {[...byAssembly.entries()].map(([name, walls]) => {
        const selected = selection.kind === "wall" && walls.some((w) => w.uid === selection.uid);
        return (
          <div
            key={name}
            className={`finding info${selected ? " selected" : ""}`}
            onClick={() => select("wall", walls[0].uid)}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>{name}</span>
              <span className="muted">×{walls.length}</span>
            </div>
            <span className="muted">{walls[0].layers.length} layers</span>
          </div>
        );
      })}
    </div>
  );
}
