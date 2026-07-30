import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import { TOOL_GROUPS, GROUP_OF_TOOL, type ToolGroupSpec } from "./navigationConfig";

/**
 * The drawing tools, as the lower zone of the navigation rail.
 *
 * Lifted out of the old free-floating Toolbar so that tools and panel destinations share one
 * rail instead of competing for the same left gutter — which is what forced the `:has()` hack
 * that shoved the tool rail sideways whenever a drawer opened.
 */
export function ToolRailSection() {
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

  const onGroup = (group: ToolGroupSpec) => {
    if (group.tools.length === 1) setTool(group.tools[0].id);   // setTool closes the flyout
    else setToolGroup(toolGroup === group.id ? null : group.id);
  };

  return (
    <>
      {TOOL_GROUPS.map((group) => {
        // Authoring is gated offline (→ 40); only Select survives.
        const disabled = offline && group.id !== "select";
        return (
          <div key={group.id} className="tool-group">
            <button
              className={`rail-item${activeGroup === group.id ? " active" : ""}`}
              title={disabled ? "Editing needs `haus serve` — unavailable offline" : group.label}
              disabled={disabled}
              aria-haspopup={group.tools.length > 1 || undefined}
              aria-expanded={toolGroup === group.id || undefined}
              aria-pressed={activeGroup === group.id}
              onClick={() => onGroup(group)}
            >
              <span className="rail-indicator"><Icon name={group.icon} size={22} /></span>
              <span className="rail-label">{group.label}</span>
            </button>

            {toolGroup === group.id && group.tools.length > 1 && (
              <div className="tool-flyout" role="menu">
                {group.tools.map((t) => (
                  <button
                    key={t.id}
                    role="menuitem"
                    className={`flyout-item${tool === t.id ? " active" : ""}`}
                    title={t.hint}
                    onClick={() => setTool(t.id)}
                  >
                    <Icon name={t.icon} size={18} className="flyout-glyph" />
                    <span>{t.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}

      <div className="rail-spacer" />

      {selection.uid && !offline && canDuplicate && (
        <button
          className="rail-item"
          title="Duplicate selected opening or placeable (⌘/Ctrl+D)"
          onClick={() => void duplicateSelection()}
        >
          <span className="rail-indicator"><Icon name="duplicate" size={22} /></span>
          <span className="rail-label">Copy</span>
        </button>
      )}
      {selection.uid && !offline && (
        <button className="rail-item" title="Delete selected (Del)" onClick={() => void deleteSelection()}>
          <span className="rail-indicator"><Icon name="delete" size={22} /></span>
          <span className="rail-label">Delete</span>
        </button>
      )}
      <button
        className={`rail-item${showFraming ? " active" : ""}`}
        title="Toggle framed floorplan / schematic"
        aria-pressed={showFraming}
        onClick={() => setShowFraming(!showFraming)}
      >
        <span className="rail-indicator"><Icon name="framing" size={22} /></span>
        <span className="rail-label">Framing</span>
      </button>
    </>
  );
}
