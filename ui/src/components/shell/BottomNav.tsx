import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import { PANELS } from "../../state/panels";
import { visibleFindings } from "../../state/locate";
import { Menu } from "../ui/Menu";
import { TOOL_GROUPS, GROUP_OF_TOOL } from "./navigationConfig";

/**
 * The phone-class replacement for the navigation rail.
 *
 * Separate component rather than a restyled rail: different DOM, different orientation,
 * different focus order. Rendering both and hiding one would duplicate ids and leave a
 * hidden nav in the tab order.
 *
 * The tools collapse into a single menu here. A phone has room for the destinations or for
 * eight tools, not both, and this app's phone case is reading a drawing rather than drafting
 * one — so the destinations get the bar and the tools get one clearly-labelled entry.
 */
export function BottomNav() {
  const activePanel = useStore((s) => s.activePanel);
  const setActivePanel = useStore((s) => s.setActivePanel);
  const model = useStore((s) => s.model);
  const tool = useStore((s) => s.tool);
  const setTool = useStore((s) => s.setTool);
  const offline = useStore((s) => s.offline);

  const findings = model ? visibleFindings(model.findings) : [];
  const errorCount = findings.filter((f) => f.severity === "error").length;
  const warnCount = findings.filter((f) => f.severity === "warn").length;

  const activeGroup = GROUP_OF_TOOL[tool];
  const activeToolLabel = TOOL_GROUPS.find((g) => g.id === activeGroup)?.label ?? "Tools";

  return (
    <nav className="bottom-nav" aria-label="Panels and tools">
      {PANELS.map((panel) => {
        const selected = activePanel === panel.id;
        const badge = panel.id === "issues" ? errorCount || warnCount : 0;
        return (
          <button
            key={panel.id}
            className={`rail-item${selected ? " active" : ""}`}
            aria-pressed={selected}
            title={panel.hint}
            onClick={() => setActivePanel(panel.id)}
          >
            <span className="rail-indicator">
              <Icon name={panel.icon} size={22} />
              {badge > 0 && (
                <span className={`rail-badge${errorCount > 0 ? " error" : " warn"}`}>
                  {badge > 99 ? "99+" : badge}
                </span>
              )}
            </span>
            <span className="rail-label">{panel.label}</span>
          </button>
        );
      })}

      <Menu
        label={activeToolLabel}
        title="Drawing tools"
        icon={TOOL_GROUPS.find((g) => g.id === activeGroup)?.icon ?? "cursor"}
        align="end"
        showLabel={false}
        triggerClassName="rail-item bottom-nav-tools"
        sections={TOOL_GROUPS.map((group) => ({
          id: group.id,
          label: group.label,
          items: group.tools.map((t) => ({
            id: t.id,
            label: t.label,
            icon: t.icon,
            hint: t.hint,
            selected: tool === t.id,
            disabled: offline && group.id !== "select",
            onSelect: () => setTool(t.id),
          })),
        }))}
      />
    </nav>
  );
}
