import { useEffect } from "react";
import { useStore } from "../state/store";
import { type Lens } from "../state/vocabulary";
import type { Model } from "../model/types";
import { formatPerms, VAPOR_CLASS_LABEL, vaporReadings, type VaporLayerReading } from "../model/vapor";

// Continuity of a tagged control layer across storey-stack / assembly-change transitions is
// checked server-side (advisory.control_continuity, → checks/advisory). The lens surfaces
// those findings plus the count of wall layers actually carrying the control layer, so the
// overlay reflects the resolved model instead of a static caption.
const CONTINUITY_CODE = "advisory.control_continuity";

export interface LensData {
  controlLayerCount: number; // wall layers carrying this control across the model
  discontinuities: { message: string; element: string | null }[];
  // Vapour lens only: the resolved permeance of each distinct vapour-control layer. A control
  // *flag* says a layer is meant to manage vapour; only the permeance says whether it can.
  vaporReadings: VaporLayerReading[];
}

// `domain` is the control keyword ("air" | "water" | "thermal" | "vapor"); substring match
// tolerates either the bare enum value or a "ControlLayer.AIR"-style serialization.
export function lensData(model: Model | null, domain: string): LensData {
  if (!model) return { controlLayerCount: 0, discontinuities: [], vaporReadings: [] };
  let controlLayerCount = 0;
  const controlLayers = [];
  for (const wall of model.walls) {
    for (const layer of wall.layers) {
      if (!(layer.control ?? []).some((c) => c.toLowerCase().includes(domain))) continue;
      controlLayerCount++;
      controlLayers.push(layer);
    }
  }
  const discontinuities = (model.findings ?? [])
    .filter((f) => f.code === CONTINUITY_CODE)
    .map((f) => ({ message: f.message, element: f.element ?? f.elements?.[0] ?? null }));
  return {
    controlLayerCount,
    discontinuities,
    vaporReadings: domain === "vapor" ? vaporReadings(controlLayers, model.catalog?.materials) : [],
  };
}

// Building-science lenses (Phase 9). A lens mutes ordinary geometry and makes one control
// layer dominant. Encoding is never color-only: each legend entry pairs color + line pattern
// + icon + label to meet the 3:1 non-text-contrast bar.
interface LensSpec {
  id: Lens;
  label: string;
  icon: string;
  colorVar: string;
  pattern: string; // dash array
  legend: string;
}

// The plan's control-layer overlay reads its stroke from the same specs the legend does, so
// the swatch in the legend and the line on the drawing can never drift apart. Encoding stays
// colour + dash (never colour alone) on the canvas for the same reason it does in the legend.
export function lensStrokeSpec(lens: Lens): { colorVar: string; pattern: string } | null {
  const spec = LENSES.find((entry) => entry.id === lens);
  return spec && spec.id !== "none" ? { colorVar: spec.colorVar, pattern: spec.pattern } : null;
}

/** Whether a resolved layer carries the control this lens is about. */
export function layerCarriesControl(control: readonly string[] | undefined, lens: Lens): boolean {
  if (lens === "none") return false;
  return (control ?? []).some((entry) => entry.toLowerCase().includes(lens));
}

const LENSES: LensSpec[] = [
  { id: "none", label: "Normal", icon: "◻", colorVar: "--ink", pattern: "0", legend: "All disciplines shown normally." },
  { id: "air", label: "Air", icon: "≋", colorVar: "--control-air", pattern: "2 3", legend: "Air-barrier continuity — discontinuities numbered." },
  { id: "water", label: "Water", icon: "☂", colorVar: "--control-water", pattern: "6 3", legend: "Water-control layer + drainage path continuity." },
  { id: "thermal", label: "Thermal", icon: "☀", colorVar: "--control-thermal", pattern: "1 4", legend: "Thermal-control layer — bridges highlighted." },
  { id: "vapor", label: "Vapour", icon: "☁", colorVar: "--control-vapor", pattern: "5 2 1 2", legend: "Vapour-control layer — permeance and retarder class per layer." },
];

export function LensBar() {
  const activeLens = useStore((s) => s.activeLens);
  const setActiveLens = useStore((s) => s.setActiveLens);
  const model = useStore((s) => s.model);
  const zoomToUid = useStore((s) => s.zoomToUid);

  // Drive a root attribute so CSS can mute base geometry while a lens is active.
  useEffect(() => {
    document.documentElement.dataset.lens = activeLens;
    return () => { document.documentElement.dataset.lens = "none"; };
  }, [activeLens]);

  const active = LENSES.find((l) => l.id === activeLens) ?? LENSES[0];
  const data = activeLens === "none" ? null : lensData(model, activeLens);

  return (
    <>
      <div className="lens-bar" role="group" aria-label="Building-science lens">
        {LENSES.map((l) => (
          <button
            key={l.id}
            className={`lens-chip${activeLens === l.id ? " active" : ""}`}
            onClick={() => setActiveLens(l.id)}
            title={l.legend}
            style={activeLens === l.id && l.id !== "none" ? { borderColor: `var(${l.colorVar})`, color: `var(${l.colorVar})` } : undefined}
          >
            <span aria-hidden>{l.icon}</span> {l.label}
          </button>
        ))}
      </div>

      {activeLens !== "none" && data && (
        <div className="lens-legend" role="note">
          <div className="lens-legend-title">
            <span aria-hidden>{active.icon}</span> {active.label} lens
          </div>
          <div className="lens-legend-row">
            <svg width="34" height="10" aria-hidden>
              <line x1="0" y1="5" x2="34" y2="5" stroke={`var(${active.colorVar})`} strokeWidth="2"
                strokeDasharray={active.pattern} />
            </svg>
            <span>{active.legend}</span>
          </div>
          {/* Real resolved-model data, not a static caption: how many wall layers carry this
              control layer, and the server's control-continuity findings (click to jump). */}
          <div className="lens-legend-row lens-legend-stat">
            {model
              ? `${data.controlLayerCount} wall layer${data.controlLayerCount === 1 ? "" : "s"} carry the ${active.label.toLowerCase()}-control layer`
              : "Model not loaded"}
          </div>
          {/* The vapour lens reports what each control layer actually *does*: its resolved
              permeance and IRC R702.7 retarder class. A layer whose material authors neither
              perm-inch nor whole-sheet perms says so — the engine refuses to substitute a
              default here (→ 32), and so does the lens. */}
          {data.vaporReadings.length > 0 && (
            <ul className="lens-vapor-readings">
              {data.vaporReadings.map((reading) => (
                <li key={`${reading.material}-${reading.layerName}`}
                  className={reading.perms == null ? "vapor-unknown" : undefined}
                  title={reading.source ?? "no source authored"}>
                  <span className="vapor-perms">{formatPerms(reading.perms)}</span>
                  <span className="vapor-class">{VAPOR_CLASS_LABEL[reading.retarderClass]}</span>
                  <span className="muted">{reading.layerName} · {reading.material}</span>
                </li>
              ))}
            </ul>
          )}
          {data.discontinuities.length > 0 ? (
            <ul className="lens-legend-issues">
              {data.discontinuities.map((issue, index) => (
                <li key={index}>
                  <button
                    type="button"
                    className="lens-issue"
                    onClick={() => issue.element && zoomToUid(issue.element)}
                    disabled={!issue.element}
                    title={issue.element ? "Jump to element" : undefined}
                  >
                    {issue.message}
                  </button>
                </li>
              ))}
            </ul>
          ) : model ? (
            <div className="lens-legend-row lens-legend-ok">No continuity gaps flagged.</div>
          ) : null}
        </div>
      )}
    </>
  );
}
