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

    A three-line delegation to :func:`~typehaus.resolve.mep_envelopes.run_polylines`, which
    is now the one place this is derived. ``routing/obstacles`` derived it a second time
    because the leaf rule forbids a router importing a check; ``resolve`` is the layer both
    may reach, so the derivation moved there and both sides became readers.
    """
    from typehaus.resolve.mep_envelopes import run_polylines as _polylines

    return _polylines(ctx.model)


def run_radii(ctx: CheckContext) -> dict[str, float]:
    """Half the real outside dimension of each run — see
    :func:`~typehaus.resolve.mep_envelopes.run_radii`, which owns it.

    A run is a centreline and an opening is a hole; whether the two meet is a question about
    the run's SURFACE. This is the ROUND reading, one number per run; a rectangular duct's
    real pair (``width`` across, ``depth`` vertically) is
    :func:`~typehaus.resolve.mep_envelopes.run_sections`, and a consumer that cares about
    the difference should ask for that instead.
    """
    from typehaus.resolve.mep_envelopes import run_radii as _radii

    return _radii(ctx.model)


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
