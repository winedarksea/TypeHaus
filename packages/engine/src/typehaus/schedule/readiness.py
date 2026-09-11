"""What is ready, what is blocked, and exactly what is in the way — derived, in one pass.

The two questions this whole surface exists to answer: does the next trade arrive with
everything in place, and is every inspection's prerequisite ready. Both are *derived*
here from three inputs that are each somebody else's: the work packages (``takeoff``), the
findings (``checks``), and the owner's authored site state (``tasks.toml`` /
``inspections.toml``).

**No dates, no durations, no auto-ordering.** Readiness is derived; dates are authored.
Nothing in this module computes when anything happens, and the absence is the point: a
fabricated lead time is the number a schedule gets built on.

There is no cycle between the two halves, though it looks like there should be. An
inspection's prerequisites read visit *status* — an authored fact — while a visit's
blockers read inspection *state*. So inspections resolve first, visits second, one pass
each, and a house can never deadlock itself by authoring a dependency.

**FAIL blocks a visit; UNKNOWN does not.** An UNKNOWN is "this engine could not evaluate
the rule", which is a real thing for the owner to look at and a terrible reason to stop a
concrete truck. It rides as ``attention`` beside the blockers instead.
"""

from __future__ import annotations

from dataclasses import replace
from fnmatch import fnmatch
from typing import Any

