import type { BuildingHeightSummary, SpaceSummary } from "../model/types";

// The engine owns these totals so every client presents the same conditioned/usable split.
export function SpaceDashboard({ summary, buildingHeight }: {
  summary?: SpaceSummary;
  buildingHeight?: BuildingHeightSummary;
}) {
  if (!summary && !buildingHeight) return null;
  const overall = summary?.overall;
  return (
    <div>
      {overall && <>
        <div className="kv">
          <span className="k">Conditioned</span><span>{overall.conditioned_sf.toFixed(0)} sf</span>
          <span className="k">Unconditioned</span><span>{overall.unconditioned_sf.toFixed(0)} sf</span>
          <span className="k">Usable</span><span>{overall.usable_sf.toFixed(0)} sf</span>
          <span className="k">Storage ratio</span><span>{(overall.storage_ratio * 100).toFixed(1)}%</span>
        </div>
      </>}
      {summary?.storeys.map((row) => (
        <div key={row.storey} className="muted" style={{ marginTop: 5 }}>
          {row.storey}: {row.usable_sf.toFixed(0)} sf usable · {(row.storage_ratio * 100).toFixed(1)}% storage
        </div>
      ))}
      {buildingHeight && <>
        <div style={{ fontWeight: 600, marginTop: 12, marginBottom: 4 }}>Height above average grade</div>
        {buildingHeight.roofs.map((roof) => (
          <div key={roof.roof_tag} className="kv" style={{ marginTop: 5 }}>
            <span className="k">{roof.roof_tag} midpoint</span><span>{metersToFeet(roof.midpoint_above_grade_m)}</span>
            <span className="k">{roof.roof_tag} peak</span><span>{metersToFeet(roof.peak_above_grade_m)}</span>
          </div>
        ))}
      </>}
    </div>
  );
}

function metersToFeet(meters: number): string {
  return `${(meters / 0.3048).toFixed(1)}'`;
}
