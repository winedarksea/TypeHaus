import type { Model } from "../model/types";

// True north on the plan. The plan never tilts (+y up); true_north_deg is the CLOCKWISE angle
// from project north to true north (same convention as three/planGeometry.ts), which is an SVG
// rotate(θ). A .hud chip, so it takes --ink; the plan's own ink is --canvas-ink.
export function NorthArrow({ model }: { model: Model }) {
  if (!model.site) return null;
  const deg = model.site.true_north_deg;
  return (
    <div className="hud" title={`True north ${deg.toFixed(0)}° clockwise of project north`}
      style={{ padding: 4, lineHeight: 0 }}>
      <svg width={34} height={34} viewBox="-17 -17 34 34" role="img" aria-label="True north">
        <g transform={`rotate(${deg})`}>
          <path d="M0 -8 L4.5 9 L0 6.5 L-4.5 9 Z" fill="var(--ink)" />
          <text x={0} y={-10} textAnchor="middle" fontSize={7} fontWeight={700}
            fill="var(--ink)" transform={`rotate(${-deg} 0 -12.5)`}>N</text>
        </g>
      </svg>
    </div>
  );
}
