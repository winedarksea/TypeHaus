"""R312 guards and window fall protection.

Split out of ``rules.py``. The stair-well guard rule below was the only guard rule in the
CODE tier, and ``structural.deck_guard`` the only other one anywhere — between them they
covered stair wells and decks, leaving every interior raised edge (a loft rail, an open
stair landing, a floor edge over a stairwell-adjacent drop) unmeasured.
"""

from __future__ import annotations

import math

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.code.mn_residential.stairs import _flight_stations
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN, inch

# --- R312.1 guards at stair-well openings ----------------------------------------------
_GUARD_MIN_HEIGHT = inch(36)  # R312.1.2, at open sides of walking surfaces
_GUARD_TRIGGER_DROP = inch(30)  # R312.1.1, the drop that makes a guard required
_GUARD_GAP_TOL_M = 0.05       # uncovered slivers under ~2" are corner laps, not open sides
_GUARD_PLANE_TOL_M = 0.15     # a railing path within 6" of the well edge guards that edge
_GUARD_WALL_FACE_TOL_M = 0.05  # the void is cut to the finished well, i.e. the wall face
_GUARD_BASE_TOL_M = 0.15      # railing base matched to the walking surface (deck_guard's tol)
_GUARD_THROAT_Z_WINDOW_M = 0.5  # only treads arriving at this surface open a throat
_GUARD_THROAT_REACH_M = 0.45   # stretch the arrival quad ~a tread to the finished edge

# R312.2: an operable window whose sill sits under 24" above the finished floor, with more
# than 72" of fall to the grade outside, needs an opening control or a guard.
_WINDOW_FALL_SILL = inch(24)
_WINDOW_FALL_DROP = inch(72)


