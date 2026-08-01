import { useEffect, useRef } from "react";
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

// Error-severity findings are the loader saying part of the plan did not resolve — the model
// on screen is *incomplete*, not merely imperfect. That deserves the same weight as a
// conflict: a persistent banner, not a line buried in a collapsed drawer the user may never
// open. Errors are dismissed by fixing the plan, so there is no dismiss button; the banner
// clears itself when the next revision resolves clean.
export function LoadErrorBanner() {
  const model = useStore((s) => s.model);
  const openIssues = useStore((s) => s.openIssues);
  const toast = useStore((s) => s.toast);
  // A toast per render would be a strobe light — one per revision is the honest cadence:
  // it fires when the errors are *new*, and stays quiet while they persist unchanged.
  const toasted = useRef<string | null>(null);

  const errors = (model?.findings ?? []).filter((f) => f.severity === "error");
  const revision = model?.revision ?? null;

  useEffect(() => {
    if (!revision || errors.length === 0 || toasted.current === revision) return;
    toasted.current = revision;
    toast(`${errors.length} error${errors.length === 1 ? "" : "s"} loading the plan`, "error");
  }, [revision, errors.length, toast]);

  if (errors.length === 0) return null;
  return (
    <div className="banner">
      <span>
        ⚠ {errors.length} error{errors.length === 1 ? "" : "s"} while loading the plan — parts of
        the model may be missing or unresolved.
      </span>
      <button className="btn" onClick={() => openIssues("error")}>Show errors</button>
    </div>
  );
}
