import { useMemo, useState } from "react";
import { useStore } from "../state/store";
import type { Model } from "../model/types";
import { formatFtIn, parseFtIn } from "../model/geometry";
import { newFloorDefaults, storeyTagError } from "../model/addFloor";

// Add a floor (POST /storeys): writes plan/storeys/<tag>.py above the top storey, optionally
// copying the current floor's walls, openings and rooms. Existing floors never move.
export function AddFloorForm({ model, onDone }: { model: Model; onDone: () => void }) {
  const client = useStore((s) => s.client);
  const activeStorey = useStore((s) => s.activeStorey);
  const defaults = useMemo(() => newFloorDefaults(model.storeys), [model.storeys]);
  const [tag, setTag] = useState(defaults.tag);
  const [elevation, setElevation] = useState(formatFtIn(defaults.elevation_m));
  const [ceiling, setCeiling] = useState(formatFtIn(defaults.ceiling_m));
  const [copy, setCopy] = useState(false);
  const [busy, setBusy] = useState(false);

  const tagError = storeyTagError(tag, model.storeys);
  const elevationM = parseFtIn(elevation);
  const ceilingM = parseFtIn(ceiling);
  const invalid = tagError !== null || elevationM === null || ceilingM === null || ceilingM <= 0;

  const submit = async () => {
    if (invalid || elevationM === null || ceilingM === null) return;
    setBusy(true);
    const { toast, reload, setActiveStorey } = useStore.getState();
    try {
      const result = await client.addStorey({
        tag, elevation: elevationM, ceiling_height: ceilingM,
        ...(copy && activeStorey ? { copy_from: activeStorey } : {}),
      });
      await reload();
      setActiveStorey(result.tag);
      const review = (result.impacts ?? []).filter((i) => i.kind !== "carried").length;
      toast(review ? `Floor ${tag} added; ${review} items were not copied` : `Floor ${tag} added`);
      onDone();
    } catch (err) {
      toast(`Could not add the floor: ${(err as Error).message}`, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="add-floor-form">
      <label className="field-label">Floor name
        <input value={tag} onChange={(e) => setTag(e.target.value.trim())} aria-invalid={tagError !== null} />
        {tagError && <span className="muted">{tagError}</span>}
      </label>
      <label className="field-label">Elevation (defaults to the top floor's ceiling)
        <input value={elevation} onChange={(e) => setElevation(e.target.value)} aria-invalid={elevationM === null} />
      </label>
      <label className="field-label">Ceiling height
        <input value={ceiling} onChange={(e) => setCeiling(e.target.value)} aria-invalid={ceilingM === null} />
      </label>
      {activeStorey && (
        <label className="field-label" style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <input type="checkbox" checked={copy} onChange={(e) => setCopy(e.target.checked)} style={{ flex: "none" }} />
          Copy {activeStorey}'s walls, openings and rooms
        </label>
      )}
      <p className="muted" style={{ fontSize: 12 }}>
        Creating the floor file clears undo history; a copied layout is one undoable step.
      </p>
      <span style={{ display: "flex", gap: 6 }}>
        <button className="btn" onClick={() => void submit()} disabled={invalid || busy}>
          {busy ? "Adding…" : "Add floor"}
        </button>
        <button className="btn" onClick={onDone} disabled={busy}>Cancel</button>
      </span>
    </div>
  );
}
