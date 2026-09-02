import { Fragment, useMemo, useState } from "react";
import { useStore } from "../state/store";
import { formatFtIn } from "../model/geometry";
import type { Condition, Transition } from "../model/types";
import { transitionCoverage } from "../model/transitions";
import { uidByTag } from "../model/tagIndex";
import { DetailViewer } from "./DetailViewer";
import { ReaderSection, ReaderShell } from "./ReaderShell";
import { Icon } from "../icons/Icon";

// "Assembly details (ie transitions)" (→ TODO Editor). The library's authored Transitions are
// printed by the engine and carried in model.json, but nothing surfaced them: this reader pairs
// each transition with the resolved conditions whose pattern it details, so "what happens where
// this wall meets that roof" is answerable without opening the plan source.
//
// It is also the way *into* the drawings. The engine derives one junction detail per bound
// condition key; this reader hands the viewer the key the user actually clicked, from the
// transition that details it or from the condition itself.

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

// Conditions grouped the way the engine draws them: one row per *distinct* key, because
// details.py derives exactly one detail per bound key however many places that junction
// recurs (twenty identical window heads share one drawing). Each row carries the union of
// the elements those conditions touch, so a tag click still zooms to a real place in the plan.
//
// The Detail button is disabled for an unbound key — no transition matches it, so the engine
// derived nothing — which beats opening somebody else's drawing and calling it this one.
function ConditionRows({ conditions, index, uncovered, onZoom, onDetail }: {
  conditions: Condition[];
  index: Map<string, string>;
  uncovered: Set<string>;
  onZoom: (tag: string) => void;
  onDetail: (key: string) => void;
}) {
  const groups = new Map<string, { count: number; tags: Set<string> }>();
  for (const condition of conditions) {
    const group = groups.get(condition.key) ?? { count: 0, tags: new Set<string>() };
    group.count += 1;
    for (const tag of condition.elements) group.tags.add(tag);
    groups.set(condition.key, group);
  }
  return (
    <ul className="reader-list">
      {[...groups.entries()].map(([key, group]) => (
        <li key={key}>
          <button
            className="btn reader-expand"
            onClick={() => onDetail(key)}
            disabled={uncovered.has(key)}
            title={uncovered.has(key)
              ? "No transition binds this condition — no detail is derived."
              : "Open the junction detail for this condition"}
          >
            Detail
          </button>
          <span className="reader-mono"> {key}</span>
          {group.count > 1 && <span className="muted"> · {group.count} places</span>}
          <span className="reader-tag-cloud">
            {[...group.tags].map((tag) => (
              <button key={tag} className="reader-tag" onClick={() => onZoom(tag)}
                disabled={!index.has(tag)} title="Zoom to element">
                {tag}
              </button>
            ))}
          </span>
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
  const [expandedKind, setExpandedKind] = useState<string | null>(null);
  // The detail viewer's open state *and* the key it should land on: `undefined` closed,
  // `null` open at the library's first drawing, a string open at that condition.
  const [detailKey, setDetailKey] = useState<string | null | undefined>(undefined);

  const index = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const coverage = useMemo(
    () => transitionCoverage(model?.transitions ?? [], model?.conditions ?? []),
    [model],
  );
  // Conditions no transition matches derive no detail (emit/draw/details.py skips them), which
  // is exactly what `uncovered` already reports — so the reader knows which Detail buttons are
  // live without a second round trip to /details.
  const uncoveredKeys = useMemo(
    () => new Set(coverage.uncovered.map((condition) => condition.key)),
    [coverage],
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
      toolbar={
        <button className="btn" onClick={() => setDetailKey(null)}
          title="Browse every derived junction drawing">
          Junction details…
        </button>
      }
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
                    <ConditionRows conditions={matches} index={index} uncovered={uncoveredKeys}
                      onZoom={jump} onDetail={setDetailKey} />
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
                const open = expandedKind === kind;
                return (
                  <Fragment key={kind}>
                    <tr>
                      <td>
                        <button className="reader-tag" onClick={() => setExpandedKind(open ? null : kind)}
                          title={open ? "Hide these conditions" : "List these conditions"}>
                          <Icon name={open ? "chevron-down" : "chevron-right"} size={14} /> <span className="reader-mono">{kind}</span>
                        </button>
                      </td>
                      <td className="num-col">{items.length}</td>
                      <td className="num-col">{undetailed || "—"}</td>
                      <td>
                        {detailing.length === 0
                          ? <span className="muted">— undetailed</span>
                          : detailing.map((transition) => transition.tag).join(", ")}
                      </td>
                    </tr>
                    {open && (
                      <tr>
                        <td colSpan={4}>
                          <ConditionRows conditions={items} index={index} uncovered={uncoveredKeys}
                            onZoom={jump} onDetail={setDetailKey} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
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

      {detailKey !== undefined && (
        <DetailViewer initialKey={detailKey} onClose={() => setDetailKey(undefined)} />
      )}
    </ReaderShell>
  );
}
