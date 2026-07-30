import { useStore } from "../../state/store";
import { visibleFindings } from "../../state/locate";
import { ALL_TRADES } from "../../state/vocabulary";
import { ALL_LAYER_VISIBILITY_GROUPS } from "../../model/visibility";
import { LENSES } from "../LensBar";
import { Menu } from "../ui/Menu";

/**
 * The bottom status rail: a quiet, tabular readout of the view you are looking at.
 *
 * It absorbs the old floating ViewChips bar. Those five chips all called the same
 * setViewsPanelOpen — a five-segment button that did one thing — and their content (level,
 * disciplines, representation) is *status*, not control. The app already had a designated
 * status surface showing storey and lens, so the readout belongs here and the top-centre of
 * the drawing, where a floor plan's subject usually sits, goes back to the drawing.
 */
export function StatusRail() {
  const model = useStore((s) => s.model);
  const activeStorey = useStore((s) => s.activeStorey);
  const representation = useStore((s) => s.representation);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const visibleLayerGroups = useStore((s) => s.visibleLayerGroups);
  const activeLens = useStore((s) => s.activeLens);
  const setActiveLens = useStore((s) => s.setActiveLens);
  const activePanel = useStore((s) => s.activePanel);
  const setActivePanel = useStore((s) => s.setActivePanel);

  const findings = model ? visibleFindings(model.findings) : [];
  const errCount = findings.filter((f) => f.severity === "error").length;
  const warnCount = findings.filter((f) => f.severity === "warn").length;
  const adviseCount = findings.filter((f) => f.severity === "info").length;

  const shownTrades = ALL_TRADES.filter((t) => visibleTrades[t]).length;
  const hiddenLayers = ALL_LAYER_VISIBILITY_GROUPS.filter((g) => !visibleLayerGroups[g]).length;
  const activeLensSpec = LENSES.find((l) => l.id === activeLens) ?? LENSES[0];

  return (
    <div className="statusrail">
      {/* The whole recipe summary is one control that opens Views — same destination the
          rail offers, reachable from wherever the eye already is. */}
      <button
        className={`status-view-readout${activePanel === "views" ? " active" : ""}`}
        onClick={() => setActivePanel("views")}
        title="Open Views — level, disciplines, representation"
      >
        <span>{activeStorey ?? "—"}</span>
        <span className="sep">·</span>
        <span>
          {shownTrades === ALL_TRADES.length ? "All disciplines" : `${shownTrades} disciplines`}
        </span>
        {hiddenLayers > 0 && (
          <>
            <span className="sep">·</span>
            <span>{hiddenLayers} layer{hiddenLayers === 1 ? "" : "s"} hidden</span>
          </>
        )}
        <span className="sep">·</span>
        <span>{representation[0].toUpperCase() + representation.slice(1)}</span>
      </button>

      <span className="sep">·</span>
      <span>Snap ✓</span>
      <span className="sep">·</span>

      <Menu
        label={`Lens: ${activeLensSpec.label}`}
        title="Building-science lens"
        align="start"
        showLabel
        triggerClassName={`status-lens-trigger${activeLens !== "none" ? " active" : ""}`}
        items={LENSES.map((lens) => ({
          id: lens.id,
          label: lens.label,
          hint: lens.legend,
          selected: activeLens === lens.id,
          onSelect: () => setActiveLens(lens.id),
        }))}
      />

      <span className="spacer" />

      <button
        className="health-pill"
        onClick={() => setActivePanel("issues")}
        title="Design health — errors · warnings · advisories (open Issues)"
      >
        <span className="hp-err">{errCount} err</span>
        <span className="hp-warn">{warnCount} warn</span>
        <span>{adviseCount} adv</span>
      </button>
      <span className="sep">·</span>
      <span>{model?.units ?? "ft-in"}</span>
    </div>
  );
}
