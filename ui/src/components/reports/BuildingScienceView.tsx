import type { CondensationProfile } from "../../model/types";
import { ReaderEmpty, ReaderSection, ReaderShell, ReaderTable, useReader } from "../ReaderShell";

const formatLoadBtuPerHour = (value: number) => `${Math.round(value).toLocaleString()} BTU/h`;
const formatRatioPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

export function BuildingScienceView() {
  const { model, data: science, close } = useReader((model) => model.building_science);
  if (!model) return null;
  if (!science) return <ReaderEmpty title="Building science" subtitle={model.project.name} onClose={close}>
    Building science data is unavailable for this model.
  </ReaderEmpty>;
  const energy = science.energy;
  const energyTerms = [
    ["Heating load at design", formatLoadBtuPerHour(energy.heating_load_btu_per_hour)],
    ["Sensible cooling load", formatLoadBtuPerHour(energy.cooling_load_btu_per_hour)],
    ["Latent cooling load", formatLoadBtuPerHour(energy.latent_btu_per_hour)],
    ["Total cooling", `${energy.cooling_tons.toFixed(2)} tons`],
    ["Sensible heat ratio", energy.sensible_heat_ratio === null ? "—" : formatRatioPercent(energy.sensible_heat_ratio)],
    ["Solar gain at peak", formatLoadBtuPerHour(energy.solar_btu_per_hour)],
    ["Peak solar hour", energy.solar_peak_hour === null ? "—" : String(energy.solar_peak_hour)],
    ["Solar excursion", formatLoadBtuPerHour(energy.solar_excursion_btu_per_hour)],
    ["Internal sensible gain", formatLoadBtuPerHour(energy.internal_sensible_btu_per_hour)],
    ["Infiltration heating", formatLoadBtuPerHour(energy.infiltration_btu_per_hour)],
    ["Ventilation heating", formatLoadBtuPerHour(energy.ventilation_btu_per_hour)],
  ];

  return <ReaderShell className="report-reader" title="Building science" subtitle={model.project.name} onClose={close}>
    <ReaderSection title="Energy loads" note="Engine-calculated design loads. Cooling BTU/h is sensible; total tons includes latent load." count={1}>
      <ReaderTable rows={energyTerms} rowKey={(row) => row[0]} columns={[
        { key: "term", header: "Term", cell: (row) => row[0] },
        { key: "value", header: "Value", num: true, cell: (row) => row[1] },
      ]} />
      <h4>Envelope load components</h4>
      <ReaderTable rows={energy.components ?? []} rowKey={(row, index) => `${row.kind}|${index}`}
        empty={<p className="muted">Envelope load components are unavailable.</p>} columns={[
          { key: "kind", header: "Component", cell: (row) => row.kind.replace(/_/g, " ") },
          { key: "area", header: "Area (sf)", num: true, cell: (row) => row.area_ft2.toFixed(1) },
          { key: "ua", header: "UA (BTU/h·°F)", num: true, cell: (row) => row.ua_btu_per_hour_f.toFixed(2) },
          { key: "delta", header: "Heating ΔT (°F)", num: true, cell: (row) => row.heating_delta_f?.toFixed(1) ?? "—" },
          { key: "solar", header: "Solar gain", num: true, cell: (row) => formatLoadBtuPerHour(row.solar_gain_btu_per_hour) },
        ]} />
      <h4>Unknown inputs</h4>
      {energy.unknown_inputs.length ? <ul>{energy.unknown_inputs.map((input, index) =>
        <li key={index}>{input}</li>)}</ul> : <p className="muted">No unknown energy inputs reported.</p>}
      <h4>Method caveats</h4>
      {energy.cooling_caveats.length ? <ul>{energy.cooling_caveats.map((caveat, index) =>
        <li key={index}>{caveat}</li>)}</ul> : <p className="muted">No cooling method caveats reported.</p>}
      {energy.wall_comparison && <p>
        {energy.wall_comparison.baseline_assembly} → {energy.wall_comparison.upgrade_assembly}
        {" "}over {energy.wall_comparison.area_ft2.toLocaleString()} sf:
        {" "}{formatLoadBtuPerHour(energy.wall_comparison.heating_savings_btu_per_hour)} heating savings at design.
      </p>}
    </ReaderSection>
    <ReaderSection title="Facade glazing" note="Window-to-wall ratio by facade, using gross wall and glazing areas." count={science.wwr.length}>
      <ReaderTable rows={science.wwr} rowKey={(row) => row.facade} columns={[
        { key: "facade", header: "Facade", cell: (row) => row.facade },
        { key: "glazing", header: "Glazing (sf)", num: true, cell: (row) => row.glazing_area_ft2.toFixed(1) },
        { key: "wall", header: "Gross wall (sf)", num: true, cell: (row) => row.gross_wall_area_ft2.toFixed(1) },
        { key: "ratio", header: "WWR", num: true, cell: (row) => formatRatioPercent(row.ratio) },
      ]} />
    </ReaderSection>
    <ReaderSection title="Condensation" note="Steady-state screening through the assembly. Expand a profile to inspect its temperature and vapor pressures." count={science.condensation.length}>
      {science.condensation.map((profile) => <CondensationResult key={profile.assembly} profile={profile} />)}
    </ReaderSection>
  </ReaderShell>;
}

function CondensationResult({ profile }: { profile: CondensationProfile }) {
  return <details className="reader-card">
    <summary>{profile.assembly} · <span className={profile.status === "safe" ? "" : "muted"}>{profile.status}</span></summary>
    {profile.crossing_layer && <p>Dew-point crossing in {profile.crossing_layer}
      {profile.crossing_fraction !== null && ` (${formatRatioPercent(profile.crossing_fraction)} through layer)`}.</p>}
    {profile.status === "safe" && <p>No condensation crossing under these screening conditions.</p>}
    {profile.status === "unknown" && <p>The condensation result could not be determined.</p>}
    {profile.unknown_materials.length > 0 && <p>Missing material properties: {profile.unknown_materials.join(", ")}.</p>}
    <ReaderTable rows={profile.points} rowKey={(_, index) => String(index)} empty={<p className="muted">No profile points available.</p>} columns={[
      { key: "position", header: "Vapor-resistance position", num: true, cell: (point) => formatRatioPercent(point.position) },
      { key: "temperature", header: "Temperature (°C)", num: true, cell: (point) => point.temperature_c.toFixed(1) },
      { key: "vapor", header: "Vapor pressure (Pa)", num: true, cell: (point) => point.vapor_pressure_pa.toFixed(0) },
      { key: "saturation", header: "Saturation pressure (Pa)", num: true, cell: (point) => point.saturation_pressure_pa.toFixed(0) },
    ]} />
  </details>;
}
