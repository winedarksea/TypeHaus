import type { SpaceSummary } from "../model/types";

// The engine owns these totals so every client presents the same conditioned/usable split.
export function SpaceDashboard({ summary }: { summary?: SpaceSummary }) {
  if (!summary) return null;
  const overall = summary.overall;
  return (
    <div style={{ marginTop: 16 }}>
      <h3>Space</h3>
      <div className="kv">
        <span className="k">Conditioned</span><span>{overall.conditioned_sf.toFixed(0)} sf</span>
        <span className="k">Unconditioned</span><span>{overall.unconditioned_sf.toFixed(0)} sf</span>
        <span className="k">Usable</span><span>{overall.usable_sf.toFixed(0)} sf</span>
        <span className="k">Storage ratio</span><span>{(overall.storage_ratio * 100).toFixed(1)}%</span>
      </div>
      {summary.storeys.map((row) => (
        <div key={row.storey} className="muted" style={{ marginTop: 5 }}>
          {row.storey}: {row.usable_sf.toFixed(0)} sf usable · {(row.storage_ratio * 100).toFixed(1)}% storage
        </div>
      ))}
    </div>
  );
}
