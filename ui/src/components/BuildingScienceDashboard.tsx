import type { BuildingScience } from "../model/types";

// Read-only M5 dashboard: values are prepared by the engine from its resolved model.
export function BuildingScienceDashboard({ science }: { science: BuildingScience | null | undefined }) {
  if (!science) return null;
  const risk = science.condensation.filter((item) => item.status === "risk");
  return (
    <div>
      <div className="kv">
        <span className="k">Heat load</span>
        <span>{Math.round(science.energy.heating_load_btu_per_hour).toLocaleString()} BTU/h</span>
        <span className="k">Cool load</span>
        <span>{Math.round(science.energy.cooling_load_btu_per_hour).toLocaleString()} BTU/h · {science.energy.cooling_tons.toFixed(2)} tons</span>
      </div>
      <div style={{ marginTop: 8 }}>
        <span className="k">Facade WWR</span>
        {science.wwr.map((item) => (
          <div className="kv" key={item.facade}>
            <span>{item.facade}</span>
            <span>{(item.ratio * 100).toFixed(1)}% · {item.glazing_area_ft2.toFixed(0)} / {item.gross_wall_area_ft2.toFixed(0)} sf</span>
          </div>
        ))}
      </div>
      {science.energy.wall_comparison && <div className="muted" style={{ marginTop: 8 }}>
        2x4 → 2x6 ({science.energy.wall_comparison.area_ft2} sf): saves {Math.round(science.energy.wall_comparison.heating_savings_btu_per_hour)} BTU/h at heating design.
      </div>}
      {risk.length > 0 ? (
        <div style={{ marginTop: 8 }}>
          {risk.map((item) => <div className="finding warn" key={item.assembly}>
            {item.assembly}: dew point in {item.crossing_layer}
          </div>)}
        </div>
      ) : <div className="muted" style={{ marginTop: 8 }}>No resolved condensation crossings.</div>}
    </div>
  );
}
