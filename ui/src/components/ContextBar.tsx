import { useStore } from "../state/store";

// Contextual tool bar (Phase 2): floats just under the top bar and renders the active
// tool's parameters. Disappears when Select is active (nothing to configure). Option lists
// come from model.catalog so they always match the house's authoring palette.
export function ContextBar() {
  const tool = useStore((s) => s.tool);
  const model = useStore((s) => s.model);
  const offline = useStore((s) => s.offline);
  const drawAssembly = useStore((s) => s.drawAssembly);
  const setDrawAssembly = useStore((s) => s.setDrawAssembly);
  const chainDraw = useStore((s) => s.chainDraw);
  const setChainDraw = useStore((s) => s.setChainDraw);
  const activeStorey = useStore((s) => s.activeStorey);

  if (tool === "select") return null;

  const assemblies = model?.catalog?.assemblies ?? [];
  const defaultAssembly =
    drawAssembly ?? assemblies[0]?.tag ?? null;

  return (
    <div className="contextbar" role="toolbar" aria-label={`${tool} options`}>
      <span className="ctx-tool-name">{TOOL_TITLES[tool]}</span>
      <span className="ctx-sep" />

      {tool === "wall" && (
        <>
          <label className="ctx-field">
            <span>Assembly</span>
            <select
              value={defaultAssembly ?? ""}
              onChange={(e) => setDrawAssembly(e.target.value || null)}
            >
              {assemblies.length === 0 && <option value="">— none —</option>}
              {assemblies.map((a) => (
                <option key={a.tag} value={a.tag}>
                  {a.tag}
                </option>
              ))}
            </select>
          </label>
          <label className="ctx-field ctx-check">
            <input
              type="checkbox"
              checked={chainDraw}
              onChange={(e) => setChainDraw(e.target.checked)}
            />
            <span>Chain</span>
          </label>
          <span className="ctx-static">Level {activeStorey ?? "—"}</span>
        </>
      )}

      {tool === "opening" && (
        <span className="ctx-static">
          Tap a wall to place — pick window / door type in the popover
        </span>
      )}

      {tool === "placeable" && (
        <span className="ctx-static">Tap the plan to place a component</span>
      )}

      {tool === "room" && (
        <span className="ctx-static">Tap inside an enclosed wall loop to claim a room</span>
      )}

      {tool === "dimension" && (
        <span className="ctx-static">Select a wall, then type a length to drive it</span>
      )}

      {offline && (
        <span className="ctx-static ctx-warn">Editing needs `haus serve`</span>
      )}
    </div>
  );
}

const TOOL_TITLES: Record<string, string> = {
  wall: "Draw Wall",
  opening: "Place Opening",
  placeable: "Place Component",
  room: "Claim Room",
  dimension: "Dimension",
};
