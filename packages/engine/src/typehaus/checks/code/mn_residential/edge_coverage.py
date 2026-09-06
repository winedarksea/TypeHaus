"""Edge coverage: what closes a plan segment, and what is left open.

One derivation behind both edge rules. ``code.R312_1_guard`` grades a stair well's four
edges and ``code.R312_1_guard_height`` grades the ring of every deck and slab, and each
asks the identical question of a segment: which stretches of it are closed by a wall, by a
glazed enclosure, by a guard, or by the stair entering through it, and which stretches are
therefore an open side.

Split out of ``fall_protection`` because it is geometry rather than code: nothing here
knows what R312 requires, only what stands where. Every function takes a *segment* and
projects onto that segment's own axis (``resolve/geometry``'s ``unit``/``normal``/
``project_onto_axis``), so an edge that runs at 30 degrees is measured the way a
north-south one is — the predecessor indexed x/y as 0/1 and could not grade a skew edge at
all.
"""

from __future__ import annotations

import math

from typehaus.checks.code.mn_residential.stairs import _flight_stations
from typehaus.checks.registry import CheckContext
from typehaus.quantities import inch

#: R312.1.2, at open sides of walking surfaces.
_GUARD_MIN_HEIGHT = inch(36)
#: R312.1.1, the drop that makes a guard required.
_GUARD_TRIGGER_DROP = inch(30)
#: Only treads arriving at this surface open a throat.
_GUARD_THROAT_Z_WINDOW_M = 0.5
#: Stretch the arrival quad ~a tread to the finished edge.
_GUARD_THROAT_REACH_M = 0.45


def _segment_cover_intervals(p0, p1, closures, railings, stair_quads, *,
                             plane_tol_m: float, wall_face_tol_m: float):
    """(covered, short, used): what covers an arbitrary plan segment, in stations along it.

    The one coverage derivation behind every guard rule. Stations are metres from ``p0``
    along the segment's own axis, so nothing here assumes an axis-aligned edge: a wall's
    footprint, a railing's sub-segments and a stair throat's arrival quad are each projected
    onto the segment's ``unit``/``normal`` frame (``resolve/geometry``). An edge that runs
    at 30 degrees is measured exactly the way a north-south one is.

    * a **closure** — a wall's layer polygons, or a full-height glazed panel's outline —
      covers the stretch its footprint spans, when that footprint straddles the segment's
      own line. Read off the polygons, not ``axis`` +/- half the thickness: an
      ``alignment=face(...)`` wall's axis is not its centreline, and a glazed enclosure has
      no axis at all;
    * a **railing** covers each sub-segment of its path whose two ends both lie within
      ``plane_tol_m`` of the segment line, and is returned in ``short`` instead when it runs
      the segment under guard height;
    * a **stair quad** covers where the flight crosses — that side is the stairway, R311's
      problem rather than an open side.
    """
    from shapely.geometry import LineString

    from typehaus.resolve.geometry import normal, project_onto_axis, sub, unit

    span = sub(p1, p0)
    axis = unit(span)
    across = normal(axis)
    covered: list[tuple[float, float]] = []
    short: list = []
    used: set[str] = set()
    for points in closures:
        if not points:
            continue
        offsets = [project_onto_axis(point, p0, across) for point in points]
        if not (min(offsets) - wall_face_tol_m <= 0.0 <= max(offsets) + wall_face_tol_m):
            continue
        stations = [project_onto_axis(point, p0, axis) for point in points]
        covered.append((min(stations), max(stations)))
    for railing, tall_enough in railings:
        for a, b in zip(railing.path, railing.path[1:], strict=False):
            pa, qa = a.xy_m, b.xy_m
            if (abs(project_onto_axis(pa, p0, across)) > plane_tol_m
                    or abs(project_onto_axis(qa, p0, across)) > plane_tol_m):
                continue
            lo, hi = sorted((project_onto_axis(pa, p0, axis),
                             project_onto_axis(qa, p0, axis)))
            if tall_enough:
                covered.append((lo, hi))
                used.add(railing.tag)
            else:
                short.append(railing)
    line = LineString([p0, p1])
    for quad in stair_quads:
        inter = line.intersection(quad)
        if inter.is_empty or getattr(inter, "length", 0.0) <= 1e-6:
            continue
        stations = [project_onto_axis(point, p0, axis)
                    for geom in getattr(inter, "geoms", [inter]) for point in geom.coords]
        covered.append((min(stations), max(stations)))
    return covered, short, used


