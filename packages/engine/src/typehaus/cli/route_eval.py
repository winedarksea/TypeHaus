"""Grade in-memory candidate plans against the unsuppressed authored baseline.

Reports show introduced/resolved findings and coverage gaps. Each alternative costs one
candidate resolve/check run; campaigns grade the complete accepted network together.
No plan source is written. Workflow and report contracts: docs/routing.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.findings import Finding
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal

#: Check id prefixes a route proposal is graded on. Everything a run can break, and nothing
#: it cannot: an energy finding that moved because a check happens to be order-dependent is
#: noise a reader has to learn to ignore, and a reader who learns to ignore this report has
#: lost the loop. Every ERROR is kept whatever its id — an error means the candidate model
#: did not even resolve, which is the most important thing this can say.
GRADED_PREFIXES = ("mep.", "integrity.", "structural.member_interference")


@dataclass
class Evaluation:
    """What one proposal did to the house's own report."""

    tag: str
    introduced: list[Finding] = field(default_factory=list)
    resolved: list[Finding] = field(default_factory=list)
    #: Why a question was not answered — a check that reported nothing evaluable about this
    #: run. A silent absence reads as a PASS and is the one failure mode a loop cannot
    #: recover from.
    coverage: list[str] = field(default_factory=list)
    #: Set when the candidate model would not resolve at all.
    refused: str | None = None


def graded(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings
            if f.severity.value == "error" or f.check_id.startswith(GRADED_PREFIXES)]


def _findings(plan: Any, directory: Path) -> list[Finding]:
    """Run graded checks with suppression lifted on both baseline and candidate.

    Otherwise a house suppressing an open MEP campaign could hide a new clash."""
    from dataclasses import replace

    from typehaus.checks import build_context, run_checks

    ctx, _ = build_context(plan, directory)
    ctx.preferences = replace(ctx.preferences, suppressed=frozenset())
    return graded(run_checks(ctx).findings)


def _key(finding: Finding) -> tuple:
    """What makes two findings "the same finding" across two runs of the checks.

    The message is in the key deliberately: a check that still FAILs a run but by a
    different number has told you something, and treating the two as one finding would
    hide exactly the improvement a loop is looking for.
    """
    return (finding.check_id, finding.result.value, tuple(sorted(finding.element_tags)),
            finding.message)


#: One baseline per (house, loaded plan) in a process: a scorecard evaluates ten targets
#: against the same unchanged house, and each pass is a full check run.
_BASELINES: dict[tuple[str, int], tuple[Any, dict[tuple, Finding]]] = {}


def evaluate_proposals(directory: Path, model: ResolvedModel,
                       proposals: list[RouteProposal]) -> list[Evaluation]:
    """One :class:`Evaluation` per proposal, each against the house's own baseline."""
    baseline = baseline_findings(model, directory)

    out = []
    drains = {p.tag: p for p in proposals if p.system == "drain"}
    for proposal in proposals:
        # A fixture's vent is graded WITH its drain (``route_fixture_vent``): alone it
        # would meet the very drain the pair replaces, and its arm would read unvented.
        partner = drains.get(proposal.tag.replace("-VENT-PROPOSED", "-PROPOSED"))
        group = [partner, proposal] if proposal.system == "vent" and partner else [proposal]
        out.append(_evaluate_one(directory, model, proposal, baseline, group))
    return out


def _evaluate_one(directory: Path, model: ResolvedModel, proposal: RouteProposal,
                  baseline: dict[tuple, Finding],
                  group: list[RouteProposal] | None = None) -> Evaluation:
    result = Evaluation(tag=proposal.tag if not group or len(group) == 1
                        else " + ".join(p.tag for p in group))
    try:
        candidate = candidate_plan_for_all(model, group or [proposal])
    except (ValueError, TypeError, KeyError) as exc:
        result.refused = f"the candidate elements would not build: {exc}"
        return result
    try:
        findings = _findings(candidate, directory)
    except Exception as exc:  # noqa: BLE001 - a resolver refusal is the answer, not a crash
        result.refused = f"the candidate model would not resolve: {exc}"
        return result

    seen = {_key(f): f for f in findings}
    result.introduced = [f for key, f in seen.items()
                         if key not in baseline and f.result.value in
                         ("fail", "unknown", "advisory")]
    result.resolved = [f for key, f in baseline.items()
                       if key not in seen and f.result.value in
                       ("fail", "unknown", "advisory")]
    result.coverage = _coverage_gaps(proposal, findings)
    return result


