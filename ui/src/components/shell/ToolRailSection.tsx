import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import { Menu } from "../ui/Menu";
import { TOOL_GROUPS, GROUP_OF_TOOL, type ToolGroupSpec } from "./navigationConfig";

/**
 * The drawing tools, as the lower zone of the navigation rail.
 *
 * Multi-tool groups open through the shared Menu rather than a bespoke `.tool-flyout`.
 * That is not only de-duplication: the old flyout was absolutely positioned at
 * `left: calc(100% + 8px)`, i.e. outside the rail — and the rail scrolls, so it clipped
 * on both axes and the palette rendered at full size with zero pixels visible. Menu
 * positions in viewport coordinates and cannot be clipped by an ancestor.
 */
export function ToolRailSection() {
  const tool = useStore((s) => s.tool);
  const setTool = useStore((s) => s.setTool);
  const offline = useStore((s) => s.offline);
  const selection = useStore((s) => s.selection);
  const deleteSelection = useStore((s) => s.deleteSelection);
  const duplicateSelection = useStore((s) => s.duplicateSelection);
  const canDuplicate = selection.kind === "opening" || selection.kind === "canvas_object";

  const activeGroup = GROUP_OF_TOOL[tool];

  const renderGroup = (group: ToolGroupSpec) => {
    // Authoring is gated offline (→ 40); only Select survives.
    const disabled = offline && group.id !== "select";
    const active = activeGroup === group.id;
    const hint = disabled ? "Editing needs `haus serve` — unavailable offline" : group.label;

    if (group.tools.length === 1) {
      return (
        <button
          key={group.id}
          className={`rail-item${active ? " active" : ""}`}
          title={hint}
          disabled={disabled}
          aria-pressed={active}
          onClick={() => setTool(group.tools[0].id)}
        >
          <span className="rail-indicator"><Icon name={group.icon} size={22} /></span>
          <span className="rail-label">{group.label}</span>
        </button>
      );
    }

    return (
      <Menu
        key={group.id}
        label={group.label}
        title={hint}
        placement="side"
        triggerClassName={`rail-item rail-menu-trigger${active ? " active" : ""}`}
        triggerContent={
          <>
            <span className="rail-indicator"><Icon name={group.icon} size={22} /></span>
            <span className="rail-label">{group.label}</span>
          </>
        }
        items={group.tools.map((t) => ({
          id: t.id,
          label: t.label,
          icon: t.icon,
          hint: t.hint,
          selected: tool === t.id,
          disabled,
          onSelect: () => setTool(t.id),
        }))}
      />
    );
  };

  return (
    <>
      {TOOL_GROUPS.map(renderGroup)}

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
    </>
  );
}
