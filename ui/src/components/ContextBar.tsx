import { useStore } from "../state/store";
import { PlaceableCatalog } from "./PlaceableCatalog";
import { defaultWallAssembly } from "../model/geometry";

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
  const roomMode = useStore((s) => s.roomMode);
  const setRoomMode = useStore((s) => s.setRoomMode);
  const roomOccupancy = useStore((s) => s.roomOccupancy);
  const setRoomOccupancy = useStore((s) => s.setRoomOccupancy);
  const activeStorey = useStore((s) => s.activeStorey);
  const placementType = useStore((s) => s.placementType);
  const placementRepeat = useStore((s) => s.placementRepeat);
  const setPlacementRepeat = useStore((s) => s.setPlacementRepeat);
  const placementCatalogOpen = useStore((s) => s.placementCatalogOpen);
  const setPlacementCatalogOpen = useStore((s) => s.setPlacementCatalogOpen);

  if (tool === "select") return null;

  const assemblies = model?.catalog?.assemblies ?? [];
  const armedType = model?.catalog?.canvas_object_types?.find((type) => type.tag === placementType);
  const defaultAssembly = drawAssembly
    ?? (defaultWallAssembly(model?.walls ?? [], activeStorey, assemblies[0]?.tag) || null);

  // Shared by the wall tool and the room tool's rectangle mode (both draw walls).
  const assemblySelect = (
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
  );
  const occupancies = model?.catalog?.occupancies ?? [];

  return (<>
    <div className="contextbar" role="toolbar" aria-label={`${tool} options`}>
      <span className="ctx-tool-name">{TOOL_TITLES[tool]}</span>
      <span className="ctx-sep" />

      {tool === "wall" && (
        <>
          {assemblySelect}
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
        <>
          <button className="btn ctx-placeable-type" aria-expanded={placementCatalogOpen}
            onClick={() => setPlacementCatalogOpen(!placementCatalogOpen)}>
            {armedType ? `${armedType.name} · ${armedType.tag}` : "Choose component…"}
          </button>
          <label className="ctx-field ctx-check">
            <input type="checkbox" checked={placementRepeat} onChange={(e) => setPlacementRepeat(e.target.checked)} />
            <span>Repeat</span>
          </label>
          <span className="ctx-static">
            {armedType ? "Tap to place · R rotates · Esc done" : "Pick a type, then tap the plan"}
          </span>
        </>
      )}

      {tool === "room" && (
        <>
          <div className="seg-group" role="group" aria-label="Room mode">
            {(["rect", "claim"] as const).map((mode) => (
              <button key={mode} className={`seg-btn${roomMode === mode ? " active" : ""}`}
                aria-pressed={roomMode === mode} onClick={() => setRoomMode(mode)}>
                {mode === "rect" ? "Draw rectangle" : "Claim"}
              </button>
            ))}
          </div>
          {roomMode === "rect" ? (
            <>
              <label className="ctx-field">
                <span>Occupancy</span>
                <select value={roomOccupancy} onChange={(e) => setRoomOccupancy(e.target.value)}>
                  {!occupancies.includes(roomOccupancy) && <option value={roomOccupancy}>{roomOccupancy}</option>}
                  {occupancies.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </label>
              {assemblySelect}
              <span className="ctx-static">Tap two opposite corners · Esc cancels</span>
            </>
          ) : (
            <span className="ctx-static">Tap inside an enclosed wall loop to claim a room</span>
          )}
        </>
      )}

      {tool === "dimension" && (
        <span className="ctx-static">Select a wall, then type a length to drive it</span>
      )}

      {offline && (
        <span className="ctx-static ctx-warn">Editing needs `haus serve`</span>
      )}
    </div>
    {/* A sibling, not a child: the bar scrolls horizontally, which would clip a dropdown. */}
    {tool === "placeable" && placementCatalogOpen && <PlaceableCatalog />}
  </>);
}

const TOOL_TITLES: Record<string, string> = {
  wall: "Draw Wall",
  opening: "Place Opening",
  placeable: "Place Component",
  room: "Room",
  dimension: "Dimension",
};
