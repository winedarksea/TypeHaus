import type { Visit, VisitStatus } from "../../model/scheduleTypes";
import { statusTransitions } from "../../model/schedule";
import { useStore } from "../../state/store";

/**
 * MD3 segmented button for a visit's status, at full touch height.
 *
 * `Verified` is disabled — with the reason on the button — while a hold the owner put on
 * themselves is still open. The engine refuses that write anyway; saying so here is the
 * same rule stated where a thumb can see it, rather than after a round trip.
 *
 * The whole group is disabled on an offline snapshot: a status recorded against a cached
 * payload lands nowhere, and painting it optimistically would tell the owner they had
 * recorded something.
 */
export function StatusSegmented({ visit, onChange }: {
  visit: Visit;
  onChange: (status: VisitStatus) => void;
}) {
  const writable = useStore((s) => s.writable);
  return (
    <div className="site-segmented" role="group" aria-label="Visit status">
      {statusTransitions(visit).map((transition) => {
        const selected = visit.status === transition.status;
        return (
          <button
            key={transition.status}
            className={`site-segment${selected ? " active" : ""}`}
            aria-pressed={selected}
            disabled={!writable || (transition.disabledBecause !== null && !selected)}
            title={!writable ? "Offline snapshot — reconnect to record anything"
                             : transition.disabledBecause ?? transition.label}
            onClick={() => onChange(transition.status)}
          >
            {transition.label}
          </button>
        );
      })}
    </div>
  );
}
