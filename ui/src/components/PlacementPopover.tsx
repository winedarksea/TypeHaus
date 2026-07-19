import { useState } from "react";
import type { MacroRequest, MacroResult } from "../engine/EngineClient";
import type { Catalog, Vec2, Wall } from "../model/types";
import { formatFtIn } from "../model/geometry";

// Placement popover for the opening + room tools (→ TODO M2 UI editing loop). A tap on a
// wall (opening tool) or in open space (room tool) anchors a small screen-pixel popover here
// rather than a modal, so placement stays fast for repeated taps. Confirming fires the
// server macro (place_opening / place_room) and, on success, selects the minted element.

type Placement =
  | { kind: "opening"; screen: Vec2; wall: Wall; along_m: number }
  | { kind: "room"; screen: Vec2; seed: Vec2 };

export function PlacementPopover({ placement, catalog, hintFile, storey, runMacro, selectByTag, onClose }: {
  placement: Placement;
  catalog: Catalog | undefined;
  hintFile: string | undefined;
  storey: string | null;
  runMacro: (request: MacroRequest) => Promise<MacroResult | null>;
  selectByTag: (kind: "wall" | "opening" | "room", tag: string) => void;
  onClose: () => void;
}) {
  const [busy, setBusy] = useState(false);

  const place = async (request: MacroRequest, kind: "opening" | "room") => {
    if (!storey || busy) return;
    setBusy(true);
    const res = await runMacro(request);
    setBusy(false);
    if (res) {
      const tag = Object.keys(res.minted).find((t) =>
        kind === "opening" ? t.startsWith("WIN-") || t.startsWith("D-") : t.startsWith("RM-"))
        ?? Object.keys(res.minted)[0];
      if (tag) selectByTag(kind, tag);
      onClose();
    }
  };

  const style: React.CSSProperties = {
    position: "absolute",
    left: placement.screen[0],
    top: placement.screen[1],
    transform: "translate(-50%, -110%)",
    zIndex: 30,
  };

  if (placement.kind === "opening") {
    const windows = catalog?.window_types ?? [];
    const doors = catalog?.door_types ?? [];
    return (
      <div className="hud popover" style={style} onClick={(e) => e.stopPropagation()}>
        <div className="muted" style={{ fontSize: 11, marginBottom: 4 }}>
          {placement.wall.tag} @ {formatFtIn(placement.along_m)}
        </div>
        {windows.length === 0 && doors.length === 0 && (
          <div className="muted">No window/door types in the library.</div>
        )}
        {windows.map((wt) => (
          <button key={wt.tag} className="btn" disabled={busy} style={{ display: "block", width: "100%", marginBottom: 4 }}
            onClick={() => void place({
              macro: "place_opening", storey: storey!, host: placement.wall.tag,
              type_ref: wt.tag, along: formatFtIn(placement.along_m), is_door: false,
              hint_file: hintFile,
            }, "opening")}>
            ❒ {wt.tag} · {formatFtIn(wt.width_m)}×{formatFtIn(wt.height_m)}
          </button>
        ))}
        {doors.map((dt) => (
          <button key={dt.tag} className="btn" disabled={busy} style={{ display: "block", width: "100%", marginBottom: 4 }}
            onClick={() => void place({
              macro: "place_opening", storey: storey!, host: placement.wall.tag,
              type_ref: dt.tag, along: formatFtIn(placement.along_m), is_door: true,
              hint_file: hintFile,
            }, "opening")}>
            🚪 {dt.tag} · {formatFtIn(dt.width_m)}×{formatFtIn(dt.height_m)}
          </button>
        ))}
        <button className="btn" onClick={onClose}>Cancel</button>
      </div>
    );
  }

  const occupancies = catalog?.occupancies ?? [];
  const [occupancy, setOccupancy] = useState(occupancies[0] ?? "living");
  return (
    <div className="hud popover" style={style} onClick={(e) => e.stopPropagation()}>
      <div className="muted" style={{ fontSize: 11, marginBottom: 4 }}>Claim room</div>
      <label style={{ display: "block", marginBottom: 6, fontSize: 12 }}>
        Occupancy{" "}
        <select value={occupancy} onChange={(e) => setOccupancy(e.target.value)}>
          {occupancies.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      </label>
      <button className="btn" disabled={busy} style={{ display: "block", width: "100%", marginBottom: 4 }}
        onClick={() => void place({
          macro: "place_room", storey: storey!,
          seed: [formatFtIn(placement.seed[0]), formatFtIn(placement.seed[1])],
          occupancy, hint_file: hintFile,
        }, "room")}>
        Claim here
      </button>
      <button className="btn" onClick={onClose}>Cancel</button>
    </div>
  );
}
