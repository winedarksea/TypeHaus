import { useEffect, useState } from "react";
import { useStore } from "../state/store";
import type { Condition } from "../model/types";
import type { DetailIndexEntry } from "../engine/EngineClient";
import { DetailViewer } from "./DetailViewer";

// Details navigator (Phase 8): promotes derived boundary conditions (model.conditions) to
// first-class linked objects. The star is the engine's authored curation flag
// (Transition.star, served per detail by GET /details and written back through the normal
// PatchOp path) — starred details make the primary drawing export and read highlighted
// here. This replaced a localStorage-only state enum that never round-tripped.
export function DetailsNavigator() {
  const model = useStore((s) => s.model);
  const workspace = useStore((s) => s.activeWorkspace);
  const select = useStore((s) => s.select);
  const client = useStore((s) => s.client);
  const applyOps = useStore((s) => s.applyOps);
  const [details, setDetails] = useState<Record<string, DetailIndexEntry>>({});
  const [viewerOpen, setViewerOpen] = useState(false);
  const revision = model?.revision;

  useEffect(() => {
    let cancelled = false;
    client
      .getDetailIndex()
      .then((entries) => {
        if (cancelled) return;
        const byKey: Record<string, DetailIndexEntry> = {};
        for (const entry of entries) byKey[entry.key] = entry;
        setDetails(byKey);
      })
      .catch(() => {
        /* offline: no index — rows render without stars */
      });
    return () => {
      cancelled = true;
    };
  }, [client, revision]);

  // Only relevant in the DOCUMENT workspace.
  if (!model || workspace !== "document") return null;

  const conditions = model.conditions ?? [];

  // Jump to the first referenced element so the junction is visible on the canvas.
  const jump = (c: Condition) => {
    const tag = c.elements[0];
    const wall = model.walls.find((w) => w.tag === tag);
    if (wall) select("wall", wall.uid);
  };

  const toggleStar = async (entry: DetailIndexEntry) => {
    if (!entry.transition) return;
    const next = !entry.star;
    // Optimistic: flip locally, and flip every detail sharing the transition — the flag
    // lives on the Transition, so all of its condition keys star together.
    setDetails((prev) => {
      const updated: Record<string, DetailIndexEntry> = {};
      for (const [key, e] of Object.entries(prev)) {
        updated[key] = e.transition === entry.transition ? { ...e, star: next } : e;
      }
      return updated;
    });
    const ok = await applyOps([
      { op: "update", type: "Transition", tag: entry.transition, fields: { star: next } },
    ]);
    if (!ok) {
      setDetails((prev) => {
        const updated: Record<string, DetailIndexEntry> = {};
        for (const [key, e] of Object.entries(prev)) {
          updated[key] = e.transition === entry.transition ? { ...e, star: !next } : e;
        }
        return updated;
      });
    }
  };

  return (
    <div>
      <div className="drawer-header" style={{ marginTop: 8 }}>
        <h3 style={{ margin: 0 }}>Details · {conditions.length}</h3>
        <button className="btn" onClick={() => setViewerOpen(true)}>Open library…</button>
      </div>
      {conditions.length === 0 ? (
        <div className="muted">No transition details generated.</div>
      ) : (
        conditions.map((c) => {
          const entry = details[c.key];
          const starred = entry?.star ?? false;
          return (
            <div key={c.key} className={`detail-row${starred ? " detail-starred" : ""}`}>
              <button className="detail-jump" onClick={() => jump(c)} title="Show junction">
                <span className="detail-marker">D</span>
                <span className="detail-name">{c.kind}</span>
                <span className="muted">{c.elements.join(", ")}</span>
              </button>
              {entry?.transition && (
                <button
                  className="btn detail-star"
                  onClick={() => void toggleStar(entry)}
                  title={starred
                    ? "Starred: in the primary drawing export — click to unstar"
                    : "Star this detail into the primary drawing export"}
                  aria-pressed={starred}
                >
                  {starred ? "★" : "☆"}
                </button>
              )}
            </div>
          );
        })
      )}
      {viewerOpen && <DetailViewer onClose={() => setViewerOpen(false)} />}
    </div>
  );
}
