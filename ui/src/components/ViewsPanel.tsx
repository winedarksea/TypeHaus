import { useState, type CSSProperties } from "react";
import { useStore } from "../state/store";
import { ALL_TRADES, DEFAULT_EARTH_OPACITY, type LabelMode, type Representation, type Trade, type ViewMode, type ThreeMode, type ViewTransform, type Workspace } from "../state/vocabulary";
import {
  ALL_LAYER_VISIBILITY_GROUPS,
  LAYER_VISIBILITY_GROUP_LABEL,
  TRADE_SURFACES,
  type LayerVisibilityGroup,
} from "../model/visibility";
import { Icon } from "../icons/Icon";

// Views (Phase 6): untangles workspace / visibility / representation, and adds saved view
// recipes. Consolidates the loose 3D trade toggles + nordic/schematic switch (relocated out
// of Panel3D) into one shared control usable by both 2D and 3D.
const TRADE_LABEL: Record<Trade, string> = {
  walls: "Walls", openings: "Openings", framing: "Framing", floors: "Floors",
  concrete: "Concrete", roof: "Roof", stairs: "Stairs", furniture: "Furniture",
  plumbing: "Plumbing", electrical: "Electrical", mechanical: "Mechanical", earth: "Site",
  drainage: "Drainage",
};

const REPRESENTATIONS: Representation[] = ["conceptual", "schematic", "detailed", "fabrication"];

// Role presets: the trades each discipline reviews. Selecting one shows exactly those
// trades (and hides the rest) so, e.g., Structure can read stair continuity with the floor
// decks dropped. `roleMatches` lights the active preset when the visible set equals it.
const ROLE_TRADES: Record<string, Trade[]> = {
  Architecture: ["walls", "openings", "floors", "roof", "stairs", "furniture"],
  Structure: ["framing", "concrete", "roof", "stairs"],
  // Drainage sits in both: it is a service run an MEP reviewer sizes, and the half of it that
  // matters on site — the tile ring, the trenches, where the leaders discharge — is read
  // against the grade sheet.
  MEP: ["plumbing", "electrical", "mechanical", "drainage"],
  Site: ["earth", "concrete", "drainage"],
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
  visibleTrades: Record<Trade, boolean>;
  // Both optional: recipes saved before the label control existed carry the boolean, and older
  // ones carry neither — see applyView for how they map onto labelMode.
  showSpaceLabels?: boolean;
  labelMode?: LabelMode;
  // Optional for the same reason: recipes saved before per-layer visibility existed simply
  // restore every layer group on, which is what they were captured with.
  visibleLayerGroups?: Record<LayerVisibilityGroup, boolean>;
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
  const setTradeVisible = useStore((s) => s.setTradeVisible);
  const labelMode = useStore((s) => s.labelMode);
  const setLabelMode = useStore((s) => s.setLabelMode);
  const visibleLayerGroups = useStore((s) => s.visibleLayerGroups);
  const setLayerGroupVisible = useStore((s) => s.setLayerGroupVisible);
  const showEverything = useStore((s) => s.showEverything);
  const earthOpacity = useStore((s) => s.earthOpacity);
  const setEarthOpacity = useStore((s) => s.setEarthOpacity);
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
    for (const trade of ALL_TRADES) s.setTradeVisible(trade, v.visibleTrades[trade] ?? true);
    for (const group of ALL_LAYER_VISIBILITY_GROUPS) {
      s.setLayerGroupVisible(group, v.visibleLayerGroups?.[group] ?? true);
    }
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
    <aside className="views-panel">
      <div className="drawer-header">
        <h3 style={{ margin: 0 }}>Views</h3>
        <button className="btn icon-btn" onClick={() => setActivePanel(null)} title="Close views"><Icon name="close" /></button>
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
