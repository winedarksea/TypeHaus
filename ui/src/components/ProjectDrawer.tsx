import { Fragment, useCallback, useMemo, useRef, useState } from "react";
import { useStore } from "../state/store";
import type { Model, Wall } from "../model/types";
import { RoofDesigner } from "./RoofDesigner";
import { DetailsNavigator } from "./DetailsNavigator";
import { Icon } from "../icons/Icon";
import { useIsCompact } from "../hooks/useBreakpoint";
import { useLightDismiss } from "../hooks/useLightDismiss";
import { AddFloorForm } from "./AddFloorForm";
import { ProjectHouseSection } from "./ProjectHouseSection";

// Left project drawer: the house, its storeys, its contents, then the always-on dashboards
// evicted from the strict inspector. Each part is a collapsible DrawerSection so the drawer
// reads as one consistent, scannable outline.
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
        <h3 style={{ margin: 0 }}>Project</h3>
        <button className="btn icon-btn" onClick={() => setActivePanel(null)} title="Close project drawer">
          <Icon name="close" />
        </button>
      </div>

      <DrawerSection title="House" defaultOpen>
        <ProjectHouseSection model={model} />
      </DrawerSection>

      <DrawerSection title="Storeys" defaultOpen>
        <Storeys model={model} />
      </DrawerSection>

      <DrawerSection title="Contents">
        <Contents model={model} />
      </DrawerSection>

      <DrawerSection
        title="Assemblies"
        defaultOpen
        right={<button className="btn" onClick={() => setWorkbench("assembly")}>Edit</button>}
      >
        <AssemblyPicker model={model} />
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

// Collapsible section. The head is a row: the toggle button, then any action as its
// sibling, so no button is ever nested inside another.
function DrawerSection({ title, defaultOpen = false, right, children }: {
  title: string;
  defaultOpen?: boolean;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="drawer-section">
      <div className="drawer-section-head">
        <button className="drawer-section-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
          <Icon name={open ? "chevron-down" : "chevron-right"} size={16} className="chev" />
          <span className="drawer-section-title">{title}</span>
        </button>
        {right && <span className="drawer-section-right">{right}</span>}
      </div>
      {open && <div className="drawer-section-body">{children}</div>}
    </section>
  );
}

// The full building -> storey tree. The level tabs over the canvas offer datums (see
// model/levels.ts); this is an index of the graph, so it shows every structure and level.
// Picking a sub-storey focuses the datum it stands on and files new work there.
function Storeys({ model }: { model: Model }) {
  const activeStorey = useStore((s) => s.activeStorey);
  const setActiveStorey = useStore((s) => s.setActiveStorey);
  const canAddFloor = useStore((s) => s.project?.capabilities.includes("add_storey") ?? false);
  const [addingFloor, setAddingFloor] = useState(false);
  // Buildings in the order the project declares them. An older model.json names no
  // building, and then there is one implicit group.
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
  const addPill = canAddFloor && !addingFloor && (
    <button className="hierarchy-level add" onClick={() => setAddingFloor(true)}>+ Add floor</button>
  );
  return (
    <div>
      {buildingGroups.map(([building, storeys], i) => (
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
            {i === buildingGroups.length - 1 && addPill}
          </div>
        </div>
      ))}
      {buildingGroups.length === 0 && addPill}
      {addingFloor && <AddFloorForm model={model} onDone={() => setAddingFloor(false)} />}
    </div>
  );
}

function Contents({ model }: { model: Model }) {
  const counts: [string, number][] = [
    ["Walls", model.walls.length],
    ["Openings", model.openings.length],
    ["Rooms", model.rooms.length],
    ["Stairs", (model.stairs ?? []).length],
    ["Roofs", (model.roofs ?? []).length],
    ["Components", (model.canvas_objects ?? []).length],
  ];
  return (
    <div className="kv">
      {counts.map(([label, n]) => (
        <Fragment key={label}>
          <span className="k">{label}</span>
          <span className="num">{n}</span>
        </Fragment>
      ))}
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
