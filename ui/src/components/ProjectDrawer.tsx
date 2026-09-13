import { Fragment, useCallback, useMemo, useRef, useState } from "react";
import { useStore } from "../state/store";
import type { Model, Wall } from "../model/types";
import { BuildingScienceDashboard } from "./BuildingScienceDashboard";
import { SpaceDashboard } from "./SpaceDashboard";
import { RoofDesigner } from "./RoofDesigner";
import { DetailsNavigator } from "./DetailsNavigator";
import { Icon } from "../icons/Icon";
import { useIsCompact } from "../hooks/useBreakpoint";
import { useLightDismiss } from "../hooks/useLightDismiss";

// Left project drawer (Phase 3 relocation; Phase 6 grows the object hierarchy + Views).
// Houses the always-on dashboards evicted from the strict inspector. Opens as one of the
// two large side panels; toggled from the top bar. The body is organized into collapsible
// DrawerSections so the drawer reads as a single, consistent, scannable outline.
export function ProjectDrawer() {
  const model = useStore((s) => s.model);
  const open = useStore((s) => s.activePanel === "project");
  const setActivePanel = useStore((s) => s.setActivePanel);
  const setWorkbench = useStore((s) => s.setWorkbench);

  // Same light dismiss as ViewsPanel, and desktop-only for the same reason (the compact
  // Sheet already scrims). Hooks before the early return.
  const panelRef = useRef<HTMLElement>(null);
  const isCompact = useIsCompact();
  const dismiss = useCallback(() => setActivePanel(null), [setActivePanel]);
  useLightDismiss(panelRef, open && !isCompact, dismiss);

  if (!open || !model) return null;

  return (
    <aside className="project-drawer" ref={panelRef}>
      <div className="drawer-header">
        <h3 style={{ margin: 0 }}>{model.project.name}</h3>
        <button className="btn" onClick={() => setActivePanel(null)} title="Close project drawer">
          <Icon name="close" />
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
// (with a chevron and an optional inline action) over a body.
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
        <Icon name={open ? "chevron-down" : "chevron-right"} size={16} className="chev" />
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
  // Storeys under the building that holds them, buildings in the order the project declares
  // them. An older model.json names no building, and then there is one implicit group.
  const buildingGroups = useMemo(() => {
    const order = (model.buildings ?? []).map((b) => b.tag);
    const names = new Map((model.buildings ?? []).map((b) => [b.tag, b.name]));
    const groups = new Map<string, typeof model.storeys>();
    for (const s of model.storeys) {
      const tag = s.building ?? "";
      const at = groups.get(tag);
      if (at) at.push(s);
      else groups.set(tag, [s]);
    }
    return [...groups.entries()]
      .sort((a, b) => (order.indexOf(a[0]) + 1 || 99) - (order.indexOf(b[0]) + 1 || 99))
      .map(([tag, storeys]) => [names.get(tag) ?? tag, storeys] as const);
  }, [model.buildings, model.storeys]);
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
      {/* The one place the FULL building -> storey tree belongs. The level tabs over the
          canvas offer datums (five here, not fourteen — see model/levels.ts); an object
          hierarchy is an index of the graph, so it shows every structure and every level in
          it. Picking a sub-storey focuses the datum it stands on and files new work there. */}
      {buildingGroups.map(([building, storeys]) => (
        <div key={building} className="hierarchy-building">
          {buildingGroups.length > 1 && <div className="hierarchy-building-name">{building}</div>}
          <div className="hierarchy-levels">
            {storeys.map((s) => (
              <button
                key={s.tag}
                className={`hierarchy-level${activeStorey === s.tag ? " active" : ""}`}
                onClick={() => setActiveStorey(s.tag)}
              >
                {s.tag}
              </button>
            ))}
          </div>
        </div>
      ))}
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