def candidate_element(model: ResolvedModel, proposal: RouteProposal) -> tuple[str, Any]:
    """``(storey, element)`` for one proposal, built exactly as its printed source reads.

    The storey is the one the proposal's own source would be filed on — the list decides
    it, and the elevations are relative to it — so the element is built at the same datum
    the printed constructor would be read at. A mismatch here would grade a route a storey
    away from the one a person would paste.
    """
    from typehaus.model.enums import DuctRouting, DuctSystem, PipeSystem, Service
    from typehaus.model.mep import ConduitRun, DuctRun, PipeRun
    from typehaus.quantities import Point2D
    from typehaus.routing.proposal import length_source as _len  # noqa: I001
    # `_len` is the literal the proposal prints: the graded run is the one a person pastes.

    storey = _storey_for(model, proposal)
    datum = next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    path = tuple(Point2D(_len(x), _len(y)) for x, y, _z in proposal.points)

    if proposal.kind == "pipe":
        element = PipeRun(
            tag=proposal.tag, system=PipeSystem(proposal.system), path=path,
            diameter=_len(proposal.diameter_m),
            elevations=tuple(_len(z - datum) for _x, _y, z in proposal.points),
            serves=proposal.serves, **proposal.echo)
    elif proposal.kind == "duct":
        section: dict[str, Any] = ({"width": _len(proposal.width_m),
                                    "depth": _len(proposal.depth_m)}
                                   if proposal.width_m or proposal.depth_m
                                   else {"diameter": _len(proposal.diameter_m)})
        element = DuctRun(
            tag=proposal.tag, system=DuctSystem(proposal.system), path=path, **section,
            routing=DuctRouting(proposal.routing or "exposed"),
            floor_ref=proposal.floor_ref, soffit_ref=proposal.soffit_ref,
            elevations=tuple(_len(z - datum) for _x, _y, z in proposal.points),
            **proposal.echo)
    else:
        # The WHOLE raceway, a z at every vertex, never a fraction of the proposal. No datum
        # subtraction: a raceway's elevations are project-frame absolute (a duct's are
        # storey-relative).
        element = ConduitRun(
            tag=proposal.tag,
            path=tuple(Point2D(_len(x), _len(y)) for x, y, _z in proposal.points),
            trade_size=_len(proposal.diameter_m),
            elevations=tuple(_len(z) for _x, _y, z in proposal.points),
            service=Service(proposal.system) if proposal.system else None,
            pull_points=proposal.pull_points, **proposal.echo)

    return storey, element


def _cleanout_elements(model: ResolvedModel, storey: str, proposal: RouteProposal) -> list:
    """The ``DrainCleanout``s a drain proposal prints, built as its source reads."""
    from typehaus.model.mep import DrainCleanout
    from typehaus.quantities import Point2D, inch
    from typehaus.routing.proposal import length_source as _len

    datum = next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    out = []
    for c in proposal.cleanouts:
        out.append(DrainCleanout(
            tag=c.tag, pipe_ref=proposal.tag,
            position=Point2D(_len(c.point[0]), _len(c.point[1])),
            cap_position=Point2D(_len(c.cap[0]), _len(c.cap[1])),
            fitting_elevation=_len(c.point[2] - datum), cap_elevation=_len(c.cap[2] - datum),
            access=c.access, wall_ref=c.wall_ref, clear_width=inch(c.clear_in),
            clear_depth=inch(c.clear_in)))
    return out


def _candidate_plan(model: ResolvedModel, proposal: RouteProposal) -> Any:
    """The house's plan with this proposal's element added, and what it replaces removed."""
    return candidate_plan_for_all(model, [proposal])


