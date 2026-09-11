import { useMemo, useState } from "react";
import { groupInspectionsByMilestone, readinessLabel, requestable }
  from "../../model/inspections";
import { useStore } from "../../state/store";
import { DetailHost } from "./DetailHost";
import { InspectionDetail } from "./InspectionDetail";

const DOT: Record<string, string> = {
  passed: "site-dot-done", failed: "site-dot-blocked", scheduled: "site-dot-progress",
  requested: "site-dot-progress", ready: "site-dot-ready", not_ready: "site-dot-attention",
  not_applicable: "site-dot-na", waived: "site-dot-na",
};

const MILESTONE_LABELS: Record<string, string> = {
  foundation: "Foundation", weathertight: "Weathertight", rough_ins: "Rough-ins",
  insulated: "Insulated and closed up", final: "Final",
};

/** Every inspection, in the order the jurisdiction's own rule states them. */
export function InspectionsList() {
  const payload = useStore((s) => s.inspections);
  const [openId, setOpenId] = useState<string | null>(null);

  const groups = useMemo(() => groupInspectionsByMilestone(payload), [payload]);
  const open = payload?.inspections.find((record) => record.id === openId) ?? null;
  const ready = requestable(payload).filter((record) => !record.entry?.requested);

  if (!payload) {
    return <p className="site-support">No inspections yet. Start the engine with `haus serve`.</p>;
  }

  return (
    <div className="site-page">
      {groups.map((group) => (
        <section key={group.milestone} className="site-section">
          <h2 className="site-section-head">
            {MILESTONE_LABELS[group.milestone] ?? group.milestone}
          </h2>
          <ul className="site-list">
            {group.inspections.map((record) => (
              <li key={record.id} className="site-list-item">
                <span className={`site-dot ${DOT[record.state] ?? ""}`} aria-hidden />
                <button className="site-list-text" onClick={() => setOpenId(record.id)}>
                  <span className="site-list-title">
                    {record.sequence + 1}. {record.label}
                  </span>
                  <span className="site-list-support">{readinessLabel(record)}</span>
                </button>
                {/* The state electrical inspector is a different office from the city's,
                    and an owner who calls the wrong one loses a day. */}
                <span className={`site-authority-chip site-authority-${record.authority}`}>
                  {record.authority === "electrical" ? "State" : record.authority}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}

      {ready.length > 0 && (
        <button
          className="site-fab"
          onClick={() => setOpenId(ready[0].id)}
        >
          Request inspection
          <span className="site-fab-count">{ready.length}</span>
        </button>
      )}

      {open && (
        <DetailHost title={open.label} onClose={() => setOpenId(null)}>
          <InspectionDetail record={open} />
        </DetailHost>
      )}
    </div>
  );
}
