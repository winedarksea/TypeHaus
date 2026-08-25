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

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, SolidSweep
from typehaus.resolve.sweep import clean_path, sweep_turns
from typehaus.takeoff.plumbing import _MIN_FITTING_TURN_DEG, _elbow_key

_M_TO_FT = 3.280839895


def pipe_run_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of pipe, grouped by system and nominal diameter.

    ``length_m`` is the resolver's own developed length — plan run plus any rise — so a
    drop through a floor is not billed as the zero plan length it projects to.
    """
    runs: dict[tuple[str, float], dict[str, object]] = {}
    for run in model.pipe_runs:
        key = (run.system, round(run.diameter_m / M_PER_IN, 3))
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


def pipe_insulation_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of pipe insulation, grouped by spec and pipe diameter.

    Insulation is bought as sleeve stock sized to the pipe it goes over, so the bore is part
    of the key exactly as it is for the pipe itself — 3/4" and 1" sleeve are two SKUs. The
    length is the host run's developed length, because the sleeve follows the pipe through
    its drops; there is nothing else it could be, which is why insulation is a field on the
    run rather than a routed element of its own.

    Runs with no ``insulation`` are absent rather than billed at zero: a bare hot line is a
    finding (``mep.hot_water_insulation``), not a row of nothing.
    """
    specs: dict[tuple[str, float], dict[str, object]] = {}
    for run in model.pipe_runs:
        if not run.insulation:
            continue
        key = (run.insulation, round(run.diameter_m / M_PER_IN, 3))
        entry = specs.setdefault(key, {"length_m": 0.0, "count": 0, "tags": []})
        entry["length_m"] = float(entry["length_m"]) + run.length_m
        entry["count"] = int(entry["count"]) + 1
        tags = entry["tags"]
        assert isinstance(tags, list)
        tags.append(run.tag)
    return [
        {"spec": spec, "pipe_diameter_in": diameter, "runs": int(entry["count"]),
         "length_ft": round(float(entry["length_m"]) * _M_TO_FT, 1),
         "tags": sorted(entry["tags"])}
        for (spec, diameter), entry in sorted(specs.items())
    ]


def duct_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of duct, grouped by system, section, routing and material.

    ``length_m`` is the resolver's own **developed** length — plan run plus every rise —
    the same rule ``pipe_run_takeoff`` above already followed. This function used to
    re-derive a plan-only sum from the path, which billed the ERV's four-storey riser as
    the zero length a vertical leg projects to; the ducts had no elevations to sum, so
    there was nothing else it could have done.

    Section is part of the key because a 12x6 and a 14x8 trunk are different sheet-metal
    orders — and a 6" round is a third order again, which is why ``diameter_in`` is its own
    column rather than a 6x6 rectangle in disguise. ``routing`` rides along because a
    joist-bay run and an exposed one are fabricated and hung differently at the same size,
    and ``material`` because 75 mm semi-rigid by the coil and galvanized by the joint are
    not the same purchase at all.
    """
    runs: dict[tuple[str, float, float, float, str, str], dict[str, object]] = {}
    for duct in model.ducts:
        key = (duct.system,
               round(duct.diameter_m / M_PER_IN, 2) if duct.diameter_m is not None else 0.0,
               round(duct.width_m / M_PER_IN, 2), round(duct.depth_m / M_PER_IN, 2),
               duct.routing, duct.material or "")
        entry = runs.setdefault(key, {"length_m": 0.0, "count": 0, "tags": []})
        entry["length_m"] = float(entry["length_m"]) + duct.length_m
        entry["count"] = int(entry["count"]) + 1
        tags = entry["tags"]
        assert isinstance(tags, list)
        tags.append(duct.tag)
    return [
        {"system": system, "diameter_in": diameter, "width_in": width, "depth_in": depth,
         "routing": routing, "material": material, "runs": int(entry["count"]),
         "length_ft": round(float(entry["length_m"]) * _M_TO_FT, 1),
         "tags": sorted(entry["tags"])}
        for (system, diameter, width, depth, routing, material), entry in sorted(runs.items())
    ]


def duct_insulation_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of duct insulation, by spec and section — the pipe rule, one trade over.

    An uninsulated outdoor-air duct through conditioned space sweats all winter, so the
    wrap on the ERV's intake and discharge is not a finish, it is the thing that keeps the
    ceiling below it dry. Billed off the host run's developed length, because the wrap
    follows the duct through its risers and there is nothing else it could be.
    """
    specs: dict[tuple[str, float, float, float], dict[str, object]] = {}
    for duct in model.ducts:
        if not duct.insulation:
            continue
        key = (duct.insulation,
               round(duct.diameter_m / M_PER_IN, 2) if duct.diameter_m is not None else 0.0,
               round(duct.width_m / M_PER_IN, 2), round(duct.depth_m / M_PER_IN, 2))
        entry = specs.setdefault(key, {"length_m": 0.0, "count": 0, "tags": []})
        entry["length_m"] = float(entry["length_m"]) + duct.length_m
        entry["count"] = int(entry["count"]) + 1
        tags = entry["tags"]
        assert isinstance(tags, list)
        tags.append(duct.tag)
    return [
        {"spec": spec, "diameter_in": diameter, "width_in": width, "depth_in": depth,
         "runs": int(entry["count"]),
         "length_ft": round(float(entry["length_m"]) * _M_TO_FT, 1),
         "tags": sorted(entry["tags"])}
        for (spec, diameter, width, depth), entry in sorted(specs.items())
    ]


