"""The vocabulary every routing check shares: a run's polyline, its radius, what covers it.

Split out of ``checks/mep/routing.py`` when a second and third routing check needed the same
five things. Nothing here grades anything — these are the geometric facts the checks in
``routing.py``, ``routing_openings.py``, ``routing_ceiling.py`` and ``drain_geometry.py``
each ask a different question of.

They are public rather than underscored because they are cross-module, and because a private
name imported from four places is a private name in nothing but spelling.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import Polygon

from typehaus.checks.registry import CheckContext

M_TO_FT = 3.280839895013123


def wall_cover(ctx: CheckContext, storeys: set[str]) -> Any:
    """The union of every wall layer polygon on the named storeys — "somewhere to strap to".

    Layer polygons rather than the axis, because the question is physical: is there framing
    under this foot of pipe. A 5 1/2" stud bay is 5 1/2" of support and the axis is a line
    with no width at all.

    Built through :mod:`typehaus.resolve.overlay` rather than a bare ``unary_union``: the
    published web app runs GEOS 3.12.1, where an overlay of many nearly-collinear wall
    polygons without a grid size is fatal rather than merely imprecise.

    **What this does not ask** is whether the wall could host the run. A 12" cast foundation
    wall is a plan footprint like any other and cannot be bored for a 2" drain;
    ``mep.wet_wall_occupancy`` and ``mep.sleeve_coverage`` own that question. A check leaning
    on this exemption is saying "there is structure here", not "this is buildable here".
    """
    from typehaus.resolve.overlay import union_all

    polygons = [Polygon(layer.polygon)
                for wall in ctx.model.walls if wall.storey in storeys
                for layer in wall.layers
                if len(layer.polygon) >= 3]
    valid = [poly for poly in polygons if poly.is_valid and not poly.is_empty]
    return union_all(valid) if valid else None


def run_polylines(ctx: CheckContext) -> list[tuple[str, str, tuple[tuple[float, float], ...],
                                                   tuple[float, ...]]]:
    """Every routed thing, as ``(kind, tag, plan path, per-vertex z)``.

    No storey: which floor a run is *in* is decided by elevation, not by filing (see
    ``routing.py``'s module note), so carrying the storey would only invite something to
    start reading it.

    Pipe, duct and raceway together: a hole in a deck, a rough opening and a room's air do
    not care which trade drew the line, and three near-identical loops would be three places
    for the rule to drift. A raceway's z is reconstructed by
    :func:`~typehaus.takeoff.runs.conduit_vertex_z`, which owns the one reading of "a
    ConduitRun rises at its last point".

    The z values are **centrelines** — see ``model/mep.py``'s note on ``PipeRun.elevations``.
    Anything asking about the run's surface adds :func:`run_radii`.
    """
    from typehaus.takeoff.runs import conduit_vertex_z

    out = []
    for run in ctx.model.pipe_runs:
        z = tuple(run.z_m) if run.z_m and len(run.z_m) == len(run.path) else ()
        out.append(("pipe", run.tag, tuple(run.path), z))
    for duct in ctx.model.ducts:
        z = tuple(duct.z_m) if len(duct.z_m) == len(duct.path) else ()
        out.append(("duct", duct.tag, tuple(duct.path), z))
    for raceway in ctx.model.conduits:
        out.append(("conduit", raceway.tag, tuple(raceway.path), conduit_vertex_z(raceway)))
    return out


def run_radii(ctx: CheckContext) -> dict[str, float]:
    """Half the outside dimension of each run, keyed by tag.

    A run is a centreline and an opening is a hole; whether the two meet is a question about
    the run's SURFACE. Six inches of duct with an inch of wrap either side is eight inches of
    obstruction, and grading its centreline alone under-reports by four. A raceway's trade
    size is a nominal bore rather than an outside diameter, but the error is under an eighth
    of an inch on 3/4" EMT and in the conservative direction.
    """
    radii: dict[str, float] = {}
    for run in ctx.model.pipe_runs:
        radii[run.tag] = (run.diameter_m or 0.0) / 2.0
    for duct in ctx.model.ducts:
        radii[duct.tag] = (duct.diameter_m or 0.0) / 2.0
    for raceway in ctx.model.conduits:
        radii[raceway.tag] = (raceway.trade_size_m or 0.0) / 2.0
    return radii


def crossing_band(segment: Any, za: float, zb: float, piece: Any) -> tuple[float, float]:
    """The run's own z range over just the part of the segment inside some plan shape.

    Banding the WHOLE segment is the tempting shortcut and it is wrong on exactly the runs
    these checks exist for: ``CD-A-DATA-NE`` climbs 3'-6" across 21 ft of gable in one
    segment, so its segment band spans four feet of elevation and reads as inside every
    opening it passes under. Interpolating at the crossing is the difference between two real
    findings and five, three of which are arithmetic. ``mep.run_in_finished_volume`` learns
    the same lesson at a different scale: it is what turns "a 4 ft diagonal somewhere" into
    "0.99 ft of pipe 33 inches into the suite bath".
    """
    from shapely.geometry import Point

    length = segment.length
    if length <= 0:
        return (min(za, zb), max(za, zb))
    zs = [za + (zb - za) * (segment.project(Point(xy)) / length)
          for xy in piece.coords]
    return (min(zs), max(zs))
