// The floorplan's fixed chrome: the storey tabs + service-lens/clearances HUD in the
// corner, and the tool hint card shown while a drawing tool is armed. Split from
// components/Canvas2D.tsx — pure presentation over props; the canvas keeps the state.
import type { Model } from "../../model/types";
import type { Tool } from "../../state/vocabulary";
import { StoreyTabs, ToolHint } from "./PlanChrome";

export function CanvasHud({
  model, serviceOptions, activeService, setActiveService, showClearances, setShowClearances,
  tool, draft, wallAssembly, onAssembly, onSplit,
}: {
  model: Model;
  serviceOptions: string[];
  activeService: string;
  setActiveService: (service: string) => void;
  showClearances: boolean;
  setShowClearances: (show: boolean) => void;
  tool: Tool;
  draft: boolean;
  wallAssembly: string;
  onAssembly: (assembly: string) => void;
  onSplit: (() => void) | null;
}) {
  return (
    <>
      <div className="canvas-context-controls">
        <StoreyTabs model={model} />
      <div className="hud" style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <label style={{ fontSize: 12 }}>Services <select value={activeService}
          onChange={(event) => setActiveService(event.target.value)}>
          <option value="">all</option>
          {serviceOptions.map((service) => <option key={service} value={service}>{service}</option>)}
        </select></label>
        <button className="btn" onClick={() => setShowClearances(!showClearances)}>
          {showClearances ? "Hide clearances" : "Clearances"}
        </button>
      </div>
      </div>
      {tool !== "select" && (
        <div className="hud" style={{ left: 12, right: "auto", bottom: "auto", top: "calc(44px + 84px)", maxWidth: 260 }}>
          <ToolHint tool={tool} draft={draft}
            assembly={tool === "wall" ? wallAssembly : null}
            assemblies={model.catalog?.assemblies.map((a) => a.tag) ?? []}
            onAssembly={onAssembly}
            onSplit={onSplit} />
        </div>
      )}
    </>
  );
}
