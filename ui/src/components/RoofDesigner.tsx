import { useEffect, useState } from "react";
import type { Model, Roof } from "../model/types";
import { useStore } from "../state/store";

// This editor only writes typed Roof inputs. The resolver remains the sole authority for roof
// planes, raked framing, attic geometry, and the R305 result shown after each resolve.
export function RoofDesigner({ model }: { model: Model }) {
  const roofs = model.roofs ?? [];
  const applyOps = useStore((state) => state.applyOps);
  const [selectedTag, setSelectedTag] = useState(roofs[0]?.tag ?? "");
  const roof = roofs.find((item) => item.tag === selectedTag) ?? roofs[0];
  const [pitch, setPitch] = useState("4/12");
  const [ridgeDirection, setRidgeDirection] = useState<"x" | "y">("x");
  const [bearings, setBearings] = useState("");
  const [overhang, setOverhang] = useState("0'");
  const height = model.building_height_summary?.roofs.find((item) => item.roof_tag === roof?.tag);

  useEffect(() => {
    if (!roof) return;
    const rise = (roof.ridge_z_m - roof.eave_z_m) / Math.max(0.001, halfSpan(roof));
    setPitch(`${Math.round(rise * 12 * 10) / 10}/12`);
    setRidgeDirection(roof.ridge_direction);
  }, [roof]);
  if (!roof) return null;

  const save = async () => {
    const refs = bearings.split(",").map((value) => value.trim()).filter(Boolean);
    const fields: Record<string, unknown> = { pitch, ridge_direction: ridgeDirection, overhang };
    if (refs.length >= 2) fields.bearing_refs = refs;
    await applyOps([{ op: "update", type: "Roof", tag: roof.tag, fields }]);
  };
  return <div style={{ marginTop: 16 }}>
    <h3>Roof designer</h3>
    <select value={roof.tag} onChange={(event) => setSelectedTag(event.target.value)}>
      {roofs.map((item) => <option key={item.tag}>{item.tag}</option>)}
    </select>
    <div className="kv" style={{ marginTop: 6 }}>
      <span className="k">Form</span><span>{roof.form}</span>
      <span className="k">Structural eave / ridge</span><span>{metersToFeet(roof.eave_z_m)} / {metersToFeet(roof.ridge_z_m)}</span>
      {height && <>
        <span className="k">Finished midpoint above average grade</span><span>{metersToFeet(height.midpoint_above_grade_m)}</span>
        <span className="k">Finished peak above average grade</span><span>{metersToFeet(height.peak_above_grade_m)}</span>
      </>}
    </div>
    <label style={{ display: "block", marginTop: 5 }}>Pitch <input value={pitch}
      onChange={(event) => setPitch(event.target.value)} /></label>
    <label style={{ display: "block", marginTop: 5 }}>Ridge <select value={ridgeDirection}
      onChange={(event) => setRidgeDirection(event.target.value as "x" | "y")}><option value="x">E–W</option><option value="y">N–S</option></select></label>
    <label style={{ display: "block", marginTop: 5 }}>Bearing walls <input placeholder="W-1, W-2"
      value={bearings} onChange={(event) => setBearings(event.target.value)} /></label>
    <label style={{ display: "block", marginTop: 5 }}>Overhang <input value={overhang}
      onChange={(event) => setOverhang(event.target.value)} /></label>
    <button className="btn" style={{ marginTop: 7 }} onClick={() => void save()}>Resolve roof</button>
    <div className="muted" style={{ fontSize: 12, marginTop: 5 }}>
      R305/headroom, raked studs, rafters, and unsupported-form findings update after resolve.
    </div>
  </div>;
}

function halfSpan(roof: Roof): number {
  const xs = roof.footprint.map((point) => point[0]);
  const ys = roof.footprint.map((point) => point[1]);
  const span = roof.ridge_direction === "x" ? Math.max(...ys) - Math.min(...ys) : Math.max(...xs) - Math.min(...xs);
  return span / 2;
}

function metersToFeet(meters: number): string {
  return `${(meters / 0.3048).toFixed(1)}'`;
}
