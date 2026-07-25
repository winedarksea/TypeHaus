import { useMemo, useState } from "react";
import { useStore } from "../state/store";
import { formatFtIn } from "../model/geometry";
import type { Condition, Model, Transition } from "../model/types";
import { transitionCoverage } from "../model/transitions";
import { ReaderSection, ReaderShell } from "./ReaderShell";

// "Assembly details (ie transitions)" (→ TODO Editor). The library's authored Transitions are
// printed by the engine and carried in model.json, but nothing surfaced them: this reader pairs
// each transition with the resolved conditions whose pattern it details, so "what happens where
// this wall meets that roof" is answerable without opening the plan source.

// Tag → uid for every record a condition or transition can name. Conditions carry authored
// *tags*; selection and zoom are keyed by *uid*, so the reader resolves once per model.
function uidByTag(model: Model): Map<string, string> {
  const index = new Map<string, string>();
  const add = (records: readonly { tag: string; uid: string }[]) => {
    for (const record of records) if (!index.has(record.tag)) index.set(record.tag, record.uid);
  };
  add(model.walls);
  add(model.openings);
  add(model.rooms);
  add(model.roofs ?? []);
  add(model.solids ?? []);
  add(model.stairs ?? []);
  add(model.floors ?? []);
  return index;
}

function ContinuityRows({ transition }: { transition: Transition }) {
  if (transition.continuity.length === 0) return <div className="muted">No control-layer continuity declared.</div>;
  return (
    <ul className="reader-list">
      {transition.continuity.map((row, index) => (
        <li key={index}>
          <span className={`control-tag control-${row.control}`}>{row.control}</span>
          <span className="reader-mono">{row.from_face}</span>
          <span className="muted"> → </span>
          <span className="reader-mono">{row.to_face}</span>
        </li>
      ))}
    </ul>
  );
}

function JoinRows({ transition }: { transition: Transition }) {
  if (transition.joins.length === 0) return null;
  return (
    <ul className="reader-list">
      {transition.joins.map((join, index) => (
        <li key={index}>
          <span className="reader-mono">{join.layer}</span>
          <span className="muted"> · {join.side} · terminates </span>
          {formatFtIn(join.termination_m)}
          <span className="muted"> · {join.treatment}</span>
        </li>
      ))}
    </ul>
  );
}

export function AssemblyDetailsView() {
  const model = useStore((s) => s.model);
  const setDetailView = useStore((s) => s.setDetailView);
  const zoomToUid = useStore((s) => s.zoomToUid);
  const [expanded, setExpanded] = useState<string | null>(null);

  const index = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const coverage = useMemo(
    () => transitionCoverage(model?.transitions ?? [], model?.conditions ?? []),
    [model],
  );
  const conditionsByKind = useMemo(() => {
    const groups = new Map<string, Condition[]>();
    for (const condition of model?.conditions ?? []) {
      groups.set(condition.kind, [...(groups.get(condition.kind) ?? []), condition]);
    }
    return [...groups.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [model]);

  if (!model) return null;

  const transitions = model.transitions ?? [];
  const assemblies = model.catalog?.assemblies ?? [];

  const jump = (tag: string) => {
    const uid = index.get(tag);
    if (uid) {
      zoomToUid(uid);
      setDetailView("none");
    }
  };

  return (
    <ReaderShell
      title="Assembly details"
      subtitle={`${transitions.length} transitions · ${model.conditions.length} resolved conditions`}
      onClose={() => setDetailView("none")}
    >
      <ReaderSection
        title="Transitions"
        note="Authored detail documentation: how each condition pattern carries its control layers across the junction."
        count={transitions.length}
      >
        {transitions.map((transition) => {
          const matches = coverage.matchesByTransition.get(transition.tag) ?? [];
          return (
            <div key={transition.tag} className="reader-card">
              <div className="reader-card-head">
                <span className="reader-mono reader-card-title">{transition.tag}</span>
                <span className="muted">{transition.pattern}</span>
                {transition.overlay && <span className="reader-chip">{transition.overlay}</span>}
                <span className="muted">{matches.length} matching condition{matches.length === 1 ? "" : "s"}</span>
              </div>
              <ContinuityRows transition={transition} />
              <JoinRows transition={transition} />
              {transition.notes && <div className="muted reader-mono">{transition.notes}</div>}
              {matches.length > 0 && (
                <>
                  <button
                    className="btn reader-expand"
                    onClick={() => setExpanded(expanded === transition.tag ? null : transition.tag)}
                  >
                    {expanded === transition.tag ? "Hide" : "Show"} matching conditions
                  </button>
                  {expanded === transition.tag && (
                    <div className="reader-tag-cloud">
                      {[...new Set(matches.flatMap((condition) => condition.elements))].map((tag) => (
                        <button key={tag} className="reader-tag" onClick={() => jump(tag)}
                          disabled={!index.has(tag)} title="Zoom to element">
                          {tag}
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </ReaderSection>

      <ReaderSection
        title="Resolved conditions"
        note={`Every junction the resolver classified, grouped by kind — what a transition pattern matches against. ${coverage.uncovered.length} carry no transition.`}
        count={model.conditions.length}
      >
        <div className="reader-table-scroll">
          <table className="reader-table">
            <thead><tr><th>Kind</th><th className="num-col">Count</th><th className="num-col">Undetailed</th><th>Detailed by</th></tr></thead>
            <tbody>
              {conditionsByKind.map(([kind, items]) => {
                const detailing = transitions.filter((transition) =>
                  (coverage.matchesByTransition.get(transition.tag) ?? [])
                    .some((condition) => condition.kind === kind));
                const undetailed = coverage.uncovered.filter((condition) => condition.kind === kind).length;
                return (
                  <tr key={kind}>
                    <td className="reader-mono">{kind}</td>
                    <td className="num-col">{items.length}</td>
                    <td className="num-col">{undetailed || "—"}</td>
                    <td>
                      {detailing.length === 0
                        ? <span className="muted">— undetailed</span>
                        : detailing.map((transition) => transition.tag).join(", ")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </ReaderSection>

      <ReaderSection
        title="Assembly stacks"
        note="Every wall/roof assembly in the catalog with its resolved layer stack, outside face first."
        count={assemblies.length}
      >
        {assemblies.map((assembly) => (
          <div key={assembly.tag} className="reader-card">
            <div className="reader-card-head">
              <span className="reader-mono reader-card-title">{assembly.tag}</span>
              {assembly.editable && <span className="reader-chip">editable</span>}
              {assembly.stc !== null && <span className="muted">STC {assembly.stc}</span>}
              {assembly.provenance && (
                <span className="muted reader-mono">
                  {assembly.provenance.file}:{assembly.provenance.line}
                </span>
              )}
            </div>
            <ul className="reader-list">
              {assembly.layers.map((layer, position) => (
                <li key={position}>
                  <span className="reader-mono">{layer.name}</span>
                  <span className="muted"> · {layer.function} · {layer.material} · </span>
                  {formatFtIn(layer.thickness_m)}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </ReaderSection>
    </ReaderShell>
  );
}
