import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import { PANELS } from "../../state/panels";
import { visibleFindings } from "../../state/locate";
import { ToolRailSection } from "./ToolRailSection";

/**
 * The permanent left navigation rail.
 *
 * Views is the most-used control in the app; this gives it a labelled destination at full
 * target size that is always visible and never moves.
 *
 * Destinations and tools share one rail rather than occupying two competing left gutters,
 * which also retires the `:has(.views-panel) .toolrail` hack: panels open to the right of a
 * rail whose width is a token, so nothing has to react to a drawer being open.
 */
export function NavigationRail() {
  const activePanel = useStore((s) => s.activePanel);
  const setActivePanel = useStore((s) => s.setActivePanel);
  const model = useStore((s) => s.model);

  const findings = model ? visibleFindings(model.findings) : [];
  const errorCount = findings.filter((f) => f.severity === "error").length;
  const warnCount = findings.filter((f) => f.severity === "warn").length;

  return (
    <nav className="nav-rail" aria-label="Panels and tools">
      {PANELS.map((panel) => {
        const selected = activePanel === panel.id;
        // Issues carries a count badge: an issue list nobody opens is the same as no checks.
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

      <div className="rail-divider" role="separator" />

      <ToolRailSection />
    </nav>
  );
}
