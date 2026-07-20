import type { CondensationProfile, Layer } from "../model/types";
import { formatFtIn } from "../model/geometry";
import { CONTROL_COLOR, materialColor } from "../nordic/palette";

// The assembly section card — the UI's read affordance for assemblies (→ 21 §Assembly
// picker, → 12 §Assembly card). Renders the selected wall's layer stack to scale from
// model.json layer thicknesses, with control-layer badges and a total-thickness rollup.
// Model-free by design: it consumes only the layer list already resolved server-side.
export function SectionCard({ layers, title, condensation }: {
  layers: Layer[]; title: string; condensation?: CondensationProfile;
}) {
  if (layers.length === 0) return <div className="muted">No layers resolved.</div>;
  const total = layers.reduce((a, l) => a + l.thickness_m, 0) || 1;
  const W = 280;
  const H = 120;
  let x = 0;

  return (
    <div className="section-card">
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>{title}</div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
        {layers.map((ly, i) => {
          const w = (ly.thickness_m / total) * W;
          const rect = (
            <g key={i}>
              <rect
                x={x}
                y={0}
                width={w}
                height={H - 22}
                fill={materialColor(ly.material)}
                stroke="var(--panel-line)"
              />
              {ly.control.map((c, ci) => (
                <line
                  key={c}
                  x1={x + 2 + ci * 4}
                  y1={2}
                  x2={x + 2 + ci * 4}
                  y2={H - 24}
                  stroke={CONTROL_COLOR[c] ?? "var(--ink)"}
                  strokeWidth={2}
                />
              ))}
            </g>
          );
          x += w;
          return rect;
        })}
        <line x1={0} y1={H - 20} x2={W} y2={H - 20} stroke="var(--line)" />
      </svg>
      <div className="layer-list" style={{ marginTop: 6 }}>
        {layers.map((ly, i) => (
          <div className="layer-row" key={i}>
            <span className="swatch" style={{ background: materialColor(ly.material) }} />
            <span style={{ flex: 1 }}>
              {ly.name} <span className="muted">({ly.function})</span>
            </span>
            {ly.control.map((c) => (
              <span
                key={c}
                title={`${c} control layer`}
                style={{ color: CONTROL_COLOR[c] ?? "var(--ink)", fontSize: 11 }}
              >
                ●
              </span>
            ))}
            <span className="muted">{formatFtIn(ly.thickness_m)}</span>
          </div>
        ))}
      </div>
      <div className="kv" style={{ marginTop: 6 }}>
        <span className="k">Total thickness</span>
        <span>{formatFtIn(total)}</span>
      </div>
      {condensation && <CondensationPlot profile={condensation} />}
    </div>
  );
}

function CondensationPlot({ profile }: { profile: CondensationProfile }) {
  if (profile.status === "unknown") {
    return <div className="muted" style={{ marginTop: 8 }}>Glaser: unknown — {profile.unknown_materials.join(", ")}</div>;
  }
  const points = profile.points;
  const vapor = points.map((p) => p.vapor_pressure_pa);
  const saturation = points.map((p) => p.saturation_pressure_pa);
  const temperature = points.map((p) => p.temperature_c);
  const path = (values: number[]) => {
    const lo = Math.min(...values);
    const hi = Math.max(...values);
    return points.map((p, i) => `${i ? "L" : "M"}${p.position * 260} ${72 - ((values[i] - lo) / (hi - lo || 1)) * 64}`).join(" ");
  };
  return <div style={{ marginTop: 10 }}>
    <span className="k">Glaser profile</span>
    <svg width="100%" viewBox="0 0 260 88" style={{ display: "block", marginTop: 3 }}>
      <rect width="260" height="72" fill="var(--panel)" stroke="var(--panel-line)" />
      <path d={path(temperature)} fill="none" stroke="var(--control-thermal)" strokeWidth="2" />
      <path d={path(vapor)} fill="none" stroke="var(--control-water)" strokeWidth="2" />
      <path d={path(saturation)} fill="none" stroke="var(--control-air)" strokeWidth="2" />
      <text x="0" y="85" fontSize="9" fill="var(--line)">temp · vapor · saturation</text>
    </svg>
    {profile.status === "risk" && <div className="finding warn">Dew point: {profile.crossing_layer}</div>}
  </div>;
}
