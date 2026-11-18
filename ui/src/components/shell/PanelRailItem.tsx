import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import type { PanelSpec } from "../../state/panels";

interface PanelRailItemProps {
  panel: PanelSpec;
  /** Count shown on the indicator; 0 hides it. */
  badge: number;
  badgeIsError: boolean;
  /** A short live line under the label (primary tile, desktop only). */
  readout?: string | null;
}

/** One panel destination, shared by the desktop rail and the phone bottom nav. */
export function PanelRailItem({ panel, badge, badgeIsError, readout }: PanelRailItemProps) {
  const selected = useStore((s) => s.activePanel === panel.id);
  const setActivePanel = useStore((s) => s.setActivePanel);
  const viewsDiscovered = useStore((s) => s.viewsDiscovered);

  let className = "rail-item";
  if (panel.primary) className += viewsDiscovered ? " rail-primary" : " rail-primary rail-primary--beckon";
  if (selected) className += " active";

  return (
    <button
      className={className}
      aria-pressed={selected}
      title={panel.hint}
      onClick={() => setActivePanel(panel.id)}
    >
      <span className="rail-indicator">
        <Icon name={panel.icon} size={22} />
        {badge > 0 && (
          <span className={`rail-badge${badgeIsError ? " error" : " warn"}`}>
            {badge > 99 ? "99+" : badge}
          </span>
        )}
      </span>
      <span className="rail-label">{panel.label}</span>
      {readout && <span className="rail-primary-readout">{readout}</span>}
    </button>
  );
}
