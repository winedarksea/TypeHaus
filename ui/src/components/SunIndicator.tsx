import { useMemo, useState } from "react";
import type { Model } from "../model/types";

// NOAA's fractional-year solar-position approximation. It is deliberately an orientation
// aid only: the editor reports azimuth/altitude but never claims a shadow simulation.
export function SunIndicator({ model }: { model: Model }) {
  const [visible, setVisible] = useState(false);
  const [day, setDay] = useState(172);
  const [hour, setHour] = useState(12);
  const position = useMemo(() => model.site ? solarPosition(model.site.lat, day, hour) : null,
    [model.site, day, hour]);

  if (!model.site) return null;
  return (
    <div className="hud" style={{ left: "auto", right: 12, bottom: 12, width: visible ? 206 : "auto" }}>
      <button className="btn" onClick={() => setVisible(!visible)} title="Solar orientation indicator">
        ☀ Sun
      </button>
      {visible && position && (
        <div style={{ marginTop: 8, display: "grid", gap: 5, fontSize: 12 }}>
          <span>Az {position.azimuth.toFixed(0)}° · Alt {position.altitude.toFixed(0)}°</span>
          <label>Day {day}<input type="range" min="1" max="365" value={day}
            onChange={(event) => setDay(Number(event.target.value))} /></label>
          <label>Solar time {hour.toFixed(1)}<input type="range" min="0" max="24" step="0.5" value={hour}
            onChange={(event) => setHour(Number(event.target.value))} /></label>
          <span className="muted">True north {model.site.true_north_deg.toFixed(0)}° · no shadow casting</span>
        </div>
      )}
    </div>
  );
}

function solarPosition(latitudeDeg: number, day: number, solarHour: number) {
  const toRad = Math.PI / 180;
  const latitude = latitudeDeg * toRad;
  // Fractional-year declination, sufficient for an on-canvas orientation aid. The slider is
  // expressed as solar time, avoiding a hidden time-zone or daylight-savings assumption.
  const gamma = (2 * Math.PI / 365) * (day - 1 + (solarHour - 12) / 24);
  const declination = 0.006918 - 0.399912 * Math.cos(gamma) + 0.070257 * Math.sin(gamma)
    - 0.006758 * Math.cos(2 * gamma) + 0.000907 * Math.sin(2 * gamma)
    - 0.002697 * Math.cos(3 * gamma) + 0.00148 * Math.sin(3 * gamma);
  const hourAngle = (solarHour - 12) * 15 * toRad;
  const altitude = Math.asin(Math.sin(latitude) * Math.sin(declination)
    + Math.cos(latitude) * Math.cos(declination) * Math.cos(hourAngle));
  const azimuth = Math.atan2(Math.sin(hourAngle), Math.cos(hourAngle) * Math.sin(latitude)
    - Math.tan(declination) * Math.cos(latitude)) / toRad + 180;
  return { altitude: altitude / toRad, azimuth: azimuth % 360 };
}
