import { useState } from "react";
import { useStore } from "../state/store";
import type { Condition } from "../model/types";
import { DetailViewer } from "./DetailViewer";

// Details navigator (Phase 8): promotes derived boundary conditions (model.conditions) to
// first-class linked objects. State is UI metadata (no engine field), persisted locally and
// keyed by condition.key. Reuses DetailViewer for the focused detail drawing.
type DetailState = "assigned" | "missing" | "draft" | "overridden" | "stale" | "conflicting";
const STATES: DetailState[] = ["assigned", "missing", "draft", "overridden", "stale", "conflicting"];
const DETAIL_STATE_KEY = "typehaus.detail-states";

function loadStates(): Record<string, DetailState> {
  try {
    return JSON.parse(window.localStorage.getItem(DETAIL_STATE_KEY) ?? "{}");
  } catch {
    return {};
  }
}

export function DetailsNavigator() {
  const model = useStore((s) => s.model);
  const workspace = useStore((s) => s.activeWorkspace);
  const select = useStore((s) => s.select);
  const [states, setStates] = useState<Record<string, DetailState>>(loadStates);
  const [viewerOpen, setViewerOpen] = useState(false);

  // Only relevant in the DOCUMENT workspace.
  if (!model || workspace !== "document") return null;

  const conditions = model.conditions ?? [];
  const stateOf = (c: Condition): DetailState => states[c.key] ?? "assigned";
  const setState = (c: Condition, next: DetailState) => {
    const updated = { ...states, [c.key]: next };
    setStates(updated);
    try {
      window.localStorage.setItem(DETAIL_STATE_KEY, JSON.stringify(updated));
    } catch {
      /* private browsing */
    }
  };

  // Jump to the first referenced element so the junction is visible on the canvas.
  const jump = (c: Condition) => {
    const tag = c.elements[0];
    const wall = model.walls.find((w) => w.tag === tag);
    if (wall) select("wall", wall.uid);
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
        conditions.map((c) => (
          <div key={c.key} className={`detail-row detail-${stateOf(c)}`}>
            <button className="detail-jump" onClick={() => jump(c)} title="Show junction">
              <span className="detail-marker">D</span>
              <span className="detail-name">{c.kind}</span>
              <span className="muted">{c.elements.join(", ")}</span>
            </button>
            <select
              className="issue-state"
              value={stateOf(c)}
              onChange={(e) => setState(c, e.target.value as DetailState)}
              aria-label="Detail state"
            >
              {STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        ))
      )}
      {viewerOpen && <DetailViewer onClose={() => setViewerOpen(false)} />}
    </div>
  );
}
