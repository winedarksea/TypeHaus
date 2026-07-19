import { useEffect, useMemo, useState } from "react";
import type { Model, Stair, Vec2 } from "../model/types";
import { formatFtIn, parseFtIn } from "../model/geometry";
import { useStore } from "../state/store";

const MAX_RISER_M = 7.75 * 0.0254;
const MIN_TREAD_M = 10 * 0.0254;
const MIN_HEADROOM_M = 6 * 0.3048 + 8 * 0.0254;

// The resolver remains authoritative: this component only mirrors its small, deterministic
// single-flight solve to give immediate feedback before the authored Stair is written back.
export function StairDesigner({ model }: { model: Model }) {
  const stairs = model.stairs ?? [];
  const applyOps = useStore((state) => state.applyOps);
  const select = useStore((state) => state.select);
  const offline = useStore((state) => state.offline);
  const [selectedTag, setSelectedTag] = useState(stairs[0]?.tag ?? "");
  const stair = stairs.find((item) => item.tag === selectedTag) ?? stairs[0];
  const [width, setWidth] = useState("");
  const [runDirection, setRunDirection] = useState<"x" | "y">("x");
  const [runReversed, setRunReversed] = useState(false);
  const [winderCount, setWinderCount] = useState<0 | 2>(0);

  useEffect(() => {
    if (!stair) return;
    setSelectedTag(stair.tag);
    setWidth(formatFtIn(stair.width_m));
    setRunDirection(stair.run_direction);
    setRunReversed(stair.run_reversed);
    setWinderCount(stair.winder_count === 2 ? 2 : 0);
  }, [stair?.uid, stair?.width_m, stair?.run_direction, stair?.run_reversed, stair?.winder_count]);

  const solved = useMemo(() => stair ? previewStair(model, stair, width, runDirection, runReversed, winderCount) : null,
    [model, stair, width, runDirection, runReversed, winderCount]);
  if (!stair || !solved) return null;

  const save = async () => {
    if (!solved.ok) return;
    const ok = await applyOps([{
      op: "update", type: "Stair", tag: stair.tag,
      fields: { width, run_direction: runDirection, run_reversed: runReversed, winder_count: winderCount },
    }]);
    if (ok) select("stair", stair.uid);
  };

  return <div style={{ marginTop: 16 }}>
    <h3>Stair designer</h3>
    <select value={stair.tag} onChange={(event) => setSelectedTag(event.target.value)}>
      {stairs.map((item) => <option key={item.tag} value={item.tag}>{item.tag} · {item.storey} → {item.to_storey}</option>)}
    </select>
    <div className="kv" style={{ marginTop: 6 }}>
      <span className="k">Floor-to-floor rise</span><span>{formatFtIn(solved.rise)}</span>
      <span className="k">Opening</span><span>{formatFtIn(solved.run)} × {formatFtIn(solved.openingWidth)}</span>
      <span className="k">Solve</span><span>{solved.riserCount} risers @ {formatFtIn(solved.riser)} · {formatFtIn(solved.tread)} tread</span>
      <span className="k">Total run</span><span>{formatFtIn(solved.run)}</span>
    </div>
    <label style={{ display: "block", marginTop: 5 }}>Clear width <input value={width}
      onChange={(event) => setWidth(event.target.value)} /></label>
    <label style={{ display: "block", marginTop: 5 }}>Run direction <select value={runDirection}
      onChange={(event) => setRunDirection(event.target.value as "x" | "y")}>
      <option value="x">E–W</option><option value="y">N–S</option>
    </select></label>
    <label style={{ display: "block", marginTop: 5 }}>Climb toward <select value={runReversed ? "reverse" : "forward"}
      onChange={(event) => setRunReversed(event.target.value === "reverse")}>
      <option value="forward">{runDirection === "x" ? "east" : "north"}</option>
      <option value="reverse">{runDirection === "x" ? "west" : "south"}</option>
    </select></label>
    <label style={{ display: "block", marginTop: 5 }}>Winders <select value={winderCount}
      onChange={(event) => setWinderCount(Number(event.target.value) as 0 | 2)}>
      <option value={0}>none</option><option value={2}>two at lower turn</option>
    </select></label>
    <StairRule pass={solved.riser <= MAX_RISER_M} label={`R311.7.5 · riser ≤ 7¾" (${formatFtIn(solved.riser)})`} />
    <StairRule pass={solved.tread >= MIN_TREAD_M} label={`R311.7.5 · tread ≥ 10" (${formatFtIn(solved.tread)})`} />
    <StairRule pass={solved.widthFits} label={`Clear width fits the ${formatFtIn(solved.openingWidth)} opening`} />
    <StairRule pass={solved.flightFits} label={`Opening clears the full flight · headroom target ≥ ${formatFtIn(MIN_HEADROOM_M)}`} />
    <button className="btn" disabled={offline || !solved.ok} style={{ marginTop: 7 }}
      title={offline ? "Editing needs haus serve" : solved.ok ? "Write the valid Stair inputs" : "Fix the red stair constraints first"}
      onClick={() => void save()}>{offline ? "Server required" : "Apply valid stair"}</button>
    {!solved.ok && <div className="finding error" style={{ marginTop: 6 }}>
      The proposed flight does not fit its opening; no change has been written.
    </div>}
    <div className="muted" style={{ fontSize: 12, marginTop: 5 }}>
      Rise is derived from storey elevations. Applying re-resolves the stringers and treads in 2D and 3D.
    </div>
  </div>;
}

