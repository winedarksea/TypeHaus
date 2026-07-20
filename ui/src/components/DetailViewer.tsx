import { useEffect, useMemo, useState } from "react";
import { useStore } from "../state/store";
import type { DetailIndexEntry, DetailPayload } from "../engine/EngineClient";
import { DetailCanvas } from "./DetailCanvas";

// The transition-details browser (→ 11b). A modal (AssemblyEditor pattern): a condition list
// grouped by junction kind with unbound/seed/authored badges, the DetailCanvas with pan/zoom,
// and a notes panel. v1 is read-only; the editor later re-uses the same scene contract —
// hit a node → its DetailAnnotation uid → a plain patchPlan update of offset/text.

export function DetailViewer({ onClose }: { onClose: () => void }) {
  const client = useStore((s) => s.client);
  const [index, setIndex] = useState<DetailIndexEntry[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [payload, setPayload] = useState<DetailPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let live = true;
    client
      .getDetailIndex()
      .then((rows) => {
        if (!live) return;
        setIndex(rows);
        if (rows.length > 0) setSelectedKey(rows[0].key);
      })
      .catch((e: Error) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [client]);

  useEffect(() => {
    if (!selectedKey) return;
    let live = true;
    setLoading(true);
    setPayload(null);
    client
      .getDetail(selectedKey)
      .then((p) => live && setPayload(p))
      .catch((e: Error) => live && setError(e.message))
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [client, selectedKey]);

  const grouped = useMemo(() => {
    const byKind = new Map<string, DetailIndexEntry[]>();
    for (const row of index) {
      const list = byKind.get(row.kind) ?? [];
      list.push(row);
      byKind.set(row.kind, list);
    }
    return [...byKind.entries()];
  }, [index]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ width: "90vw", height: "85vh", display: "flex" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ width: 260, overflowY: "auto", borderRight: "1px solid var(--panel-line)", paddingRight: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0 }}>Details</h3>
            <button className="btn" onClick={onClose}>Close</button>
          </div>
          {error && <div className="finding error">{error}</div>}
          {grouped.map(([kind, rows]) => (
            <div key={kind} style={{ marginTop: 10 }}>
              <div className="muted" style={{ textTransform: "uppercase", fontSize: 11 }}>{kind}</div>
              {rows.map((row) => (
                <div
                  key={row.key}
                  className="finding info"
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
            {loading && <div className="muted">Rendering…</div>}
            {payload && <DetailCanvas payload={payload} />}
          </div>
          {payload && <NotesPanel payload={payload} />}
        </div>
      </div>
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
