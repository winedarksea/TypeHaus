import { useMemo, useState } from "react";
import { currentMilestone, firstBlockerLabel, groupByMilestone, nextVisit }
  from "../../model/schedule";
import { useStore } from "../../state/store";
import { DetailHost } from "./DetailHost";
import { NextVisitCard } from "./NextVisitCard";
import { VisitDetail } from "./VisitDetail";

const DOT: Record<string, string> = {
  ready: "site-dot-ready", blocked: "site-dot-blocked", in_progress: "site-dot-progress",
  done: "site-dot-done", verified: "site-dot-done",
};

/**
 * The build board: what is ready now, what is blocked and on what, grouped by milestone.
 *
 * The current milestone is expanded and the rest are collapsed, because the question an
 * owner-builder asks this screen is "what do I do today", not "show me the whole job".
 */
export function BuildBoard() {
  const schedule = useStore((s) => s.schedule);
  const [openSlug, setOpenSlug] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [milestoneFilter, setMilestoneFilter] = useState<string | null>(null);

  const groups = useMemo(() => groupByMilestone(schedule), [schedule]);
  const current = currentMilestone(schedule);
  const openVisit = schedule?.visits.find((visit) => visit.slug === openSlug) ?? null;

  if (!schedule) {
    return <p className="site-support">No board yet. Start the engine with `haus serve`.</p>;
  }

  return (
    <div className="site-page">
      <NextVisitCard visit={nextVisit(schedule)} onOpen={setOpenSlug} />

      <div className="site-chip-row" role="group" aria-label="Filter by milestone">
        <button
          className={`site-filter-chip${milestoneFilter === null ? " active" : ""}`}
          aria-pressed={milestoneFilter === null}
          onClick={() => setMilestoneFilter(null)}
        >
          All
        </button>
        {groups.map(({ milestone }) => (
          <button
            key={milestone.id}
            className={`site-filter-chip${milestoneFilter === milestone.id ? " active" : ""}`}
            aria-pressed={milestoneFilter === milestone.id}
            onClick={() => setMilestoneFilter(
              milestoneFilter === milestone.id ? null : milestone.id)}
          >
            {milestone.label}
          </button>
        ))}
      </div>

      {groups
        .filter(({ milestone }) => milestoneFilter === null || milestone.id === milestoneFilter)
        .map(({ milestone, ready, blocked, done }) => {
          const isOpen = expanded === null
            ? milestone.id === current || milestoneFilter === milestone.id
            : expanded === milestone.id;
          return (
            <section key={milestone.id} className="site-section">
              <button
                className="site-section-head site-section-toggle"
                aria-expanded={isOpen}
                onClick={() => setExpanded(isOpen ? "" : milestone.id)}
              >
                {milestone.label}
                <span className="site-list-support">
                  {milestone.state.replace("_", " ")} · {ready.length} ready ·{" "}
                  {blocked.length} blocked · {done.length} done
                </span>
              </button>

              {isOpen && (
                <>
                  {ready.length > 0 && (
                    <ul className="site-list">
                      {ready.map((visit) => (
                        <li key={visit.slug} className="site-list-item">
                          <span className={`site-dot ${DOT[visit.readiness]}`} aria-hidden />
                          <button className="site-list-text" onClick={() => setOpenSlug(visit.slug)}>
                            <span className="site-list-title">{visit.label}</span>
                            <span className="site-list-support">
                              {[visit.assignee, visit.scheduled].filter(Boolean).join(" · ")
                                || "Ready — nobody booked yet"}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}

                  {blocked.length > 0 && (
                    <ul className="site-list">
                      {blocked.map((visit) => (
                        <li key={visit.slug} className="site-list-item">
                          <span className="site-dot site-dot-blocked" aria-hidden />
                          <button className="site-list-text" onClick={() => setOpenSlug(visit.slug)}>
                            <span className="site-list-title">{visit.label}</span>
                            <span className="site-list-support">
                              {firstBlockerLabel(visit) ?? "blocked"}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}

                  {done.length > 0 && (
                    <details className="site-collapsed">
                      <summary>{done.length} done</summary>
                      <ul className="site-list">
                        {done.map((visit) => (
                          <li key={visit.slug} className="site-list-item">
                            <span className={`site-dot ${DOT[visit.readiness]}`} aria-hidden />
                            <button className="site-list-text" onClick={() => setOpenSlug(visit.slug)}>
                              <span className="site-list-title">{visit.label}</span>
                              <span className="site-list-support">{visit.readiness}</span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                </>
              )}
            </section>
          );
        })}

      {schedule.stale.length > 0 && (
        <p className="site-support site-stale-footer">
          Authored but no longer derived from the model: {schedule.stale.join(", ")}
        </p>
      )}

      {openVisit && (
        <DetailHost title={openVisit.label} onClose={() => setOpenSlug(null)}>
          <VisitDetail visit={openVisit} />
        </DetailHost>
      )}
    </div>
  );
}
