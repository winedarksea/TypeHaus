import { type Tool, useStore } from "../state/store";

const TOOLS: { id: Tool; label: string; title: string }[] = [
  { id: "select", label: "⌖", title: "Select (tap)" },
  { id: "wall", label: "▟", title: "Draw wall (node → node)" },
  { id: "opening", label: "❒", title: "Place opening" },
  { id: "room", label: "▣", title: "Claim room" },
  { id: "dimension", label: "↔", title: "Driven dimension" },
];

export function Toolbar() {
  const tool = useStore((s) => s.tool);
  const setTool = useStore((s) => s.setTool);
  const showFraming = useStore((s) => s.showFraming);
  const setShowFraming = useStore((s) => s.setShowFraming);

  return (
    <div className="toolrail">
      {TOOLS.map((t) => (
        <button
          key={t.id}
          className={`tool-btn${tool === t.id ? " active" : ""}`}
          title={t.title}
          onClick={() => setTool(t.id)}
        >
          {t.label}
        </button>
      ))}
      <div style={{ flex: 1 }} />
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
