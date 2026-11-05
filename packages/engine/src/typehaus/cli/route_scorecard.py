"""``haus route --scorecard``: one fixed set of catlin targets, measured the same way each time.

The router is tuned toward how a plumber would lay it out (docs/routing.md, "Plumber's
rules"), and a change can only be said to help when it is measured. Each target is searched
as ``haus route`` would search it, every proposal is graded with ``--evaluate``'s own
machinery, and the numbers land in one dict. ``tests/test_route_scorecard.py`` compares it
with the checked-in baseline and refuses a regression.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost
    from typehaus.routing.proposal import RouteProposal


@dataclass(frozen=True)
class ScoreTarget:
    name: str
    mode: str  # "tree" | "fixture" | "run"
    tag: str
    level: str | None = None


#: The fixed list: a drain tree per storey, the three fixtures with no 3D vent (TODO C6-E7),
#: the hand-drawn kitchen drain, and three supply runs.
TARGETS: tuple[ScoreTarget, ...] = (
    ScoreTarget("tree:basement", "tree", "PR-B-BATH-DRAIN"),
    ScoreTarget("tree:main", "tree", "PR-B-MAIN-DRAIN", level="main"),
    ScoreTarget("tree:second", "tree", "PR-M-S-SUITE-DRAIN"),
    ScoreTarget("fixture:BATH2-TUB", "fixture", "FX-M-BATH2-TUB"),
    ScoreTarget("fixture:SUITEBATH-LAV", "fixture", "FX-S-SUITEBATH-LAV"),
    ScoreTarget("fixture:SUITEBATH-TUBSH", "fixture", "FX-S-SUITEBATH-TUBSH"),
    ScoreTarget("run:KITCH-DRAIN", "run", "PR-B-KITCH-DRAIN"),
    ScoreTarget("run:SUITE-LAV-CW", "run", "PR-S-SUITE-LAV-CW"),
    ScoreTarget("run:BATH2-LAV-HW", "run", "PR-M-BATH2-LAV-HW"),
    ScoreTarget("run:CW-SUITE", "run", "PR-B-CW-SUITE"),
)

#: ``--evaluate`` check ids each metric reads, by what they grade.
BORE_CHECKS = frozenset({
    "mep.run_through_stud", "mep.run_through_plate", "mep.run_through_header",
    "mep.run_member_crossing", "mep.run_through_floor_member", "mep.run_in_joist_flange",
    "mep.run_through_blocking", "mep.run_through_beam"})
TRAP_ARM_CHECKS = frozenset({"mep.trap_arm_length"})
VENT_CHECKS = frozenset({"mep.vent_reachability", "mep.vent_grade",
                         "mep.vent_termination_height"})
CLEANOUT_CHECKS = frozenset({"mep.drain_cleanouts"})

#: Per-metric slack before a rise counts as a regression. Everything absent is an integer
#: count compared exactly. Search time is a wall clock and wanders with the machine.
TOLERANCE: dict[str, tuple[float, float]] = {  # metric -> (factor, absolute)
    "developed_ft": (1.10, 0.5),
    "search_s": (2.0, 5.0),
}

#: Metrics where MORE is better.
HIGHER_IS_BETTER = frozenset({"proposals", "cleanouts_placed", "rack_shared"})


def run_scorecard(directory: Path, model: ResolvedModel, cost: RouteCost,
                  targets: tuple[ScoreTarget, ...] = TARGETS) -> dict[str, Any]:
    """Search, measure and grade every target; ``{"targets": {...}, "totals": {...}}``."""
    from typehaus.cli.route_eval import baseline_findings, evaluate_network

    found: dict[str, tuple[list[RouteProposal], int, float]] = {}
    for target in targets:
        start = time.perf_counter()
        proposals, expected = _propose_target(model, target, cost)
        found[target.name] = (proposals, expected, time.perf_counter() - start)

    baseline = baseline_findings(model, directory)
    out: dict[str, dict[str, Any]] = {}
    for target in targets:
        proposals, expected, seconds = found[target.name]
        evaluation = (evaluate_network(directory, model, proposals, baseline=baseline)
                      if proposals else None)
        out[target.name] = _metrics(model, proposals, expected, seconds, evaluation, cost)
    totals: dict[str, Any] = {}
    for metrics in out.values():
        for key, value in metrics.items():
            if isinstance(value, dict):
                bucket = totals.setdefault(key, {})
                for sub, count in value.items():
                    bucket[sub] = bucket.get(sub, 0) + count
            else:
                totals[key] = round(totals.get(key, 0) + value, 3)
    return {"targets": out, "totals": totals}


def _propose_target(model: ResolvedModel, target: ScoreTarget, cost: RouteCost
                    ) -> tuple[list[RouteProposal], int]:
    """``(proposals, terminals expected)`` — a tree expects one branch per fixture served."""
    from typehaus.cli.cmd_route import _propose
    from typehaus.cli.cmd_route_tree import _propose_tree

    if target.mode == "tree":
        made, _problems, _notices, _refusals = _propose_tree(
            model, target.tag, slope=None, margin_ft=8.0, level=target.level,
            avoid=frozenset(), via=[], explain=False, cost=cost)
        return [p for p, _s in made], _tree_terminals(model, target)
    made, _problems, _notices, _refusals = _propose(
        model, [target.tag], mode=target.mode, slope=None, margin_ft=8.0, band=None,
        avoid=frozenset(), via=[], explain=False, cost=cost)
    return [p for p, _s in made], 1


def _tree_terminals(model: ResolvedModel, target: ScoreTarget) -> int:
    from typehaus.cli.route_support import _storey_of
    from typehaus.model.spatial import Fixture

    main = next((r for r in model.pipe_runs if r.tag == target.tag), None)
    if main is None:
        return 1
    fixtures = [t for t in main.serves if isinstance(model.plan.by_tag(t), Fixture)]
    if target.level is not None:
        fixtures = [t for t in fixtures if _storey_of(model, t) == target.level]
    return max(1, len(fixtures))


def _metrics(model: ResolvedModel, proposals: list[RouteProposal], expected: int,
             seconds: float, evaluation: Any, cost: RouteCost) -> dict[str, Any]:
    from typehaus.resolve.mep_fitting_direction import forbidden_turns
    from typehaus.resolve.mep_fittings import SERVICE_BY_SYSTEM
    from typehaus.routing.rack import rack_shared

    fittings: Counter[str] = Counter()
    forbidden = 0
    for proposal in proposals:
        for record in proposal.fittings():
            fittings[record.order_key.rsplit("-", 1)[0]] += 1
        service = SERVICE_BY_SYSTEM.get(proposal.system, proposal.system)
        forbidden += len(forbidden_turns(service, proposal.points,
                                         getattr(proposal, "patterns", None)))
    introduced = list(evaluation.introduced) if evaluation is not None else []

    def count(ids: frozenset[str], results: tuple[str, ...] = ("fail", "unknown")) -> int:
        return sum(1 for f in introduced if f.check_id in ids and f.result.value in results)

    return {
        "proposals": len(proposals),
        "refusals": max(0, expected - len({p.tag for p in proposals})),
        "developed_ft": round(sum(p.developed_ft() for p in proposals), 2),
        "fittings": dict(sorted(fittings.items())),
        "forbidden_fittings": forbidden,
        "bores": dict(sorted(_bores(model, proposals).items())),
        "illegal_bores": count(BORE_CHECKS, ("fail",)),
        "trap_arm_gaps": count(TRAP_ARM_CHECKS),
        "vent_gaps": count(VENT_CHECKS),
        "cleanouts_required": count(CLEANOUT_CHECKS),
        "cleanouts_placed": sum(len(getattr(p, "cleanouts", ())) for p in proposals),
        "exterior_wall_ft": round(sum(_exterior_ft(model, p) for p in proposals), 2),
        "rack_shared": rack_shared(proposals, spacing_m=cost.rack_spacing_in * 0.0254),
        "eval_fail": sum(1 for f in introduced if f.result.value == "fail"),
        "eval_unknown": sum(1 for f in introduced if f.result.value == "unknown"),
        "search_s": round(seconds, 2),
    }


def _segments(proposal: RouteProposal):
    for a, b in zip(proposal.points, proposal.points[1:], strict=False):
        yield (a[0], a[1]), (b[0], b[1]), a[2], b[2]


def _bores(model: ResolvedModel, proposals: list[RouteProposal]) -> Counter[str]:
    """Members each proposal passes through, by kind: stud/plate/header, joist, truss pass."""
    from shapely.geometry import LineString, box

    from typehaus.resolve.mep_bore_geometry import leg_crossings as wall_crossings
    from typehaus.resolve.mep_crossings import leg_crossings as floor_crossings
    from typehaus.resolve.mep_crossings import member_window
    from typehaus.resolve.pipe_sections import pipe_outside_diameter_m

    out: Counter[str] = Counter()
    kinds = {f.tag: getattr(member_window(f), "kind", None) for f in model.floors}
    for proposal in proposals:
        radius = pipe_outside_diameter_m(proposal.diameter_m,
                                         proposal.echo.get("material")) / 2.0
        for a, b, za, zb in _segments(proposal):
            reach = (LineString([a, b]) if a != b else LineString([a, (a[0] + 1e-6, a[1])])
                     ).buffer(radius + 0.01)
            for wall in model.walls:
                if not wall.members or not reach.intersects(box(*_wall_bounds(wall))):
                    continue
                for cut in wall_crossings(wall, a, b, za, zb, radius):
                    out[cut.category] += 1
            for floor in model.floors:
                kind = {"open_web": "truss_pass", "i_joist": "i_joist"}.get(
                    kinds[floor.tag], "joist")
                out[kind] += len(floor_crossings(floor, a, b, za, zb))
    return out


def _wall_bounds(wall: Any) -> tuple[float, float, float, float]:
    xs = [p[0] for layer in wall.layers for p in layer.polygon] or [wall.axis[0][0]]
    ys = [p[1] for layer in wall.layers for p in layer.polygon] or [wall.axis[0][1]]
    return (min(xs), min(ys), max(xs), max(ys))


def _exterior_ft(model: ResolvedModel, proposal: RouteProposal) -> float:
    """Feet of this proposal inside an exterior insulated wall's stud cavity."""
    from shapely.geometry import LineString, Polygon

    from typehaus.routing.obstacles import exterior_cavities

    total = 0.0
    for a, b, za, zb in _segments(proposal):
        segment = LineString([a, b]) if a != b else None
        for _tag, ring, z0, z1 in exterior_cavities(model):
            if not (z0 <= (za + zb) / 2.0 <= z1):
                continue
            if segment is None:
                if Polygon(ring).covers(LineString([a, a]).centroid):
                    total += abs(zb - za)
                continue
            total += segment.intersection(Polygon(ring)).length
    return total / 0.3048


