import { useCallback, useRef, useState, type CSSProperties } from "react";
import { useStore } from "../state/store";
import { activeLevelKey, levelsOf } from "../model/levels";
import { DEFAULT_EARTH_OPACITY, type LabelMode, type Representation, type ViewMode, type ThreeMode, type ViewTransform, type Workspace } from "../state/vocabulary";
import { migrateSavedVisibility, type VisibleTrades } from "../model/tradeVisibility";
import { DisciplinesGrid } from "./views/DisciplinesGrid";
import { Icon } from "../icons/Icon";
import { useIsCompact } from "../hooks/useBreakpoint";
import { useLightDismiss } from "../hooks/useLightDismiss";

// Views (Phase 6): untangles workspace / visibility / representation, and adds saved view
// recipes. Consolidates the loose 3D trade toggles + nordic/schematic switch (relocated out
// of Panel3D) into one shared control usable by both 2D and 3D. The discipline grid and the
// role presets live in views/DisciplinesGrid.tsx.

const REPRESENTATIONS: Representation[] = ["conceptual", "schematic", "detailed", "fabrication"];

const WORKSPACES: Workspace[] = ["design", "analyze", "document"];
const WORKSPACE_HINT: Record<Workspace, string> = {
  design: "Authoring tools; detail markers hidden.",
  analyze: "Same canvas, emphasis on checks and dashboards.",
  document: "Adds D-tag detail markers at documented junctions.",
};

const LABEL_MODE_HINT: Record<LabelMode, string> = {
  all: "Every room and object names itself.",
  hover: "A label appears only under the pointer; selected elements always show theirs.",
  off: "No name text on the plan.",
};

interface SavedView {
  name: string;
  activeStorey: string | null;
  viewMode: ViewMode;
  threeMode: ThreeMode;
  representation: Representation;
  // Keyed by trade. A recipe saved under the older 13-name vocabulary, or carrying the
  // retired per-layer groups, is folded onto the current trades by migrateSavedVisibility.
  visibleTrades: Record<string, boolean>;
  // Both optional: recipes saved before the label control existed carry the boolean, and older
  // ones carry neither — see applyView for how they map onto labelMode.
  showSpaceLabels?: boolean;
  labelMode?: LabelMode;
  // Retired (2026-09-12): kept on the type so an old recipe still reads, folded into
  // visibleTrades on apply.
  visibleLayerGroups?: Record<string, boolean>;
  // Optional for the same reason again: a recipe saved before the ground slider existed
  // restores the translucent default it was captured at.
  earthOpacity?: number;
  workspace?: Workspace;
  view: ViewTransform;
}
const SAVED_VIEWS_KEY = "typehaus.saved-views";

function loadViews(): SavedView[] {
  try {
    return JSON.parse(window.localStorage.getItem(SAVED_VIEWS_KEY) ?? "[]");
  } catch {
    return [];
  }
}
function persistViews(views: SavedView[]): void {
  try {
    window.localStorage.setItem(SAVED_VIEWS_KEY, JSON.stringify(views));
  } catch {
    /* private browsing */
  }
}

