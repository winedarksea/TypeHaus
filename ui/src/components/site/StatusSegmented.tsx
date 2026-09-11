import type { Visit, VisitStatus } from "../../model/scheduleTypes";
import { statusTransitions } from "../../model/schedule";

/**
 * MD3 segmented button for a visit's status, at full touch height.
 *
 * `Verified` is disabled — with the reason on the button — while a hold the owner put on
 * themselves is still open. The engine refuses that write anyway; saying so here is the
 * same rule stated where a thumb can see it, rather than after a round trip.
 */
export function StatusSegmented({ visit, onChange }: {
  visit: Visit;
  onChange: (status: VisitStatus) => void;
}) {
  return (
    <div className="site-segmented" role="group" aria-label="Visit status">
      {statusTransitions(visit).map((transition) => {
        const selected = visit.status === transition.status;
        return (
          <button
            key={transition.status}
            className={`site-segment${selected ? " active" : ""}`}
            aria-pressed={selected}
            disabled={transition.disabledBecause !== null && !selected}
            title={transition.disabledBecause ?? transition.label}
            onClick={() => onChange(transition.status)}
          >
            {transition.label}
          </button>
        );
      })}
    </div>
  );
}
