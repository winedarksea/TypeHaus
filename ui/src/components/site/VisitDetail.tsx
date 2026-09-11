import { useMemo } from "react";
import type { Visit } from "../../model/scheduleTypes";
import { attention, blockers, visitSheets } from "../../model/schedule";
import { ArrivalBrief } from "./ArrivalBrief";
import { uidByTag } from "../../model/tagIndex";
import { useStore } from "../../state/store";
import { StatusSegmented } from "./StatusSegmented";

/**
 * The arrival package: everything the owner needs in hand when this sub turns up, and the
 * checklist they walk afterwards.
 *
 * Shared by the bottom sheet and the side sheet (→ DetailHost). Click-to-locate crosses back
 * to the design surface: a handoff item names elements, and "where is that" is a question
 * only the drawing answers.
 */
export function VisitDetail({ visit }: { visit: Visit }) {
  const model = useStore((s) => s.model);
  const setVisit = useStore((s) => s.setVisit);
  const tickItem = useStore((s) => s.tickItem);
  const clearConstraint = useStore((s) => s.clearConstraint);
  const setCheckpoint = useStore((s) => s.setCheckpoint);
  const addException = useStore((s) => s.addException);
  const writable = useStore((s) => s.writable);
  const contractors = useStore((s) => s.schedule?.contractors ?? {});
  const setSurface = useStore((s) => s.setSurface);
  const setSitePage = useStore((s) => s.setSitePage);
  const zoomToUid = useStore((s) => s.zoomToUid);
  const openDocuments = useStore((s) => s.openDocuments);

  const index = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const today = new Date().toISOString().slice(0, 10);

  const locate = (tag: string) => {
    const uid = index.get(tag);
    if (!uid) return;
    setSurface("design");
    zoomToUid(uid);
  };

  const sheets = visitSheets(visit);
  const open = blockers(visit);
  const soft = attention(visit);
  const authored = visit.constraints.filter((c) => c.kind === "authored");
  const contractor = visit.contractor ? contractors[visit.contractor] : undefined;
  const dates = visit.dates;

  return (
    <div className="site-detail">
      {/* Exceptions first, always. "We went ahead against an open hold" outranks every
          other line on this visit, and the hold it names is still open. */}
      {visit.exceptions.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">Went ahead anyway</h3>
          <ul className="site-list">
            {visit.exceptions.map((item, i) => (
              <li key={`${item.at}:${i}`} className="site-list-item">
                <span className="site-dot site-dot-blocked" aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{item.hold}</span>
                  <span className="site-list-support">
                    {item.at}{item.note ? ` — ${item.note}` : ""}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {visit.needs_rewalk && (
        <p className="site-chip site-chip-warn">
          The handoff set changed under existing ticks — walk it again.
          {visit.orphan_ticks.length > 0
            && ` ${visit.orphan_ticks.length} tick(s) name nothing this model derives.`}
        </p>
      )}

      {visit.checkpoints.length === 0 ? (
        <StatusSegmented visit={visit} onChange={(status) => void setVisit({ slug: visit.slug, status })} />
      ) : (
        <section className="site-section">
          <h3 className="site-section-head">Checkpoints</h3>
          {/* The visit's own status DERIVES from these, which is why there is no status
              row above: writing both would be two ladders again. */}
          <ul className="site-list">
            {visit.checkpoints.map((point) => (
              <li key={point.id} className="site-list-item">
                <span className={`site-dot ${point.status === "done" ? "site-dot-done"
                  : point.status === "in_progress" ? "site-dot-progress" : ""}`} aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{point.label || point.id}</span>
                  <span className="site-list-support">
                    {point.after.length > 0 ? `after ${point.after.join(", ")}` : ""}
                    {point.cure_days ? ` · ${point.cure_days} day cure` : ""}
                  </span>
                </span>
                <select
                  className="site-input" value={point.status} disabled={!writable}
                  aria-label={`${point.label || point.id} status`}
                  onChange={(e) => void setCheckpoint(
                    visit.slug, point.id,
                    e.target.value as "todo" | "in_progress" | "done")}
                >
                  <option value="todo">To do</option>
                  <option value="in_progress">On site</option>
                  <option value="done">Done</option>
                </select>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="site-field-row">
        <label className="site-field">
          <span>Planned</span>
          <input type="date" className="site-input" value={visit.planned ?? ""}
                 disabled={!writable}
                 onChange={(e) => void setVisit({ slug: visit.slug,
                                                  planned: e.target.value || null })} />
        </label>
        <label className="site-field">
          <span>Booked</span>
          <input type="date" className="site-input" value={visit.booked?.date ?? ""}
                 disabled={!writable}
                 onChange={(e) => void setVisit({
                   slug: visit.slug,
                   booked: e.target.value
                     ? { date: e.target.value, window: visit.booked?.window ?? null,
                         confirmed_by: visit.booked?.confirmed_by ?? null,
                         confirmed_at: new Date().toISOString().slice(0, 10),
                         note: visit.booked?.note ?? null }
                     : null })} />
        </label>
        <label className="site-field">
          <span>Days on site</span>
          <input type="number" min={1} className="site-input"
                 value={visit.duration_days ?? ""} disabled={!writable}
                 onChange={(e) => void setVisit({
                   slug: visit.slug,
                   duration_days: e.target.value ? Number(e.target.value) : null })} />
        </label>
      </div>

      <p className="site-support">
        {dates.suggested_start
          ? `Earliest ${dates.suggested_start} to ${dates.suggested_finish}`
          : dates.why || "Needs confirmation — nobody has said how long this takes."}
        {dates.threatened_by_days
          ? ` · booking THREATENED by ${dates.threatened_by_days} day(s) — the engine will not move it`
          : ""}
      </p>

      <dl className="site-facts">
        {visit.assignee && (
          <div><dt>Sub</dt><dd>{visit.assignee}</dd></div>
        )}
        {visit.contact && (
          <div>
            <dt>Contact</dt>
            <dd><a href={`tel:${visit.contact.replace(/[^\d+]/g, "")}`}>{visit.contact}</a></dd>
          </div>
        )}
        {visit.scheduled && <div><dt>Scheduled</dt><dd>{visit.scheduled}</dd></div>}
        {visit.estimate_fmt && <div><dt>Estimate</dt><dd>{visit.estimate_fmt}</dd></div>}
      </dl>

      {visit.holdback_open && (
        <p className="site-chip site-chip-warn">
          Verified, gate passed, holdback open — some rows are billed and unpaid.
        </p>
      )}

      {open.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">In the way</h3>
          <ul className="site-list">
            {open.map((constraint, i) => (
              <li key={`${constraint.kind}:${constraint.ref ?? i}`} className="site-list-item">
                <span className="site-dot site-dot-blocked" aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{constraint.label}</span>
                  <span className="site-list-support">
                    {constraint.kind === "inspection" ? "inspection" : constraint.kind}
                  </span>
                </span>
                {constraint.kind === "inspection" && (
                  <button className="site-assist-chip" onClick={() => setSitePage("inspections")}>
                    Open
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {authored.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">Holds you put on yourself</h3>
          <ul className="site-list">
            {authored.map((constraint) => (
              <li key={constraint.label} className="site-list-item">
                <input
                  type="checkbox"
                  className="site-check"
                  checked={constraint.cleared !== null}
                  disabled={!writable || constraint.ticket_kind === "locate"}
                  aria-label={constraint.label}
                  title={constraint.ticket_kind === "locate"
                    ? "A locate ticket is its own clearance — it arms and lapses by statute"
                    : ""}
                  onChange={(e) => void clearConstraint(
                    visit.slug, constraint.label, e.target.checked ? today : null)}
                />
                <span className="site-list-text">
                  <span className="site-list-title">{constraint.label}</span>
                  {(constraint.owner || constraint.next_action || constraint.follow_up) && (
                    <span className="site-list-support">
                      {[constraint.owner ? `on ${constraint.owner}` : "",
                        constraint.next_action,
                        constraint.follow_up ? `chase ${constraint.follow_up}` : ""]
                        .filter(Boolean).join(" · ")}
                    </span>
                  )}
                  {constraint.derived && (
                    <span className="site-list-support">{constraint.derived}</span>
                  )}
                  {constraint.cleared && (
                    <span className="site-list-support">cleared {constraint.cleared}</span>
                  )}
                </span>
                {constraint.cleared === null && constraint.severity === "blocking"
                  && (visit.readiness === "done" || visit.readiness === "in_progress") && (
                  <button
                    className="site-assist-chip" disabled={!writable}
                    title="Record that the work went ahead against this hold. The hold stays open."
                    onClick={() => void addException(
                      visit.slug, constraint.label, "went ahead on site")}
                  >
                    Went ahead
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {visit.handoff.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">Leave in place</h3>
          <ul className="site-list">
            {visit.handoff.map((item) => (
              <li key={item.id} className="site-list-item">
                <input
                  type="checkbox"
                  className="site-check"
                  checked={item.checked}
                  aria-label={item.label}
                  disabled={!writable}
                  onChange={(e) => void tickItem(visit.slug, item.id, e.target.checked)}
                />
                <span className="site-list-text">
                  <span className="site-list-title">{item.label}</span>
                  {/* The provenance sentence is the item: several of these exist precisely
                      to say "the model knows the count and not the positions" out loud. */}
                  {item.derived && <span className="site-list-support">{item.derived}</span>}
                  {visit.skipped.find((x) => x.id === item.id) && (
                    <span className="site-list-support">
                      skipped: {visit.skipped.find((x) => x.id === item.id)!.reason}
                    </span>
                  )}
                  <span className="site-tag-row">
                    {item.element_tags.slice(0, 8).map((tag) => (
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
                    {item.sheet_ref && (
                      <button
                        className="site-assist-chip"
                        onClick={() => {
                          setSurface("design");
                          openDocuments("drawings", { sheet: item.sheet_ref! });
                        }}
                      >
                        Open {item.sheet_ref}
                      </button>
                    )}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {soft.length > 0 && (
        <section className="site-section">
          <h3 className="site-section-head">Worth a look — not blocking</h3>
          <ul className="site-list">
            {soft.map((constraint, i) => (
              <li key={`${constraint.ref ?? ""}:${i}`} className="site-list-item">
                <span className="site-dot site-dot-attention" aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{constraint.label}</span>
                  <span className="site-list-support">{constraint.ref}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {(visit.materials.length > 0 || dates.materials.length > 0) && (
        <section className="site-section">
          <h3 className="site-section-head">On site before they arrive</h3>
          <ul className="site-list">
            {(dates.materials.length ? dates.materials : visit.materials).map((item) => (
              <li key={item.id} className="site-list-item">
                <span className={`site-dot ${item.received ? "site-dot-done"
                  : item.why ? "site-dot-attention" : ""}`} aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{item.label || item.id}</span>
                  <span className="site-list-support">
                    {item.received ? `received ${item.received}`
                      : item.why ? item.why
                        : item.order_by ? `order by ${item.order_by}`
                          : item.expected ? `expected ${item.expected} — not a delivery yet`
                            : "not ordered"}
                    {item.source ? ` · ${item.source}` : ""}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {contractor && (
        <section className="site-section">
          <h3 className="site-section-head">{contractor.name}</h3>
          <p className="site-support">
            {[contractor.phone, contractor.email, contractor.trades.join(", ")]
              .filter(Boolean).join(" · ")}
          </p>
          {contractor.missing_documents.length > 0 && (
            <p className="site-chip site-chip-warn">
              Missing: {contractor.missing_documents.join(", ")} — worth chasing, never a
              reason to turn a good sub away.
            </p>
          )}
        </section>
      )}

      {visit.readiness === "verified" && (
        <section className="site-section">
          <h3 className="site-section-head">Before you pay</h3>
          {/* Attention ticks, not blocks, and no dollars: the money lives in costs.toml. */}
          <ul className="site-list">
            {["invoice matches the verified scope", "lien waiver received"].map((label) => (
              <li key={label} className="site-list-item">
                <span className="site-dot site-dot-attention" aria-hidden />
                <span className="site-list-text">
                  <span className="site-list-title">{label}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <ArrivalBrief visit={visit} sheets={sheets} contractorName={contractor?.name ?? null} />

      {sheets.length > 0 && (
        <p className="site-support">Bring: {sheets.join(", ")}</p>
      )}

      {visit.rows.length > 0 && (
        <button
          className="site-assist-chip"
          onClick={() => { setSurface("design"); useStore.getState().setDetailView("bom"); }}
        >
          Open {visit.rows.length} row(s) in the BOM
        </button>
      )}

      {visit.implicit && (
        <p className="site-support">
          Nobody has split this package into arrivals yet. Run{" "}
          <code>haus schedule --propose {visit.package}</code> and paste what you accept into
          tasks.toml — the engine proposes, you commit.
        </p>
      )}

      {visit.note && <p className="site-support">{visit.note}</p>}
    </div>
  );
}