function StairRule({ pass, label }: { pass: boolean; label: string }) {
  return <div className={`finding ${pass ? "info" : "error"}`} style={{ marginTop: 5, padding: "4px 6px" }}>
    {pass ? "✓" : "×"} {label}
  </div>;
}

interface StairPreview {
  rise: number;
  run: number;
  openingWidth: number;
  riserCount: number;
  riser: number;
  tread: number;
  widthFits: boolean;
  flightFits: boolean;
  ok: boolean;
}

function previewStair(model: Model, stair: Stair, widthText: string, direction: "x" | "y",
                      reversed: boolean, winderCount: 0 | 2): StairPreview {
  const from = model.storeys.find((storey) => storey.tag === stair.storey);
  const to = model.storeys.find((storey) => storey.tag === stair.to_storey);
  const rise = Math.max(0, (to?.elevation_m ?? 0) - (from?.elevation_m ?? 0));
  const xs = stair.outline.map((point) => point[0]);
  const ys = stair.outline.map((point) => point[1]);
  const minX = Math.min(...xs); const maxX = Math.max(...xs);
  const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const run = direction === "x" ? maxX - minX : maxY - minY;
  const openingWidth = direction === "x" ? maxY - minY : maxX - minX;
  const riserCount = Math.ceil(rise / MAX_RISER_M);
  const riser = riserCount ? rise / riserCount : Infinity;
  const requestedWidth = parseLength(widthText);
  const straightTreads = riserCount - 1 - winderCount;
  const tread = straightTreads > 0 ? (run - (winderCount ? requestedWidth ?? Infinity : 0)) / straightTreads : 0;
  const widthFits = requestedWidth !== null && requestedWidth <= openingWidth + 1e-9;
  const [startX, startY] = stair.start ?? defaultStart(direction, reversed, [minX, minY], [maxX, maxY]);
  const signedRun = (reversed ? -1 : 1) * run;
  const flightFits = direction === "x"
    ? Math.min(startX, startX + signedRun) >= minX - 1e-9 && Math.max(startX, startX + signedRun) <= maxX + 1e-9
      && startY >= minY - 1e-9 && startY + (requestedWidth ?? Infinity) <= maxY + 1e-9
    : Math.min(startY, startY + signedRun) >= minY - 1e-9 && Math.max(startY, startY + signedRun) <= maxY + 1e-9
      && startX >= minX - 1e-9 && startX + (requestedWidth ?? Infinity) <= maxX + 1e-9;
  const ok = rise > 0 && riser <= MAX_RISER_M && tread >= MIN_TREAD_M && widthFits && flightFits;
  return { rise, run, openingWidth, riserCount, riser, tread, widthFits, flightFits, ok };
}

function defaultStart(direction: "x" | "y", reversed: boolean, min: Vec2, max: Vec2): Vec2 {
  return direction === "x" ? [reversed ? max[0] : min[0], min[1]] : [min[0], reversed ? max[1] : min[1]];
}

function parseLength(value: string): number | null {
  return parseFtIn(value);
}