export function ViewsPanel() {
  const open = useStore((s) => s.activePanel === "views");
  const setActivePanel = useStore((s) => s.setActivePanel);
  const model = useStore((s) => s.model);

  const activeStorey = useStore((s) => s.activeStorey);
  const setActiveStorey = useStore((s) => s.setActiveStorey);
  const representation = useStore((s) => s.representation);
  const setRepresentation = useStore((s) => s.setRepresentation);
  const threeMode = useStore((s) => s.threeMode);
  const setThreeMode = useStore((s) => s.setThreeMode);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const labelMode = useStore((s) => s.labelMode);
  const setLabelMode = useStore((s) => s.setLabelMode);
  const earthOpacity = useStore((s) => s.earthOpacity);
  const setEarthOpacity = useStore((s) => s.setEarthOpacity);
  const workspace = useStore((s) => s.activeWorkspace);
  const setWorkspace = useStore((s) => s.setActiveWorkspace);
  const viewMode = useStore((s) => s.viewMode);

  const [views, setViews] = useState<SavedView[]>(loadViews);
  const [newName, setNewName] = useState("");

  // Light dismiss, desktop only: at compact the panel is wrapped in a Sheet, which already
  // scrims and dismisses. Hooks run before the early return below, as they must.
  const panelRef = useRef<HTMLElement>(null);
  const isCompact = useIsCompact();
  const dismiss = useCallback(() => setActivePanel(null), [setActivePanel]);
  useLightDismiss(panelRef, open && !isCompact, dismiss);

  if (!open || !model) return null;

  const saveCurrent = () => {
    const name = newName.trim() || `View ${views.length + 1}`;
    const s = useStore.getState();
    const recipe: SavedView = {
      name,
      activeStorey: s.activeStorey,
      viewMode: s.viewMode,
      threeMode: s.threeMode,
      representation: s.representation,
      visibleTrades: { ...s.visibleTrades },
      earthOpacity: s.earthOpacity,
      labelMode: s.labelMode,
      workspace: s.activeWorkspace,
      view: { ...s.view },
    };
    const next = [...views.filter((v) => v.name !== name), recipe];
    setViews(next);
    persistViews(next);
    setNewName("");
  };

  const applyView = (v: SavedView) => {
    const s = useStore.getState();
    s.setActiveStorey(v.activeStorey);
    s.setViewMode(v.viewMode);
    s.setThreeMode(v.threeMode);
    s.setRepresentation(v.representation);
    const migrated: VisibleTrades = migrateSavedVisibility(v.visibleTrades, v.visibleLayerGroups);
    s.showOnlyTrades(Object.entries(migrated).flatMap(([trade, on]) => (on ? [trade] : [])) as
      Parameters<typeof s.showOnlyTrades>[0]);
    s.setEarthOpacity(v.earthOpacity ?? DEFAULT_EARTH_OPACITY);
    // Backward compat: a pre-labelMode recipe only knew "space labels on/off".
    s.setLabelMode(v.labelMode ?? (v.showSpaceLabels === false ? "off" : "all"));
    s.setActiveWorkspace(v.workspace ?? "design");
    s.setView(v.view);
  };

  const deleteView = (name: string) => {
    const next = views.filter((v) => v.name !== name);
    setViews(next);
    persistViews(next);
  };

  return (
    <aside className="views-panel" ref={panelRef}>
      <div className="drawer-header">
        <h3 style={{ margin: 0 }}>Views</h3>
        <button className="btn icon-btn" onClick={() => setActivePanel(null)} title="Close views"><Icon name="close" /></button>
      </div>

      <DisciplinesGrid viewMode={viewMode} />

      <h3>Level</h3>
      {/* Levels, not storeys: fourteen storeys stand on five datums here (→ model/levels.ts). */}
      <select value={activeLevelKey(model, activeStorey) ?? ""}
        onChange={(e) => setActiveStorey(e.target.value || null)} style={{ width: "100%" }}>
        {levelsOf(model).map((l) => (
          <option key={l.key} value={l.key}>{l.key}</option>
        ))}
      </select>

      {/* Relocated from the topbar (Phase 11): the workspace only re-emphasizes panels, which
          is a view-recipe concern, not a top-level mode; the assembly and BOM readers open
          separately. */}
      <h3>Workspace</h3>
      <div className="seg-row">
        {WORKSPACES.map((w) => (
          <button key={w} className={`seg-btn${workspace === w ? " active" : ""}`}
            onClick={() => setWorkspace(w)} title={WORKSPACE_HINT[w]}>
            {w[0].toUpperCase() + w.slice(1)}
          </button>
        ))}
      </div>
      <div className="muted views-hint">{WORKSPACE_HINT[workspace]}</div>

      <h3>Representation</h3>
      <div className="seg-row">
        {REPRESENTATIONS.map((r) => (
          <button key={r} className={`seg-btn${representation === r ? " active" : ""}`} onClick={() => setRepresentation(r)}>
            {r[0].toUpperCase() + r.slice(1)}
          </button>
        ))}
      </div>

      <h3>3D shading</h3>
      <div className="seg-row">
        {(["nordic", "schematic"] as ThreeMode[]).map((m) => (
          <button key={m} className={`seg-btn${threeMode === m ? " active" : ""}`} onClick={() => setThreeMode(m)}>
            {m}
          </button>
        ))}
      </div>

      {/* Ground opacity is a companion to the Site checkbox above, not a replacement for it:
          the checkbox answers "is there ground at all", this answers "how much of the basement
          does it let through". The default is the translucent reference the sheet has always
          been drawn at; 100% is real dirt, which is the only way to read the above-grade model
          without the below-grade storey showing through it. */}
      <h3>Ground</h3>
      <div className={`slider-row${visibleTrades.earth ? "" : " disabled"}`}
        style={{ "--slider-fill": `${Math.round(earthOpacity * 100)}%` } as CSSProperties}>
        <label className="slider-label" htmlFor="earth-opacity">Opacity</label>
        <input
          id="earth-opacity"
          type="range"
          min={0}
          max={100}
          step={1}
          value={Math.round(earthOpacity * 100)}
          disabled={!visibleTrades.earth}
          onChange={(e) => setEarthOpacity(Number(e.target.value) / 100)}
          aria-label="Ground opacity"
        />
        <output className="slider-value" htmlFor="earth-opacity">
          {Math.round(earthOpacity * 100)}%
        </output>
      </div>
      <div className="muted views-hint">
        {visibleTrades.earth
          ? "Site sheet only, in 3D. At 100% the earth is solid and hides everything below grade."
          : "Site is hidden — turn it on under Disciplines to use this."}
      </div>

      <h3>Labels</h3>
      <div className="seg-row">
        {(["all", "hover", "off"] as LabelMode[]).map((m) => (
          <button key={m} className={`seg-btn${labelMode === m ? " active" : ""}`}
            onClick={() => setLabelMode(m)} title={LABEL_MODE_HINT[m]}>
            {m[0].toUpperCase() + m.slice(1)}
          </button>
        ))}
      </div>
      <div className="muted views-hint">{LABEL_MODE_HINT[labelMode]}</div>

      <h3>Saved views</h3>
      <div style={{ display: "flex", gap: 6 }}>
        <input
          value={newName}
          placeholder="Name this view…"
          onChange={(e) => setNewName(e.target.value)}
          style={{ flex: 1, padding: "5px 7px" }}
        />
        <button className="btn" onClick={saveCurrent}>Save</button>
      </div>
      {views.length === 0 ? (
        <div className="muted" style={{ marginTop: 6 }}>No saved views yet.</div>
      ) : (
        <div style={{ marginTop: 6 }}>
          {views.map((v) => (
            <div key={v.name} className="saved-view-row">
              <button className="saved-view-apply" onClick={() => applyView(v)}>{v.name}</button>
              <button className="saved-view-del" onClick={() => deleteView(v.name)} title="Delete"><Icon name="close" size={16} /></button>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
