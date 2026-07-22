import { useEffect } from "react";
import { useStore, type Lens } from "../state/store";

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

const LENSES: LensSpec[] = [
  { id: "none", label: "Normal", icon: "◻", colorVar: "--ink", pattern: "0", legend: "All disciplines shown normally." },
  { id: "air", label: "Air", icon: "≋", colorVar: "--control-air", pattern: "2 3", legend: "Air-barrier continuity — discontinuities numbered." },
  { id: "water", label: "Water", icon: "☂", colorVar: "--control-water", pattern: "6 3", legend: "Water-control layer + drainage path continuity." },
  { id: "thermal", label: "Thermal", icon: "☀", colorVar: "--control-thermal", pattern: "1 4", legend: "Thermal-control layer — bridges highlighted." },
];

export function LensBar() {
  const activeLens = useStore((s) => s.activeLens);
  const setActiveLens = useStore((s) => s.setActiveLens);

  // Drive a root attribute so CSS can mute base geometry while a lens is active.
  useEffect(() => {
    document.documentElement.dataset.lens = activeLens;
    return () => { document.documentElement.dataset.lens = "none"; };
  }, [activeLens]);

  const active = LENSES.find((l) => l.id === activeLens) ?? LENSES[0];

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

      {activeLens !== "none" && (
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
        </div>
      )}
    </>
  );
}
