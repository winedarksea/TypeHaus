"""R312.1.1 at the open side of a *flight* — the shape of the rule nothing measured.

``code.R312_1_guard`` grades the four edges of a stair well against the deck that hosts it,
and ``code.R312_1_guard_height`` grades the ring of every floor deck. A flight's own side is
neither: it is a sloped walking surface that climbs out of one floor without belonging to
any deck ring, and until this module it was the one raised walking surface in the model no
rule looked at. Catlin's ST-S2A stood 30"-120" over the study it climbs out of, open on the
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

from typing import Any

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
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
