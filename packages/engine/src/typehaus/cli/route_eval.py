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
    from typehaus.checks import build_context, run_checks

    ctx, _ = build_context(model.plan, directory)
    baseline = {_key(f): f for f in graded(run_checks(ctx).findings)}

    out = []
    for proposal in proposals:
        out.append(_evaluate_one(directory, model, proposal, baseline))
    return out


def _evaluate_one(directory: Path, model: ResolvedModel, proposal: RouteProposal,
                  baseline: dict[tuple, Finding]) -> Evaluation:
    from typehaus.checks import build_context, run_checks

    result = Evaluation(tag=proposal.tag)
    try:
        candidate = _candidate_plan(model, proposal)
    except (ValueError, TypeError, KeyError) as exc:
        result.refused = f"the candidate elements would not build: {exc}"
        return result
    try:
        ctx, _ = build_context(candidate, directory)
        findings = graded(run_checks(ctx).findings)
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


def _candidate_plan(model: ResolvedModel, proposal: RouteProposal) -> Any:
    """The house's plan with this proposal's element added, and what it replaces removed.

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
        # A raceway's elevations are project-frame absolute and it rises only at its last
        # vertex, so only the legalised first leg is representable as one element. The
        # evaluation grades that leg and the coverage note below says the rest is not here.
        from typehaus.routing.trades.conduit import legalize

        leg = legalize(proposal.points)[0]
        element = ConduitRun(
            tag=proposal.tag,
            path=tuple(Point2D(_len(x), _len(y)) for x, y in leg.points),
            trade_size=_len(proposal.diameter_m),
            start_elevation=_len(leg.z_m),
            end_elevation=_len(leg.rise_to_m if leg.rise_to_m is not None
                               else leg.z_m),
            service=Service(proposal.system) if proposal.system else None)

    replaced = _replaced_tags(model, proposal)
    keep = [e for e in model.plan.storey_elements(storey)
            if getattr(e, "tag", None) not in replaced]
    return model.plan.with_elements(storey, (*keep, element))


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
    for run in model.pipe_runs:
        if proposal.serves and any(tag in run.serves for tag in proposal.serves):
            out.add(run.tag)
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
    if proposal.kind == "conduit":
        out.append(f"{proposal.tag}: only the first flat leg is in the candidate model — a "
                   "ConduitRun rises at its last vertex, so a multi-plane route is several "
                   "elements and this grades one of them")
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