def candidate_plan_for_all(model: ResolvedModel,
                           proposals: list[RouteProposal]) -> Any:
    """The house's plan holding **every** proposal at once, grouped by storey.

    A campaign's result is a network, and a network is only as good as it is *together*: a
    drain that clears the house one at a time and clashes with the vent laid after it passes
    every per-route evaluation and fails the only one that matters. ``with_elements`` replaces
    a storey's whole list, so the proposals are grouped and applied once per storey — applying
    them one at a time would have each call overwrite the last.
    """
    by_storey: dict[str, list[Any]] = {}
    replaced: set[str] = set()
    for proposal in proposals:
        storey, element = candidate_element(model, proposal)
        by_storey.setdefault(storey, []).append(element)
        by_storey[storey].extend(_cleanout_elements(model, storey, proposal))
        replaced |= _replaced_tags(model, proposal)

    # The replaced runs leave EVERY storey: a second-floor branch is often filed on the
    # storey below it (PR-M-S-SUITE-LAV-DRAIN), and leaving it graded the proposal against
    # its own ghost.
    plan = model.plan
    for storey in model.plan.storeys:
        current = plan.storey_elements(storey.tag)
        # A replaced run's own cleanouts go with it. A valve, stop or shutoff on it follows it
        # to the proposal that now carries its station (see ``_host_proposal``), and goes only
        # where none does: it has no pipe left to sit on.
        keep = []
        for e in current:
            if getattr(e, "tag", None) in replaced:
                continue
            e = _follow(e, replaced, proposals)
            if e is not None:
                keep.append(e)
        added = by_storey.get(storey.tag, [])
        if added or len(keep) != len(current):
            plan = plan.with_elements(storey.tag, (*keep, *added))
    return plan


#: Fields that name a run by tag: a bond's ends and a register's duct.
_RUN_REFS = ("from_ref", "to_ref", "duct_ref")


def _follow(e: Any, replaced: set[str], proposals: list[RouteProposal]) -> Any:
    """``e`` re-pointed at the proposal standing in for the run it names, or ``None`` when it
    must go with it: a valve follows its station, a bond's ends or a register's ``duct_ref`` the
    ``<run>-PROPOSED`` of the run they name, as the proposal's pasted source would carry them."""
    from typehaus.model.mep import PipeAccessory

    proposed = {p.tag for p in proposals}
    ref = getattr(e, "pipe_ref", None)
    if ref in replaced:
        if not isinstance(e, PipeAccessory):
            return None
        host = _host_proposal(e, ref, proposals) or (
            f"{ref}-PROPOSED" if f"{ref}-PROPOSED" in proposed else None)
        return None if host is None else e.model_copy(update={"pipe_ref": host})
    named = {k: f"{getattr(e, k)}-PROPOSED" for k in _RUN_REFS
             if getattr(e, k, None) in replaced and f"{getattr(e, k)}-PROPOSED" in proposed}
    return e.model_copy(update=named) if named else e


def _host_proposal(acc: Any, ref: str, proposals: list[RouteProposal]) -> str | None:
    """The proposal standing in for ``ref`` that passes within 3" of ``acc``'s plan station.
    A run split in two (a trunk and its fixture end) leaves the valve on the piece it sits on."""
    if acc.position is None:
        return None
    x, y = acc.position.x, acc.position.y
    best: tuple[float, str] | None = None
    for p in proposals:
        if ref not in getattr(p, "replaces", ()) and p.tag != f"{ref}-PROPOSED":
            continue
        gap = min((_gap((x.meters, y.meters, 0.0), [(a[0], a[1], 0.0), (b[0], b[1], 0.0)])
                   for a, b in zip(p.points, p.points[1:], strict=False)), default=9.0)
        if gap <= 0.0762 and (best is None or gap < best[0]):
            best = (gap, p.tag)
    return None if best is None else best[1]


def baseline_findings(model: ResolvedModel, directory: Path) -> dict[tuple, Finding]:
    """The house's own graded findings, keyed — computed once and shared by many networks."""
    key = (str(directory), id(model.plan))
    held = _BASELINES.get(key)
    if held is None or held[0] is not model.plan:  # the plan is held, so its id is not reused
        held = _BASELINES[key] = (model.plan, {_key(f): f for f in _findings(model.plan,
                                                                             directory)})
    return held[1]


