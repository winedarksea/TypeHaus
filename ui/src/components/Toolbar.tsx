import { type Tool, type ToolGroup, useStore } from "../state/store";

// Task rail (Phase 2): high-level groups. A group with a single tool activates it directly;
// a multi-tool group opens a small flyout palette. Tools map onto the existing Tool union so
// every entry is functional against the current engine + Canvas2D handlers.
interface GroupSpec {
  id: ToolGroup;
  glyph: string;
  label: string;
  tools: { id: Tool; glyph: string; label: string; hint: string }[];
}

const GROUPS: GroupSpec[] = [
  { id: "select", glyph: "⌖", label: "Select", tools: [
    { id: "select", glyph: "⌖", label: "Select", hint: "Select and move elements" },
  ] },
  { id: "build", glyph: "▟", label: "Build", tools: [
    { id: "wall", glyph: "▟", label: "Wall", hint: "Draw wall (tap → tap; Shift = ortho)" },
    { id: "room", glyph: "▣", label: "Room", hint: "Claim a room" },
    { id: "stair", glyph: "▤", label: "Stair", hint: "Add a stair (tap on a floor)" },
  ] },
  { id: "openings", glyph: "❒", label: "Openings", tools: [
    { id: "opening", glyph: "❒", label: "Window / Door", hint: "Place a window or door on a wall" },
  ] },
  { id: "components", glyph: "▦", label: "Components", tools: [
    { id: "placeable", glyph: "▦", label: "Place", hint: "Place furniture, fixtures, and devices" },
  ] },
  { id: "measure", glyph: "↔", label: "Measure", tools: [
    { id: "dimension", glyph: "↔", label: "Dimension", hint: "Drive a wall's length" },
  ] },
];

// Which group owns the currently-active tool (drives the active highlight on the rail).
const GROUP_OF_TOOL: Record<Tool, ToolGroup> = {
  select: "select",
  wall: "build",
  room: "build",
  stair: "build",
  opening: "openings",
  placeable: "components",
  dimension: "measure",
};

export function Toolbar() {
  const tool = useStore((s) => s.tool);
  const setTool = useStore((s) => s.setTool);
  const toolGroup = useStore((s) => s.toolGroup);
  const setToolGroup = useStore((s) => s.setToolGroup);
  const showFraming = useStore((s) => s.showFraming);
  const setShowFraming = useStore((s) => s.setShowFraming);
  const offline = useStore((s) => s.offline);
  const selection = useStore((s) => s.selection);
  const deleteSelection = useStore((s) => s.deleteSelection);
  const duplicateSelection = useStore((s) => s.duplicateSelection);
  const canDuplicate = selection.kind === "opening" || selection.kind === "canvas_object";

  const activeGroup = GROUP_OF_TOOL[tool];

  const onGroup = (g: GroupSpec) => {
    if (g.tools.length === 1) {
      setTool(g.tools[0].id); // single tool → activate immediately (setTool closes the flyout)
    } else {
      setToolGroup(toolGroup === g.id ? null : g.id); // toggle the flyout palette
    }
  };

  return (
    <div className="toolrail">
      {GROUPS.map((g) => {
        // Authoring is gated offline (→ 40); only Select survives.
        const disabled = offline && g.id !== "select";
        return (
          <div key={g.id} className="tool-group">
            <button
              className={`tool-btn${activeGroup === g.id ? " active" : ""}`}
              title={disabled ? "Editing needs `haus serve` — unavailable offline" : g.label}
              disabled={disabled}
              aria-haspopup={g.tools.length > 1 || undefined}
              aria-expanded={toolGroup === g.id || undefined}
              onClick={() => onGroup(g)}
            >
              {g.glyph}
            </button>
            {toolGroup === g.id && g.tools.length > 1 && (
              <div className="tool-flyout" role="menu">
                {g.tools.map((t) => (
                  <button
                    key={t.id}
                    role="menuitem"
                    className={`flyout-item${tool === t.id ? " active" : ""}`}
                    title={t.hint}
                    onClick={() => setTool(t.id)}
                  >
                    <span className="flyout-glyph">{t.glyph}</span>
                    <span>{t.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
      <div style={{ flex: 1 }} />
      {selection.uid && !offline && canDuplicate && (
        <button className="tool-btn" title="Duplicate selected opening or placeable (⌘/Ctrl+D)"
          onClick={() => void duplicateSelection()}>
          ⧉
        </button>
      )}
      {selection.uid && !offline && (
        <button className="tool-btn" title="Delete selected (Del)" onClick={() => void deleteSelection()}>
          🗑
        </button>
      )}
      <button
        className={`tool-btn${showFraming ? " active" : ""}`}
        title="Toggle framed floorplan / schematic"
        onClick={() => setShowFraming(!showFraming)}
      >
        {showFraming ? "▤" : "▢"}
      </button>
    </div>
  );
}
