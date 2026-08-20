import { useEffect, useMemo, useRef, useState } from "react";
import { useStore } from "../state/store";
import { ALL_TRADES } from "../state/vocabulary";
import { ALL_LAYER_VISIBILITY_GROUPS, LAYER_VISIBILITY_GROUP_LABEL } from "../model/visibility";

// Command palette (Phase 4): fuzzy-searchable actions + recent commands. The registry is
// built here from live store actions so commands always stay wired to real behaviour.
interface Command {
  id: string;
  title: string;
  group: string;
  shortcut?: string;
  disabled?: boolean;
  run: () => void;
}

// Tiny subsequence fuzzy matcher — returns a score (lower = tighter) or null for no match.
function fuzzyScore(query: string, text: string): number | null {
  if (!query) return 0;
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  let ti = 0;
  let score = 0;
  let lastHit = -1;
  for (const ch of q) {
    const found = t.indexOf(ch, ti);
    if (found === -1) return null;
    if (lastHit >= 0) score += found - lastHit; // reward adjacency
    lastHit = found;
    ti = found + 1;
  }
  return score + (t.startsWith(q) ? -5 : 0);
}

export function CommandPalette() {
  const open = useStore((s) => s.commandPaletteOpen);
  const setOpen = useStore((s) => s.setCommandPaletteOpen);
  const recent = useStore((s) => s.recentCommands);
  const pushRecent = useStore((s) => s.pushRecentCommand);

  const undo = useStore((s) => s.undo);
  const redo = useStore((s) => s.redo);
  const setTool = useStore((s) => s.setTool);
  const setViewMode = useStore((s) => s.setViewMode);
  const setThreeMode = useStore((s) => s.setThreeMode);
  const threeMode = useStore((s) => s.threeMode);
  const setTradeVisible = useStore((s) => s.setTradeVisible);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const setActivePanel = useStore((s) => s.setActivePanel);
  const setRepresentation = useStore((s) => s.setRepresentation);
  const setActiveWorkspace = useStore((s) => s.setActiveWorkspace);
  const setActiveLens = useStore((s) => s.setActiveLens);
  const setLayerGroupVisible = useStore((s) => s.setLayerGroupVisible);
  const visibleLayerGroups = useStore((s) => s.visibleLayerGroups);
  const showEverything = useStore((s) => s.showEverything);
  const setDetailView = useStore((s) => s.setDetailView);
  const reload = useStore((s) => s.reload);
  const offline = useStore((s) => s.offline);

  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands = useMemo<Command[]>(() => {
    const list: Command[] = [
      { id: "undo", title: "Undo", group: "Edit", shortcut: "⌘Z", run: () => void undo() },
      { id: "redo", title: "Redo", group: "Edit", shortcut: "⇧⌘Z", run: () => void redo() },
      { id: "tool-select", title: "Tool: Select", group: "Tools", run: () => setTool("select") },
      { id: "tool-wall", title: "Tool: Draw Wall", group: "Tools", disabled: offline, run: () => setTool("wall") },
      { id: "tool-opening", title: "Tool: Place Opening", group: "Tools", disabled: offline, run: () => setTool("opening") },
      { id: "tool-room", title: "Tool: Claim Room", group: "Tools", disabled: offline, run: () => setTool("room") },
      { id: "tool-dimension", title: "Tool: Dimension", group: "Tools", disabled: offline, run: () => setTool("dimension") },
      { id: "view-2d", title: "View: 2D plan", group: "View", run: () => setViewMode("2d") },
      { id: "view-split", title: "View: Split 2D / 3D", group: "View", run: () => setViewMode("split") },
      { id: "view-3d", title: "View: 3D", group: "View", run: () => setViewMode("3d") },
      { id: "three-nordic", title: "3D: Nordic shading", group: "View", run: () => setThreeMode("nordic") },
      { id: "three-schematic", title: "3D: Schematic shading", group: "View", run: () => setThreeMode("schematic") },
      { id: "drawer-project", title: "Open Project drawer", group: "Panels", run: () => setActivePanel("project") },
      { id: "panel-views", title: "Open Views panel", group: "Panels", run: () => setActivePanel("views") },
      { id: "ws-design", title: "Workspace: Design", group: "Workspace", run: () => setActiveWorkspace("design") },
      { id: "ws-analyze", title: "Workspace: Analyze", group: "Workspace", run: () => setActiveWorkspace("analyze") },
      { id: "ws-document", title: "Workspace: Document", group: "Workspace", run: () => setActiveWorkspace("document") },
      { id: "rep-conceptual", title: "Detail: Conceptual", group: "View", run: () => setRepresentation("conceptual") },
      { id: "rep-schematic", title: "Detail: Schematic", group: "View", run: () => setRepresentation("schematic") },
      { id: "rep-detailed", title: "Detail: Detailed", group: "View", run: () => setRepresentation("detailed") },
      { id: "rep-fabrication", title: "Detail: Fabrication", group: "View", run: () => setRepresentation("fabrication") },
      { id: "lens-none", title: "Lens: Normal", group: "Lens", run: () => setActiveLens("none") },
      { id: "lens-air", title: "Lens: Air", group: "Lens", run: () => setActiveLens("air") },
      { id: "lens-water", title: "Lens: Water", group: "Lens", run: () => setActiveLens("water") },
      { id: "lens-thermal", title: "Lens: Thermal", group: "Lens", run: () => setActiveLens("thermal") },
      { id: "lens-vapor", title: "Lens: Vapour (permeance)", group: "Lens", run: () => setActiveLens("vapor") },
      { id: "run-checks", title: "Run checks (reload model)", group: "Model", run: () => void reload() },
      { id: "reader-assembly", title: "Assembly details (transitions)", group: "Model", run: () => setDetailView("assembly") },
      { id: "reader-bom", title: "Bill of materials", group: "Model", run: () => setDetailView("bom") },
      { id: "reader-circuits", title: "Circuits (panel schedule)", group: "Model", run: () => setDetailView("circuits") },
      { id: "reader-lighting", title: "Lighting (luminaire schedule)", group: "Model", run: () => setDetailView("lighting") },
      { id: "reader-plumbing", title: "Plumbing (riser, fixture units)", group: "Model", run: () => setDetailView("plumbing") },
      { id: "reader-data", title: "Data (low-voltage schedule)", group: "Model", run: () => setDetailView("data") },
      { id: "reader-estimate", title: "Estimate (priced rows, bid ladder)", group: "Model", run: () => setDetailView("estimate") },
      { id: "show-everything", title: "Show everything (clear visibility filters)", group: "Isolate", run: showEverything },
    ];
    for (const trade of ALL_TRADES) {
      list.push({
        id: `trade-${trade}`,
        title: `Toggle ${trade} visibility`,
        group: "Isolate",
        run: () => setTradeVisible(trade, !visibleTrades[trade]),
      });
    }
    for (const group of ALL_LAYER_VISIBILITY_GROUPS) {
      list.push({
        id: `layer-${group}`,
        title: `Toggle ${LAYER_VISIBILITY_GROUP_LABEL[group].toLowerCase()} layers`,
        group: "Isolate",
        run: () => setLayerGroupVisible(group, !visibleLayerGroups[group]),
      });
    }
    // Keep an unused reference so a shading toggle reads intent; threeMode drives the label.
    void threeMode;
    return list;
  }, [undo, redo, setTool, setViewMode, setThreeMode, threeMode, setTradeVisible, visibleTrades,
    setActivePanel, setRepresentation, setActiveWorkspace, setActiveLens,
    setLayerGroupVisible, visibleLayerGroups, showEverything, setDetailView, reload, offline]);

  const results = useMemo(() => {
    if (!query) {
      const recentCmds = recent
        .map((id) => commands.find((c) => c.id === id))
        .filter((c): c is Command => !!c);
      const rest = commands.filter((c) => !recent.includes(c.id));
      return [...recentCmds, ...rest];
    }
    return commands
      .map((c) => ({ c, s: fuzzyScore(query, `${c.group} ${c.title}`) }))
      .filter((x): x is { c: Command; s: number } => x.s !== null)
      .sort((a, b) => a.s - b.s)
      .map((x) => x.c);
  }, [query, commands, recent]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      // Focus after the modal paints.
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => setActive(0), [query]);

  if (!open) return null;

  const runCommand = (c: Command | undefined) => {
    if (!c || c.disabled) return;
    pushRecent(c.id);
    setOpen(false);
    c.run();
  };

  return (
    <div className="cmdk-backdrop" onClick={() => setOpen(false)}>
      <div className="cmdk" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Command palette">
        <input
          ref={inputRef}
          className="cmdk-input"
          placeholder="Type a command…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActive((a) => Math.min(results.length - 1, a + 1));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setActive((a) => Math.max(0, a - 1));
            } else if (e.key === "Enter") {
              e.preventDefault();
              runCommand(results[active]);
            } else if (e.key === "Escape") {
              e.preventDefault();
              setOpen(false);
            }
          }}
        />
        <div className="cmdk-list">
          {results.length === 0 && <div className="cmdk-empty muted">No matching commands</div>}
          {!query && recent.length > 0 && <div className="cmdk-section">Recent</div>}
          {results.map((c, i) => (
            <button
              key={c.id}
              className={`cmdk-item${i === active ? " active" : ""}${c.disabled ? " disabled" : ""}`}
              onMouseEnter={() => setActive(i)}
              onClick={() => runCommand(c)}
              disabled={c.disabled}
            >
              <span className="cmdk-group">{c.group}</span>
              <span className="cmdk-title">{c.title}</span>
              {c.shortcut && <span className="cmdk-shortcut">{c.shortcut}</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
