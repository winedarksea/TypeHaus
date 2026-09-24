"""``--evaluate``: run the checks against a model that HOLDS the proposal, and diff.

This is the second half of the loop and the half the router cannot do for itself. A search
result is not a fact about the building — ``routing`` may not import ``checks``, for the
reason ``cmd_route``'s docstring gives — so the only honest way to learn whether a proposed
route is any good is to build a candidate model containing it and grade that model with the
same checks that gate the build.

**No source round-trip and no file written.** The candidate is built by constructing the
``PipeRun``/``DuctRun``/``ConduitRun`` objects directly and handing them to
``PlanModel.with_elements``, so the house on disk is untouched and the dialect printer is
not in the loop. What is graded is the geometry, which is what the proposal is about.

**The report is a DIFF, not a report card.** Catlin is not clean in the MEP set and is not
required to be; what matters about a proposal is what it changes. A finding the house
already carries is not this route's fault and printing it as though it were would bury the
one line that is.

Cost is one resolve + one check run per alternative, which is why this is opt-in.
"""

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
    """The graded findings of ``plan``, with ``[checks] suppress`` LIFTED.

    A house working an open campaign blanket-suppresses exactly the checks a route can
    break — catlin suppresses ``mep.run_interference`` and ``mep.riser_through_deck`` — and
    ``run_checks`` drops a suppressed finding before this diff ever sees it. So a proposal
    laned through a duct used to print "no new FAIL". Both sides of the diff are lifted,
    so a clash the house already carries is still not this route's fault.
    """
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


def evaluate_proposals(directory: Path, model: ResolvedModel,
                       proposals: list[RouteProposal]) -> list[Evaluation]:
    """One :class:`Evaluation` per proposal, each against the house's own baseline."""
    baseline = {_key(f): f for f in _findings(model.plan, directory)}

    out = []
    for proposal in proposals:
        out.append(_evaluate_one(directory, model, proposal, baseline))
    return out


def _evaluate_one(directory: Path, model: ResolvedModel, proposal: RouteProposal,
                  baseline: dict[tuple, Finding]) -> Evaluation:
    result = Evaluation(tag=proposal.tag)
    try:
        candidate = _candidate_plan(model, proposal)
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
                         if key not in baseline and f.result.value in ("fail", "unknown")]
    result.resolved = [f for key, f in baseline.items()
                       if key not in seen and f.result.value in ("fail", "unknown")]
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
    # `_len` is the SAME literal the proposal prints, so the candidate graded here and the
    # source a person pastes describe one run. Building a `Length` from raw metres instead
    # would grade geometry a sixteenth of an inch off the one that was offered.

    storey = _storey_for(model, proposal)
    datum = next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    path = tuple(Point2D(_len(x), _len(y)) for x, y, _z in proposal.points)

    if proposal.kind == "pipe":
        element = PipeRun(
            tag=proposal.tag, system=PipeSystem(proposal.system), path=path,
            diameter=_len(proposal.diameter_m),
            elevations=tuple(_len(z - datum) for _x, _y, z in proposal.points),
            serves=proposal.serves)
    elif proposal.kind == "duct":
        section: dict[str, Any] = ({"width": _len(proposal.width_m),
                                    "depth": _len(proposal.depth_m)}
                                   if proposal.width_m or proposal.depth_m
                                   else {"diameter": _len(proposal.diameter_m)})
        element = DuctRun(
            tag=proposal.tag, system=DuctSystem(proposal.system), path=path, **section,
            routing=DuctRouting(proposal.routing or "exposed"),
            floor_ref=proposal.floor_ref, soffit_ref=proposal.soffit_ref,
            elevations=tuple(_len(z - datum) for _x, _y, z in proposal.points))
    else:
        # **The WHOLE raceway, with a z at every vertex** (2026-09-19). This used to grade
        # the legalised FIRST LEG only — a raceway was a plan polyline plus two end
        # elevations, so a route with two changes of height was not one element and the
        # evaluation could only speak for part of it. ``ConduitRun.elevations`` retired
        # that: the candidate is the route as found, and an evaluation that grades a
        # fraction of a proposal is worse than no evaluation, because it reads as one.
        #
        # **No datum subtraction.** A raceway's elevations are project-frame ABSOLUTE,
        # because a trunk crosses storeys and a panel-to-attic riser has no one storey to
        # be relative to. The duct branch above subtracts because a DuctRun's are
        # storey-relative; doing it here would grade a run a storey out of place.
        element = ConduitRun(
            tag=proposal.tag,
            path=tuple(Point2D(_len(x), _len(y)) for x, y, _z in proposal.points),
            trade_size=_len(proposal.diameter_m),
            elevations=tuple(_len(z) for _x, _y, z in proposal.points),
            service=Service(proposal.system) if proposal.system else None)

    return storey, element


