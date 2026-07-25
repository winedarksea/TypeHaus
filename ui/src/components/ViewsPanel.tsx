import { useState } from "react";
import { useStore } from "../state/store";
import { ALL_TRADES, type Representation, type Trade, type ViewMode, type ThreeMode, type ViewTransform, type Workspace } from "../state/vocabulary";
import {
  ALL_LAYER_VISIBILITY_GROUPS,
  LAYER_VISIBILITY_GROUP_LABEL,
  TRADE_SURFACES,
  type LayerVisibilityGroup,
} from "../model/visibility";

// Views (Phase 6): untangles workspace / visibility / representation, and adds saved view
// recipes. Consolidates the loose 3D trade toggles + nordic/schematic switch (relocated out
// of Panel3D) into one shared control usable by both 2D and 3D.
const TRADE_LABEL: Record<Trade, string> = {
  walls: "Walls", openings: "Openings", framing: "Framing", floors: "Floors",
  concrete: "Concrete", roof: "Roof", stairs: "Stairs", furniture: "Furniture",
  plumbing: "Plumbing", electrical: "Electrical", mechanical: "Mechanical", earth: "Site",
};

const REPRESENTATIONS: Representation[] = ["conceptual", "schematic", "detailed", "fabrication"];

// Role presets: the trades each discipline reviews. Selecting one shows exactly those
// trades (and hides the rest) so, e.g., Structure can read stair continuity with the floor
// decks dropped. `roleMatches` lights the active preset when the visible set equals it.
const ROLE_TRADES: Record<string, Trade[]> = {
  Architecture: ["walls", "openings", "floors", "roof", "stairs", "furniture"],
  Structure: ["framing", "concrete", "roof", "stairs"],
  MEP: ["plumbing", "electrical", "mechanical"],
  Site: ["earth", "concrete"],
};
function roleMatches(role: keyof typeof ROLE_TRADES, visible: Record<Trade, boolean>): boolean {
  const wanted = new Set(ROLE_TRADES[role]);
  return ALL_TRADES.every((trade) => visible[trade] === wanted.has(trade));
}

const WORKSPACES: Workspace[] = ["design", "analyze", "document"];
const WORKSPACE_HINT: Record<Workspace, string> = {
  design: "Authoring tools; detail markers hidden.",
  analyze: "Same canvas, emphasis on checks and dashboards.",
  document: "Adds D-tag detail markers at documented junctions.",
};

interface SavedView {
  name: string;
  activeStorey: string | null;
  viewMode: ViewMode;
  threeMode: ThreeMode;
  representation: Representation;
  visibleTrades: Record<Trade, boolean>;
  showSpaceLabels?: boolean; // optional: older saved recipes predate the overlay toggle
  // Optional for the same reason: recipes saved before per-layer visibility existed simply
  // restore every layer group on, which is what they were captured with.
  visibleLayerGroups?: Record<LayerVisibilityGroup, boolean>;
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

// Compact filter-chip bar (Phase 6): a glanceable summary of the active view recipe that
// opens the full Views panel. Renders near the top of the canvas.
export function ViewChips() {
  const model = useStore((s) => s.model);
  const activeStorey = useStore((s) => s.activeStorey);
  const representation = useStore((s) => s.representation);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const visibleLayerGroups = useStore((s) => s.visibleLayerGroups);
  const open = useStore((s) => s.viewsPanelOpen);
  const setOpen = useStore((s) => s.setViewsPanelOpen);
  if (!model) return null;
  const shown = ALL_TRADES.filter((t) => visibleTrades[t]).length;
  const allOn = shown === ALL_TRADES.length;
  const hiddenLayers = ALL_LAYER_VISIBILITY_GROUPS.filter((g) => !visibleLayerGroups[g]);
  return (
    <div className="view-chips">
      <button className="view-chip" onClick={() => setOpen(!open)} title="Level">
        {activeStorey ?? "—"}
      </button>
      <button className="view-chip" onClick={() => setOpen(!open)} title="Disciplines shown">
        {allOn ? "All disciplines" : `${shown} disciplines`}
      </button>
      {hiddenLayers.length > 0 && (
        <button className="view-chip" onClick={() => setOpen(!open)}
          title={`Hidden assembly layers: ${hiddenLayers.map((g) => LAYER_VISIBILITY_GROUP_LABEL[g]).join(", ")}`}>
          {hiddenLayers.length} layer{hiddenLayers.length === 1 ? "" : "s"} hidden
        </button>
      )}
      <button className="view-chip" onClick={() => setOpen(!open)} title="Representation">
        {representation[0].toUpperCase() + representation.slice(1)}
      </button>
      <button className={`view-chip chip-more${open ? " active" : ""}`} onClick={() => setOpen(!open)} title="Views">
        Views ▾
      </button>
    </div>
  );
}

export function ViewsPanel() {
  const open = useStore((s) => s.viewsPanelOpen);
  const setOpen = useStore((s) => s.setViewsPanelOpen);
  const model = useStore((s) => s.model);

  const activeStorey = useStore((s) => s.activeStorey);
  const setActiveStorey = useStore((s) => s.setActiveStorey);
  const representation = useStore((s) => s.representation);
  const setRepresentation = useStore((s) => s.setRepresentation);
  const threeMode = useStore((s) => s.threeMode);
  const setThreeMode = useStore((s) => s.setThreeMode);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const setTradeVisible = useStore((s) => s.setTradeVisible);
  const showSpaceLabels = useStore((s) => s.showSpaceLabels);
  const setShowSpaceLabels = useStore((s) => s.setShowSpaceLabels);
  const visibleLayerGroups = useStore((s) => s.visibleLayerGroups);
  const setLayerGroupVisible = useStore((s) => s.setLayerGroupVisible);
  const showEverything = useStore((s) => s.showEverything);
  const workspace = useStore((s) => s.activeWorkspace);
  const setWorkspace = useStore((s) => s.setActiveWorkspace);
  const viewMode = useStore((s) => s.viewMode);

  const [views, setViews] = useState<SavedView[]>(loadViews);
  const [newName, setNewName] = useState("");

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
      visibleLayerGroups: { ...s.visibleLayerGroups },
      showSpaceLabels: s.showSpaceLabels,
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
    for (const trade of ALL_TRADES) s.setTradeVisible(trade, v.visibleTrades[trade] ?? true);
    for (const group of ALL_LAYER_VISIBILITY_GROUPS) {
      s.setLayerGroupVisible(group, v.visibleLayerGroups?.[group] ?? true);
    }
    s.setShowSpaceLabels(v.showSpaceLabels ?? true);
    s.setActiveWorkspace(v.workspace ?? "design");
    s.setView(v.view);
  };

