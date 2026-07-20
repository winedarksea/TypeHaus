import { useEffect, useState } from "react";
import { useStore } from "./state/store";
import { subscribePwa, promptInstall, type PwaState } from "./pwa/register";
import { fsAccessSupported } from "./engine/openHouse";
import { Toolbar } from "./components/Toolbar";
import { Canvas2D } from "./components/Canvas2D";
import { Panel3D } from "./components/Panel3D";
import { Sidebar } from "./components/Sidebar";
import { ConflictBanner } from "./components/ConflictBanner";
import { ExtentsHUD } from "./components/ExtentsHUD";
import { Toasts } from "./components/Toasts";
import { useTheme, type ThemePreference } from "./theme/theme";

export function App() {
  const { preference: themePreference, setPreference: setThemePreference } = useTheme();
  const init = useStore((s) => s.init);
  const connected = useStore((s) => s.connected);
  const viewMode = useStore((s) => s.viewMode);
  const setViewMode = useStore((s) => s.setViewMode);
  const model = useStore((s) => s.model);
  const loading = useStore((s) => s.loading);
  const error = useStore((s) => s.error);
  const undo = useStore((s) => s.undo);
  const redo = useStore((s) => s.redo);
  const offline = useStore((s) => s.offline);
  const offlineHouse = useStore((s) => s.offlineHouse);
  const openOfflineHouse = useStore((s) => s.openOfflineHouse);

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
        {offline && (
          <span className="badge-offline" title={`offline — ${offlineHouse ?? "in-browser engine"}`}>
            OFFLINE{offlineHouse ? ` · ${offlineHouse}` : ""}
          </span>
        )}
        <div className="spacer" />
        {pwa.installable && (
          <button className="btn" onClick={() => void promptInstall()} title="Install Type:Haus">
            Install
          </button>
        )}
        {(["2d", "split", "3d"] as const).map((m) => (
          <button
            key={m}
            className={`seg-btn${viewMode === m ? " active" : ""}`}
            onClick={() => setViewMode(m)}
          >
            {m.toUpperCase()}
          </button>
        ))}
        <div className="theme-selector" role="group" aria-label="Appearance">
          {(["system", "light", "dark"] as ThemePreference[]).map((choice) => (
            <button
              key={choice}
              className={`seg-btn${themePreference === choice ? " active" : ""}`}
              onClick={() => setThemePreference(choice)}
              title={`Use ${choice === "system" ? "system appearance" : `${choice} appearance`}`}
              aria-pressed={themePreference === choice}
            >
              {choice === "system" ? "System" : choice[0].toUpperCase() + choice.slice(1)}
            </button>
          ))}
        </div>
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
