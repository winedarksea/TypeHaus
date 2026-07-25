import { useState } from "react";
import type { PatchOp } from "../engine/EngineClient";
import type { DoorOperation, DoorTypeSpec, Opening, Vec2 } from "../model/types";

// Trade names for the operation vocabulary; the raw enum values read as jargon in a picker.
const DOOR_OPERATION_LABELS: Record<DoorOperation, string> = {
  swing: "swing",
  double_swing: "French (double)",
  slide: "sliding",
  pocket: "pocket",
  bifold: "bifold",
  overhead: "overhead (sectional)",
};

// Settings popover for a double-clicked door (→ TODO "click doors and modify their
// settings"). Type/handing edits apply immediately as a single-field PatchOp, matching
// the inline-commit pattern used elsewhere (PlacementPopover); position/sill-height stay
// on the existing FtInKeypad flow since they need numeric ft-in entry, not a toggle.
export function DoorSettingsPopover({
  opening, screen, doorTypes, applyOps, onEditPosition, onEditSillHeight, toast, onClose,
}: {
  opening: Opening;
  screen: Vec2;
  doorTypes: DoorTypeSpec[];
  applyOps: (ops: PatchOp[]) => Promise<boolean>;
  onEditPosition: () => void;
  onEditSillHeight: () => void;
  toast: (message: string, kind?: "info" | "error") => void;
  onClose: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const currentType = doorTypes.find((dt) => dt.tag === opening.type_ref) ?? null;

  const update = async (fields: Record<string, unknown>, label: string) => {
    if (busy) return;
    setBusy(true);
    const ok = await applyOps([{ op: "update", type: "Door", tag: opening.tag, fields }]);
    setBusy(false);
    if (ok) toast(`${opening.tag} ${label} updated`);
  };

  const style: React.CSSProperties = {
    position: "absolute",
    left: screen[0],
    top: screen[1],
    transform: "translate(-50%, -110%)",
    zIndex: 30,
  };

  return (
    <div className="hud popover" style={style} onClick={(e) => e.stopPropagation()}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{opening.tag}</div>
      <label style={{ display: "block", marginBottom: 6, fontSize: 12 }}>
        Type{" "}
        <select
          value={opening.type_ref ?? ""}
          disabled={busy || doorTypes.length === 0}
          onChange={(e) => void update({ type_ref: e.target.value }, "type")}
        >
          {currentType === null && opening.type_ref && (
            <option value={opening.type_ref}>{opening.type_ref}</option>
          )}
          {doorTypes.map((dt) => (
            <option key={dt.tag} value={dt.tag}>
              {dt.tag} · {DOOR_OPERATION_LABELS[dt.operation]}
            </option>
          ))}
        </select>
      </label>
      <div style={{ display: "flex", gap: 4, marginBottom: 6 }}>
        <button className="btn" disabled={busy} style={{ flex: 1 }}
          onClick={() => void update({ flip_hinge: !opening.flip_hinge }, "hinge side")}>
          {opening.flip_hinge ? "Hinge: flipped" : "Hinge: default"}
        </button>
        <button className="btn" disabled={busy} style={{ flex: 1 }}
          onClick={() => void update({ flip_swing: !opening.flip_swing }, "swing direction")}>
          {opening.flip_swing ? "Swing: flipped" : "Swing: default"}
        </button>
      </div>
      <button className="btn" style={{ display: "block", width: "100%", marginBottom: 4 }}
        onClick={onEditPosition}>
        Edit position…
      </button>
      <button className="btn" style={{ display: "block", width: "100%", marginBottom: 4 }}
        onClick={onEditSillHeight}>
        Edit sill height…
      </button>
      <button className="btn" onClick={onClose}>Done</button>
    </div>
  );
}
