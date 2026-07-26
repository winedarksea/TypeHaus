import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { useStore } from "../state/store";
import type { DetailIndexEntry, DetailPayload } from "../engine/EngineClient";
import { DetailCanvas } from "./DetailCanvas";
import {
  detailAnnotationAnchor, newDetailAnnotationSpec, type DetailAnnotationAnchor,
} from "../model/detailAnnotations";

// The transition-details browser (→ 11b). A modal (AssemblyEditor pattern): a condition list
// grouped by junction kind with unbound/seed/authored badges, the DetailCanvas with pan/zoom,
// and a notes panel.
//
// Editing is a two-step contract, both steps riding the one journaled write path:
//   1. `seed_detail_annotations` mints an authored DetailAnnotation (the "Add note" field
//      below) — a detail's own seed callouts are drawn with `uid: null` and cannot be
//      addressed, so without this the editor has nothing to edit.
//   2. every later edit is a plain PatchOp on that element — the anchor-relative drag commits
//      as `update DetailAnnotation { offset }`, which the source writer serializes as a
//      canonical `pt(m(...))`.
// Both need the house to carry an editable `plan/details.py` holding a `DETAIL_NOTES` list;
// without one the coordinator has nowhere to write and the toast says so.

// `initialKey` is the condition key the caller wants on screen — a wall's own junction, the
// condition a transition details. Without it every entry point landed on `rows[0]`, so
// "view the detail for *this*" answered with somebody else's drawing. null/undefined keeps
// the old first-row behaviour for the callers that genuinely mean "open the library".
export function DetailViewer({ initialKey, onClose }: { initialKey?: string | null; onClose: () => void }) {
  const client = useStore((s) => s.client);
  const applyOps = useStore((s) => s.applyOps);
  const runMacro = useStore((s) => s.runMacro);
  const model = useStore((s) => s.model);
  const toast = useStore((s) => s.toast);
  // Refetch the drawing after any patch: a committed annotation drag bumps the revision, and
  // the fresh payload carries the persisted (anchor-relative) offset.
  const revision = useStore((s) => s.model?.revision);
  const [index, setIndex] = useState<DetailIndexEntry[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [payload, setPayload] = useState<DetailPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // Set when the caller asked for a key the index does not carry — an unbound condition
  // derives no detail at all (details.py skips conditions no transition matches), so the
  // viewer says which drawing it fell back to instead of silently showing the wrong one.
  const [missingKey, setMissingKey] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    client
      .getDetailIndex()
      .then((rows) => {
        if (!live) return;
        setIndex(rows);
        if (rows.length === 0) return;
        const wanted = initialKey ? rows.find((row) => row.key === initialKey) : undefined;
        setSelectedKey((wanted ?? rows[0]).key);
        if (initialKey && !wanted) setMissingKey(initialKey);
      })
      .catch((e: Error) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [client, initialKey]);

  // The modal owns Escape while it is open: the App-level chain closes the reader *underneath*
  // it (App.tsx Esc hierarchy), which would leave the drawing floating over a bare canvas.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      onClose();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  // Drop the old drawing when the user picks a different detail (but not on a same-key refetch).
  useEffect(() => { setPayload(null); }, [selectedKey]);

  useEffect(() => {
    if (!selectedKey) return;
    let live = true;
    setLoading(true);
    client
      .getDetail(selectedKey)
      // Keep the prior drawing on screen while a revision-triggered refetch is in flight — a
      // committed drag would otherwise flash the detail away and reset pan/zoom mid-edit.
      .then((p) => live && setPayload(p))
      .catch((e: Error) => live && setError(e.message))
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [client, selectedKey, revision]);

  const moveAnnotation = async (tag: string, offset: [number, number]): Promise<boolean> => {
    const ok = await applyOps([
      { op: "update", type: "DetailAnnotation", tag, fields: { offset } },
    ]);
    if (ok) toast(`${tag} moved`);
    return ok;
  };

  const selectedEntry = index.find((row) => row.key === selectedKey) ?? null;
  // Only offerable once the model is loaded and the detail cuts a wall we can anchor to.
  const anchor = model && selectedEntry
    ? detailAnnotationAnchor(model, selectedEntry.elements) : null;

  const addAnnotation = async (text: string): Promise<boolean> => {
    if (!selectedKey || !anchor) return false;
    const result = await runMacro({
      macro: "seed_detail_annotations",
      condition_key: selectedKey,
      annotations: [newDetailAnnotationSpec(anchor, text)],
    });
    if (result) toast("Note added — drag it to place it");
    return result !== null;
  };

  const grouped = useMemo(() => {
    const byKind = new Map<string, DetailIndexEntry[]>();
    for (const row of index) {
      const list = byKind.get(row.kind) ?? [];
      list.push(row);
      byKind.set(row.kind, list);
    }
    return [...byKind.entries()];
  }, [index]);

  // Portalled to <body>: opened from the assembly reader the modal would otherwise sit inside
  // `.workbench-backdrop`, whose `backdrop-filter` makes it the containing block for
  // position:fixed descendants — the drawing would be clipped into the reader's padding box
  // instead of covering the viewport.
  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ width: "90vw", height: "85vh", display: "flex" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ width: 260, overflowY: "auto", borderRight: "1px solid var(--panel-line)", paddingRight: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0 }}>Details</h3>
            <button className="btn" onClick={onClose}>Close</button>
          </div>
          {error && <div className="finding error">{error}</div>}
          {missingKey && (
            <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>
              No derived detail for <span className="reader-mono">{missingKey}</span> — no
              transition binds it. Showing the first detail instead.
            </div>
          )}
          {grouped.map(([kind, rows]) => (
            <div key={kind} style={{ marginTop: 10 }}>
              <div className="muted" style={{ textTransform: "uppercase", fontSize: 11 }}>{kind}</div>
              {rows.map((row) => (
                <div
                  key={row.key}
                  className="finding info"
                  // Opened at a key, the selected entry is usually far down a 43-row list;
                  // without this the drawing is right but the list looks untouched.
                  ref={row.key === selectedKey
                    ? (node) => node?.scrollIntoView({ block: "nearest" })
                    : undefined}
                  onClick={() => setSelectedKey(row.key)}
                  style={{ outline: row.key === selectedKey ? "2px solid var(--accent)" : "none", cursor: "pointer" }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 6 }}>
                    <span>{row.title}</span>
                    <span className={`badge ${row.state === "authored" ? "" : "confirm"}`}>{row.state}</span>
                  </div>
                  <span className="muted" style={{ fontSize: 11 }}>{row.elements.join(" · ")}</span>
                </div>
              ))}
            </div>
          ))}
        </div>

        <div style={{ flex: 1, display: "flex", flexDirection: "column", paddingLeft: 8 }}>
          <div style={{ flex: 1, minHeight: 0 }}>
            {loading && !payload && <div className="muted">Rendering…</div>}
            {payload && <DetailCanvas payload={payload} onMoveAnnotation={moveAnnotation} />}
          </div>
          {payload && <AddAnnotationBar anchor={anchor} onAdd={addAnnotation} />}
          {payload && <NotesPanel payload={payload} />}
        </div>
      </div>
    </div>,
    document.body,
  );
}