def duct_fitting_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Duct elbows counted **off the geometry**, by system, fitting and size.

    The same derivation ``takeoff/plumbing.py::fitting_takeoff`` makes for pipe, reused
    rather than restated: a run's own 3D polyline is walked by
    :func:`~typehaus.resolve.sweep.sweep_turns`, each interior turn is measured in 3D — so
    a riser meeting a horizontal branch is the 90° it actually is — and snapped to the
    stock angle it is bought as. This is only possible now: a duct with no elevations had
    no 3D polyline, so every one of its turns was a plan turn and every riser was invisible.

    No tees. There is no parent inference for an air-side system the way ``drain_tie_ins``
    gives one for drainage, and a guessed count billed as a count is worse than an absence.
    A radial install barely has any: that is the point of a manifold, whose takeoffs are
    part of the manifold.
    """
    counts: dict[tuple[str, str], dict[str, object]] = {}
    for duct in model.ducts:
        if len(duct.z_m) != len(duct.path):
            continue
        size = (duct.diameter_m if duct.diameter_m is not None
                else max(duct.width_m, duct.depth_m))
        sweep = SolidSweep(
            path=clean_path([(x, y, z) for (x, y), z in zip(duct.path, duct.z_m)]),
            profile=((size / 2.0, 0.0),))
        for turn in sweep_turns(sweep):
            if turn.angle_deg < _MIN_FITTING_TURN_DEG:
                continue  # a change of pitch, not a fitting
            key = (duct.system, _elbow_key(turn.angle_deg, size))
            entry = counts.setdefault(key, {"count": 0, "tags": set()})
            entry["count"] = int(entry["count"]) + 1
            tags = entry["tags"]
            assert isinstance(tags, set)
            tags.add(duct.tag)
    return [{"system": system, "fitting": fitting, "count": int(entry["count"]),
             "tags": sorted(entry["tags"])}
            for (system, fitting), entry in sorted(counts.items())]


def sleeve_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Cast-in-place slab sleeves by the piece, grouped by sleeve diameter.

    A sleeve is a purchased sleeve, not a hole: it is ordered ahead of the pour, and its
    count is what the concrete crew sets. Depth rides along because a sleeve is cut to the
    slab it passes through.
    """
    sleeves: dict[float, dict[str, object]] = {}
    for sleeve in model.sleeves:
        key = round(sleeve.sleeve_d_m / M_PER_IN, 2)
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
