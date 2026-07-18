import { useEffect } from "react";
import { useStore } from "./state/store";
import { Toolbar } from "./components/Toolbar";
import { Canvas2D } from "./components/Canvas2D";
import { Panel3D } from "./components/Panel3D";
import { Sidebar } from "./components/Sidebar";
import { ConflictBanner } from "./components/ConflictBanner";
import { ExtentsHUD } from "./components/ExtentsHUD";
import { Toasts } from "./components/Toasts";

export function App() {
  const init = useStore((s) => s.init);
  const connected = useStore((s) => s.connected);
  const viewMode = useStore((s) => s.viewMode);
  const setViewMode = useStore((s) => s.setViewMode);
  const model = useStore((s) => s.model);
  const loading = useStore((s) => s.loading);
  const error = useStore((s) => s.error);
  const undo = useStore((s) => s.undo);
  const redo = useStore((s) => s.redo);

  useEffect(() => {
    void init();
  }, [init]);

  // Desktop accelerators (touch keeps on-screen equivalents, → 21).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) void redo();
        else void undo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo]);

  return (
    <div className="app">
      <div className="topbar">
        <span className="title">Type:Haus</span>
        <span className="muted">{model?.project.name ?? "—"}</span>
        <div className="spacer" />
        {(["2d", "split", "3d"] as const).map((m) => (
          <button
            key={m}
            className={`seg-btn${viewMode === m ? " active" : ""}`}
            onClick={() => setViewMode(m)}
          >
            {m.toUpperCase()}
          </button>
        ))}
        <button className="btn" onClick={() => void undo()}>
          ↶
        </button>
        <button className="btn" onClick={() => void redo()}>
          ↷
        </button>
        <span
          className={`status-dot${connected ? " up" : ""}`}
          title={connected ? "engine connected" : "engine disconnected"}
        />
      </div>

      <Toolbar />

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
              </div>
            ) : (
              <Canvas2D />
            )}
            <ConflictBanner />
            <ExtentsHUD />
          </div>
        )}
        {viewMode !== "2d" && (
          <div className="pane" style={{ borderRight: "none" }}>
            <Panel3D />
          </div>
        )}
      </div>

      <Sidebar />
      <Toasts />
    </div>
  );
}
