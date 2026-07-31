import { useState } from "react";
import type { PatchOp } from "../engine/EngineClient";
import type { Opening, Vec2, WindowOperation, WindowTypeSpec } from "../model/types";

// Trade names for the operation vocabulary (mirrors DOOR_OPERATION_LABELS): the raw enum
// values read as jargon in a picker, and "fixed" in particular is the one a client must not
// mis-pick — hence the parenthetical.
export const WINDOW_OPERATION_LABELS: Record<WindowOperation, string> = {
  fixed: "fixed (picture)",
  casement: "casement",
  double_hung: "double-hung",
  slider: "slider",
  awning: "awning",
  tilt_turn: "tilt & turn",
};

// Settings popover for a clicked window — mirrors DoorSettingsPopover. Type edits apply
// immediately as a single-field PatchOp; position/sill-height defer to the FtInKeypad flow
// since they need numeric ft-in entry. Windows have no hinge/swing, so those toggles are
// absent; a Delete action is offered in their place.
export function WindowSettingsPopover({
  opening, screen, windowTypes, applyOps, onEditPosition, onEditSillHeight, onDelete, toast, onClose,
}: {
  opening: Opening;
  screen: Vec2;
  windowTypes: WindowTypeSpec[];
  applyOps: (ops: PatchOp[]) => Promise<boolean>;
  onEditPosition: () => void;
  onEditSillHeight: () => void;
  onDelete: () => void;
  toast: (message: string, kind?: "info" | "error") => void;
  onClose: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const currentType = windowTypes.find((wt) => wt.tag === opening.type_ref) ?? null;

  const update = async (fields: Record<string, unknown>, label: string) => {
    if (busy) return;
    setBusy(true);
    const ok = await applyOps([{ op: "update", type: "Window", tag: opening.tag, fields }]);
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
          disabled={busy || windowTypes.length === 0}
          onChange={(e) => void update({ type_ref: e.target.value }, "type")}
        >
          {currentType === null && opening.type_ref && (
            <option value={opening.type_ref}>{opening.type_ref}</option>
          )}
          {windowTypes.map((wt) => (
            <option key={wt.tag} value={wt.tag}>
              {wt.tag} · {WINDOW_OPERATION_LABELS[wt.operation] ?? wt.operation}
            </option>
          ))}
        </select>
      </label>
      <button className="btn" style={{ display: "block", width: "100%", marginBottom: 4 }}
        onClick={onEditPosition}>
        Edit position…
      </button>
      <button className="btn" style={{ display: "block", width: "100%", marginBottom: 4 }}
        onClick={onEditSillHeight}>
        Edit sill height…
      </button>
      <button className="btn" style={{ display: "block", width: "100%", marginBottom: 4 }}
        onClick={onDelete}>
        Delete
      </button>
      <button className="btn" onClick={onClose}>Done</button>
    </div>
  );
}