  const deleteView = (name: string) => {
    const next = views.filter((v) => v.name !== name);
    setViews(next);
    persistViews(next);
  };

  return (
    <aside className="views-panel">
      <div className="drawer-header">
        <h3 style={{ margin: 0 }}>Views</h3>
        <button className="btn" onClick={() => setOpen(false)} title="Close views">✕</button>
      </div>

      <h3>Level</h3>
      <select value={activeStorey ?? ""} onChange={(e) => setActiveStorey(e.target.value || null)} style={{ width: "100%" }}>
        {model.storeys.map((s) => (
          <option key={s.tag} value={s.tag}>{s.tag}</option>
        ))}
      </select>

      {/* Relocated from the topbar (Phase 11): the workspace only re-emphasizes panels, which
          is a view-recipe concern, not a top-level mode. Its old buttons now open the assembly
          and BOM readers. */}
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

      <h3>Roles</h3>
      {/* Role presets isolate the trades one discipline cares about in a single tap — e.g.
          Structure drops floor decks so stair runs stay legible across levels, without
          hunting through the per-trade checkboxes below. */}
      <div className="seg-row" style={{ flexWrap: "wrap" }}>
        {(Object.keys(ROLE_TRADES) as (keyof typeof ROLE_TRADES)[]).map((role) => (
          <button
            key={role}
            className={`seg-btn${roleMatches(role, visibleTrades) ? " active" : ""}`}
            onClick={() => { for (const trade of ALL_TRADES) setTradeVisible(trade, ROLE_TRADES[role].includes(trade)); }}
            title={`Show only ${role} trades`}
          >
            {role}
          </button>
        ))}
        <button className="seg-btn" onClick={showEverything}>
          All
        </button>
      </div>

      <h3>Disciplines</h3>
      {/* Both viewers read this same set. A trade the 2D plan has no geometry for (roof
          surfaces, the site sheet, below-grade solids) is marked rather than left to look
          broken when its checkbox does nothing on the plan side. */}
      <div className="trade-grid">
        {ALL_TRADES.map((trade) => {
          const planOnly3D = !TRADE_SURFACES[trade].plan;
          return (
            <label key={trade} className={`trade-chip${visibleTrades[trade] ? " on" : ""}`}
              title={planOnly3D ? `${TRADE_LABEL[trade]} — drawn in 3D only` : TRADE_LABEL[trade]}>
              <input
                type="checkbox"
                checked={visibleTrades[trade]}
                onChange={(e) => setTradeVisible(trade, e.target.checked)}
              />
              {TRADE_LABEL[trade]}
              {planOnly3D && <span className="trade-surface" aria-label="3D only">3D</span>}
            </label>
          );
        })}
      </div>
      {viewMode === "2d" && (
        <div className="muted views-hint">Trades marked 3D have no plan geometry to hide.</div>
      )}

      <h3>Assembly layers</h3>
      {/* Per-layer visibility (→ TODO "a per-layer visibility control would settle it"): drop
          the weather skin and the cavity fill independently, in the plan and the model alike,
          so a closure band can be told apart from the insulation behind it. */}
      <div className="trade-grid">
        {ALL_LAYER_VISIBILITY_GROUPS.map((group) => (
          <label key={group} className={`trade-chip${visibleLayerGroups[group] ? " on" : ""}`}>
            <input
              type="checkbox"
              checked={visibleLayerGroups[group]}
              onChange={(e) => setLayerGroupVisible(group, e.target.checked)}
            />
            {LAYER_VISIBILITY_GROUP_LABEL[group]}
          </label>
        ))}
      </div>

      <h3>Plan overlays</h3>
      <label className={`trade-chip${showSpaceLabels ? " on" : ""}`}>
        <input
          type="checkbox"
          checked={showSpaceLabels}
          onChange={(e) => setShowSpaceLabels(e.target.checked)}
        />
        Space labels
      </label>

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
              <button className="saved-view-del" onClick={() => deleteView(v.name)} title="Delete">✕</button>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
