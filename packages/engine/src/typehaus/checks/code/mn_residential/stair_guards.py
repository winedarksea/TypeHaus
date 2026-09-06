"""R312.1.1 at the open side of a *flight* — the shape of the rule nothing measured.

``code.R312_1_guard`` grades the four edges of a stair well against the deck that hosts it,
and ``code.R312_1_guard_height`` grades the ring of every floor deck. A flight's own side is
neither: it is a sloped walking surface that climbs out of one floor without belonging to
any deck ring — the one raised walking surface in the model this module covers.
Catlin's ST-S2A stood 30"-120" over the study it climbs out of, open on the
south side for 10'-0", at a clean 0-FAIL report.

The two rules divide on one line, and it is the stair's own ``outline`` — the well. Inside
it, an unguarded edge is the well's and ``code.R312_1_guard`` adjudicates it edge by edge.
Outside it, the flight has left the shaft and stands in a room, which is this rule. No
overlap, no seam.

Every input is resolved output: the nosing stations of
:mod:`typehaus.resolve.stairs.walkline`, the same derivation the R311.7 rules and the
railing resolver measure against.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.checks.code.mn_residential._common import (
    _fail,
    _na,
    _pass,
    _unknown,
)
from typehaus.checks.code.mn_residential.fall_protection import _GUARD_TRIGGER_DROP
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import inch

#: R312.1.2 exception 1: a guard on the open side of a stair is measured from the line
#: joining the nosings and may stand 34", where every other guard owes 36". Those two inches
#: are why this rule cannot borrow ``fall_protection``'s height constant.
_STAIR_GUARD_MIN_HEIGHT = inch(34)
#: A railing whose plan line runs within this of a nosing end stands on that side.
#: ``fall_protection``'s number for the same question asked at a floor edge.
_RAIL_PLANE_TOL_M = 0.20
#: How far a wall's own face may miss a nosing end and still be the wall it lands on.
_WALL_FACE_TOL_M = 0.05
#: A nosing end sits *on* the well line, so containment there is a coin toss. Step an inch
#: outboard and ask what is on the other side of it instead.
_OUTBOARD_STEP_M = inch(1).meters


def _landing_below(decks: list[tuple[Any, float]], probe: Any, surface: float,
                   riser: float,
                   base: float | None) -> float | None:
    """What a fall from this nosing end would land on, or ``None`` if nothing is modeled.

    The highest floor datum under it, or the floor the flight springs from — which a placed
    stair always has, so the ``None`` here is the unplaced one, not a house with a bare
    site. Never PASS by absence: the caller turns it into an UNKNOWN naming the stair.

    A deck within one riser *above* the nosing counts too, and that is the arrival: a tread
    one riser under the floor beside it is a step across, not a drop. The riser is the
    stair's own number rather than a tolerance — it is the definition of the next level up.
    """
    under = [z for poly, z in decks
             if z <= surface + riser + 1e-9 and poly.covers(probe)]
    if base is not None:
        under.append(base)
    return max(under) if under else None


@check(Tier.CODE, "code.R312_1_1_stair_open_side")
def stair_open_side_guard(ctx: CheckContext) -> list[Finding]:
    """R312.1.1 — the open side of a flight standing over 30" up carries a 34" guard.

    Every nosing's two ends are put to three questions, in the order a builder would ask
    them:

    * **Is it still in the shaft?** A step outboard that lands inside the stair's own
      outline is looking at the stairway, not at a room — a switchback lane facing its own
      other lane across the well partition's reservation, a winder's inner corner. That void
      is the well's, and ``code.R312_1_guard`` already grades it edge by edge.
    * **How far is the fall?** :func:`_landing_below`. 30" or under and the rule does not
      reach, which is why ST-S2A's three winders and the five-riser garage stair are silent
      here rather than exempted by a special case.
    * **Is the side closed?** A wall whose own band brackets the nosing — ``z0`` at or under
      it, ``z1`` above. Both halves matter: a partition standing on the deck *above* a
      flight passes over it without closing anything, and W-A-GC-S sits 1 3/8" outboard of
      ST-S2A's south side doing exactly that.

    What survives is an open side, and it wants a guard: a ``Railing`` in a guard role
    running that line, either raked with the flight (``serves_stair``) or level at the
    nosing's own elevation where a flight arrives beside a deck guard. A guard that runs the
    line under 34" fails on height instead — the same two-verdict shape as
    ``code.R312_1_guard``, so a short guard never reads as a missing one.
    """
    from shapely.geometry import LineString, Point, Polygon

    from typehaus.model.structure import Railing
    from typehaus.resolve.stairs.walkline import flight_stations

    cid, code = "code.R312_1_1_stair_open_side", "R312.1.1"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    decks = [(Polygon(floor.deck_outline), floor.deck_z0_m) for floor in ctx.model.floors
             if floor.deck_outline and len(floor.deck_outline) >= 3]
    guards = [(LineString([p.xy_m for p in e.path]), e)
              for e in ctx.plan.all_elements()
              if isinstance(e, Railing) and len(e.path) >= 2
              and e.role in ("guard", "guard_and_handrail")]
    walls = [(LineString(w.axis), w) for w in ctx.model.walls]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        shaft = Polygon(stair.outline) if len(stair.outline) >= 3 else None
        open_sides: list[tuple[float, tuple[float, float]]] = []  # (drop, plan point)
        short: set[str] = set()
        standing: set[str] = set()
        unmeasured = 0
        for key, stations in flight_stations(stair).items():
            # The synthetic arrival station a tread flight is extended by is the deck past
            # the top riser, not a tread — the same station ``_unserved_nosings`` drops for
            # the same reason. Measuring it would read the arrival floor as a 30" fall.
            used = (stations[:-1] if key.startswith("tread") and len(stations) >= 3
                    else stations)
            for a, b, z in used:
                for near, far in ((a, b), (b, a)):
                    probe = Point(near)
                    if shaft is not None and shaft.covers(_outboard(near, far)):
                        continue
                    landing = _landing_below(decks, probe, z, stair.riser_height_m,
                                             stair.base_elevation_m)
                    if landing is None:
                        unmeasured += 1
                        continue
                    drop = z - landing
                    if drop <= _GUARD_TRIGGER_DROP.meters + 1e-9:
                        continue
                    if any(line.distance(probe) <= wall.thickness_m / 2.0 + _WALL_FACE_TOL_M
                           and wall.z0_m <= z + 0.05 < wall.z1_m for line, wall in walls):
                        continue
                    running = [g for line, g in guards
                               if line.distance(probe) <= _RAIL_PLANE_TOL_M
                               and (g.serves_stair == stair.tag
                                    or abs(g.base_elevation.meters - z) <= _RAIL_PLANE_TOL_M)]
                    if not running:
                        open_sides.append((drop, near))
                    for guard in running:
                        target = (short if guard.height.meters + 1e-9
                                  < _STAIR_GUARD_MIN_HEIGHT.meters else standing)
                        target.add(guard.tag)
        if open_sides:
            drop, point = max(open_sides)
            out.append(_fail(cid, f"{stair.tag}: {len(open_sides)} nosing end(s) stand on an "
                             f"open side with no guard — worst at ({point[0] / .3048:.1f}', "
                             f"{point[1] / .3048:.1f}') over a {drop / .0254:.0f}\" fall; "
                             "R312.1.1 guards the open sides of a stair more than 30\" up",
                             (stair.tag,), code))
        elif short:
            names = sorted(short)
            out.append(_fail(cid, f"{stair.tag}: guard(s) {', '.join(names)} run its open "
                             "side under the 34\" R312.1.2 minimum measured from the nosing "
                             "line", (stair.tag, *names), "R312.1.2"))
        elif unmeasured:
            out.append(_unknown(cid, f"{stair.tag}: {unmeasured} nosing end(s) have no "
                                "floor modeled beneath them and the flight states no base "
                                "elevation, so the 30\" trigger cannot be measured",
                                (stair.tag,), code))
        else:
            how = (f" — open side guarded by {', '.join(sorted(standing))}"
                   if standing else "")
            out.append(_pass(cid, f"{stair.tag}: every nosing end is inside its own well, "
                             f"walled, or under the 30\" trigger{how}", code))
    return out


def _outboard(near: tuple[float, float], far: tuple[float, float]) -> Any:
    """``near`` stepped an inch away from the flight — the point that asks what is beside it.

    Degenerate stations (a zero-width tread) step nowhere and stay on the nosing end, which
    reads as inside the shaft. That is the right way to be wrong: a stair with no width is
    a resolver problem, not a guard deficiency.
    """
    from shapely.geometry import Point

    run = ((near[0] - far[0]) ** 2 + (near[1] - far[1]) ** 2) ** 0.5
    if run < 1e-9:
        return Point(near)
    step = _OUTBOARD_STEP_M / run
    return Point(near[0] + (near[0] - far[0]) * step, near[1] + (near[1] - far[1]) * step)


# --- R311.7.1 at a stair head that lands on a WALL TOP ---------------------------------
#: R311.7.1's minimum stairway width, which the landing at the head of a flight owes too.
_WALL_TOP_LANDING_MIN_WIDTH = inch(36)
#: How far the arrival elevation may sit off the wall's own top and still be that top. A
#: threshold board's thickness: ``ST-SG-PORCH`` arrives 1" over ``W-SG-E1`` because 12" of
#: wall top is decked flush with the porch plank beside it.
_WALL_TOP_ARRIVAL_TOL_M = inch(3).meters
#: A guard is not an obstruction. R311.7.1 lets a handrail project into the required width
#: and ``code.R311_7_1_stair_width`` already grades that projection; what this rule asks is
#: what *else* stands on the wall top, which is a different question with a different answer.
_GUARD_SOLID_CATEGORIES = ("railing", "railing_infill", "railing_glass")
#: A solid must rise above the wall top to obstruct it — flashing let into the top does not.
_STANDS_PROUD_M = inch(1).meters


def _arrival_of(stair) -> tuple[tuple[float, float], tuple[float, float],
                                tuple[float, float], float] | None:
    """``(a, b, travel, z)`` for the top flight's arrival station, or ``None``.

    ``travel`` is the unit plan direction the flight is going when it arrives — the
    direction the landing extends in, which is the whole point of deriving it here rather
    than from ``run_direction``: a winder or a switchback arrives on a lane of its own.
    """
    from typehaus.resolve.stairs.walkline import flight_stations

    best = None
    for stations in flight_stations(stair).values():
        if len(stations) < 2:
            continue
        if best is None or stations[-1][2] > best[-1][2]:
            best = stations
    if best is None:
        return None
    (a0, b0, _z0), (a1, b1, z1) = best[-2], best[-1]
    mid0 = ((a0[0] + b0[0]) / 2.0, (a0[1] + b0[1]) / 2.0)
    mid1 = ((a1[0] + b1[0]) / 2.0, (a1[1] + b1[1]) / 2.0)
    run = math.hypot(mid1[0] - mid0[0], mid1[1] - mid0[1])
    if run < 1e-9:
        return None
    travel = ((mid1[0] - mid0[0]) / run, (mid1[1] - mid0[1]) / run)
    return a1, b1, travel, (stair.arrival_elevation_m
                            if stair.arrival_elevation_m is not None else z1)


#: Cross-sections taken along the landing when measuring its clear width. A dozen over a
#: foot of threshold resolves a round column's waist without pretending to sub-millimetre
#: precision on a hand-poured wall top.
_LANDING_SECTIONS = 12


def _clear_across(region, a, b, travel) -> float:
    """The narrowest clear width the landing offers **across** the direction of travel.

    Not ``_min_clear_width``: that erosion returns the narrowest corridor in *any*
    direction, which on a 12"-deep threshold is the 12" depth — R311.7.6's dimension, not
    R311.7.1's. Width is measured square to travel, section by section, and the answer at
    each section is the WIDEST contiguous run across it: a column standing mid-landing
    leaves two passages and you walk through one of them, not through their sum.
    """
    from shapely.geometry import LineString

    if region.is_empty:
        return 0.0
    minx, miny, maxx, maxy = region.bounds
    reach = math.hypot(maxx - minx, maxy - miny) + 1.0
    across = (b[0] - a[0], b[1] - a[1])
    run = math.hypot(*across)
    if run < 1e-9:
        return 0.0
    across = (across[0] / run, across[1] / run)
    depth = max((travel[0] * (x - a[0]) + travel[1] * (y - a[1]))
                for x, y in region.exterior.coords) if hasattr(region, "exterior") else max(
        (travel[0] * (x - a[0]) + travel[1] * (y - a[1]))
        for piece in region.geoms for x, y in piece.exterior.coords)
    widest_per_section = []
    for index in range(1, _LANDING_SECTIONS + 1):
        station = depth * index / (_LANDING_SECTIONS + 1)
        centre = ((a[0] + b[0]) / 2.0 + travel[0] * station,
                  (a[1] + b[1]) / 2.0 + travel[1] * station)
        cut = LineString([(centre[0] - across[0] * reach, centre[1] - across[1] * reach),
                          (centre[0] + across[0] * reach, centre[1] + across[1] * reach)])
        sliced = region.intersection(cut)
        if sliced.is_empty:
            return 0.0
        widest_per_section.append(max((part.length
                                       for part in getattr(sliced, "geoms", [sliced])),
                                      default=0.0))
    return min(widest_per_section, default=0.0)

@check(Tier.CODE, "code.R311_7_1_wall_top_landing")
def wall_top_landing_width(ctx: CheckContext) -> list[Finding]:
    """R311.7.1 — a flight whose head lands on a WALL TOP gets 36" of clear landing there.

    The shape of the rule with nothing on either end of it. ``code.R311_7_1_stair_width``
    measures the flight; ``code.R311_7_6_landing_depth`` measures a landing that is an
    element. A stair that springs from the top of a concrete wall has neither: the wall top
    it crosses is a walking surface that no ``FloorSystem`` and no ``Slab`` models, and the
    board decking it may be trim with nothing to frame under it — ``ST-SG-PORCH``'s is 3 sf
    of composite plank, deliberately not an element, priced with the porch it matches.

    So the rule is driven off the **wall top**, never off a landing element. The head of the
    top flight is put inside a ``ResolvedWall`` footprint whose ``z1_m`` is the arrival
    elevation, with no floor deck or slab covering it; the landing is then that wall's own
    footprint, banded to the stair's width and swept the way the flight is travelling. Every
    solid standing proud of the wall top is cut out of it and what remains is measured with
    the same erosion R311.6 uses on a hallway.

    Drawn in the sunken garden's north strip, ``ST-SG-PORCH``'s threshold ran straight
    through ``PT-SG-BR3`` — a 12" ROUND column on a 12" wall, edge to edge, leaving 10" of
    passage one side and 14" the other — at zero findings, because the column's east face is
    exactly tangent to the stair's head and there was no threshold *element* to overlap.
    Guards are excused from the subtraction on purpose: R311.7.1 admits a handrail's
    projection and ``code.R311_7_1_stair_width`` is where that is graded.
    """
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    cid, code = "code.R311_7_1_wall_top_landing", "R311.7.1"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    modelled = [(Polygon(floor.deck_outline), floor.deck_z1_m) for floor in ctx.model.floors
                if floor.deck_outline and len(floor.deck_outline) >= 3]
    modelled += [(Polygon(solid.outline), solid.z1_m) for solid in ctx.model.solids
                 if solid.category == "slab" and len(solid.outline) >= 3]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        arrival = _arrival_of(stair)
        if arrival is None:
            continue
        a, b, travel, z = arrival
        # A step forward of the arrival riser line, so a head sitting exactly on the wall's
        # own face is asked about the wall it is entering rather than about the boundary.
        step = (( a[0] + b[0]) / 2.0 + travel[0] * _STANDS_PROUD_M,
                (a[1] + b[1]) / 2.0 + travel[1] * _STANDS_PROUD_M)
        probe = Point(step)
        if any(abs(top - z) <= _WALL_TOP_ARRIVAL_TOL_M and poly.covers(probe)
               for poly, top in modelled):
            continue  # it arrives on a modeled walking surface; other rules measure that
        wall = next((w for w in ctx.model.walls
                     if abs(w.z1_m - z) <= _WALL_TOP_ARRIVAL_TOL_M and w.layers
                     and unary_union([Polygon(layer.polygon)
                                      for layer in w.layers]).covers(probe)), None)
        if wall is None:
            continue
        top = unary_union([Polygon(layer.polygon) for layer in wall.layers])
        reach = max(top.bounds[2] - top.bounds[0], top.bounds[3] - top.bounds[1]) + 1.0
        band = Polygon([a, b, (b[0] + travel[0] * reach, b[1] + travel[1] * reach),
                        (a[0] + travel[0] * reach, a[1] + travel[1] * reach)])
        landing = top.intersection(band)
        if landing.is_empty or landing.area <= 1e-9:
            continue
        blockers = [solid for solid in ctx.model.solids
                    if solid.category not in _GUARD_SOLID_CATEGORIES
                    and len(solid.outline) >= 3
                    and abs(solid.z0_m - wall.z1_m) <= _WALL_TOP_ARRIVAL_TOL_M
                    and solid.z1_m > wall.z1_m + _STANDS_PROUD_M
                    and Polygon(solid.outline).intersects(landing)]
        clear_of = landing
        for solid in blockers:
            clear_of = clear_of.difference(Polygon(solid.outline))
        clear = _clear_across(clear_of, a, b, travel)
        names = ", ".join(sorted(solid.tag for solid in blockers)) or "nothing"
        where = (f"{stair.tag}'s head lands on {wall.tag}'s top at "
                 f"{z / .3048:.2f}' with no floor or slab modeled there")
        if clear + 1e-9 < _WALL_TOP_LANDING_MIN_WIDTH.meters:
            out.append(_fail(cid, f"{where}; {names} leave{'' if len(blockers) == 1 else ''} "
                             f"{clear / .0254:.1f}\" of clear width across it, under "
                             f"R311.7.1's 36\"", (stair.tag, wall.tag,
                                                  *(s.tag for s in blockers)), code))
        else:
            out.append(_pass(cid, f"{where}, and {names} standing on it leaves "
                             f"{clear / .0254:.1f}\" clear (>= 36\")", code))
    if not out:
        return [_na(cid, "N/A — no stair in the plan lands its head on a wall top; every "
                    "flight arrives on a floor deck or a slab, which "
                    "code.R311_7_6_landing_depth measures", (), code)]
    return out
