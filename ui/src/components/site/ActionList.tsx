import { useMemo, useState } from "react";
import { actionList, type ActionUrgency } from "../../model/schedule";
import { useStore } from "../../state/store";

const HEADS: Record<ActionUrgency, string> = {
  now: "Now",
  today: "Today",
  soon: "Coming up",
  release: "What releases them",
};

const DOT: Record<ActionUrgency, string> = {
  now: "site-dot-blocked", today: "site-dot-ready",
  soon: "site-dot-progress", release: "site-dot-attention",
};

/**
 * The top of the board: everything standing on the owner, worst first.
 *
 * This replaces "Next visit", which answered a question the board could not answer. On a
 * house with nothing ready it showed the first blocked visit — where you are going, not
 * what to do — and on a house mid-build it showed one thing while four others were on fire.
 */
export function ActionList({ onOpen }: { onOpen: (slug: string) => void }) {
  const schedule = useStore((s) => s.schedule);
  const inspections = useStore((s) => s.inspections);
  const setSitePage = useStore((s) => s.setSitePage);
  const [lookahead, setLookahead] = useState(14);

  const actions = useMemo(
    () => actionList(schedule, inspections, new Date(), lookahead),
    [schedule, inspections, lookahead]);

  if (actions.length === 0) {
    return (
      <section className="site-card" aria-label="Actions">
        <h2 className="site-card-head">Nothing is on you right now</h2>
        <p className="site-support">
          No exceptions, no expiring locates, no threatened bookings and nothing booked
          today. Open a milestone below to see what is waiting.
        </p>
      </section>
    );
  }

  const groups: ActionUrgency[] = ["now", "today", "soon", "release"];
  return (
    <section className="site-card" aria-label="Actions">
      <h2 className="site-card-head">
        What is on you
        <label className="site-list-support">
          {" "}lookahead{" "}
          <select
            className="site-input" value={lookahead}
            aria-label="Lookahead window in days"
            onChange={(e) => setLookahead(Number(e.target.value))}
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
        </label>
      </h2>
      {groups.map((urgency) => {
        const rows = actions.filter((action) => action.urgency === urgency);
        if (rows.length === 0) return null;
        return (
          <div key={urgency}>
            <h3 className="site-section-head">{HEADS[urgency]}</h3>
            <ul className="site-list">
              {rows.map((action) => (
                <li key={action.id} className="site-list-item">
                  <span className={`site-dot ${DOT[urgency]}`} aria-hidden />
                  <button
                    className="site-list-text"
                    onClick={() => {
                      if (action.slug) onOpen(action.slug);
                      else setSitePage("inspections");
                    }}
                  >
                    <span className="site-list-title">{action.title}</span>
                    <span className="site-list-support">{action.detail}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
