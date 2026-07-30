import { useEffect, useState } from "react";
import { useStore } from "./state/store";
import { visibleFindings } from "./state/locate";
import { subscribePwa, type PwaState } from "./pwa/register";
import { fsAccessSupported } from "./engine/openHouse";
import { Toolbar } from "./components/Toolbar";
import { TopBar } from "./components/shell/TopBar";
import { ContextBar } from "./components/ContextBar";
import { CommandPalette } from "./components/CommandPalette";
import { IssuesDrawer } from "./components/IssuesDrawer";
import { ViewsPanel, ViewChips } from "./components/ViewsPanel";
import { Workbench } from "./components/Workbench";
import { AssemblyDetailsView } from "./components/AssemblyDetailsView";
import { BomView } from "./components/BomView";
import { CircuitsView } from "./components/CircuitsView";
import { HvacView } from "./components/HvacView";
import { PlumbingView } from "./components/PlumbingView";
import { LightingView } from "./components/LightingView";
import { LensBar } from "./components/LensBar";
import { Preview3D } from "./components/Preview3D";
import { Canvas2D } from "./components/Canvas2D";
import { Panel3D } from "./components/Panel3D";
import { Inspector } from "./components/Inspector";
import { ProjectDrawer } from "./components/ProjectDrawer";
import { ConflictBanner } from "./components/ConflictBanner";
import { ExtentsHUD } from "./components/ExtentsHUD";
import { Toasts } from "./components/Toasts";

// Interaction-state label shown near the top-left canvas corner (Phase 2).
function interactionLabel(tool: string, subOperation: boolean): string {
  switch (tool) {
    case "wall":
      return subOperation ? "DRAW WALL — chaining" : "DRAW WALL";
    case "opening":
      return "PLACE OPENING";
    case "placeable":
      return "PLACE COMPONENT";
    case "room":
      return "CLAIM ROOM";
    case "dimension":
      return "MEASURE";
    default:
      return "SELECT";
  }
}

export function App() {
  const init = useStore((s) => s.init);
  const viewMode = useStore((s) => s.viewMode);
  const model = useStore((s) => s.model);
  const loading = useStore((s) => s.loading);
  const error = useStore((s) => s.error);
  const undo = useStore((s) => s.undo);
  const redo = useStore((s) => s.redo);
  const openOfflineHouse = useStore((s) => s.openOfflineHouse);
  const activeStorey = useStore((s) => s.activeStorey);
  const tool = useStore((s) => s.tool);
  const setTool = useStore((s) => s.setTool);
  const subOperation = useStore((s) => s.subOperation);
  const setSubOperation = useStore((s) => s.setSubOperation);
  const selection = useStore((s) => s.selection);
  const select = useStore((s) => s.select);
  const setActivePanel = useStore((s) => s.setActivePanel);
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen);
  const detailView = useStore((s) => s.detailView);
  const setDetailView = useStore((s) => s.setDetailView);
  const activeLens = useStore((s) => s.activeLens);

  const [pwa, setPwa] = useState<PwaState>({
    online: true,
    installable: false,
    installed: false,
  });
  useEffect(() => subscribePwa(setPwa), []);

  useEffect(() => {
    void init();
  }, [init]);

  // Desktop accelerators (touch keeps on-screen equivalents, → 21).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const typing =
        target && (target.tagName === "INPUT" || target.tagName === "SELECT" || target.tagName === "TEXTAREA");
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen(!useStore.getState().commandPaletteOpen);
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) void redo();
        else void undo();
      } else if (e.key === "Escape" && !typing) {
        // Predictable Esc hierarchy (Phase 2): close reader → cancel sub-op → exit tool →
        // clear selection. Canvas2D independently clears its in-flight draft; here we advance
        // the outer state.
        if (useStore.getState().detailView !== "none") {
          setDetailView("none");
        } else if (subOperation) {
          setSubOperation(false);
        } else if (tool !== "select") {
          setTool("select");
        } else if (selection.uid) {
          select(null, null);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo, subOperation, tool, selection.uid, setSubOperation, setTool, select,
    setCommandPaletteOpen, setDetailView]);

  const findings = model ? visibleFindings(model.findings) : [];
  const errCount = findings.filter((f) => f.severity === "error").length;
  const warnCount = findings.filter((f) => f.severity === "warn").length;
  const adviseCount = findings.filter((f) => f.severity === "info").length;

  return (
    <div className="app">
      <div className="canvas-layer">
        <div className={`stage${viewMode === "split" ? " split" : ""}`}>
          {viewMode !== "3d" && (
            <div className="pane">
              {loading && !model ? (
                <div style={{ padding: 24 }} className="muted">
                  Loading model…
                </div>
              ) : error && !model ? (
                <div style={{ padding: 24, color: "var(--error)" }}>
                  Cannot reach engine: {error}
                  <br />
                  <span className="muted">Run `haus serve` in the house directory.</span>
                  {fsAccessSupported() && (
                    <div style={{ marginTop: 16 }}>
                      <button className="btn" onClick={() => void openOfflineHouse()}>
                        Open house folder (offline)
                      </button>
                      <div className="muted" style={{ marginTop: 6, fontSize: 12 }}>
                        Runs the engine in your browser — view, checks, and 3D. Editing needs
                        `haus serve`.
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <Canvas2D />
              )}
              <ConflictBanner />
              <ExtentsHUD />
            </div>
          )}
          {viewMode !== "2d" && (
            <div className="pane">
              <Panel3D />
            </div>
          )}
        </div>
      </div>

      <TopBar pwa={pwa} />

      <Toolbar />
      <ContextBar />
      <div className="interaction-state" aria-live="polite">
        {interactionLabel(tool, subOperation)}
      </div>
      <ViewChips />
      <LensBar />
      <Preview3D />
      <ViewsPanel />
      <ProjectDrawer />
      <Inspector />

      <div className="statusrail">
        <span>{activeStorey ?? "—"}</span>
        <span className="sep">·</span>
        <span>Snap ✓</span>
        <span className="sep">·</span>
        <span>Lens: {activeLens === "none" ? "Normal" : activeLens[0].toUpperCase() + activeLens.slice(1)}</span>
        <span className="spacer" />
        <button
          className="health-pill"
          onClick={() => setActivePanel("issues")}
          title="Design health — errors · warnings · advisories (open Issues)"
        >
          <span className="hp-err">{errCount} err</span>
          <span className="hp-warn">{warnCount} warn</span>
          <span>{adviseCount} adv</span>
        </button>
        <span className="sep">·</span>
        <span>{model?.units ?? "ft-in"}</span>
      </div>

      <IssuesDrawer />
      {detailView === "assembly" && <AssemblyDetailsView />}
      {detailView === "bom" && <BomView />}
      {detailView === "circuits" && <CircuitsView />}
      {detailView === "lighting" && <LightingView />}
      {detailView === "hvac" && <HvacView />}
      {detailView === "plumbing" && <PlumbingView />}
      <Workbench />
      <CommandPalette />
      <Toasts />
    </div>
  );
}
