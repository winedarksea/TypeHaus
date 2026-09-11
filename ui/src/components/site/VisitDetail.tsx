import { useMemo } from "react";
import type { Visit } from "../../model/scheduleTypes";
import { attention, blockers, visitSheets } from "../../model/schedule";
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

  return (
    <div className="site-detail">
      <StatusSegmented visit={visit} onChange={(status) => void setVisit({ slug: visit.slug, status })} />

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
                  aria-label={constraint.label}
                  onChange={(e) => void clearConstraint(
                    visit.slug, constraint.label, e.target.checked ? today : null)}
                />
                <span className="site-list-text">
                  <span className="site-list-title">{constraint.label}</span>
                  {constraint.cleared && (
                    <span className="site-list-support">cleared {constraint.cleared}</span>
                  )}
                </span>
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
                  onChange={(e) => void tickItem(visit.slug, item.id, e.target.checked)}
                />
                <span className="site-list-text">
                  <span className="site-list-title">{item.label}</span>
                  {/* The provenance sentence is the item: several of these exist precisely
                      to say "the model knows the count and not the positions" out loud. */}
                  {item.derived && <span className="site-list-support">{item.derived}</span>}
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