def _segment_cover_intervals(p0, p1, walls, railings, stair_quads, *,
                             plane_tol_m: float, wall_face_tol_m: float):
    """(covered, short, used): what covers an arbitrary plan segment, in stations along it.

    The one coverage derivation behind every guard rule. Stations are metres from ``p0``
    along the segment's own axis, so nothing here assumes an axis-aligned edge: a wall's
    footprint, a railing's sub-segments and a stair throat's arrival quad are each projected
    onto the segment's ``unit``/``normal`` frame (``resolve/geometry``). An edge that runs
    at 30 degrees is measured exactly the way a north-south one is.

    * a **wall** covers the stretch its layer polygons span, when that footprint straddles
      the segment's own line (read off the polygons, not ``axis`` +/- half the thickness —
      an ``alignment=face(...)`` wall's axis is not its centreline);
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
    for wall in walls:
        points = [point for layer in wall.layers for point in layer.polygon]
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


def _uncovered_runs(p0, p1, walls, railings, stair_quads, *, gap_tol_m: float,
                    plane_tol_m: float, wall_face_tol_m: float):
    """The stretches of ``p0``->``p1`` nothing guards, as ``(station0, station1)`` pairs.

    Runs at or under ``gap_tol_m`` are dropped: a corner lap or a resolution sliver is not
    an open side.
    """
    from typehaus.resolve.floors import _subtract_interval
    from typehaus.resolve.geometry import length, sub

    run = length(sub(p1, p0))
    covered, short, used = _segment_cover_intervals(
        p0, p1, walls, railings, stair_quads,
        plane_tol_m=plane_tol_m, wall_face_tol_m=wall_face_tol_m)
    remaining = [(0.0, run)]
    for lo, hi in covered:
        remaining = _subtract_interval(remaining, lo, hi)
    return [(lo, hi) for lo, hi in remaining if hi - lo > gap_tol_m], short, used


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

@check(Tier.CODE, "code.R312_1_guard")
def stairwell_guard(ctx: CheckContext) -> list[Finding]:
    """R312.1 — every open side of a stair well's walking surface carries a guard.

    Each STAIR floor opening's four edges are classified against the resolved geometry:
    an edge is covered where a wall's plan footprint stands at it full guard height,
    where an authored Railing runs along it at >= 36" with its base on the walking
    surface, or where the stair itself enters (the throat — that side is the stairway,
    R311's problem, not an open side). Whatever length remains is an open side with no
    guard: a FAIL naming the edge and the uncovered interval. A railing that runs an
    edge under 36" fails on height rather than counting as coverage, and a house with
    no stair wells reports UNKNOWN — never PASS by absence.
    """

    from typehaus.model.floors import FloorOpening, FloorOpeningPurpose, FloorSystem
    from typehaus.model.structure import Railing
    from typehaus.resolve.floors import _rectangular_opening_box

    cid, code = "code.R312_1_guard", "R312.1"
    openings_by_tag = {e.tag: e for e in ctx.plan.all_elements()
                       if isinstance(e, FloorOpening)}
    hosts = [(fs, opening_tag) for fs in ctx.plan.all_elements()
             if isinstance(fs, FloorSystem) for opening_tag in fs.openings]
    wells = [(fs, openings_by_tag[tag]) for fs, tag in hosts
             if tag in openings_by_tag
             and openings_by_tag[tag].purpose is FloorOpeningPurpose.STAIR]
    if not wells:
        return [_unknown(cid, "no stair floor openings in the plan", (), code)]

    all_railings = [e for e in ctx.plan.all_elements() if isinstance(e, Railing)]
    out: list[Finding] = []
    for fs, opening in wells:
        floor = next((f for f in ctx.model.floors if f.tag == fs.tag), None)
        if floor is None or not floor.deck_outline:
            out.append(_unknown(cid, f"{opening.tag}: host floor {fs.tag} resolved no "
                                "deck to measure a walking surface from",
                                (opening.tag, fs.tag), code))
            continue
        box = _rectangular_opening_box(opening)
        if box is None:
            out.append(_unknown(cid, f"{opening.tag}: outline is not an axis-aligned "
                                "rectangle", (opening.tag,), code))
            continue
        minx, maxx, miny, maxy = box
        surface = floor.deck_z1_m
        walls = [w for w in ctx.model.walls
                 if w.storey == floor.storey
                 and w.z0_m <= surface + 0.1
                 and w.z1_m >= surface + _GUARD_MIN_HEIGHT.meters - 0.02]
        railings = [(r, r.height.meters + 1e-9 >= _GUARD_MIN_HEIGHT.meters)
                    for r in all_railings
                    if abs(r.base_elevation.meters - surface) < _GUARD_BASE_TOL_M]
        stair_quads = _stair_throat_quads(ctx, surface)

        edges = (("west", 0, minx, miny, maxy), ("east", 0, maxx, miny, maxy),
                 ("south", 1, miny, minx, maxx), ("north", 1, maxy, minx, maxx))
        gaps: list[str] = []
        roof_closed: list[str] = []
        short_guards: list = []
        guarding_tags: set[str] = set()
        for name, across, edge_across, along0, along1 in edges:
            p0 = (edge_across, along0) if across == 0 else (along0, edge_across)
            p1 = (edge_across, along1) if across == 0 else (along1, edge_across)
            runs, short, used = _uncovered_runs(
                p0, p1, walls, railings, stair_quads, gap_tol_m=_GUARD_GAP_TOL_M,
                plane_tol_m=_GUARD_PLANE_TOL_M, wall_face_tol_m=_GUARD_WALL_FACE_TOL_M)
            short_guards.extend(short)
            guarding_tags |= used
            # Stations are metres from ``p0``; the edges are authored low-to-high along
            # their own axis, so the station is the offset from ``along0``.
            for station0, station1 in runs:
                lo, hi = along0 + station0, along0 + station1
                q0 = (edge_across, lo) if across == 0 else (lo, edge_across)
                q1 = (edge_across, hi) if across == 0 else (hi, edge_across)
                if _roof_closed_run(ctx, q0, q1, surface):
                    roof_closed.append(f"{name} edge {lo / .3048:.2f}'..{hi / .3048:.2f}'")
                    continue
                gaps.append(f"{name} edge {lo / .3048:.2f}'..{hi / .3048:.2f}' "
                            f"({(hi - lo) / .3048:.2f}')")
        if gaps:
            out.append(_fail(cid, f"{opening.tag}: open side(s) with no guard, wall or "
                             f"stair entry — {'; '.join(gaps)}",
                             (opening.tag, fs.tag), code))
        elif short_guards:
            names = sorted({r.tag for r in short_guards})
            worst = min(r.height.inches for r in short_guards)
            out.append(_fail(cid, f"{opening.tag}: guard(s) {', '.join(names)} run the "
                             f"well edge at {worst:.0f}\", under the 36\" R312.1.2 "
                             "minimum", (opening.tag, *names), code))
        else:
            note = ""
            if roof_closed:
                inches = _ROOF_CLOSES_EDGE_M / M_PER_IN
                note = (f"; {', '.join(roof_closed)} carries no guard because the roof "
                        f"structure stands under {inches:.0f} inches over the deck there "
                        "— no walking surface, so R312.1.1 does not reach it")
            out.append(_pass(cid, f"{opening.tag}: every open side is guarded "
                             f"({', '.join(sorted(guarding_tags)) or 'walls'} and the "
                             f"stair throat close the well){note}", code))
    return out


# --- R312.1.1/.1.2 guard height at every raised walking surface ------------------------
# How far a railing's base may sit from the surface it guards and still be its guard.
_EDGE_RAILING_BASE_TOL_M = 0.15
# A railing whose path runs within this of the edge is guarding that edge.
_EDGE_RAILING_PLANE_TOL_M = 0.20
# Uncovered run under this is a corner lap or a resolution sliver, not an open side.
_EDGE_GAP_TOL_M = 0.30


#: How far a wall's footprint may stand off a deck edge and still be the wall that closes
#: it. 6", not the well rule's 2": a *well* void is cut to the finished wall face, whereas a
#: deck's own outline is the subfloor sheet, which stops at the framing and leaves the
#: finish, the ledger and the framing gap between it and the resolved wall polygon —
#: FS-SG-PORCH's north edge stands 2 3/4" off W-M-S1's cladding face and is plainly closed
#: by it.
_EDGE_WALL_FACE_TOL_M = 0.15
#: Steps outboard of an edge at which to ask what walking surface is beside it. Two floor
#: systems of one storey abut across the wall or beam between them, so their deck outlines
#: never touch; a foot of reach spans that and no more.
_EDGE_NEIGHBOUR_PROBE_M = (0.08, 0.16, 0.24, 0.32)


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


@check(Tier.CODE, "code.R312_1_guard_height")
def raised_surface_guard_height(ctx: CheckContext) -> list[Finding]:
    """R312.1.1 — a walking surface more than 30" above what is below it needs a 36" guard.

    Between them, ``code.R312_1_guard`` (stair wells) and ``structural.deck_guard`` (decks)
    covered two shapes of the same requirement and left the general one unmeasured: any
    raised walking surface. A loft, a mezzanine, an open landing, a floor that steps down to
    a lower one, **a slab step** — all of them are R312.1.1 and none had a rule.

    The census is every framed floor deck *and* every ``slab`` solid. There is no
    ``ResolvedModel.slabs``, and a raised slab is the same walking surface a framed deck is:
    ``SL-G-STEP-0``'s 34" drop was in neither this rule's census nor ``code.R312_1_guard``'s
    and so was graded by nothing at all.

    **Coverage, not proximity.** Each edge is graded run by run through
    :func:`_uncovered_runs`, the derivation ``code.R312_1_guard`` uses. The predicate this
    rule started with was a plain ``LineString`` distance from the guard path to the *whole*
    edge, which a guard satisfies by covering the midpoint however much of either end is
    open: ``RL-SG-PORCH``'s east leg carries a 3'-0" doorway to ``ST-SG-PORCH`` and that
    test reported PASS with the doorway, without it, and would have with a 12'-0" one.

    An uncovered run is then put to three questions, each of which can end it:

    * **What is beside it?** Probed *outboard*, not at the midpoint on the edge itself. Two
      floor systems of one storey abut across the wall between them and their deck outlines
      never touch, so an on-the-line probe reads every interior seam as a fall to grade.
    * **How far is the fall?** To the highest surface out there, or to the site grade when
      nothing is modeled under it. With no grade datum this is an UNKNOWN, never a PASS: a
      30" trigger cannot be evaluated without knowing where the bottom is.
    * **Is it roofed too low to stand in?** The attic deck's gable edges run out under the
      eaves, where there is no walking surface on either side to guard.
    """
    from shapely.geometry import LineString, Point, Polygon

    from typehaus.model.structure import Railing

    cid, code = "code.R312_1_guard_height", "R312.1.1"
    surfaces = [(floor.tag, list(floor.deck_outline), floor.deck_z1_m)
                for floor in ctx.model.floors
                if floor.deck_outline and len(floor.deck_outline) >= 3]
    surfaces += [(solid.tag, list(solid.outline), solid.z1_m)
                 for solid in ctx.model.solids
                 if solid.category == "slab" and len(solid.outline) >= 3]
    if not surfaces:
        return [_unknown(cid, "no floor decks or slabs resolve, so there is no raised "
                         "walking surface to measure", (), code)]
    grade = ctx.plan.project.site.grade
    railings = [e for e in ctx.plan.all_elements() if isinstance(e, Railing)]
    out: list[Finding] = []
    for tag, ring, surface in surfaces:
        neighbours = [(Polygon(other_ring), other_z)
                      for other_tag, other_ring, other_z in surfaces if other_tag != tag]
        outward = _outward_normals(ring)
        # Deliberately **not** filtered by storey. A storey tag is a filing convention, not
        # a level: this project's freestanding structures share tags with whatever house
        # storey they were convenient to file on (the sunken garden's masonry guards are on
        # ``basement`` while the porch deck they stand on is on ``main``), and a guard that
        # is physically at the edge, at full height, guards it whatever it is filed under.
        # The two z tests below are the real question and answer it on their own —
        # ``structural.deck_guard`` has credited guard walls this way since it was written.
        walls = [w for w in ctx.model.walls
                 if w.z0_m <= surface + 0.1
                 and w.z1_m >= surface + _GUARD_MIN_HEIGHT.meters - 0.02]
        near_railings = [(r, r.height.meters + 1e-9 >= _GUARD_MIN_HEIGHT.meters)
                         for r in railings
                         if abs(r.base_elevation.meters - surface)
                         < _EDGE_RAILING_BASE_TOL_M]
        quads = _stair_throat_quads(ctx, surface)
        unguarded: list[str] = []
        unknown_edges: list[str] = []
        short: list[str] = []
        for index, (a, b) in enumerate(zip(ring, ring[1:] + ring[:1], strict=True)):
            seg = LineString([a, b])
            if seg.length <= _EDGE_GAP_TOL_M:
                continue
            runs, low, _used = _uncovered_runs(
                a, b, walls, near_railings, quads, gap_tol_m=_EDGE_GAP_TOL_M,
                plane_tol_m=_EDGE_RAILING_PLANE_TOL_M,
                wall_face_tol_m=_EDGE_WALL_FACE_TOL_M)
            short.extend(r.tag for r in low)
            nx, ny = outward[index]
            for station0, station1 in runs:
                start, stop = seg.interpolate(station0), seg.interpolate(station1)
                mx, my = (start.x + stop.x) / 2.0, (start.y + stop.y) / 2.0
                beside = [z for step in _EDGE_NEIGHBOUR_PROBE_M for poly, z in neighbours
                          if poly.covers(Point(mx + nx * step, my + ny * step))]
                below = max(beside) if beside else None
                if below is not None and below >= surface - _GUARD_TRIGGER_DROP.meters:
                    continue  # the walking surface carries on across this edge
                if below is None:
                    if grade is None:
                        unknown_edges.append(f"({mx / .3048:.0f}', {my / .3048:.0f}')")
                        continue
                    below = grade.meters
                if surface - below <= _GUARD_TRIGGER_DROP.meters + 1e-9:
                    continue  # under 30" — no guard required
                if _roof_closed_run(ctx, (start.x, start.y), (stop.x, stop.y), surface):
                    continue  # roofed under 30" — no walking surface on either side of it
                unguarded.append(
                    f"({start.x / .3048:.1f}', {start.y / .3048:.1f}')..."
                    f"({stop.x / .3048:.1f}', {stop.y / .3048:.1f}') "
                    f"{(station1 - station0) / .3048:.1f}' of open side over a "
                    f"{(surface - below) / .3048:.1f}' drop")
        if unguarded:
            out.append(_fail(cid, f'{tag}: unguarded edge(s) over a 30" drop — '
                             f"{'; '.join(unguarded)}", (tag,), code))
        elif short:
            names = sorted(set(short))
            out.append(_fail(cid, f"{tag}: guard(s) {', '.join(names)} stand under the "
                             '36" R312.1.2 minimum', (tag, *names), "R312.1.2"))
        elif unknown_edges:
            out.append(_unknown(cid, f"{tag}: edge(s) at {', '.join(unknown_edges)} "
                                "have nothing modeled beneath them and the site states no "
                                'grade datum, so the 30" trigger cannot be evaluated',
                                (tag,), code))
        else:
            out.append(_pass(cid, f'{tag}: every edge over a 30" drop is closed by a '
                             'wall, a 36" guard or a stair entry', code))
    return out


@check(Tier.CODE, "code.R312_2_window_fall_protection")
def window_fall_protection(ctx: CheckContext) -> list[Finding]:
    """R312.2 — an operable window with a sill under 24" and a drop over 72" outside.

    Applicability is geometry — sill height above the floor, fall height to the grade
    outside — and both are resolved. R312.2 is then satisfied by a window opening control,
    a fall-prevention device, or a guard at the window.

    Compliance is read off ``WindowType.fall_protection``, which is what makes FAIL a fair
    verdict here: there is now an authored change that clears it. Before that field existed
    this rule could only report UNKNOWN, because failing a house for a condition it had no
    way to declare compliance with is not a code check, it is a dead end.
    """
    cid, code = "code.R312_2_window_fall_protection", "R312.2"
    grade = ctx.plan.project.site.grade
    if grade is None:
        return [_unknown(cid, "the site states no average-grade datum, so no window's "
                         "exterior drop can be measured", (), code)]
    window_types = {t.tag: t for t in ctx.plan.library.window_types}
    storeys = {s.tag: s for s in ctx.plan.storeys}
    triggered: list[tuple[str, str]] = []
    cleared = 0
    for opening in ctx.model.openings:
        if opening.is_door or opening.type_ref is None:
            continue
        window_type = window_types.get(opening.type_ref)
        if window_type is None:
            continue
        operation = getattr(getattr(window_type, "operation", None), "value", None)
        if operation == "fixed":
            continue
        wall = ctx.model.wall(opening.host_wall)
        storey = storeys.get(wall.storey) if wall else None
        if storey is None:
            continue
        sill_above_floor = opening.sill_m
        sill_above_grade = storey.elevation.meters + opening.sill_m - grade.meters
        if (sill_above_floor < _WINDOW_FALL_SILL.meters
                and sill_above_grade > _WINDOW_FALL_DROP.meters):
            triggered.append((opening.tag, window_type.fall_protection))
        else:
            cleared += 1
    if not triggered:
        return [_pass(cid, f"no operable window has a sill under 24\" with more than 72\" of "
                      f"drop outside ({cleared} operable window(s) checked)", code)]
    out: list[Finding] = []
    for tag, protection in sorted(triggered):
        if protection == "none":
            out.append(_fail(cid, f"{tag} sits under 24\" above the floor with more than 72\" "
                             "of fall outside and declares no fall protection; R312.2 "
                             "requires an opening control, a fall-prevention device, or a "
                             "guard", (tag,), code))
        else:
            out.append(_pass(cid, f"{tag} triggers R312.2 and its type declares a "
                             f"{protection}", code))
    return out


# R312.1.3: a 4" sphere must not pass through the guard's infill. The stair-side triangle
# formed by tread, riser and bottom rail gets 6" instead, which is the one place the code
# relaxes rather than tightens.
_GUARD_SPHERE = inch(4)

#: The resolved categories the infill lands in (→ resolve/railings/parts.py). Posts and rails
#: keep ``"railing"`` and are deliberately not measured here: the gap between two posts is
#: what the infill fills, not an opening.
_INFILL_CATEGORIES = ("railing_infill", "railing_glass")

#: How far off the bay's own line an infill solid may sit and still be in that bay. A guard
#: turning a corner puts two legs' worth of pickets within reach of one bay's station range;
#: this is what separates them. Generous enough for a thick panel centred on the guard line.
_GUARD_INFILL_PLANE_TOL_M = 0.05

#: Two solids whose projections agree to this are in the same band of a raking run — the
#: grouping that lets a sloped cable guard be measured band by band rather than as one smear.
_BAND_TOL_M = 1e-4


@check(Tier.CODE, "code.R312_1_3_guard_opening_limit")
def guard_opening_limit(ctx: CheckContext) -> list[Finding]:
    """R312.1.3 — a 4" sphere must not pass through a required guard.

    The rule that stops a guard from being a guard in name only. A 36"-tall rail with two
    horizontal members is exactly the fixture that passes every height check and fails this
    one, and it is a common enough mistake that "cable rail spacing" is its own trade term.

    ``baluster_spacing`` is deliberately not ``post_spacing``: the posts are the structural
    rhythm (typically 4'-6'), the balusters are the infill between them. Conflating the two
    would pass every guard in every house.

    The verdict is then **cross-checked against the resolved geometry**: the largest clear
    gap between adjacent infill solids, measured bay by bay, both along the run and up it.
    An authored field can disagree with the drawn geometry — a guard whose drawn opening and
    whose authored opening disagree is a resolver bug, worth surfacing here rather than
    trusting either half alone: ``panel`` passes only because a lite is *drawn* edge to edge
    rather than on a claim, and ``mesh``/``cable`` are graded on what the model actually
    shows.

    Guard *walls* (a masonry parapet, ``Wall.guard``) are censused too and pass by
    construction — solid masonry admits nothing, the same reasoning ``infill == "panel"``
    already gets.
    """
    from typehaus.model.elements import Wall
    from typehaus.model.structure import Railing

    cid, code = "code.R312_1_3_guard_opening_limit", "R312.1.3"
    guards = [e for e in ctx.plan.all_elements() if isinstance(e, Railing)
              and e.role in ("guard", "guard_and_handrail")]
    guard_walls = [e for e in ctx.plan.all_elements()
                   if isinstance(e, Wall) and e.guard]
    if not guards and not guard_walls:
        return [_unknown(cid, "no guard railings in the plan", (), code)]
    out: list[Finding] = []
    for wall in guard_walls:
        out.append(_pass(cid, f"{wall.tag} is a solid masonry guard — no opening for a 4\" "
                         "sphere", code))
    for guard in guards:
        out.append(_grade_guard(ctx, guard, cid, code))
    return out


def _grade_guard(ctx: CheckContext, guard, cid: str, code: str) -> Finding:
    drawn = _largest_drawn_opening_m(ctx, guard)
    if guard.infill is None:
        return _unknown(cid, f"{guard.tag} states no infill, so the 4\" sphere test "
                        "has nothing to measure", (guard.tag,), code)
    # The authored gap is graded first, because when both are wrong it is the one the author
    # can act on: the drawn opening is a consequence of it, and quoting the consequence sends
    # the reader looking for a resolver bug that is not there.
    if (guard.baluster_spacing is not None
            and guard.baluster_spacing.meters > _GUARD_SPHERE.meters + 1e-9):
        return _fail(cid, f"{guard.tag} leaves {guard.baluster_spacing.inches:.1f}\" "
                     f"between its {guard.infill}; R312.1.3 passes no opening a 4\" "
                     "sphere fits through", (guard.tag,), code)
    if drawn is not None and drawn > _GUARD_SPHERE.meters + 1e-9:
        # The authored field is compliant and the drawing is not. This is the case the
        # cross-check exists for, and geometry wins: what is drawn is what gets built.
        return _fail(cid, f"{guard.tag} draws a {drawn / .0254:.1f}\" clear opening between "
                     f"adjacent {guard.infill}; R312.1.3 passes no opening a 4\" sphere "
                     "fits through", (guard.tag,), code)
    if guard.infill == "panel":
        # A solid panel admits nothing by construction; there is no gap to measure.
        return _pass(cid, f"{guard.tag} is panel-filled — no opening for a 4\" "
                     "sphere", code)
    if guard.baluster_spacing is None:
        return _unknown(cid, f"{guard.tag} is {guard.infill}-filled but states no "
                        "baluster_spacing (the clear gap, not the post rhythm)",
                        (guard.tag,), code)
    if drawn is None:
        return _unknown(cid, f"{guard.tag} holds its {guard.infill} to "
                        f"{guard.baluster_spacing.inches:.1f}\" but resolves no infill "
                        "geometry, so the authored gap cannot be confirmed against what "
                        "the model draws", (guard.tag,), code)
    return _pass(cid, f"{guard.tag} holds its {guard.infill} to "
                 f"{guard.baluster_spacing.inches:.1f}\" (<= 4\"), and draws "
                 f"{drawn / .0254:.1f}\" between adjacent {guard.infill}", code)


def _largest_drawn_opening_m(ctx: CheckContext, guard) -> float | None:
    """The widest clear gap between adjacent infill solids, over every bay of the guard.

    Measured in two directions because the two styles open in different ones: pickets leave
    their gaps *along* the run, cable leaves them *up* it, and a sheet leaves none either
    way. Both are the same sphere test, so the larger of the two is the answer.

    ``None`` when the guard resolved no infill at all — which is a different statement from
    "no gap", and is reported as UNKNOWN rather than as a pass.
    """
    from typehaus.resolve.geometry import length, normal, project_onto_axis, sub, unit
    from typehaus.resolve.railings import railing_post_stations

    prefix = f"{guard.tag}-"
    solids = [s for s in ctx.model.solids
              if s.category in _INFILL_CATEGORIES and s.tag.startswith(prefix)]
    if not solids:
        return None
    path = [p.xy_m for p in guard.path]
    if len(path) < 2:
        return None
    stations = railing_post_stations(path, max(guard.post_spacing.meters, 0.3))
    largest = 0.0
    for a, b in zip(stations[:-1], stations[1:], strict=True):
        bay = length(sub(b, a))
        if bay <= 1e-9:
            continue
        axis = unit(sub(b, a))
        across = normal(axis)
        placed: list[tuple[float, float, float, float]] = []
        for solid in solids:
            us = [project_onto_axis(point, a, axis) for point in solid.outline]
            u0, u1 = min(us), max(us)
            # Centred inside this bay, and *on* its line. Both halves matter on a guard that
            # turns a corner: the neighbouring leg shares an endpoint, so a station test
            # alone counts the perpendicular leg's pickets here — they project onto this
            # axis at plausible stations and invent a gap that is not in any bay.
            offsets = [abs(project_onto_axis(point, a, across)) for point in solid.outline]
            if (-1e-6 <= (u0 + u1) / 2.0 <= bay + 1e-6
                    and min(offsets) <= _GUARD_INFILL_PLANE_TOL_M):
                placed.append((u0, u1, solid.z0_m, solid.z1_m))
        if not placed:
            continue
        largest = max(largest, _interior_gap([(u0, u1) for u0, u1, _z0, _z1 in placed]))
        # Group by plan footprint before measuring up: on a rake one bay holds several
        # bands at different elevations, and merging those would smear a real gap shut.
        bands: dict[tuple[int, int], list[tuple[float, float]]] = {}
        for u0, u1, z0, z1 in placed:
            key = (round(u0 / _BAND_TOL_M), round(u1 / _BAND_TOL_M))
            bands.setdefault(key, []).append((z0, z1))
        for spans in bands.values():
            largest = max(largest, _interior_gap(spans))
    return largest


def _interior_gap(intervals: list[tuple[float, float]]) -> float:
    """The widest uncovered run strictly between the merged extremes of ``intervals``."""
    merged: list[list[float]] = []
    for lo, hi in sorted(intervals):
        if merged and lo <= merged[-1][1] + 1e-12:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return max((merged[i + 1][0] - merged[i][1] for i in range(len(merged) - 1)),
               default=0.0)
