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


def _edge_cover_intervals(edge_across: float, along0: float, along1: float, across: int,
                          along: int, walls, railings, stair_quads):
    """(covered, short_guards): interval cover along one well edge, and any railing that
    runs the edge but is too short to be a guard."""
    from shapely.geometry import LineString

    from typehaus.resolve.floors import _wall_footprint_span

    covered: list[tuple[float, float]] = []
    short: list = []
    used: set[str] = set()
    for wall in walls:
        span_across = _wall_footprint_span(wall, across)
        span_along = _wall_footprint_span(wall, along)
        if span_across is None or span_along is None:
            continue
        if not (span_across[0] - _GUARD_WALL_FACE_TOL_M <= edge_across
                <= span_across[1] + _GUARD_WALL_FACE_TOL_M):
            continue
        covered.append(span_along)
    for railing, tall_enough in railings:
        for p, q in zip(railing.path, railing.path[1:], strict=False):
            pa, qa = p.xy_m, q.xy_m
            if (abs(pa[across] - edge_across) > _GUARD_PLANE_TOL_M
                    or abs(qa[across] - edge_across) > _GUARD_PLANE_TOL_M):
                continue
            lo, hi = sorted((pa[along], qa[along]))
            if tall_enough:
                covered.append((lo, hi))
                used.add(railing.tag)
            else:
                short.append(railing)
    edge_line = LineString([(edge_across, along0), (edge_across, along1)]
                           if across == 0 else
                           [(along0, edge_across), (along1, edge_across)])
    for quad in stair_quads:
        inter = edge_line.intersection(quad)
        if inter.is_empty or getattr(inter, "length", 0.0) <= 1e-6:
            continue
        values = [pt[along] for geom in getattr(inter, "geoms", [inter])
                  for pt in geom.coords]
        covered.append((min(values), max(values)))
    return covered, short, used



#: A well edge under a roof lower than this is not an open side. R312.1.1 scopes guards to
#: *walking surfaces*; where the roof structure stands less than the code's own 30" fall
#: dimension above the deck there is no walking surface on either side of the edge, and the
#: roof plane closes the void more completely than the 36" guard it displaces could. 30",
#: not 36": between the two a guard is unbuildable but a person could still be prone there,
#: and that should stay a FAIL so it forces a design answer rather than passing quietly.
_ROOF_CLOSES_EDGE_M = _GUARD_TRIGGER_DROP.meters
#: Sampling step along an edge when asking whether the roof closes it.
_ROOF_SAMPLE_STEP_M = 0.25


def _roof_closed_interval(ctx: CheckContext, across: int, edge_across: float,
                          lo: float, hi: float, surface: float) -> bool:
    """Is this whole stretch of a well edge roofed too low to stand or walk in?

    Sampled rather than tested at the ends: the underside is linear along a rake but an
    edge may run across the ridge, where the ends are the two LOWEST points. Sampling
    catches that; two-point testing would exempt a full-height opening under a peak.
    """
    from typehaus.resolve.roof_geometry import roof_bearing_footprint, roof_underside_at

    if hi - lo <= 0:
        return True
    steps = max(2, int((hi - lo) / _ROOF_SAMPLE_STEP_M) + 1)
    for index in range(steps + 1):
        station = lo + (hi - lo) * index / steps
        point = ((edge_across, station) if across == 0 else (station, edge_across))
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
    from shapely.geometry import Polygon as _ShapelyPolygon

    from typehaus.model.floors import FloorOpening, FloorOpeningPurpose, FloorSystem
    from typehaus.model.structure import Railing
    from typehaus.resolve.floors import _rectangular_opening_box, _subtract_interval

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
        stair_quads = []
        for stair in ctx.model.stairs:
            for stations in _flight_stations(stair).values():
                pairs = list(zip(stations, stations[1:], strict=False))
                for index, ((a0, b0, z0), (a1, b1, z1)) in enumerate(pairs):
                    if max(z0, z1) < surface - _GUARD_THROAT_Z_WINDOW_M:
                        continue
                    if index == len(pairs) - 1:
                        # The nosing line's extrapolated arrival station lands a tread
                        # short of the finished well edge (the void is cut to the
                        # trimmer, not to the top nosing); stretch the final quad along
                        # the travel direction so the throat actually reaches the edge
                        # it enters through. Along travel only — never sideways, which
                        # would eat into genuinely open sides beside the flight.
                        run = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
                        if run > 1e-9:
                            ux, uy = (a1[0] - a0[0]) / run, (a1[1] - a0[1]) / run
                            reach = _GUARD_THROAT_REACH_M
                            a1 = (a1[0] + ux * reach, a1[1] + uy * reach)
                            b1 = (b1[0] + ux * reach, b1[1] + uy * reach)
                    quad = _ShapelyPolygon([a0, b0, b1, a1])
                    if quad.is_valid and quad.area > 1e-6:
                        stair_quads.append(quad)

        edges = (("west", 0, minx, miny, maxy), ("east", 0, maxx, miny, maxy),
                 ("south", 1, miny, minx, maxx), ("north", 1, maxy, minx, maxx))
        gaps: list[str] = []
        roof_closed: list[str] = []
        short_guards: list = []
        guarding_tags: set[str] = set()
        for name, across, edge_across, along0, along1 in edges:
            along = 1 - across
            covered, short, used = _edge_cover_intervals(
                edge_across, along0, along1, across, along, walls, railings, stair_quads)
            short_guards.extend(short)
            guarding_tags |= used
            remaining = [(along0, along1)]
            for lo, hi in covered:
                remaining = _subtract_interval(remaining, lo, hi)
            for lo, hi in remaining:
                if hi - lo <= _GUARD_GAP_TOL_M:
                    continue
                if _roof_closed_interval(ctx, across, edge_across, lo, hi, surface):
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