from typehaus.findings import GATE_OK, Finding, Result, fold_results
from typehaus.schedule.applicability import applicability
from typehaus.schedule.milestones import (
    MILESTONE_OF_TRADE,
    build_milestones,
    milestone_of_inspection,
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
from typehaus.takeoff.visit_state import VisitEntry, package_of

#: A visit is under way — enough for an inspection that ``requires`` it to be callable.
_UNDER_WAY = ("in_progress", "done", "verified")
#: A predecessor visit is out of the way only when the work is actually finished.
_SETTLED = ("done", "verified")

_INSPECTION_PREFIX = "insp/"


def _matches(tag: str, patterns: tuple[str, ...]) -> bool:
    """A tag against the visit's globs. No patterns means the whole package."""
    return not patterns or any(fnmatch(tag, pattern) for pattern in patterns)


def build_visits(work_items: Any, visits_state: Any, specs: tuple[Any, ...],
                 costs_entries: Any = None) -> tuple[Visit, ...]:
    """One :class:`Visit` per authored visit, or one implicit visit per package.

    The implicit visit is what makes a house that has authored nothing still get a complete
    board: its slug **is** the package slug, and its predecessors are the package's own
    plus every inspection whose ``gates`` names its trade.
    """
    gating: dict[str, list[str]] = {}
    for spec in specs:
        for trade in spec.gates:
            gating.setdefault(trade, []).append(f"{_INSPECTION_PREFIX}{spec.id}")

    out: list[Visit] = []
    for item in work_items:
        authored = visits_state.for_package(item.slug) if visits_state is not None else {}
        implied = tuple(item.depends_on) + tuple(sorted(gating.get(item.trade, ())))
        if not authored:
            out.append(_visit(item, item.slug, VisitEntry(), implied, implicit=True,
                              costs_entries=costs_entries))
            continue
        for slug in sorted(authored):
            out.append(_visit(item, slug, authored[slug],
                              tuple(authored[slug].depends_on) or implied,
                              implicit=False, costs_entries=costs_entries))
    return tuple(out)


def expand_package_dependencies(visits: tuple[Visit, ...]) -> tuple[Visit, ...]:
    """Rewrite a dependency on a *package* into one on each visit derived from it.

    A package's predecessors come from ``TRADE_PREDECESSORS`` and name package slugs. The
    moment somebody splits one of those packages into arrivals, the package slug stops being
    a visit and the dependency dangles — which is exactly what "names no current visit"
    reports, and reporting it would be wrong here: the owner did not break anything, they
    split a package the engine's own predecessor map still refers to by its old name.
    """
    slugs = {visit.slug for visit in visits}
    by_package: dict[str, list[str]] = {}
    for visit in visits:
        if visit.slug != visit.package:
            by_package.setdefault(visit.package, []).append(visit.slug)
    if not by_package:
        return visits
    out: list[Visit] = []
    for visit in visits:
        expanded: list[str] = []
        for dependency in visit.depends_on:
            if dependency in slugs or dependency.startswith(_INSPECTION_PREFIX):
                expanded.append(dependency)
            else:
                # Every arrival in the predecessor package, or the name itself when it
                # matches nothing — a genuinely stale dependency still has to be visible.
                expanded.extend(by_package.get(dependency, [dependency]))
        out.append(replace(visit, depends_on=tuple(dict.fromkeys(expanded))))
    return tuple(out)


def _visit(item: Any, slug: str, entry: VisitEntry, depends_on: tuple[str, ...], *,
           implicit: bool, costs_entries: Any) -> Visit:
    from typehaus.model.ids import derive_guid

    rows = tuple(row for row in item.rows
                 if not entry.rows or f"{row[0]}:{row[1]}" in entry.rows)
    tags = tuple(tag for tag in item.element_tags
                 if _matches(tag, entry.element_tags))
    constraints = tuple(Constraint("authored", None, c.label, c.cleared)
                        for c in entry.constraints)
    label = entry.label or item.title
    # A holdback is only *open* once the owner has verified the work and some row on it is
    # billed but unpaid. Before that there is nothing to hold back.
    holdback = bool(entry.status == "verified" and _unpaid(rows, costs_entries))
    return Visit(
        slug=slug,
        id=derive_guid(_PROJECT_UUID["value"], slug),
        package=package_of(slug), label=label, trade=item.trade, storey=item.storey,
        milestone=MILESTONE_OF_TRADE.get(item.trade, ""),
        status=entry.status, scheduled=entry.scheduled, assignee=entry.assignee,
        contact=entry.contact, note=entry.note, depends_on=tuple(depends_on),
        rows=rows, element_tags=tags, constraints=constraints,
        checked=tuple(entry.checked), estimate_fmt=item.estimate.fmt(),
        holdback_open=holdback, implicit=implicit)


#: Set once per :func:`make_ready` call. ``WorkItem`` carries its derived GlobalId but not
#: the project uuid it came from, and threading a parameter through for one value would put
#: the project's identity in five signatures that have no other use for it.
_PROJECT_UUID: dict[str, Any] = {"value": None}


def _unpaid(rows: tuple[tuple[str, str], ...], costs_entries: Any) -> bool:
    entries = getattr(costs_entries, "entries", {}) or {}
    for section, key in rows:
        entry = entries.get(section, {}).get(key)
        if entry is not None and getattr(entry, "actual_cost", None) is not None \
                and not getattr(entry, "paid", False):
            return True
    return False


def inspection_readiness(specs: tuple[Any, ...], state: Any, visits: tuple[Visit, ...],
                         findings: list[Finding], model: Any,
                         extra_ids: frozenset[str] = frozenset()
                         ) -> tuple[InspectionReadiness, ...]:
    """Every inspection, in profile order, with everything standing between it and a call."""
    by_id = {spec.id: spec for spec in specs}
    status_of = {visit.slug: visit.status for visit in visits}
    by_check: dict[str, list[Finding]] = {}
    for finding in findings:
        by_check.setdefault(finding.check_id, []).append(finding)

    records: dict[str, InspectionReadiness] = {}
    out: list[InspectionReadiness] = []
    for sequence, spec in enumerate(specs):
        entry = state.entries.get(spec.id) if state is not None else None
        evidence = applicability(model, spec.applies_when) if model is not None else None
        matched = [f for cid in spec.check_ids for f in by_check.get(cid, [])]
        result, detail = fold_results(matched) if spec.check_ids else (Result.PASS, "")
        prerequisites = _prerequisites(spec, entry, records, status_of, result, detail,
                                       matched)
        record = InspectionReadiness(
            id=spec.id, label=spec.label, authority=spec.authority, sequence=sequence,
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
        records[spec.id] = record
        out.append(record)
    return tuple(out)


def _prerequisites(spec: Any, entry: Any, records: dict[str, InspectionReadiness],
                   status_of: dict[str, str], result: Result, detail: str,
                   matched: list[Finding]) -> tuple[Prerequisite, ...]:
    out: list[Prerequisite] = []
    for after in spec.after:
        earlier = records.get(after)
        out.append(Prerequisite(
            "inspection", after,
            f"{earlier.label if earlier else after} resolved",
            met=bool(earlier and earlier.resolved)))
    for slug in (entry.requires if entry is not None else ()):
        out.append(Prerequisite("visit", slug, f"{slug} under way",
                                met=status_of.get(slug, "todo") in _UNDER_WAY))
    if spec.check_ids:
        out.append(Prerequisite(
            "check", None,
            (f"{len(matched)} engine check(s) pass" if result in GATE_OK
             else f"{result.value}: {detail}"),
            met=result in GATE_OK))
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
    inspection_by_id = {record.id: record for record in inspections}
    fails = [f for f in findings if f.result is Result.FAIL and f.element_tags]
    unknowns = [f for f in findings if f.result is Result.UNKNOWN and f.element_tags]

    out: dict[str, VisitReadiness] = {}
    for visit in visits:
        constraints: list[Constraint] = []
        for dependency in visit.depends_on:
            if dependency.startswith(_INSPECTION_PREFIX):
                key = dependency[len(_INSPECTION_PREFIX):]
                record = inspection_by_id.get(key)
                constraints.append(Constraint(
                    "inspection", key,
                    f"{record.label if record else key} passed",
                    cleared="yes" if record is not None and record.resolved else None))
            elif dependency in status_of:
                constraints.append(Constraint(
                    "visit", dependency, f"{dependency} complete",
                    cleared="yes" if status_of[dependency] in _SETTLED else None))
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
    _PROJECT_UUID["value"] = getattr(
        getattr(getattr(model, "plan", None), "project", None), "project_uuid", None)
    extras = tuple(inspections_state.extra) if inspections_state is not None else ()
    specs = tuple(profile.inspections) + tuple(item.as_spec() for item in extras)
    visits_state = getattr(tasks_state, "visits", None)
    visits = expand_package_dependencies(
        build_visits(work_items, visits_state, specs, costs_state))
    inspections = inspection_readiness(specs, inspections_state, visits, findings, model,
                                       frozenset(item.id for item in extras))
    readiness = visit_readiness(visits, inspections, findings)
    milestones = build_milestones(visits, inspections)

    derived = {visit.slug for visit in visits}
    known = {spec.id for spec in specs}
    stale = sorted(
        [slug for slug in (visits_state.entries if visits_state is not None else ())
         if slug not in derived]
        + [f"{_INSPECTION_PREFIX}{key}"
           for key in (inspections_state.entries if inspections_state is not None else ())
           if key not in known])
    return Board(profile_name=profile.name, visits=visits, readiness=readiness,
                 inspections=inspections, milestones=milestones, stale=tuple(stale))