def evaluate_network(directory: Path, model: ResolvedModel,
                     proposals: list[RouteProposal], *,
                     baseline: dict[tuple, Finding] | None = None) -> Evaluation:
    """Grade all accepted proposals together, including network and run/run checks.

    An empty campaign is explicitly ungraded. Individual route evaluations cannot establish
    that the combined network works."""
    result = Evaluation(tag="campaign")
    if not proposals:
        result.refused = "nothing was laid, so there is no network to grade"
        return result
    try:
        if baseline is None:
            baseline = baseline_findings(model, directory)
        candidate = candidate_plan_for_all(model, proposals)
    except (ValueError, TypeError, KeyError) as exc:
        result.refused = f"the candidate elements would not build: {exc}"
        return result
    try:
        findings = _findings(candidate, directory)
    except Exception as exc:  # noqa: BLE001 - a resolver refusal is the answer, not a crash
        result.refused = f"the candidate model would not resolve: {exc}"
        return result

    seen = {_key(f): f for f in findings}
    result.introduced = [f for key, f in seen.items()
                         if key not in baseline and f.result.value in
                         ("fail", "unknown", "advisory")]
    result.resolved = [f for key, f in baseline.items()
                       if key not in seen and f.result.value in
                       ("fail", "unknown", "advisory")]
    result.coverage = sorted({gap for proposal in proposals
                              for gap in _coverage_gaps(proposal, findings)})
    return result


def _storey_for(model: ResolvedModel, proposal: RouteProposal) -> str:
    """The storey the replaced run lives on, else the one the proposal's tag names."""
    base = proposal.tag.split("-PROPOSED")[0]
    for run in (*model.pipe_runs, *model.ducts, *model.conduits):
        if run.tag == base:
            return str(run.storey)
    for storey in model.plan.storeys:
        if any(getattr(e, "tag", None) == base
               for e in model.plan.storey_elements(storey.tag)):
            return str(storey.tag)
    return str(model.plan.storeys[0].tag) if model.plan.storeys else "main"


def _replaced_tags(model: ResolvedModel, proposal: RouteProposal) -> set[str]:
    """What this proposal stands in for: the run of its own name, and any serving its
    fixtures. Leaving the old run in place would grade the proposal against its own ghost —
    two pipes in one lane, and a ``run_interference`` FAIL that is an artefact of the
    evaluation rather than of the route.

    ``proposal.replaces``, when set, is the whole answer. Otherwise a run the proposal ties
    INTO (an ancestor of what it replaces, with an end of the proposal on it) is never
    replaced, however much of its ``serves`` the proposal covers."""
    runs = {r.tag for r in (*model.pipe_runs, *model.ducts, *model.conduits)}
    if getattr(proposal, "replaces", ()):
        return set(proposal.replaces) & runs
    base = proposal.tag.split("-PROPOSED")[0]
    # **Runs only.** The base of a fixture branch's tag is the FIXTURE, not a run, and
    # dropping it from the candidate storey deletes the very thing the branch drains —
    # every check that reads the fixture then reports UNKNOWN and the evaluation blames
    # the proposal for it.
    out = {base} & runs
    descendants = _descendants(model, base, proposal.system)
    for run in model.pipe_runs:
        # **Same system, and that is not a refinement.** A fixture is served by a drain AND
        # a hot AND a cold run, all three naming it in ``serves``; without this test a drain
        # proposal deleted the supply lines to its own basin, and every ``pipe_ref`` on the
        # house's valves and fixtures then pointed at a run that no longer resolved. It is
        # invisible on a single ``--evaluate`` of one branch and unmissable the moment a
        # campaign evaluates seventeen at once.
        if run.system != proposal.system or run.tag in descendants:
            continue
        # A run replaced serves nothing the proposal does not: the trunk a branch ties
        # into serves the same fixture and stays.
        if proposal.serves and run.serves and set(run.serves) <= set(proposal.serves):
            out.add(run.tag)
    return out - _tied_into(model, proposal, out)


def _tied_into(model: ResolvedModel, proposal: RouteProposal, replaced: set[str]) -> set[str]:
    """Replaced-looking runs that are really the ones the proposal ties into: an ancestor
    (by tie-in) of another replaced run, with an end of the proposal standing on it."""
    parents = _tie_parents(model, proposal.system)
    ancestors = {up for tag in replaced for up in _chain(parents, tag)} & replaced
    if not ancestors or not proposal.points:
        return set()
    ends = (proposal.points[0], proposal.points[-1])
    out = set()
    for run in model.pipe_runs:
        if run.tag not in ancestors or not run.z_m or len(run.z_m) != len(run.path):
            continue
        line = [(x, y, z) for (x, y), z in zip(run.path, run.z_m, strict=False)]
        if any(_gap(end, line) <= 0.05 for end in ends):
            out.add(run.tag)
    return out


def _chain(parents: dict[str, str], tag: str) -> list[str]:
    out: list[str] = []
    while tag in parents and parents[tag] not in out:
        tag = parents[tag]
        out.append(tag)
    return out