@check(Tier.CODE, "code.R312_1_guard_height")
def raised_surface_guard_height(ctx: CheckContext) -> list[Finding]:
    """R312.1.1 — a walking surface more than 30" above what is below it needs a 36" guard.

    Between them, ``code.R312_1_guard`` (stair wells) and ``structural.deck_guard`` (decks)
    covered two shapes of the same requirement and left the general one unmeasured: any
    raised floor edge. A loft, a mezzanine, an open landing, a floor that steps down to a
    lower one — all of them are R312.1.1 and none had a rule.

    The drop is measured against what is actually beneath the edge: the highest floor deck
    below it, or the site grade for an edge with nothing under it. Where an exterior edge
    has no grade datum to fall to, this reports UNKNOWN — a 30" trigger cannot be evaluated
    without knowing where the bottom is.
    """
    from shapely.geometry import LineString, Point, Polygon

    from typehaus.model.structure import Railing

    cid, code = "code.R312_1_guard_height", "R312.1.1"
    decks = [floor for floor in ctx.model.floors
             if floor.deck_outline and len(floor.deck_outline) >= 3]
    if not decks:
        return [_unknown(cid, "no floor decks resolve, so there is no raised walking "
                         "surface to measure", (), code)]
    grade = ctx.plan.project.site.grade
    railings = [e for e in ctx.plan.all_elements() if isinstance(e, Railing)]
    out: list[Finding] = []
    for deck in decks:
        surface = deck.deck_z1_m
        ring = list(deck.deck_outline)
        lower = [(Polygon(other.deck_outline), other.deck_z1_m)
                 for other in decks
                 if other.tag != deck.tag and other.deck_outline
                 and other.deck_z1_m < surface - 1e-6]
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
        near_railings = [r for r in railings
                         if abs(r.base_elevation.meters - surface) < _EDGE_RAILING_BASE_TOL_M]
        unguarded: list[str] = []
        unknown_edges: list[str] = []
        short: list[str] = []
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            seg = LineString([a, b])
            if seg.length <= _EDGE_GAP_TOL_M:
                continue
            mid = seg.interpolate(0.5, normalized=True)
            probe = Point(mid.x, mid.y)
            below = max([z for poly, z in lower if poly.covers(probe)], default=None)
            if below is None:
                if grade is None:
                    unknown_edges.append(f"({mid.x / .3048:.0f}', {mid.y / .3048:.0f}')")
                    continue
                below = grade.meters
            if surface - below <= _GUARD_TRIGGER_DROP.meters + 1e-9:
                continue  # under 30" — no guard required
            if any(seg.distance(_wall_line(w)) <= w.thickness_m / 2.0 + 0.05 for w in walls):
                continue  # a full-height wall stands on this edge
            guarding = [r for r in near_railings
                        if _railing_runs_edge(r, seg)]
            if not guarding:
                unguarded.append(f"({mid.x / .3048:.0f}', {mid.y / .3048:.0f}') "
                                 f"{(surface - below) / .3048:.1f}' drop")
            else:
                low = [r for r in guarding
                       if r.height.meters + 1e-9 < _GUARD_MIN_HEIGHT.meters]
                short.extend(r.tag for r in low)
        if unguarded:
            out.append(_fail(cid, f"{deck.tag}: unguarded edge(s) over a 30\" drop — "
                             f"{'; '.join(unguarded)}", (deck.tag,), code))
        elif short:
            names = sorted(set(short))
            out.append(_fail(cid, f"{deck.tag}: guard(s) {', '.join(names)} stand under the "
                             "36\" R312.1.2 minimum", (deck.tag, *names), "R312.1.2"))
        elif unknown_edges:
            out.append(_unknown(cid, f"{deck.tag}: edge(s) at {', '.join(unknown_edges)} "
                                "have nothing modeled beneath them and the site states no "
                                "grade datum, so the 30\" trigger cannot be evaluated",
                                (deck.tag,), code))
        else:
            out.append(_pass(cid, f"{deck.tag}: every edge over a 30\" drop is closed by a "
                             "wall or a 36\" guard", code))
    return out


def _wall_line(wall):
    from shapely.geometry import LineString

    return LineString(wall.axis)


def _railing_runs_edge(railing, seg) -> bool:
    from shapely.geometry import LineString

    points = [p.xy_m for p in railing.path]
    if len(points) < 2:
        return False
    return LineString(points).distance(seg) <= _EDGE_RAILING_PLANE_TOL_M


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
    That is what closes the defect this rule shipped with — it used to pass ``RL-SG-BALCONY``
    on the authored field alone while the 3D view showed a 42" guard with two bars and a
    wide-open 40" gap between them, because the infill had never been drawn. A guard whose
    drawn opening and whose authored opening disagree is a resolver bug, and saying so here
    is worth more than either half alone: ``panel`` now passes because a lite is *drawn*
    edge to edge rather than on a claim, and ``mesh``/``cable`` are graded on what the model
    actually shows.

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