def _uncovered_runs(p0, p1, closures, railings, stair_quads, *, gap_tol_m: float,
                    plane_tol_m: float, wall_face_tol_m: float):
    """The stretches of ``p0``->``p1`` nothing guards, as ``(station0, station1)`` pairs.

    Runs at or under ``gap_tol_m`` are dropped: a corner lap or a resolution sliver is not
    an open side.
    """
    from typehaus.resolve.floors import _subtract_interval
    from typehaus.resolve.geometry import length, sub

    run = length(sub(p1, p0))
    covered, short, used = _segment_cover_intervals(
        p0, p1, closures, railings, stair_quads,
        plane_tol_m=plane_tol_m, wall_face_tol_m=wall_face_tol_m)
    remaining = [(0.0, run)]
    for lo, hi in covered:
        remaining = _subtract_interval(remaining, lo, hi)
    return [(lo, hi) for lo, hi in remaining if hi - lo > gap_tol_m], short, used


#: A resolved solid in this category standing full height at an edge closes it as
#: completely as a wall does. The breezeway is a glazed vestibule — ``GL-BW-WALL-W`` and
#: ``GL-BW-WALL-E`` run its full 4'-0" length from under the deck to the roof — and a guard
#: inside a wall of glass is a rail inside a wall. What the glass itself owes is R308.4's
#: safety glazing, which ``code.R308_4_safety_glazing`` grades.
_ENCLOSING_SOLID_CATEGORIES = ("glazing",)


def _closures_at(ctx: CheckContext, surface: float) -> list[list[tuple[float, float]]]:
    """Every wall and glazed enclosure standing full guard height at ``surface``, as plan
    footprints.

    One census, one z test: base at or under the walking surface, top at or over the 36"
    R312.1.2 wants of a guard. Deliberately **not** filtered by storey — a storey tag is a
    filing convention, not a level, and this project's freestanding structures are filed on
    whatever storey was convenient (the sunken garden's guards are on ``basement`` while the
    porch deck they stand on is on ``main``). The two z tests are the real question.
    """
    def stands(z0: float, z1: float) -> bool:
        return (z0 <= surface + 0.1
                and z1 >= surface + _GUARD_MIN_HEIGHT.meters - 0.02)

    out = [[point for layer in wall.layers for point in layer.polygon]
           for wall in ctx.model.walls if stands(wall.z0_m, wall.z1_m)]
    out += [list(solid.outline) for solid in ctx.model.solids
            if solid.category in _ENCLOSING_SOLID_CATEGORIES
            and len(solid.outline) >= 3 and stands(solid.z0_m, solid.z1_m)]
    return [points for points in out if points]


