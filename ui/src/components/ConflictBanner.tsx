import { useStore } from "../state/store";

// Stale-source detection surfaces as a canvas banner with reload as the only mutation
// path (#30, → 21 §Conflict banner). A 409 from PATCH /plan populates store.conflict.
export function ConflictBanner() {
  const conflict = useStore((s) => s.conflict);
  const reload = useStore((s) => s.reload);
  const dismiss = useStore((s) => s.dismissConflict);
  const writebackFailure = useStore((s) => s.writebackFailure);
  const dismissWriteback = useStore((s) => s.dismissWritebackFailure);
  // A failed writeback is the same class of event — the edit is gone and only a reload
  // reconciles — so it reuses this banner rather than a dismissable toast.
  if (writebackFailure && !conflict) {
    return (
      <div className="banner">
        <span>
          ⚠ Your edit could not be written to the plan source and was reverted:{" "}
          {writebackFailure}
        </span>
        <button
          className="btn"
          onClick={async () => {
            await reload();
            dismissWriteback();
          }}
        >
          Reload
        </button>
      </div>
    );
  }
  if (!conflict) return null;
  return (
    <div className="banner">
      <span>
        ⚠ The plan source changed on disk. Your edit was rejected to avoid clobbering it.
        {conflict.changed?.length ? ` Changed: ${conflict.changed.join(", ")}.` : ""}
      </span>
      <button
        className="btn"
        onClick={async () => {
          await reload();
          dismiss();
        }}
      >
        Reload
      </button>
    </div>
  );
}
