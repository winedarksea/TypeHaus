import { useMemo, useState } from "react";
import type { Inspection } from "../../model/scheduleTypes";
import { authorityOf, callWindowOpen, nextCallDate, readinessLabel, telHref }
  from "../../model/inspections";
import { uidByTag } from "../../model/tagIndex";
import { useStore } from "../../state/store";

const CHECK_DOT: Record<string, string> = {
  pass: "site-dot-done", fail: "site-dot-blocked",
  unknown: "site-dot-attention", not_applicable: "site-dot-na",
};

/**
 * One inspection: what is unmet, what the engine found, and the phone call.
 *
 * The engine checks are shown **including the passes**, unlike the design surface's findings
 * view which drops PASS and N/A. Before an inspection the green ones are the point: they are
 * what you tell the inspector you already looked at.
 */
export function InspectionDetail({ record }: { record: Inspection }) {
  const model = useStore((s) => s.model);
  const inspections = useStore((s) => s.inspections);
  const setInspection = useStore((s) => s.setInspection);
  const addAttempt = useStore((s) => s.addAttempt);
  const writable = useStore((s) => s.writable);
  const tickOnSite = useStore((s) => s.tickOnSite);
  const setSitePage = useStore((s) => s.setSitePage);
  const setSurface = useStore((s) => s.setSurface);
  const zoomToUid = useStore((s) => s.zoomToUid);

  const index = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const authority = authorityOf(inspections, record);
  const href = telHref(authority);
  const now = new Date();
  const open = callWindowOpen(now, authority?.window ?? null);
  const earliest = nextCallDate(now, authority);
  const today = now.toISOString().slice(0, 10);
  const entry = record.entry;
  // A date the owner PICKS, not a "today" stamp. The inspector came on Tuesday and this
  // gets filled in on Thursday about as often as not, and a stamped today is then a lie
  // in the one place the record has to be right.
  const [when, setWhen] = useState(today);
  const [corrections, setCorrections] = useState("");
  const [approved, setApproved] = useState("");

  const locate = (tag: string) => {
    const uid = index.get(tag);
    if (!uid) return;
    setSurface("design");
    zoomToUid(uid);
  };

  return (
    <div className="site-detail">
      <p className="site-chip">{readinessLabel(record)}</p>
      {record.applies !== true && record.evidence && (
        <p className="site-support">{record.evidence}</p>
      )}

      {/* The on-site items are deliberately excluded here: they are prerequisites, and they
          get their own checkbox section below, where they can actually be ticked. Listing
          them twice made the longest list on the page half a copy of the one under it. */}
      {record.prerequisites.some((p) => !p.met && p.kind !== "on_site") && (
        <section className="site-section">
          <h3 className="site-section-head">Before you can call</h3>
          <ul className="site-list">
            {record.prerequisites
              .filter((p) => !p.met && p.kind !== "on_site")
              .map((prerequisite, i) => (
              <li key={`${prerequisite.kind}:${prerequisite.ref ?? i}`} className="site-list-item">
                <span className="site-dot site-dot-blocked" aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{prerequisite.label}</span>
                  <span className="site-list-support">{prerequisite.kind.replace("_", " ")}</span>
                </span>
                {prerequisite.kind === "visit" && (
                  <button className="site-assist-chip" onClick={() => setSitePage("board")}>
                    Board
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {record.on_site.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">On site when they arrive</h3>
          <ul className="site-list">
            {record.on_site.map((item) => (
              <li key={item.label} className="site-list-item">
                <input
                  type="checkbox"
                  className="site-check"
                  checked={item.checked}
                  aria-label={item.label}
                  onChange={(e) => void tickOnSite(record.id, item.label, e.target.checked)}
                />
                <span className="site-list-text">
                  <span className="site-list-title">{item.label}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {record.checks.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">What the engine checked</h3>
          <ul className="site-list">
            {record.checks.map((check, i) => (
              <li key={`${check.check_id}:${i}`} className="site-list-item">
                <span className={`site-dot ${CHECK_DOT[check.result] ?? ""}`} aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{check.detail}</span>
                  <span className="site-list-support">{check.check_id}</span>
                  <span className="site-tag-row">
                    {check.element_tags.slice(0, 8).map((tag) => (
                      <button
                        key={tag}
                        className="site-tag"
                        disabled={!index.has(tag)}
                        onClick={() => locate(tag)}
                        title={index.has(tag) ? `Find ${tag} on the drawing` : tag}
                      >
                        {tag}
                      </button>
                    ))}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="site-section">
        <h3 className="site-section-head">{authority?.label ?? record.authority}</h3>
        {authority?.window && (
          <p className="site-support">
            {open === null ? authority.window
              : open ? `Calling now: ${authority.window}`
                : `Closed right now — ${authority.window}`}
            {earliest ? ` · earliest ${earliest}` : ""}
          </p>
        )}
        {href && <a className="site-assist-chip" href={href}>{authority?.phone}</a>}

        <div className="site-field-row">
          <label className="site-field">
            <span>Requested</span>
            <input
              type="date" className="site-input" value={entry?.requested ?? ""}
              disabled={!writable}
              onChange={(e) => void setInspection({ id: record.id,
                                                    requested: e.target.value || null })}
            />
          </label>
          <label className="site-field">
            <span>Appointment</span>
            <input
              type="date" className="site-input" value={entry?.scheduled ?? ""}
              disabled={!writable}
              onChange={(e) => void setInspection({ id: record.id,
                                                    scheduled: e.target.value || null })}
            />
          </label>
        </div>

        <div className="site-field-row">
          <label className="site-field">
            <span>Result date</span>
            <input type="date" className="site-input" value={when}
                   disabled={!writable}
                   onChange={(e) => setWhen(e.target.value)} />
          </label>
          <label className="site-field">
            <span>Corrections (one per line)</span>
            <textarea className="site-input" rows={2} value={corrections}
                      disabled={!writable}
                      onChange={(e) => setCorrections(e.target.value)} />
          </label>
          <label className="site-field">
            <span>Approved scope, for a partial (globs or visit slugs)</span>
            <input className="site-input" value={approved} disabled={!writable}
                   placeholder="FT-B-*"
                   onChange={(e) => setApproved(e.target.value)} />
          </label>
        </div>

        {/* Every one of these APPENDS an attempt. Nothing here overwrites the last card:
            the corrections a reinspection exists to answer live on the attempt that
            raised them, and a second call used to delete them. */}
        <div className="site-action-row">
          <button
            className="site-button" disabled={!writable}
            onClick={() => void addAttempt({ id: record.id, date: when, result: "pass" })}
          >
            Passed
          </button>
          <button
            className="site-button" disabled={!writable || !approved.trim()}
            title={approved.trim() ? "" : "A partial must name the scope it released"}
            onClick={() => void addAttempt({
              id: record.id, date: when, result: "partial",
              approved: approved.split(/[,\s]+/).filter(Boolean),
              corrections: corrections.split("\n").map((x) => x.trim()).filter(Boolean),
            })}
          >
            Partial
          </button>
          <button
            className="site-button site-button-danger" disabled={!writable}
            onClick={() => void addAttempt({
              id: record.id, date: when, result: "fail",
              corrections: corrections.split("\n").map((x) => x.trim()).filter(Boolean),
            })}
          >
            Failed
          </button>
        </div>

        {entry?.inspector && <p className="site-support">Inspector: {entry.inspector}</p>}
        {entry?.note && <p className="site-support">{entry.note}</p>}
        {entry?.waived && (
          <p className="site-support">
            Waived by {entry.waived.by}
            {entry.waived.date ? ` on ${entry.waived.date}` : ""}
            {entry.waived.ref ? ` (${entry.waived.ref})` : ""}
          </p>
        )}
        {record.scope.length > 0 && (
          <p className="site-support">This instance covers {record.scope.join(", ")}.</p>
        )}
        {record.approved.length > 0 && record.state !== "passed" && (
          <p className="site-support">
            Released so far: {record.approved.join(", ")} — every other visit stays blocked.
          </p>
        )}
      </section>

      {record.attempts.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">
            {record.attempts.length} attempt{record.attempts.length > 1 ? "s" : ""}
          </h3>
          <ul className="site-list">
            {record.attempts.map((attempt, i) => (
              <li key={`${attempt.date}:${i}`} className="site-list-item">
                <span className={`site-dot ${attempt.result === "pass"
                  ? "site-dot-done" : "site-dot-blocked"}`} aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">
                    {attempt.date} — {attempt.result}
                    {attempt.inspector ? ` · ${attempt.inspector}` : ""}
                  </span>
                  {attempt.corrections.map((line) => (
                    <span key={line} className="site-list-support">· {line}</span>
                  ))}
                  {attempt.approved.length > 0 && (
                    <span className="site-list-support">
                      released {attempt.approved.join(", ")}
                    </span>
                  )}
                  {attempt.note && (
                    <span className="site-list-support">{attempt.note}</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