def write_scorecard(directory: Path, model: ResolvedModel, cost: RouteCost,
                    out_dir: Path | None) -> int:
    """Run the scorecard, print its table, and write ``report.json``/``scorecard.md``."""
    import json

    from typehaus.cli._shared import console

    card = run_scorecard(directory, model, cost)
    table = markdown(card)
    console.print(table, markup=False, highlight=False)
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "report.json").write_text(json.dumps(card, indent=1, sort_keys=True) + "\n")
        (out_dir / "scorecard.md").write_text(table)
    return 0


def regressions(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Every metric that got worse than the baseline allows, as a sentence each."""
    out: list[str] = []
    for name, before in baseline.get("targets", {}).items():
        after = current.get("targets", {}).get(name)
        if after is None:
            out.append(f"{name}: missing from the current scorecard")
            continue
        for key, old in before.items():
            new = after.get(key)
            if isinstance(old, dict):
                old, new = sum(old.values()), sum((new or {}).values())
                key = f"{key} (total)"
            if new is None:
                continue
            if _worse(key, float(old), float(new)):
                out.append(f"{name}: {key} {old} -> {new}")
    return out


def _worse(key: str, old: float, new: float) -> bool:
    if key in HIGHER_IS_BETTER:
        return new < old
    factor, absolute = TOLERANCE.get(key, (1.0, 0.0))
    return new > max(old * factor, old + absolute) + 1e-9


def markdown(card: dict[str, Any]) -> str:
    """The scorecard as one table: a row per target, a column per scalar metric."""
    rows = card["targets"]
    columns = [k for k, v in next(iter(rows.values())).items() if not isinstance(v, dict)]
    lines = ["| target | " + " | ".join(columns) + " |",
             "|---|" + "---|" * len(columns)]
    for name, metrics in [*rows.items(), ("TOTAL", card["totals"])]:
        lines.append(f"| {name} | " + " | ".join(str(metrics.get(c, "")) for c in columns)
                     + " |")
    for key in ("fittings", "bores"):
        lines.append(f"\n{key}: " + ", ".join(f"{k} {v}" for k, v in
                                               sorted(card["totals"].get(key, {}).items())))
    return "\n".join(lines) + "\n"