def _candidate_plan(model: ResolvedModel, proposal: RouteProposal) -> Any:
    """The house's plan with this proposal's element added, and what it replaces removed."""
    storey, element = candidate_element(model, proposal)
    replaced = _replaced_tags(model, proposal)
    keep = [e for e in model.plan.storey_elements(storey)
            if getattr(e, "tag", None) not in replaced]
    return model.plan.with_elements(storey, (*keep, element))


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
        replaced |= _replaced_tags(model, proposal)

    plan = model.plan
    for storey, elements in by_storey.items():
        keep = [e for e in plan.storey_elements(storey)
                if getattr(e, "tag", None) not in replaced]
        plan = plan.with_elements(storey, (*keep, *elements))
    return plan


def evaluate_network(directory: Path, model: ResolvedModel,
                     proposals: list[RouteProposal]) -> Evaluation:
    """Contract 3 for a whole campaign: the MEP checks against ALL of it at once.

    The per-route evaluation answers "does this lane work"; this answers "does this SET
    work", which is a different question and the one a campaign is for. Drain capacity and
    slope, vent connectivity, bay packing, run-against-run interference and the ERV static
    budget are all network properties, and every one of them is already a check — so this
    runs the same registry over a candidate model holding the whole result rather than
    restating any of it here.
    """
    result = Evaluation(tag="campaign")
    if not proposals:
        result.refused = "nothing was laid, so there is no network to grade"
        return result
    try:
        baseline = {_key(f): f for f in _findings(model.plan, directory)}
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
                         if key not in baseline and f.result.value in ("fail", "unknown")]
    result.resolved = [f for key, f in baseline.items()
                       if key not in seen and f.result.value in ("fail", "unknown")]
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
    evaluation rather than of the route."""
    base = proposal.tag.split("-PROPOSED")[0]
    # **Runs only.** The base of a fixture branch's tag is the FIXTURE, not a run, and
    # dropping it from the candidate storey deletes the very thing the branch drains —
    # every check that reads the fixture then reports UNKNOWN and the evaluation blames
    # the proposal for it.
    runs = {r.tag for r in (*model.pipe_runs, *model.ducts, *model.conduits)}
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
        if proposal.serves and any(tag in run.serves for tag in proposal.serves):
            out.add(run.tag)
    return out


def _descendants(model: ResolvedModel, base: str, system: str) -> set[str]:
    """Runs that tie in (transitively) to ``base``. A trunk serves its branches' fixtures,
    but a branch hung off the trunk is downstream of the proposal, not replaced by it."""
    from typehaus.resolve.mep_ports import placed_ports
    from typehaus.resolve.mep_queries import drain_tie_ins
    from typehaus.resolve.mep_tie_ins import supply_tie_in_records

    runs = [r for r in model.pipe_runs if r.system == system]
    if not any(r.tag == base for r in runs):
        return set()
    if system == "drain":
        parents = drain_tie_ins(runs)
    else:
        parents = {rec.child: rec.parent
                   for rec in supply_tie_in_records(runs, placed_ports(model)) if rec.parent}
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


def payload(directory: Path, storey: str, datum_for, proposals: list[RouteProposal],
            evaluations: list[Evaluation], problems: list[str],
            notices: list[str], refusals: list | None = None) -> dict:
    """Contracts 2 and 3 of the roadmap, together and in one shape.

    Together because a proposal and what it does to the house are one answer: shipping the
    first without the second is what "the engine proposes" would mean with nobody judging
    it. ``datum_for`` maps a proposal's storey to the elevation its source is written
    against — zero for a raceway, whose elevations are project-frame absolute.
    """
    return {
        "house": str(directory),
        "storey": storey,
        "proposals": [p.as_dict(storey_datum_m=datum_for(p)) for p in proposals],
        "evaluations": [as_dict(e) for e in evaluations],
        "problems": list(problems),
        "notices": list(notices),
        # Contract 3's blocked terminals, structured: the tag, where the conflict is, and
        # the mobility class that says what could be done about it. ``problems`` carries
        # the same facts as prose for a human reader; this is the half an agent reads.
        "refusals": [r.payload() for r in (refusals or [])],
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
