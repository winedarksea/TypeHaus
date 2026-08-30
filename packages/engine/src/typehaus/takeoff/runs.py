"""Per-run routing quality: one row per pipe, duct and conduit run.

Every other MEP takeoff groups — pipe by system and diameter, duct by section, conduit by
trade size — because that is what an estimator orders against. Grouping is exactly wrong
for the question this module answers, which is *"is this run longer than it needs to be?"*.
That question is per run, and until now nothing in the engine asked it: ``model/mep.py``
declares auto-routing a non-goal, and a non-goal still leaves the authored route ungraded.

The row's four lengths are the whole idea:

``developed_ft``
    What gets billed — the resolver's own 3D length, plan run plus every rise.
``plan_ft`` / ``rise_ft``
    The two halves of it, so a long number can be read as "it wanders" or "it climbs".
``straight_ft``
    The 3D distance from the first vertex to the last: the shortest a run between those
    two points could possibly be. **3D, not plan** — a pure riser has zero plan length,
    and grading it against that would report every riser in the house as infinitely
    inefficient.

``ratio`` is ``developed / straight``, and it is a *report*, not a verdict. A high ratio can
be a bad route or it can be the only legal route; :mod:`typehaus.checks.mep.routing` is
where the line gets drawn, with a threshold and an UNKNOWN band. Here it only sorts.

Costs come from :func:`typehaus.cli.prices.rate_for` — the same join
:func:`~typehaus.cli.prices.estimate_costs` uses, so a run's cost and the estimate line it
rolls into cannot drift. ``[ducts]`` is qualified by material and would price a semi-rigid
radial at the sheet-metal rate under any second, hand-rolled lookup.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, SolidSweep
from typehaus.resolve.sweep import clean_path, sweep_turns
from typehaus.takeoff.plumbing import _MIN_FITTING_TURN_DEG

_M_TO_FT = 3.280839895013123

#: Below this a ``straight_ft`` denominator is noise — two vertices a few inches apart make
#: any ratio, and the run that produced them is a stub nobody is going to shorten.
MIN_STRAIGHT_FT = 1.0


def _plan_length_m(path: tuple[tuple[float, float], ...]) -> float:
    return sum(math.dist(a, b) for a, b in zip(path, path[1:], strict=False))


def _rise_m(z: tuple[float, ...]) -> float:
    return sum(abs(b - a) for a, b in zip(z, z[1:], strict=False))


def _straight_m(path: tuple[tuple[float, float], ...], z: tuple[float, ...]) -> float:
    """3D first-vertex-to-last-vertex distance — the shortest this run could be."""
    if len(path) < 2:
        return 0.0
    plan = math.dist(path[0], path[-1])
    drop = (z[-1] - z[0]) if len(z) == len(path) else 0.0
    return math.hypot(plan, drop)


def _elbows(path: tuple[tuple[float, float], ...], z: tuple[float, ...], size_m: float) -> int:
    """Interior turns, counted the way ``takeoff/mep.py`` bills fittings.

    Reused rather than restated: the same :func:`~typehaus.resolve.sweep.sweep_turns` walk,
    the same ``_MIN_FITTING_TURN_DEG`` floor that treats a change of pitch as a rake and not
    a fitting. A schedule that counted elbows differently from the section that buys them
    would be two answers to one question.
    """
    if len(path) != len(z) or len(path) < 3:
        return 0
    sweep = SolidSweep(
        path=clean_path([(x, y, height) for (x, y), height in zip(path, z, strict=False)]),
        profile=((max(size_m, M_PER_IN) / 2.0, 0.0),))
    return sum(1 for turn in sweep_turns(sweep) if turn.angle_deg >= _MIN_FITTING_TURN_DEG)


def conduit_vertex_z(run: Any) -> tuple[float, ...]:
    """A conduit's per-vertex z, which it does not carry.

    ``ResolvedConduitRun`` holds two end elevations and the convention that the run rises at
    its LAST point (→ ``model/mep.py`` ConduitRun). Reconstructing the profile that
    convention implies is what makes ``straight_ft`` and ``elbows`` honest for a raceway:
    without it every riser reads as a ratio-5 offender against a zero-length plan hypotenuse.

    Public because :mod:`typehaus.checks.mep.routing` needs the same reconstruction to decide
    which floor a raceway segment is *in* — one reading of the convention, not two.
    """
    start = run.z_start_m if run.z_start_m is not None else 0.0
    end = run.z_end_m if run.z_end_m is not None else start
    return (*([start] * (len(run.path) - 1)), end)


def _row(tag: str, uid: str, storey: str, system: str, kind: str, size_in: float,
         routing: str, path: tuple[tuple[float, float], ...], z: tuple[float, ...],
         developed_m: float, size_m: float, refs: str) -> dict[str, Any]:
    plan_m = _plan_length_m(path)
    straight_m = _straight_m(path, z)
    straight_ft = straight_m * _M_TO_FT
    developed_ft = developed_m * _M_TO_FT
    return {
        "tag": tag, "uid": uid, "storey": storey, "kind": kind, "system": system,
        "size_in": round(size_in, 2), "routing": routing, "refs": refs,
        "developed_ft": round(developed_ft, 2),
        "plan_ft": round(plan_m * _M_TO_FT, 2),
        "rise_ft": round(_rise_m(z) * _M_TO_FT, 2),
        "straight_ft": round(straight_ft, 2),
        # None rather than a number when the denominator is noise — see MIN_STRAIGHT_FT.
        # A ratio of "inf" printed beside a 9" stub is a distraction, not a finding.
        "ratio": (round(developed_ft / straight_ft, 2)
                  if straight_ft >= MIN_STRAIGHT_FT else None),
        "elbows": _elbows(path, z, size_m),
        "vertices": len(path),
    }


def _price(prices: Any, section: str, key: object, qualifier: object,
           quantity_ft: float) -> dict[str, Any]:
    """The run's own $ line, or an explicit miss. Never a silent zero."""
    from typehaus.cli.prices import rate_for

    resolved, rate = rate_for(prices, section, key, qualifier)
    if rate is None:
        return {"price_key": resolved, "cost_low": None, "cost_high": None}
    cost = rate.times(quantity_ft)
    return {"price_key": resolved,
            "cost_low": round(cost.low, 2), "cost_high": round(cost.high, 2)}


