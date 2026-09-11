"""What is ready, what is blocked, and exactly what is in the way — derived, in one pass.

The two questions this whole surface exists to answer: does the next trade arrive with
everything in place, and is every inspection's prerequisite ready. Both are *derived*
here from three inputs that are each somebody else's: the work packages (``takeoff``), the
findings (``checks``), and the owner's authored site state (``tasks.toml`` /
``inspections.toml``).

**No dates, no durations, no auto-ordering.** Readiness is derived; dates are authored.
Nothing in this module computes when anything happens, and the absence is the point: a
fabricated lead time is the number a schedule gets built on.

The two halves still resolve in one pass each — an inspection's prerequisites read visit
*status*, an authored fact, while a visit's blockers read inspection *state*. What that does
**not** buy is a house that cannot deadlock itself: the derivation terminates and the board
can still come out 40 visits blocked and nothing ready, which is worse than an error because
nothing says so. :mod:`typehaus.schedule.graph` detects the loops and
:class:`~typehaus.schedule.model.Board` carries them as ``errors``.

**FAIL blocks a visit; UNKNOWN does not.** An UNKNOWN is "this engine could not evaluate
the rule", which is a real thing for the owner to look at and a terrible reason to stop a
concrete truck. It rides as ``attention`` beside the blockers instead.
"""

from __future__ import annotations

from typing import Any

from typehaus.findings import GATE_OK, Finding, Result, fold_results
from typehaus.schedule.applicability import applicability
from typehaus.schedule.graph import (
    INSPECTION_PREFIX as _INSPECTION_PREFIX,
)
from typehaus.schedule.graph import (
    dropped_gates,
    expand_package_dependencies,
    find_cycles,
)
from typehaus.schedule.milestones import (
    build_milestones,
    milestone_of_inspection,
    milestone_table,
)
from typehaus.schedule.model import (
    Applicability,
    Board,
    Constraint,
    InspectionReadiness,
    Prerequisite,
    Visit,
    VisitReadiness,
)
from typehaus.schedule.visits import PROJECT_UUID, build_visits, mark_handoff_drift

#: A visit is under way — enough for an inspection that ``requires`` it to be callable.
_UNDER_WAY = ("in_progress", "done", "verified")
#: A predecessor visit is out of the way only when the work is actually finished.
_SETTLED = ("done", "verified")


def inspection_readiness(specs: tuple[Any, ...], state: Any, visits: tuple[Visit, ...],
                         findings: list[Finding], model: Any,
                         extra_ids: frozenset[str] = frozenset()
                         ) -> tuple[InspectionReadiness, ...]:
    """Every inspection **instance**, in profile order, with what stands before each call.

    One spec can have several instances — catlin pours its footings twice and is inspected
    twice — so this walks the specs in order and, inside each, every instance key the house
    authored. The bare spec id is the default instance and always exists, even with nothing
    authored against it.
    """
    by_id = {spec.id: spec for spec in specs}
    status_of = {visit.slug: visit.status for visit in visits}
    by_check: dict[str, list[Finding]] = {}
    for finding in findings:
        by_check.setdefault(finding.check_id, []).append(finding)

    records: dict[str, list[InspectionReadiness]] = {}
    out: list[InspectionReadiness] = []
    sequence = 0
    for spec in specs:
        authored = (state.instances(spec.id) if state is not None else {})
        keys = tuple(dict.fromkeys((spec.id, *sorted(authored))))
        evidence = applicability(model, spec.applies_when) if model is not None else None
        matched = [f for cid in spec.check_ids for f in by_check.get(cid, [])]
        result, detail = fold_results(matched) if spec.check_ids else (Result.PASS, "")
        for key in keys:
            entry = authored.get(key)
            if entry is None and key != spec.id:
                continue
            prerequisites = _prerequisites(spec, entry, records, status_of, result, detail,
                                           matched)
            record = InspectionReadiness(
                id=key, label=_instance_label(spec, key, entry), authority=spec.authority,
                sequence=sequence, spec_id=spec.id,
                scope=tuple(entry.scope) if entry is not None else (),
                approved=tuple(entry.approved) if entry is not None else (),
                attempts=(tuple(a.as_dict() for a in entry.attempts)
                          if entry is not None else ()),
                state=_inspection_state(entry, evidence, prerequisites),
                after=tuple(spec.after), gates=tuple(spec.gates), applicability=evidence,
                prerequisites=prerequisites,
                checks=tuple((f.check_id, f.result.value, f.message, f.element_tags)
                             for f in matched),
                on_site=tuple((label, label in (entry.checked if entry else ()))
                              for label in spec.on_site),
                entry=entry.as_dict() if entry is not None else None,
                extra=spec.id in extra_ids,
                milestone=milestone_of_inspection(spec, by_id),
                code_refs=tuple(spec.code_refs),
            )
            records.setdefault(spec.id, []).append(record)
            out.append(record)
            sequence += 1
    return tuple(out)


