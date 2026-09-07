import { useEffect, useMemo, useState } from "react";
import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import { findSheet, groupSheets, nextSheet, prevSheet } from "../../model/sheets";
import type { SheetManifest } from "../../engine/EngineClient";
import { PdfPage } from "./PdfPage";

/**
 * The permit drawings: the sheet index on the left, the page on the right.
 *
 * The set is not composed here or on demand anywhere — `haus print` is gated on the permit
 * checklist, and a route or a button that rendered a set would be a second door around that
 * gate. This reads what `haus print` left in `out/`, and says so plainly when nothing is
 * there rather than offering a button that cannot work.
 */
export function DrawingsTab() {
  const client = useStore((s) => s.client);
  const selection = useStore((s) => s.documentsSelection);
  const openDocuments = useStore((s) => s.openDocuments);

  const [manifest, setManifest] = useState<SheetManifest | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setError(null);
    void (async () => {
      try {
        const found = await client.getSheets();
        if (live) setManifest(found);
      } catch (err) {
        if (live) setError(err instanceof Error ? err.message : String(err));
        return;
      }
      try {
        const pdf = await client.getArtifact("permit_pdf");
        if (live) setBlob(pdf);
      } catch (err) {
        if (live) setError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => { live = false; };
  }, [client]);

  const sheets = manifest?.sheets ?? [];
  const groups = useMemo(() => groupSheets(sheets), [sheets]);
  // The cover until something is picked: a set opens at page one.
  const active = findSheet(sheets, selection.sheet) ?? sheets[0] ?? null;

  const pick = (number: string) => openDocuments("drawings", { sheet: number,
    note: selection.note ?? undefined });

  if (error !== null) {
    return (
      <div className="muted" role="status">
        <p>{error}</p>
        <p>
          Run <code>haus print &lt;house&gt;</code> to compose the permit set. It refuses
          while the permit checklist has a failure or an unknown — which is the point: a set
          that does not pass should not exist.
        </p>
      </div>
    );
  }

  if (manifest === null) return <div className="muted">Looking for the drawing set…</div>;

  return (
    <div className="doc-split">
      <nav className="doc-list" aria-label="Sheet index">
        {groups.map((group) => (
          <div key={group.series}>
            <h4 className="doc-list-group-title">{group.label}</h4>
            {group.sheets.map((sheet) => (
              <button
                key={sheet.number}
                className={`doc-list-item${active?.number === sheet.number ? " active" : ""}`}
                aria-current={active?.number === sheet.number ? "true" : undefined}
                onClick={() => pick(sheet.number)}
              >
                <span className="doc-list-item-number">{sheet.number}</span>
                {sheet.title}
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="doc-detail">
        <div className="doc-detail-head">
          <h3 className="doc-detail-title">
            {active ? `${active.number} · ${active.title}` : "No sheets in this set"}
          </h3>
          {/* The stamp is the set's own, decided by the same gate that decided whether to
              print at all — never re-derived here, or the screen could claim a status the
              printed sheet does not carry. */}
          <span className="doc-stamp">{manifest.issue}</span>
        </div>

        <div className="doc-chip-row">
          <button className="btn" onClick={() => {
            const previous = prevSheet(sheets, active?.number ?? null);
            if (previous) pick(previous.number);
          }} disabled={!prevSheet(sheets, active?.number ?? null)}>
            <Icon name="arrow-left" size={16} /> Previous
          </button>
          <button className="btn" onClick={() => {
            const following = nextSheet(sheets, active?.number ?? null);
            if (following) pick(following.number);
          }} disabled={!nextSheet(sheets, active?.number ?? null)}>
            Next <Icon name="chevron-right" size={16} />
          </button>
          <span className="doc-meta">
            {active ? `page ${active.page} of ${sheets.length}` : "—"}
          </span>
          <span className="spacer" style={{ flex: 1 }} />
          <OpenPdfButton blob={blob} name={manifest.pdf} />
        </div>

        {active
          ? <PdfPage blob={blob} page={active.page}
              label={`Sheet ${active.number}, ${active.title}`} />
          : <div className="doc-pdf-empty">This set has no sheets.</div>}

        {/* Provenance, in the small print where a reader looks for it: which paper, printed
            when, and off which model. The hash is what makes a stale set visible — a
            drawing that disagrees with the plan on screen says so here. */}
        <p className="doc-meta">
          {manifest.paper} · printed {manifest.printed_at} · engine {manifest.engine_version}
          {" · model "}
          <span className="doc-meta-hash">{manifest.content_hash.slice(0, 12)}</span>
        </p>
      </div>
    </div>
  );
}

/** Opens the whole set in the browser's own PDF viewer — for printing, and for a reader who
 *  would rather page through it than click the index. */
function OpenPdfButton({ blob, name }: { blob: Blob | null; name: string }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!blob) return;
    const made = URL.createObjectURL(blob);
    setUrl(made);
    return () => { URL.revokeObjectURL(made); setUrl(null); };
  }, [blob]);
  if (!url) return null;
  return (
    <a className="btn" href={url} target="_blank" rel="noreferrer" title={`Open ${name}`}>
      <Icon name="open-in-new" size={16} /> Open PDF
    </a>
  );
}
