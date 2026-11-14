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
from pathlib import Path
from typing import TYPE_CHECKING, Any

from typehaus.cli.route_check_groups import (
    BORE_CHECKS,
    CLEANOUT_CHECKS,
    DUCT_CHECKS,
    FITTING_PATTERN_CHECKS,
    TRAP_ARM_CHECKS,
    VENT_CHECKS,
    bores,
    segments,
)
from typehaus.cli.route_scorecard_modes import Found, propose_target
from typehaus.cli.route_scorecard_targets import TARGETS, ScoreTarget

__all__ = ["TARGETS", "ScoreTarget", "run_scorecard", "write_scorecard", "regressions",
           "markdown"]

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost
    from typehaus.routing.proposal import RouteProposal

#: Per-metric slack before a rise counts as a regression. Everything absent is an integer
#: count compared exactly. Search time is a wall clock and wanders with the machine.
TOLERANCE: dict[str, tuple[float, float]] = {  # metric -> (factor, absolute)
    "developed_ft": (1.10, 0.5),
    "search_s": (2.0, 5.0),
}

#: Metrics where MORE is better.
HIGHER_IS_BETTER = frozenset({"proposals", "cleanouts_placed", "rack_shared", "relaid"})


#: ``run_scorecard``'s per-card state, set before the fork so workers inherit it copy-on-write.
_CARD: dict[str, Any] = {}

#: Rows start longest first (a pool's tail is its slowest row): whole-network searches, then
#: campaigns and groups, then the rest.
_WEIGHT = {"tree": 0, "trunk": 0, "lift": 0, "house": 1, "manifold": 1, "group": 1}


def run_scorecard(directory: Path, model: ResolvedModel, cost: RouteCost,
                  targets: tuple[ScoreTarget, ...] = TARGETS,
                  jobs: int | None = None) -> dict[str, Any]:
    """Search, measure and grade every target; ``{"targets": {...}, "totals": {...}}``.

    Rows are independent, so each runs search and evaluation in a forked worker (``jobs``, else
    ``$HAUS_SCORECARD_JOBS``, else half the cores up to 4; 1 runs in-process). Metrics are the
    same either way; ``search_s`` is a wall clock and reads a little higher under load."""
    import multiprocessing
    import os

    from typehaus.cli.route_eval import baseline_findings

    jobs = jobs or int(os.environ.get("HAUS_SCORECARD_JOBS", 0)) or min(
        4, max(1, (os.cpu_count() or 2) // 2))
    _CARD.update(directory=directory, model=model, cost=cost,
                 baseline=baseline_findings(model, directory),
                 targets={t.name: t for t in targets})
    order = sorted(targets, key=lambda t: _WEIGHT.get(t.mode, 2))
    try:
        if jobs == 1 or len(targets) == 1 or not hasattr(os, "fork"):
            rows = [_row(t.name) for t in order]
        else:
            with multiprocessing.get_context("fork").Pool(min(jobs, len(targets))) as pool:
                rows = list(pool.imap_unordered(_row, [t.name for t in order]))
    finally:
        _CARD.clear()
    by_name = dict(rows)
    out = {t.name: by_name[t.name] for t in targets}
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


def _row(name: str) -> tuple[str, dict[str, Any]]:
    """One target: search it, grade the whole result as a network, and measure it."""
    from typehaus.cli.route_eval import evaluate_network

    card = _CARD
    start = time.perf_counter()
    found = propose_target(card["directory"], card["model"], card["targets"][name],
                           card["cost"])
    seconds = time.perf_counter() - start
    evaluation = (evaluate_network(card["directory"], card["model"], found.proposals,
                                   baseline=card["baseline"])
                  if found.proposals else None)
    return name, _metrics(card["model"], found, seconds,
                          evaluation.introduced if evaluation else [], card["cost"],
                          refused=evaluation.refused if evaluation else None,
                          coverage=evaluation.coverage if evaluation else ())


def _metrics(model: ResolvedModel, found: Found, seconds: float, introduced: list[Any],
             cost: RouteCost, refused: str | None = None,
             coverage: Sequence[str] = ()) -> dict[str, Any]:
    """``refused``/``coverage`` come from the evaluation: a refused or uncovered grade is
    ungraded, not clean, so it is counted rather than folded into 0 FAIL."""
    from typehaus.resolve.mep_fitting_direction import forbidden_turns
    from typehaus.resolve.mep_fittings import SERVICE_BY_SYSTEM
    from typehaus.routing.rack import rack_shared

    proposals = found.proposals
    fittings: Counter[str] = Counter()
    forbidden = 0
    for proposal in proposals:
        for record in proposal.fittings():
            fittings[record.order_key.rsplit("-", 1)[0]] += 1
        service = SERVICE_BY_SYSTEM.get(proposal.system, proposal.system)
        forbidden += len(forbidden_turns(service, proposal.points,
                                         getattr(proposal, "patterns", None)))

    def count(ids: frozenset[str], results: tuple[str, ...] = ("fail", "unknown")) -> int:
        return sum(1 for f in introduced if f.check_id in ids and f.result.value in results)

    return {
        "proposals": len(proposals),
        "refusals": found.refused,
        "relaid": found.relaid,
        "relay_refused": found.relay_refused,
        "developed_ft": round(sum(p.developed_ft() for p in proposals
                                  if found.ft_tag in (None, p.tag)), 2),
        "fittings": dict(sorted(fittings.items())),
        "forbidden_fittings": forbidden,
        "bores": dict(sorted(bores(model, proposals).items())),
        "illegal_bores": count(BORE_CHECKS, ("fail",)),
        "trap_arm_gaps": count(TRAP_ARM_CHECKS),
        "vent_gaps": count(VENT_CHECKS),
        "fitting_pattern_gaps": count(FITTING_PATTERN_CHECKS),
        "duct_gaps": count(DUCT_CHECKS),
        "campaign_lifts": found.lifts,
        "cleanouts_required": count(CLEANOUT_CHECKS),
        "cleanouts_placed": sum(len(getattr(p, "cleanouts", ())) for p in proposals),
        "exterior_wall_ft": round(sum(_exterior_ft(model, p) for p in proposals), 2),
        "rack_shared": rack_shared(proposals, spacing_m=cost.rack_spacing_in * 0.0254),
        "eval_fail": sum(1 for f in introduced if f.result.value == "fail"),
        "eval_unknown": sum(1 for f in introduced if f.result.value == "unknown"),
        "eval_refused": int(bool(refused)),
        "eval_coverage_gaps": len(coverage),
        "search_s": round(seconds, 2),
    }


def _exterior_ft(model: ResolvedModel, proposal: RouteProposal) -> float:
    """Feet of this proposal inside an exterior insulated wall's stud cavity."""
    from shapely.geometry import LineString, Polygon

    from typehaus.routing.obstacles import exterior_cavities

    total = 0.0
    for a, b, za, zb in segments(proposal):
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
        if after.get("proposals", 0) > 0 and after.get("eval_refused", 0) > 0:
            out.append(f"{name}: evaluation refused (candidate would not resolve), ungraded")
        # New keys absent from an older baseline compare against 0.
        for key, old in {"eval_refused": 0, "eval_coverage_gaps": 0, **before}.items():
            if key == "eval_refused":
                continue  # reported above, whatever the baseline says
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