def _instance_label(spec: Any, key: str, entry: Any) -> str:
    """The spec's label, plus what this instance covers where it is not the only one."""
    from typehaus.schedule.inspection_state import instance_of

    name = instance_of(key)
    return f"{spec.label} — {name}" if name else spec.label


def _prerequisites(spec: Any, entry: Any, records: dict[str, list[InspectionReadiness]],
                   status_of: dict[str, str], result: Result, detail: str,
                   matched: list[Finding]) -> tuple[Prerequisite, ...]:
    out: list[Prerequisite] = []
    for after in spec.after:
        # A predecessor names a *spec*, so every instance of it has to stand aside: two
        # footing pours means two footing inspections before the wall inspection.
        earlier = records.get(after) or []
        label = earlier[0].label if earlier else after
        out.append(Prerequisite(
            "inspection", after,
            f"{label} resolved" + (f" ({len(earlier)} instances)"
                                   if len(earlier) > 1 else ""),
            met=bool(earlier) and all(record.resolved for record in earlier)))
    for slug in (entry.requires if entry is not None else ()):
        out.append(Prerequisite("visit", slug, f"{slug} under way",
                                met=status_of.get(slug, "todo") in _UNDER_WAY))
    # One line per check id, met or not. A single folded count ("3 checks pass") hides
    # which of the three is the one standing between the owner and the phone call.
    for check_id in spec.check_ids:
        hits = [f for f in matched if f.check_id == check_id]
        outcome, why = fold_results(hits) if hits else (Result.UNKNOWN, "no finding")
        out.append(Prerequisite(
            "check", check_id,
            f"{check_id}: {'pass' if outcome in GATE_OK else f'{outcome.value} — {why}'}",
            met=outcome in GATE_OK))
    for label in spec.on_site:
        out.append(Prerequisite("on_site", None, label,
                                met=label in (entry.checked if entry is not None else ())))
    return tuple(out)


def _inspection_state(entry: Any, evidence: Applicability | None,
                      prerequisites: tuple[Prerequisite, ...]) -> str:
    """The AHJ's own record first, then this building's, then what is left to do.

    ``waived`` outranks ``not_applicable`` because it is the *stronger* statement: the
    authority has spoken about this house, and a later model change that made the condition
    reappear must not quietly re-open a gate the AHJ already closed.
    """
    if entry is not None and entry.waived:
        return "waived"
    if evidence is not None and evidence.applies is False:
        return "not_applicable"
    if entry is not None and entry.result == "pass":
        return "passed"
    if entry is not None and entry.result in ("fail", "partial"):
        # `partial` stays `failed` as a *state* — the inspection is not finished — and
        # releases the scope it approved through `InspectionReadiness.releases`.
        return "failed"
    if entry is not None and entry.scheduled:
        return "scheduled"
    if entry is not None and entry.requested:
        return "requested"
    return "ready" if all(p.met for p in prerequisites) else "not_ready"


