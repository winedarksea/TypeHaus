"""MEP quantities: pipe and duct by the lineal foot, sleeves by the piece.

All three were resolved and none was billed. ``ResolvedPipeRun`` has carried ``length_m``,
``diameter_m`` and ``system`` since MEP Phase 2; ``ResolvedDuct`` its path and section;
``ResolvedSleeve`` its diameters. The BOM simply never asked.

Grouping is by what an estimator actually orders against — pipe by system *and* diameter
(3" DWV and 3/4" copper are different orders), duct by system and section, sleeves by
diameter — the same "group on the thing that changes the price" rule the framing and glazing
sections already follow.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895
_M_TO_IN = 39.37007874015748


def pipe_run_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of pipe, grouped by system and nominal diameter.

    ``length_m`` is the resolver's own developed length — plan run plus any rise — so a
    drop through a floor is not billed as the zero plan length it projects to.
    """
    runs: dict[tuple[str, float], dict[str, object]] = {}
    for run in model.pipe_runs:
        key = (run.system, round(run.diameter_m * _M_TO_IN, 3))
        entry = runs.setdefault(key, {"length_m": 0.0, "count": 0, "tags": []})
        entry["length_m"] += run.length_m
        entry["count"] += 1
        entry["tags"].append(run.tag)
    return [
        {"system": system, "diameter_in": diameter, "runs": int(entry["count"]),
         "length_ft": round(float(entry["length_m"]) * _M_TO_FT, 1),
         "tags": sorted(entry["tags"])}
        for (system, diameter), entry in sorted(runs.items())
    ]


def duct_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of duct, grouped by system and section.

    Section is part of the key because a 12x6 and a 14x8 trunk are different sheet-metal
    orders; ``routing`` rides along because a joist-bay run and an exposed one are fabricated
    and hung differently even at the same size.
    """
    runs: dict[tuple[str, float, float, str], dict[str, object]] = {}
    for duct in model.ducts:
        length_m = sum(
            ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            for a, b in zip(duct.path[:-1], duct.path[1:])
        )
        key = (duct.system, round(duct.width_m * _M_TO_IN, 2),
               round(duct.depth_m * _M_TO_IN, 2), duct.routing)
        entry = runs.setdefault(key, {"length_m": 0.0, "count": 0, "tags": []})
        entry["length_m"] += length_m
        entry["count"] += 1
        entry["tags"].append(duct.tag)
    return [
        {"system": system, "width_in": width, "depth_in": depth, "routing": routing,
         "runs": int(entry["count"]),
         "length_ft": round(float(entry["length_m"]) * _M_TO_FT, 1),
         "tags": sorted(entry["tags"])}
        for (system, width, depth, routing), entry in sorted(runs.items())
    ]


def sleeve_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Cast-in-place slab sleeves by the piece, grouped by sleeve diameter.

    A sleeve is a purchased sleeve, not a hole: it is ordered ahead of the pour, and its
    count is what the concrete crew sets. Depth rides along because a sleeve is cut to the
    slab it passes through.
    """
    sleeves: dict[float, dict[str, object]] = {}
    for sleeve in model.sleeves:
        key = round(sleeve.sleeve_d_m * _M_TO_IN, 2)
        entry = sleeves.setdefault(key, {"count": 0, "length_m": 0.0, "tags": []})
        entry["count"] += 1
        entry["length_m"] += max(sleeve.z1_m - sleeve.z0_m, 0.0)
        entry["tags"].append(sleeve.tag)
    return [
        {"sleeve_diameter_in": diameter, "count": int(entry["count"]),
         "total_length_ft": round(float(entry["length_m"]) * _M_TO_FT, 2),
         "tags": sorted(entry["tags"])}
        for diameter, entry in sorted(sleeves.items())
    ]