// The one authoring control the detail editor needs. A detail's own callouts are seeds with no
// uid, so this is how a drawing gets its first addressable — and therefore draggable —
// annotation. Disabled (with the reason shown) rather than hidden when the detail cuts nothing
// the anchor vocabulary can name.
function AddAnnotationBar({
  anchor,
  onAdd,
}: {
  anchor: DetailAnnotationAnchor | null;
  onAdd: (text: string) => Promise<boolean>;
}) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    const trimmed = text.trim();
    if (!trimmed || !anchor || busy) return;
    setBusy(true);
    const ok = await onAdd(trimmed);
    setBusy(false);
    if (ok) setText(""); // a failed write keeps the text so the user can retry
  };

  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center", paddingTop: 6 }}>
      <input
        style={{ flex: 1 }}
        placeholder={anchor ? "Add a note to this detail…" : "This detail cuts no anchorable wall"}
        value={text}
        disabled={!anchor || busy}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") void submit(); }}
        aria-label="New detail annotation"
      />
      <button className="btn" disabled={!anchor || busy || !text.trim()} onClick={() => void submit()}>
        {busy ? "Adding…" : "Add note"}
      </button>
    </div>
  );
}

function NotesPanel({ payload }: { payload: DetailPayload }) {
  return (
    <div style={{ maxHeight: 160, overflowY: "auto", borderTop: "1px solid var(--panel-line)", paddingTop: 6 }}>
      {payload.notes && <div className="muted" style={{ fontSize: 12 }}>Notes: {payload.notes}</div>}
      {payload.annotations.length > 0 ? (
        payload.annotations.map((a, i) => (
          <div key={i} className="finding info" style={{ fontSize: 12 }}>
            <b>{a.kind}</b> @ {a.anchor_face} — {a.text}
            {a.state !== "authored" && <span className="badge confirm" style={{ marginLeft: 6 }}>seed</span>}
          </div>
        ))
      ) : (
        <div className="muted" style={{ fontSize: 12 }}>No authored annotations — seed notes shown on the drawing.</div>
      )}
      {payload.findings.length > 0 &&
        payload.findings.map((f, i) => (
          <div key={`f${i}`} className="finding error" style={{ fontSize: 12 }}>{f.check_id}: {f.message}</div>
        ))}
    </div>
  );
}
