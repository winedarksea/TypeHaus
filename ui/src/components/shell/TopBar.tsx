import { useStore } from "../../state/store";
import { useIsCompact } from "../../hooks/useBreakpoint";
import { Icon } from "../../icons/Icon";
import { Menu } from "../ui/Menu";
import { OverflowMenu } from "./OverflowMenu";
import { REPORTS, VIEW_MODES } from "./navigationConfig";
import type { PwaState } from "../../pwa/register";
import type { ViewMode } from "../../state/vocabulary";

/**
 * The top app bar: identity and location on the left, global actions on the right.
 *
 * Two rules keep it from silting up — the bar carries only what is used constantly (view
 * mode, undo/redo, search), and everything else goes behind a named trigger.
 */
export function TopBar({ pwa }: { pwa: PwaState }) {
  const model = useStore((s) => s.model);
  const offline = useStore((s) => s.offline);
  const offlineHouse = useStore((s) => s.offlineHouse);
  const activePanel = useStore((s) => s.activePanel);
  const setActivePanel = useStore((s) => s.setActivePanel);
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen);
  const detailView = useStore((s) => s.detailView);
  const setDetailView = useStore((s) => s.setDetailView);
  const viewMode = useStore((s) => s.viewMode);
  const setViewMode = useStore((s) => s.setViewMode);
  const isCompact = useIsCompact();
  const undo = useStore((s) => s.undo);
  const redo = useStore((s) => s.redo);

  const activeReport = REPORTS.find((r) => r.id === detailView);

  return (
    <header className="topbar">
      <button
        className={`btn icon-btn${activePanel === "project" ? " active" : ""}`}
        onClick={() => setActivePanel("project")}
        title="Toggle project drawer"
        aria-pressed={activePanel === "project"}
      >
        <Icon name="menu" />
      </button>

      {/* On a phone the wordmark yields to the breadcrumb: which storey you are on is
          navigational, the app's own name is not. */}
      {!isCompact && <span className="title">Type:Haus</span>}

      {/* Project name only. The active storey is already stated three other places — the
          storey switcher on the canvas, the Views panel's Level control, and the status
          rail's view readout — and a breadcrumb that cannot be navigated is just a label. */}
      <nav className="breadcrumb" aria-label="Project">
        <span className="crumb-current">{model?.project.name ?? "—"}</span>
      </nav>

      {offline && (
        <span className="badge-offline" title={`offline — ${offlineHouse ?? "in-browser engine"}`}>
          OFFLINE{offlineHouse ? ` · ${offlineHouse}` : ""}
        </span>
      )}

      <div className="spacer" />

      {/* One trigger for the six full-screen readers. Reflects the open one so the bar still
          says where you are. Folds into the overflow on a phone, where there is only room for
          the constant actions. */}
      {!isCompact && <Menu
        label={activeReport ? activeReport.label : "Reports"}
        title="Reports — assembly, BOM, circuits, HVAC, plumbing, lighting"
        icon="report"
        triggerClassName={`btn reports-trigger${activeReport ? " active" : ""}`}
        align="end"
        items={REPORTS.map((report) => ({
          id: report.id,
          label: report.label,
          icon: report.icon,
          hint: report.hint,
          selected: detailView === report.id,
          onSelect: () => setDetailView(detailView === report.id ? "none" : report.id),
        }))}
      />}

      <div className="seg-group" role="group" aria-label="View mode">
        {VIEW_MODES.filter((mode) => !(isCompact && mode.id === "split")).map((mode) => (
          <button
            key={mode.id}
            className={`seg-btn${viewMode === mode.id ? " active" : ""}`}
            onClick={() => setViewMode(mode.id as ViewMode)}
            aria-pressed={viewMode === mode.id}
            title={mode.hint}
          >
            <Icon name={mode.icon} size={18} />
            {!isCompact && <span className="seg-btn-label">{mode.label}</span>}
          </button>
        ))}
      </div>

      {!isCompact && (
        <>
          <button className="btn icon-btn" onClick={() => void undo()} title="Undo (⌘Z)">
            <Icon name="undo" />
          </button>
          <button className="btn icon-btn" onClick={() => void redo()} title="Redo (⇧⌘Z)">
            <Icon name="redo" />
          </button>
          <button
            className="btn icon-btn"
            onClick={() => setCommandPaletteOpen(true)}
            title="Command palette (⌘K)"
          >
            <Icon name="search" />
          </button>
        </>
      )}

      <OverflowMenu pwa={pwa} compact={isCompact} />
    </header>
  );
}
