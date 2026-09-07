import { useEffect, useMemo, useState } from "react";
import { useStore } from "../../state/store";
import { groupNotes, matchesNote } from "../../model/notes";
import type { NoteEntry } from "../../engine/EngineClient";
import { MarkdownBody } from "./MarkdownBody";

/**
 * The house's design and product notes: why this connector, what the ERV was certified at,
 * which member the mill has to cut.
 *
 * The kinds down the left are the engine's, and they are derived from evidence rather than
 * from filenames (emit/notes_index.py) — a note a detail sheet prints is a construction note,
 * a note the engineering register names as an oracle is a calculation. So the chips that jump
 * to a drawing are not a guess: they are the same binding G-002's sheet-note index prints.
 */
export function NotesTab({ filter }: { filter: string }) {
  const client = useStore((s) => s.client);
  const selection = useStore((s) => s.documentsSelection);
  const openDocuments = useStore((s) => s.openDocuments);

  const [notes, setNotes] = useState<NoteEntry[] | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    void client.getNotes()
      .then((found) => { if (live) setNotes(found); })
      .catch((err) => { if (live) setError(err instanceof Error ? err.message : String(err)); });
    return () => { live = false; };
  }, [client]);

  const needle = filter.trim().toLowerCase();
  const shown = useMemo(
    () => (notes ?? []).filter((entry) => matchesNote(entry, needle)),
    [notes, needle],
  );
  const groups = useMemo(() => groupNotes(shown), [shown]);

  // The brief until something is picked — it is the one note that describes the whole house.
  const active = (notes ?? []).find((entry) => entry.path === selection.note)
    ?? shown[0] ?? null;

  useEffect(() => {
    let live = true;
    setMarkdown(null);
    if (!active) return;
    void client.getNote(active.path)
      .then((text) => { if (live) setMarkdown(text); })
      .catch(() => { if (live) setMarkdown(null); });
    return () => { live = false; };
  }, [client, active?.path]);

  if (error !== null) return <div className="muted" role="alert">{error}</div>;
  if (notes === null) return <div className="muted">Reading the house's notes…</div>;
  if (!notes.length) return <div className="muted">This house has no notes yet.</div>;

  return (
    <div className="doc-split">
      <nav className="doc-list" aria-label="Notes">
        {groups.map((group) => (
          <div key={group.kind}>
            <h4 className="doc-list-group-title">
              {group.label} <span className="doc-tab-count">{group.notes.length}</span>
            </h4>
            <p className="doc-list-group-note">{group.note}</p>
            {group.notes.map((entry) => (
              <button
                key={entry.path}
                className={`doc-list-item${active?.path === entry.path ? " active" : ""}`}
                aria-current={active?.path === entry.path ? "true" : undefined}
                onClick={() => openDocuments("notes", { note: entry.path,
                  sheet: selection.sheet ?? undefined })}
              >
                {entry.title}
                {entry.on_sheets.length > 0 && (
                  <span className="doc-list-item-sub">on {entry.on_sheets.join(", ")}</span>
                )}
              </button>
            ))}
          </div>
        ))}
        {!groups.length && <p className="muted">No note matches “{filter}”.</p>}
      </nav>

      <div className="doc-detail">
        {active && (
          <>
            <div className="doc-detail-head">
              <h3 className="doc-detail-title">{active.title}</h3>
              <span className="doc-meta doc-meta-hash">{active.path}</span>
            </div>
            {active.on_sheets.length > 0 && (
              <div className="doc-chip-row">
                <span className="doc-meta">Prints on</span>
                {active.on_sheets.map((sheet) => (
                  <button key={sheet} className="doc-chip"
                    title={`Open sheet ${sheet}`}
                    onClick={() => openDocuments("drawings", { sheet,
                      note: active.path })}>
                    {sheet}
                  </button>
                ))}
              </div>
            )}
            {markdown === null
              ? <div className="muted">Loading…</div>
              : <MarkdownBody markdown={markdown} titledAs={active.title} />}
          </>
        )}
      </div>
    </div>
  );
}