def _gap(point: tuple, line: list[tuple]) -> float:
    """3-D distance from ``point`` to a polyline (a single vertex counts)."""
    import math

    best = float("inf")
    for a, b in zip(line, line[1:], strict=False) if len(line) > 1 else [(line[0], line[0])]:
        d = [b[i] - a[i] for i in range(3)]
        span = sum(v * v for v in d)
        t = 0.0 if span <= 0 else max(0.0, min(1.0, sum(
            (point[i] - a[i]) * d[i] for i in range(3)) / span))
        best = min(best, math.dist(point, [a[i] + t * d[i] for i in range(3)]))
    return best


def _tie_parents(model: ResolvedModel, system: str) -> dict[str, str]:
    """Child run -> the run it ties into, for the systems that derive one."""
    from typehaus.resolve.mep_ports import placed_ports
    from typehaus.resolve.mep_queries import drain_tie_ins
    from typehaus.resolve.mep_tie_ins import supply_tie_in_records

    runs = [r for r in model.pipe_runs if r.system == system]
    if system == "drain":
        return {c: p for c, p in drain_tie_ins(runs).items() if p}
    if system in ("water_cold", "water_hot"):
        return {rec.child: rec.parent
                for rec in supply_tie_in_records(runs, placed_ports(model)) if rec.parent}
    return {}


def _descendants(model: ResolvedModel, base: str, system: str) -> set[str]:
    """Runs that tie in (transitively) to ``base``. A trunk serves its branches' fixtures,
    but a branch hung off the trunk is downstream of the proposal, not replaced by it."""
    if not any(r.tag == base and r.system == system for r in model.pipe_runs):
        return set()
    parents = _tie_parents(model, system)
    out: set[str] = set()
    grew = True
    while grew:
        found = {c for c, p in parents.items() if (p == base or p in out) and c != base}
        grew = not found <= out
        out |= found
    return out


def _coverage_gaps(proposal: RouteProposal, findings: list[Finding]) -> list[str]:
    """What was NOT graded about this proposal, said out loud.

    An absent finding reads as a pass, and for a loop that iterates on the report that is
    the one error it cannot recover from. These are the known holes as of Phase 1 and each
    is closed by a named later phase rather than by this list growing quieter.
    """
    out: list[str] = []
    if not any(proposal.tag in f.element_tags for f in findings):
        out.append(f"{proposal.tag}: no check named this run at all — it is either outside "
                   "every MEP check's scope or its geometry is not evaluable")
    if proposal.kind == "duct" and proposal.routing == "exposed":
        out.append(f"{proposal.tag}: routed EXPOSED, so the bay and soffit occupancy checks "
                   "have nothing to grade it against — that is a real gap, not a pass")
    return out


def as_dict(item: Evaluation) -> dict:
    """Contract 3 of the roadmap: the evaluation report, as JSON-able data."""
    def value(item: Any) -> Any:
        return item.get("value") if isinstance(item, dict) else item

    def row(finding) -> dict:
        data = finding.model_dump(mode="json")
        return {"check_id": data.get("check_id"), "result": value(data.get("result")),
                "severity": value(data.get("severity")),
                "element_tags": list(data.get("element_tags") or ()),
                "message": data.get("message")}

    return {
        "tag": item.tag, "refused": item.refused,
        "introduced": [row(f) for f in item.introduced],
        "resolved": [row(f) for f in item.resolved],
        "coverage": list(item.coverage),
    }


def render_reports(evaluations: list[Evaluation]) -> list[str]:
    """The evaluation report, as console lines. Contract 3 of the roadmap."""
    lines: list[str] = []
    for item in evaluations:
        lines.append(f"[bold]evaluation {item.tag}[/bold]")
        if item.refused:
            lines.append(f"  [red]{item.refused}[/red]")
            continue
        if not item.introduced:
            lines.append("  [green]no new FAIL or UNKNOWN in the MEP set[/green]")
        for finding in item.introduced:
            lines.append(f"  [red]NEW {finding.result.value.upper()} "
                         f"{finding.check_id}: {finding.message}[/red]")
        for finding in item.resolved:
            lines.append(f"  [green]RESOLVED {finding.result.value.upper()} "
                         f"{finding.check_id}: {finding.message}[/green]")
        for note in item.coverage:
            lines.append(f"  [yellow]not graded: {note}[/yellow]")
    return lines
