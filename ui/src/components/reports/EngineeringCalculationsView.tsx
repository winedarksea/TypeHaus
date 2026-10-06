import { useEffect, useMemo, useState } from "react";
import { useStore } from "../../state/store";
import type { EngineeringCalculations } from "../../engine/engineeringTypes";
import { loadEngineeringCalculations } from "../../engine/engineeringCache";
import { calculationGroups, matchesCalculation, selectedCalculation, type CalculationPage } from "../../model/calculationNavigation";
import { ReaderFilter, ReaderShell } from "../ReaderShell";
import { MarkdownBody } from "../documents/MarkdownBody";
import { useIsCompact } from "../../hooks/useBreakpoint";

export function EngineeringCalculationsView() {
  const model = useStore((state) => state.model);
  const client = useStore((state) => state.client);
  const close = useStore((state) => state.closeReader);
  const reload = useStore((state) => state.reloadIfStale);
  const [payload, setPayload] = useState<EngineeringCalculations | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [selected, setSelected] = useState("00-cover.md");
  const [filter, setFilter] = useState("");
  const compact = useIsCompact();
  const [navigationOpen, setNavigationOpen] = useState(false);
  const revision = model?.revision;

  useEffect(() => {
    let live = true;
    setPayload(null);
    setError(null);
    if (!revision) return;
    void loadEngineeringCalculations(client, revision).then(async (result) => {
      if (!live) return;
      if (result.revision !== revision) {
        await reload(result.revision);
        if (live) setAttempt((value) => value + 1);
        return;
      }
      setSelected((path) => selectedCalculation(result, path));
      setPayload(result);
    }).catch((failure: unknown) => {
      if (live) setError(failure instanceof Error ? failure.message : String(failure));
    });
    return () => { live = false; };
  }, [client, revision, attempt, reload]);

  const groups = useMemo(() => payload ? calculationGroups(payload) : [], [payload]);
  if (!model) return null;
  const current = payload?.revision === revision ? payload : null;
  const choose = (page: CalculationPage) => (
    <button key={page.path} className={`doc-list-item${selected === page.path ? " active" : ""}`}
      aria-current={selected === page.path ? "true" : undefined}
      onClick={() => { setSelected(page.path); setNavigationOpen(false); }}>
      {page.title}
    </button>
  );
  const matching = groups.some((group) => group.pages.some((page) => matchesCalculation(page, filter))
    || group.members?.some((family) => family.pages.some((page) => matchesCalculation(page, filter))));

  return (
    <ReaderShell className="report-reader" wide title="Engineering calculations" subtitle={model.project.name} onClose={close}
      toolbar={<ReaderFilter value={filter}
        onChange={(value) => { setFilter(value); if (compact) setNavigationOpen(true); }}
        placeholder="Filter calculations…" label="Filter calculations" />}>
      <p className="finding warn" role="note">Draft calculations · Not for construction. Engineering review and sealing are recorded in the package.</p>
      {error !== null ? <div role="alert"><p>{error}</p>
        <button className="btn" onClick={() => setAttempt((value) => value + 1)}>Retry</button>
      </div> : !current ? <p className="muted" role="status">Preparing live calculations…</p> : (
        <div className="doc-split">
          <details className="calculation-index" open={!compact || navigationOpen}
            onToggle={(event) => { if (compact) setNavigationOpen(event.currentTarget.open); }}>
            <summary>Calculation package index</summary>
            <nav className="doc-list" aria-label="Calculation package">
            {groups.map((group) => (
              <div key={group.title}>
                <h4 className="doc-list-group-title">{group.title}</h4>
                {group.pages.filter((page) => matchesCalculation(page, filter)).map(choose)}
                {group.members?.map((family) => {
                  const pages = family.pages.filter((page) => matchesCalculation(page, filter));
                  if (!pages.length) return null;
                  return <details key={`${family.family}|${filter}`} open={filter.trim() ? true : undefined}>
                    <summary>{family.family} members · {family.pages.length}</summary>
                    {pages.map(choose)}
                  </details>;
                })}
              </div>
            ))}
            {!matching && <p className="muted">No calculation matches “{filter}”.</p>}
            </nav>
          </details>
          <div className="doc-detail" key={selected}>
            <MarkdownBody key={`${current.revision}|${selected}`} markdown={current.files[selected]} />
          </div>
        </div>
      )}
    </ReaderShell>
  );
}