def visit_readiness(visits: tuple[Visit, ...],
                    inspections: tuple[InspectionReadiness, ...],
                    findings: list[Finding]) -> dict[str, VisitReadiness]:
    """Per visit: the state, and the ordered list of what is in the way.

    The order is the order an owner can act on: a predecessor that has not finished, then
    an inspection that has not passed, then a hold they put on themselves, then a red
    finding on the elements this visit builds. UNKNOWNs come last and never block.
    """
    status_of = {visit.slug: visit.status for visit in visits}
    # A dependency may target one checkpoint inside a visit: "pour after the footing
    # inspection" is a statement about the pour, not about the whole arrival.
    checkpoint_status = {
        f"{visit.slug}#{point['id']}": str(point["status"])
        for visit in visits for point in visit.checkpoints}
    inspection_by_id = {record.id: record for record in inspections}
    by_spec: dict[str, list[InspectionReadiness]] = {}
    for record in inspections:
        by_spec.setdefault(record.spec_id or record.id, []).append(record)
    fails = [f for f in findings if f.result is Result.FAIL and f.element_tags]
    unknowns = [f for f in findings if f.result is Result.UNKNOWN and f.element_tags]

    out: dict[str, VisitReadiness] = {}
    for visit in visits:
        constraints: list[Constraint] = []
        for dependency in visit.depends_on:
            if dependency.startswith(_INSPECTION_PREFIX):
                key = dependency[len(_INSPECTION_PREFIX):]
                # A bare spec id means EVERY instance of it; a key with a slash in it
                # means that one. `insp/footing` on a house that pours its footings twice
                # has to wait for both, and the default instance is not the whole story.
                matched = (by_spec.get(key, []) if "/" not in key
                           else [inspection_by_id[key]] if key in inspection_by_id
                           else [])
                label = matched[0].label if matched else key
                if len(matched) > 1:
                    label = f"{matched[0].label.split(' — ')[0]} ({len(matched)} instances)"
                released = bool(matched) and all(
                    record.releases(visit.element_tags) for record in matched)
                constraints.append(Constraint(
                    "inspection", key, f"{label} passed",
                    cleared="yes" if released else None))
            elif dependency in status_of:
                constraints.append(Constraint(
                    "visit", dependency, f"{dependency} complete",
                    cleared="yes" if status_of[dependency] in _SETTLED else None))
            elif dependency in checkpoint_status:
                constraints.append(Constraint(
                    "visit", dependency, f"{dependency} done",
                    cleared="yes" if checkpoint_status[dependency] == "done" else None))
            else:
                # A dependency naming nothing in this model is surfaced, never dropped:
                # it means the plan moved on under the authored visit.
                constraints.append(Constraint(
                    "visit", dependency,
                    f"{dependency} — names no current visit or inspection", cleared=None))
        constraints.extend(visit.constraints)
        tags = set(visit.element_tags)
        constraints.extend(
            Constraint("finding", f.check_id, f.message,
                       element_tags=tuple(t for t in f.element_tags if t in tags))
            for f in fails if tags.intersection(f.element_tags))
        constraints.extend(
            Constraint("attention", f.check_id, f.message, severity="attention",
                       element_tags=tuple(t for t in f.element_tags if t in tags))
            for f in unknowns if tags.intersection(f.element_tags))
        blocked = any(c.severity == "blocking" and not c.met for c in constraints)
        if visit.status in ("done", "verified", "in_progress"):
            state = visit.status
        else:
            state = "blocked" if blocked else "ready"
        out[visit.slug] = VisitReadiness(visit.slug, state, tuple(constraints))
    return out


def make_ready(model: Any, work_items: Any, tasks_state: Any, inspections_state: Any,
               profile: Any, findings: list[Finding] | None = None,
               costs_state: Any = None) -> Board:
    """The whole board, derived. The one entry point the CLI and the server share."""
    findings = list(findings or [])
    PROJECT_UUID["value"] = getattr(
        getattr(getattr(model, "plan", None), "project", None), "project_uuid", None)
    extras = tuple(inspections_state.extra) if inspections_state is not None else ()
    specs = tuple(profile.inspections) + tuple(item.as_spec() for item in extras)
    visits_state = getattr(tasks_state, "visits", None)
    visits = mark_handoff_drift(
        expand_package_dependencies(
            build_visits(work_items, visits_state, specs, costs_state,
                         {slug: entry.status for slug, entry
                          in getattr(tasks_state, "entries", {}).items()})),
        model)
    inspections = inspection_readiness(specs, inspections_state, visits, findings, model,
                                       frozenset(item.id for item in extras))
    readiness = visit_readiness(visits, inspections, findings)
    milestones = build_milestones(visits, inspections, milestone_table(tasks_state))
    errors = [f"dependency loop: {' -> '.join(loop)}"
              for loop in find_cycles(visits, inspections)]
    dropped = tuple(sorted((trade, ref)
                           for trade, refs in dropped_gates(specs).items()
                           for ref in refs))

    derived = {visit.slug for visit in visits}
    known = {spec.id for spec in specs}
    stale = sorted(
        [slug for slug in (visits_state.entries if visits_state is not None else ())
         if slug not in derived]
        + [f"{_INSPECTION_PREFIX}{key}"
           for key in (inspections_state.entries if inspections_state is not None else ())
           if key not in known])
    return Board(profile_name=profile.name, visits=visits, readiness=readiness,
                 inspections=inspections, milestones=milestones, stale=tuple(stale),
                 errors=tuple(errors), dropped_gates=dropped,
                 package_rows={item.slug: tuple(item.rows) for item in work_items},
                 package_tags={item.slug: tuple(item.element_tags)
                               for item in work_items})
