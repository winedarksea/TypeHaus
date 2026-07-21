import { type Tool, useStore } from "../state/store";

const TOOLS: { id: Tool; label: string; title: string }[] = [
  { id: "select", label: "⌖", title: "Select (tap)" },
  { id: "wall", label: "▟", title: "Draw wall (tap → tap; Shift = ortho)" },
  { id: "opening", label: "❒", title: "Place a window or door on a wall" },
  { id: "placeable", label: "▦", title: "Place furniture, fixtures, and devices" },
  { id: "room", label: "▣", title: "Claim a room" },
  { id: "dimension", label: "↔", title: "Drive a wall's length" },
];

export function Toolbar() {
  const tool = useStore((s) => s.tool);
  const setTool = useStore((s) => s.setTool);
  const showFraming = useStore((s) => s.showFraming);
  const setShowFraming = useStore((s) => s.setShowFraming);
  const offline = useStore((s) => s.offline);
  const selection = useStore((s) => s.selection);
  const deleteSelection = useStore((s) => s.deleteSelection);
  const duplicateSelection = useStore((s) => s.duplicateSelection);
  const canDuplicate = selection.kind === "opening" || selection.kind === "canvas_object";

  return (
    <div className="toolrail">
      {TOOLS.map((t) => {
        // Authoring is gated offline (→ 40): the in-browser engine can't run libcst
        // writeback, so drawing/placing tools stay visible but disabled with a hint.
        const disabled = offline && t.id !== "select";
        return (
          <button
            key={t.id}
            className={`tool-btn${tool === t.id ? " active" : ""}`}
            title={disabled ? "Editing needs `haus serve` — unavailable offline" : t.title}
            disabled={disabled}
            onClick={() => setTool(t.id)}
          >
            {t.label}
          </button>
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