def run_schedule(model: ResolvedModel, prices: Any = None) -> list[dict[str, Any]]:
    """One row per ``PipeRun`` / ``DuctRun`` / ``ConduitRun``, worst ratio first.

    ``prices`` is optional and the house's own (decision #28); without it the rows carry
    every length and no dollars. With it, each row prices through the *same*
    :func:`~typehaus.cli.prices.rate_for` join the estimate uses.

    Sorted by ``ratio`` descending with ``developed_ft`` breaking ties, because the reader's
    question is "which run should I look at first" and the answer is the longest detour, not
    the alphabetically first tag. Rows whose denominator was too short to grade sort last.
    """
    rows: list[dict[str, Any]] = []

    for run in model.pipe_runs:
        z = run.z_m if run.z_m is not None and len(run.z_m) == len(run.path) else ()
        row = _row(run.tag, run.uid, run.storey, run.system, "pipe",
                   run.diameter_m / M_PER_IN, "—", tuple(run.path), tuple(z),
                   run.length_m, run.diameter_m,
                   ", ".join(run.serves))
        if prices is not None:
            row.update(_price(prices, "pipe_runs", run.system, None, row["developed_ft"]))
        rows.append(row)

    for duct in model.ducts:
        size_m = duct.diameter_m if duct.diameter_m is not None else max(duct.width_m,
                                                                        duct.depth_m)
        z = duct.z_m if len(duct.z_m) == len(duct.path) else ()
        row = _row(duct.tag, duct.uid, duct.storey, duct.system, "duct",
                   size_m / M_PER_IN, duct.routing, tuple(duct.path), tuple(z),
                   duct.length_m, size_m,
                   duct.floor_ref or duct.soffit_ref or "")
        if prices is not None:
            row.update(_price(prices, "ducts", duct.system, duct.material,
                              row["developed_ft"]))
        rows.append(row)

    for raceway in model.conduits:
        z = conduit_vertex_z(raceway)
        # Power and comms are two different orders on two different days — the same split
        # ``conduit_takeoff`` and ``data_raceway_takeoff`` make, so the $ here lands in the
        # section the estimate would have put it in.
        is_data = raceway.service in ("data", None)
        row = _row(raceway.tag, raceway.uid, raceway.storey, raceway.service or "spare",
                   "conduit", raceway.trade_size_m / M_PER_IN, "—", tuple(raceway.path), z,
                   raceway.length_m, raceway.trade_size_m,
                   " → ".join(part for part in (raceway.from_ref, raceway.to_ref) if part))
        if prices is not None:
            section = "data_raceways" if is_data else "conduit"
            key: object = (raceway.service or "spare") if is_data else row["size_in"]
            row.update(_price(prices, section, key, None, row["developed_ft"]))
        rows.append(row)

    rows.sort(key=lambda item: (item["ratio"] is None,
                                -(item["ratio"] or 0.0),
                                -float(item["developed_ft"])))
    return rows


def conduit_schedule(model: ResolvedModel) -> list[dict[str, Any]]:
    """Every raceway as a *run*, power and comms together — the pull list.

    ``takeoff/electrical.py::conduit_takeoff`` and ``takeoff/data.py::data_raceway_takeoff``
    each group a disjoint half by trade size, which is right for ordering pipe and useless
    for the reader asking "what is in this raceway and where does it go". Neither one can
    answer it alone, and the answer is per run.

    It lives here rather than in ``takeoff/electrical.py`` because that module is already
    598 lines, over the 500-line limit ``AGENTS.md`` sets, and because a conduit is a *run*
    — the same object this module schedules pipe and duct as.
    """
    return [
        {"tag": run.tag, "uid": run.uid, "storey": run.storey,
         "service": run.service or "spare",
         "trade_size_in": round(run.trade_size_m / M_PER_IN, 2),
         "from_ref": run.from_ref, "to_ref": run.to_ref,
         "length_ft": round(run.length_m * _M_TO_FT, 1),
         "vertices": len(run.path)}
        for run in sorted(model.conduits, key=lambda item: item.tag)
    ]
