import type { Inspection, Visit } from "../../model/scheduleTypes";
import { firstBlockerLabel, visitSheets } from "../../model/schedule";
import { authorityOf, requestable, telHref } from "../../model/inspections";
import { useStore } from "../../state/store";

/**
 * The top of the board: what to do next, in one card.
 *
 * Three things, in the order they cost you if you miss them. A visit the sub called done
 * but nobody walked is first — the crew is still reachable and the work is still visible.
 * Then the inspections you could phone in this morning, with the number. Then the sheets to
 * put in the truck.
 */
export function NextVisitCard({ visit, onOpen }: {
  visit: Visit | null;
  onOpen: (slug: string) => void;
}) {
  const inspections = useStore((s) => s.inspections);
  const setSitePage = useStore((s) => s.setSitePage);
  const ready: Inspection[] = requestable(inspections).filter(
    (record) => !record.entry?.requested);

  if (!visit && ready.length === 0) return null;

  const sheets = visit ? visitSheets(visit) : [];
  const blocker = visit ? firstBlockerLabel(visit) : null;

  return (
    <section className="site-card" aria-label="Next">
      <h2 className="site-card-head">Next</h2>

      {visit && (
        <button className="site-card-visit" onClick={() => onOpen(visit.slug)}>
          <span className="site-list-title">{visit.label}</span>
          <span className="site-list-support">
            {visit.readiness === "done"
              ? "The sub says it is finished — walk the handoff list"
              : visit.readiness === "in_progress"
                ? "On site now"
                : visit.readiness === "blocked"
                  ? `Nothing is ready yet. First: ${blocker ?? "unblock this visit"}`
                  : "Ready to book"}
          </span>
        </button>
      )}

      {ready.length > 0 && (
        <ul className="site-list">
          {ready.map((record) => {
            const authority = authorityOf(inspections, record);
            const href = telHref(authority);
            return (
              <li key={record.id} className="site-list-item">
                <span className="site-dot site-dot-ready" aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{record.label}</span>
                  <span className="site-list-support">
                    {authority?.label ?? record.authority}
                    {authority?.window ? ` · call ${authority.window}` : ""}
                    {authority?.lead_days
                      ? `, ${authority.lead_days} business day${authority.lead_days > 1 ? "s" : ""} ahead`
                      : ""}
                  </span>
                </span>
                {href ? (
                  <a className="site-assist-chip" href={href}>{authority?.phone}</a>
                ) : (
                  <button className="site-assist-chip" onClick={() => setSitePage("inspections")}>
                    Open
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {sheets.length > 0 && (
        <p className="site-support">Sheets to bring: {sheets.join(", ")}</p>
      )}
    </section>
  );
}
