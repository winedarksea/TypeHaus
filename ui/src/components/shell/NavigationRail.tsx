import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import { PANELS } from "../../state/panels";
import { visibleFindings } from "../../state/locate";
import { activeLevelKey } from "../../model/levels";
import { PanelRailItem } from "./PanelRailItem";
import { ToolRailSection } from "./ToolRailSection";
import { DOCUMENT_DESTINATIONS, SITE_DESTINATION } from "./navigationConfig";

/**
 * The permanent left navigation rail.
 *
 * Views is the most-used control in the app, so it is the primary tile: tinted, above a
 * divider, with the active level as a live readout, and pulsing until first opened.
 *
 * Destinations and tools share one rail rather than occupying two competing left gutters,
 * which also retires the `:has(.views-panel) .toolrail` hack: panels open to the right of a
 * rail whose width is a token, so nothing has to react to a drawer being open.
 */
export function NavigationRail() {
  const model = useStore((s) => s.model);
  const engineReady = useStore((s) => s.engineReady);
  const detailView = useStore((s) => s.detailView);
  const setDetailView = useStore((s) => s.setDetailView);
  const openDocuments = useStore((s) => s.openDocuments);
  const documentsTab = useStore((s) => s.documentsTab);
  const activeStorey = useStore((s) => s.activeStorey);
  const documentsOpen = detailView === "documents";

  const findings = model ? visibleFindings(model.findings) : [];
  const errorCount = findings.filter((f) => f.severity === "error").length;
  const warnCount = findings.filter((f) => f.severity === "warn").length;

  return (
    <nav className="nav-rail" aria-label="Panels and tools">
      {PANELS.filter((p) => p.primary).map((panel) => (
        <PanelRailItem key={panel.id} panel={panel} badge={0} badgeIsError={false}
          readout={model ? activeLevelKey(model, activeStorey) : null} />
      ))}
      <div className="rail-divider" role="separator" />

      {/* Issues carries a count badge: an issue list nobody opens is the same as no checks. */}
      {PANELS.filter((p) => !p.primary).map((panel) => (
        <PanelRailItem key={panel.id} panel={panel}
          badge={panel.id === "issues" ? errorCount || warnCount : 0}
          badgeIsError={errorCount > 0} />
      ))}

      {/* Documents sits with the panels rather than with the tools: it is a destination
          you go to, not something you do to the drawing. One entry per tab, so a report is
          one click rather than two — see navigationConfig.DOCUMENT_DESTINATIONS. Active
          follows the open tab, and re-clicking the open one returns to the canvas. */}
      {DOCUMENT_DESTINATIONS.map((doc) => {
        const active = documentsOpen && documentsTab === doc.tab;
        return (
          <button
            key={doc.tab}
            className={`rail-item${active ? " active" : ""}`}
            aria-pressed={active}
            title={doc.hint}
            onClick={() => (active ? setDetailView("none") : openDocuments(doc.tab))}
          >
            <span className="rail-indicator">
              <Icon name={doc.icon} size={22} />
            </span>
            <span className="rail-label">{doc.label}</span>
          </button>
        );
      })}

      {/* Getting the thing built. One destination, because the board and the inspections
          are pages inside it with their own nav. */}
      <button
        className="rail-item"
        title={SITE_DESTINATION.hint}
        disabled={!engineReady}
        onClick={() => useStore.getState().setSurface("site")}
      >
        <span className="rail-indicator">
          <Icon name={SITE_DESTINATION.icon} size={22} />
        </span>
        <span className="rail-label">{SITE_DESTINATION.label}</span>
      </button>

      <div className="rail-divider" role="separator" />

      <ToolRailSection />
    </nav>
  );
}