def _stair_throat_quads(ctx: CheckContext, surface: float) -> list:
    """The plan quads where a flight arrives at (or leaves through) ``surface``.

    Where a stair enters an edge, that side is the stairway and R311 adjudicates it — it is
    not an open side wanting a guard. Shared by the stair-well rule and the raised-surface
    rule, which ask the same question of a well edge and of a deck edge.
    """
    from shapely.geometry import Polygon as _ShapelyPolygon

    quads = []
    for stair in ctx.model.stairs:
        for stations in _flight_stations(stair).values():
            pairs = list(zip(stations, stations[1:], strict=False))
            for index, ((a0, b0, z0), (a1, b1, z1)) in enumerate(pairs):
                if max(z0, z1) < surface - _GUARD_THROAT_Z_WINDOW_M:
                    continue
                if index == len(pairs) - 1:
                    # The nosing line's extrapolated arrival station lands a tread short of
                    # the finished edge (a well is cut to the trimmer, not to the top
                    # nosing; a threshold board over a wall top is not an element at all);
                    # stretch the final quad along the travel direction so the throat
                    # actually reaches the edge it enters through. Along travel only —
                    # never sideways, which would eat into genuinely open sides beside it.
                    run = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
                    if run > 1e-9:
                        ux, uy = (a1[0] - a0[0]) / run, (a1[1] - a0[1]) / run
                        reach = _GUARD_THROAT_REACH_M
                        a1 = (a1[0] + ux * reach, a1[1] + uy * reach)
                        b1 = (b1[0] + ux * reach, b1[1] + uy * reach)
                quad = _ShapelyPolygon([a0, b0, b1, a1])
                if quad.is_valid and quad.area > 1e-6:
                    quads.append(quad)
    return quads


#: A well edge under a roof lower than this is not an open side. R312.1.1 scopes guards to
#: *walking surfaces*; where the roof structure stands less than the code's own 30" fall
#: dimension above the deck there is no walking surface on either side of the edge, and the
#: roof plane closes the void more completely than the 36" guard it displaces could. 30",
#: not 36": between the two a guard is unbuildable but a person could still be prone there,
#: and that should stay a FAIL so it forces a design answer rather than passing quietly.
_ROOF_CLOSES_EDGE_M = _GUARD_TRIGGER_DROP.meters
#: Sampling step along an edge when asking whether the roof closes it.
_ROOF_SAMPLE_STEP_M = 0.25


def _roof_closed_run(ctx: CheckContext, p0, p1, surface: float) -> bool:
    """Is this whole stretch of an edge roofed too low to stand or walk in?

    Sampled rather than tested at the ends: the underside is linear along a rake but an
    edge may run across the ridge, where the ends are the two LOWEST points. Sampling
    catches that; two-point testing would exempt a full-height opening under a peak.
    """
    import math as _math

    from typehaus.resolve.roof_geometry import roof_bearing_footprint, roof_underside_at

    run = _math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    if run <= 0:
        return True
    steps = max(2, int(run / _ROOF_SAMPLE_STEP_M) + 1)
    for index in range(steps + 1):
        t = index / steps
        point = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
        clear = None
        for roof in ctx.model.roofs:
            footprint = roof_bearing_footprint(ctx.model, roof)
            if footprint is None:
                continue
            xs = [corner[0] for corner in footprint]
            ys = [corner[1] for corner in footprint]
            if not (min(xs) <= point[0] <= max(xs) and min(ys) <= point[1] <= max(ys)):
                continue
            height = roof_underside_at(ctx.model, roof, point) - surface
            clear = height if clear is None else min(clear, height)
        if clear is None or clear >= _ROOF_CLOSES_EDGE_M:
            return False
    return True

def _outward_normals(ring) -> list[tuple[float, float]]:
    """The outward unit normal of every edge of a plan ring, in ring order.

    Signed area fixes the winding first, so a ring authored either way answers the same.
    Which side is *out* is what makes "what is beside this edge" answerable at all.
    """
    area = sum(ring[i][0] * ring[(i + 1) % len(ring)][1]
               - ring[(i + 1) % len(ring)][0] * ring[i][1]
               for i in range(len(ring))) / 2.0
    sign = 1.0 if area >= 0 else -1.0
    out: list[tuple[float, float]] = []
    for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
        dx, dy = b[0] - a[0], b[1] - a[1]
        run = math.hypot(dx, dy)
        out.append((0.0, 0.0) if run < 1e-12 else (sign * dy / run, -sign * dx / run))
    return out
