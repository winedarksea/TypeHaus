import { useState } from "react";
import { useStore } from "../state/store";
import { visibleFindings } from "../state/locate";
import type { Finding, Severity } from "../model/types";
import { Icon } from "../icons/Icon";

// Issue states are UI metadata layered over the engine's Finding (which has no such notion).
// Persisted to localStorage, keyed by a stable identity derived from the finding.
type IssueState = "open" | "acknowledged" | "resolved" | "waived" | "n-a" | "stale";
const STATES: IssueState[] = ["open", "acknowledged", "resolved", "waived", "n-a", "stale"];
const ISSUE_STATE_KEY = "typehaus.issue-states";

function findingKey(f: Finding): string {
  return `${f.code ?? f.message}::${f.element ?? f.elements?.[0] ?? ""}`;
}

function loadStates(): Record<string, IssueState> {
  try {
    return JSON.parse(window.localStorage.getItem(ISSUE_STATE_KEY) ?? "{}");
  } catch {
    return {};
  }
}

const SEVERITY_ORDER: Severity[] = ["error", "warn", "info"];
const SEVERITY_LABEL: Record<Severity, string> = { error: "Errors", warn: "Warnings", info: "Advisories" };

export function IssuesDrawer() {
  const open = useStore((s) => s.activePanel === "issues");
  const setActivePanel = useStore((s) => s.setActivePanel);
  // Set when another surface opened this drawer *about* a severity (the load-error banner).
  // Always visible and always clearable — a filter you can't see is a drawer that looks empty.
  const severityFilter = useStore((s) => s.issuesSeverityFilter);
  const openIssues = useStore((s) => s.openIssues);
  const model = useStore((s) => s.model);
  const zoomToUid = useStore((s) => s.zoomToUid);
  const [states, setStates] = useState<Record<string, IssueState>>(loadStates);

  if (!open) return null;

  const findings = model ? visibleFindings(model.findings) : [];
  const stateOf = (f: Finding): IssueState => states[findingKey(f)] ?? "open";
  const setState = (f: Finding, next: IssueState) => {
    const updated = { ...states, [findingKey(f)]: next };
    setStates(updated);
    try {
      window.localStorage.setItem(ISSUE_STATE_KEY, JSON.stringify(updated));
    } catch {
      /* private browsing */
    }
  };

  const jump = (f: Finding) => {
    const uid = f.element ?? f.elements?.[0] ?? null;
    if (uid) zoomToUid(uid);
  };

  const grouped = SEVERITY_ORDER.filter((sev) => !severityFilter || sev === severityFilter)
    .map((sev) => ({
      sev,
      items: findings.filter((f) => f.severity === sev),
    })).filter((g) => g.items.length > 0);

  return (
    <div className="issues-drawer" role="region" aria-label="Issues">
      <div className="issues-header">
        <h3 style={{ margin: 0 }}>Issues · {findings.length}</h3>
        <button className="btn" onClick={() => setActivePanel(null)} title="Collapse issues">
          <Icon name="close" />
        </button>
      </div>
      {severityFilter && (
        <div className="issues-filter">
          Showing {SEVERITY_LABEL[severityFilter].toLowerCase()} only
          <button className="btn" onClick={() => openIssues(null)}>Show all</button>
        </div>
      )}
      <div className="issues-body">
        {grouped.length === 0 && <div className="muted" style={{ padding: 12 }}>
          {severityFilter ? `No ${SEVERITY_LABEL[severityFilter].toLowerCase()}.` : "All checks pass."}
        </div>}
        {grouped.map((g) => (
          <div key={g.sev} className="issues-group">
            <div className={`issues-group-head sev-${g.sev}`}>
              {SEVERITY_LABEL[g.sev]} · {g.items.length}
            </div>
            {g.items.map((f, i) => {
              const st = stateOf(f);
              return (
                <div key={i} className={`issue-row state-${st}`}>
                  <button className="issue-jump" onClick={() => jump(f)} title="Zoom to element">
                    <span className={`sev-dot sev-${g.sev}`} aria-hidden />
                    <span className="issue-text">
                      {f.code && <b>{f.code} </b>}
                      {f.message}
                    </span>
                  </button>
                  <select
                    className="issue-state"
                    value={st}
                    onChange={(e) => setState(f, e.target.value as IssueState)}
                    aria-label="Issue state"
                  >
                    {STATES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
