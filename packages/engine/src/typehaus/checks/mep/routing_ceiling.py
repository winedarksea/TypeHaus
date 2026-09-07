"""``mep.run_in_finished_volume`` — a run hanging in a room somebody lives in.

``mep.run_over_void`` asks whether there is anything to strap a run to.
``mep.run_through_opening`` asks what it goes through. Neither asks the question a person
standing in the room asks, which is whether the pipe is *in the room*, and
``run_route_efficiency``'s docstring used to say why: "the model has no per-room ceiling
plane". It has had one since the ceiling work — :class:`~typehaus.resolve.model.ResolvedCeiling`
— and this check is what that record makes writable.

Named for the predicate rather than "below the ceiling", because the same predicate covers a
riser standing in the middle of a room, which no ceiling comparison would catch.

**Three things decide real findings from arithmetic here**, and all three were measured
rather than reasoned:

**The band has a floor, and it is the storey datum.** ``ResolvedCeiling`` carries no floor
plane. Without a lower edge a basement main is graded against every room stacked above it
and the naive count on catlin is 435 rows; with it, 66. The storey base is the honest edge —
below it the run is in some other storey's business.

**Depth is the severity, not length.** Ranking by crossing length puts the long shallow runs
on top; ranking by intrusion puts the real defects there. ``PR-B-KITCH-DRAIN`` hangs 9.9"
below the gym's ceiling for 9.1 ft and 6.7" below the theater's for 14.5 ft — genuinely bad,
and still not the worst. ``PR-A-STUBATH-DRAIN``'s dog-leg (fixed before this check landed;
``test_run_in_finished_volume`` puts it back) dived through **the suite bath's entire
107 1/2" of height**. The message leads with the depth, and the depth is clamped to the
room: a pipe whose bottom is under the storey datum is on its way through the floor, and
"116 inches below the ceiling" of a 107-inch room is not a number anybody can use.

**The clip is three-dimensional.** The plan piece inside the room is projected back onto the
segment's own parameter and intersected with the interval where the pipe's *surface* is
actually in the air — the same lesson
:func:`~typehaus.checks.mep.routing_geometry.crossing_band` records for openings. Without
it, a segment that merely passes overhead at one end reads as being in the room for its
whole length.

**What it cannot answer is the attic.** Every ``RM-A-*`` room resolves ``z0_m = None``
(``FollowRoof``): there is no flat plane to compare against, so those rooms are named in an
explicit UNKNOWN rather than passing quietly. A clean report that claimed to cover them
would be claiming coverage it does not have.

**Known soft spot.** The wall exemption asks only whether the run is inside a wall's plan
footprint and z band — see
:func:`~typehaus.checks.mep.routing_geometry.wall_cover`. A 12" cast foundation wall
satisfies that and cannot host a 2" drain. ``mep.wet_wall_occupancy`` and
``mep.sleeve_coverage`` own that question, which is the right division of labour and exactly
why a reroute must not "fix" a crossing by hugging a concrete wall.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, MultiLineString, Point, Polygon

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.mep.routing import VOID_BUFFER_M
from typehaus.checks.mep.routing_geometry import M_TO_FT, run_polylines, run_radii, wall_cover
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import EXPOSED_SERVICE_OCCUPANCIES, Occupancy
from typehaus.quantities import M_PER_IN

#: What each trade can actually terminate at, by run kind. **Per trade, not one list**, and
#: that is what makes the grace rule mean something: a drain ending near a light switch has
#: not connected to anything, and a one-list version excused ``PR-A-STUBATH-DRAIN``'s
#: dog-leg because ``ED-S-SUITEBATH-SW`` happened to sit 8.9" from the stack head.
#:
#: ``Equipment`` is in all three because it genuinely is: an air handler takes duct, an ERV
#: takes a condensate line, and both take power. ``Furniture`` is in none — a sofa is not a
#: terminal, and 127 of them would excuse most of the house. ``Luminaire`` is not a kind at
#: all; a light fixture is an ``ElectricalDevice``.
_TERMINAL_KINDS = {
    "pipe": frozenset({"Fixture", "Appliance", "Equipment"}),
    "duct": frozenset({"Register", "Equipment"}),
    "conduit": frozenset({"ElectricalDevice", "Alarm", "Equipment"}),
}


def _soffit_union(ctx: CheckContext) -> Any:
    """The plan union of every resolved soffit — a run inside a bulkhead is boxed out.

    A soffit is the authored answer to exactly this finding, so a route that has already
    been covered by one must stop being reported, or the fix cannot be verified.
    """
    from typehaus.resolve.overlay import union_all

    polygons = [Polygon(soffit.outline) for soffit in ctx.model.soffits
                if len(soffit.outline) >= 3]
    valid = [poly for poly in polygons if poly.is_valid and not poly.is_empty]
    return union_all(valid) if valid else None


def _terminals_in(ctx: CheckContext, storey: str,
                  outline: Any) -> dict[str, list[tuple[float, float]]]:
    """Terminal plan points inside this ceiling's polygon, per trade.

    Membership in the room comes from the **polygon**, not from an authored ``room=``
    field — the trick ``soffit_occupancy`` already uses, and for the same reason: a missing
    or wrong room tag must not be able to turn a connection into a transit finding.

    Membership on the STOREY does come from the filing, and it has to. A plan polygon is
    two-dimensional: read across the whole model it collects the basement lavatory and the
    attic water closet standing at the same x/y as this room, and a drain diving through
    the suite bath gets excused by a fixture two floors below it.
    """
    out: dict[str, list[tuple[float, float]]] = {kind: [] for kind in _TERMINAL_KINDS}
    for element in ctx.plan.storey_elements(storey):
        kinds = [trade for trade, allowed in _TERMINAL_KINDS.items()
                 if element.element_kind in allowed]
        if not kinds:
            continue
        position = getattr(element, "position", None)
        xy = getattr(position, "xy_m", None)
        if xy is None or not outline.covers(Point(xy)):
            continue
        for trade in kinds:
            out[trade].append(xy)
    return out


def _terminates_in_room(path: tuple[tuple[float, float], ...], index: int,
                        terminals: Any, grace_m: float) -> bool:
    """True when this segment is the run's own first or last leg AND that terminal vertex
    lands within ``grace_m`` of a terminal element inside this room's outline.

    A drop that ends at a thing in the room *is* the connection to it; a run passing through
    is not. Only ``index == 0`` or ``len(path) - 2`` qualifies — an interior segment is
    transit, and no amount of proximity makes it a connection.
    """
    if index == 0:
        vertex = path[0]
    elif index == len(path) - 2:
        vertex = path[-1]
    else:
        return False
    return any((vertex[0] - x) ** 2 + (vertex[1] - y) ** 2 <= grace_m * grace_m
               for x, y in terminals)


def _air_interval(za: float, zb: float, radius: float, floor: float, ceiling: float,
                  tol: float) -> tuple[float, float] | None:
    """The ``t`` sub-interval of a segment where the pipe's OUTSIDE is in the room's air.

    ``bottom(t) = z(t) - radius`` must be under the ceiling by more than ``tol``, and
    ``top(t) = z(t) + radius`` must be over the storey's floor. Both are linear in ``t``, so
    each is a half-line and the answer is their intersection with ``[0, 1]``.
    """
    lo, hi = 0.0, 1.0
    for coefficient, limit, want_below in (
            (zb - za, ceiling - tol + radius, True),    # z(t) < ceiling - tol + radius
            (zb - za, floor - radius, False)):          # z(t) > floor - radius
        offset = limit - za
        if abs(coefficient) < 1e-12:
            if (za < limit) != want_below:
                return None
            continue
        bound = offset / coefficient
        # A negative coefficient flips the inequality, which is why the sense is recomputed
        # rather than assumed: a segment that falls and one that rises cross the same plane
        # from opposite ends of their own parameter.
        below = (coefficient > 0) == want_below
        if below:
            hi = min(hi, bound)
        else:
            lo = max(lo, bound)
    return (lo, hi) if hi - lo > 1e-9 else None


@check(Tier.ADVISORY, "mep.run_in_finished_volume")
def run_in_finished_volume(ctx: CheckContext) -> list[Finding]:
    """A pipe, duct or raceway may not hang in the open air of a finished room.

    ADVISORY: no IRC section says a duct may not cross a living room, and there is no
    citation to hang a ``PermitItemSpec`` on. It is the buildability twin of
    ``mep.run_over_void``, and ``CheckReport.counts()`` counts a FAIL regardless of
    severity, so it holds a clean house to the same standard a code check would.

    A room is finished unless its occupancy is in
    :data:`~typehaus.model.enums.EXPOSED_SERVICE_OCCUPANCIES` — a mechanical room's ceiling
    is a service plane and pipe hangs there by design. Everything else is graded, hallways
    and stairwells included: those are the rooms people look *up* in.
    """
    cid = "mep.run_in_finished_volume"
    rules = ctx.preferences.mep
    runs = run_polylines(ctx)
    if not runs:
        return [unknown(cid, "no pipe, duct or conduit run is modeled, so there is no "
                             "route to grade", ())]
    if not ctx.model.ceilings:
        return [unknown(cid, f"{len(runs)} runs: this model resolves no ceiling plane, so "
                             "there is nothing to say a room's air ends at", ())]

    occupancies = {room.tag: room.occupancy for room in ctx.model.rooms}
    storey_z = {storey.tag: storey.elevation.meters for storey in ctx.plan.storeys}
    radii = run_radii(ctx)
    soffits = _soffit_union(ctx)
    tol = rules.ceiling_intrusion_in * M_PER_IN
    grace_m = rules.terminal_grace_in * M_PER_IN

    graded: list[tuple[Any, float, float, list, Any]] = []
    follow_roof: set[str] = set()
    for ceiling in ctx.model.ceilings:
        if ceiling.z0_m is None:
            follow_roof.add(ceiling.room_ref)
            continue
        occupancy = occupancies.get(ceiling.room_ref)
        if occupancy is not None and Occupancy(occupancy) in EXPOSED_SERVICE_OCCUPANCIES:
            continue
        if len(ceiling.outline) < 3:
            continue
        outline = Polygon(ceiling.outline)
        if not outline.is_valid or outline.is_empty:
            continue
        floor = storey_z.get(ceiling.storey, 0.0)
        graded.append((ceiling, floor, ceiling.z0_m,
                       _terminals_in(ctx, ceiling.storey, outline), outline))

    out: list[Finding] = []
    covers: dict[str, Any] = {}
    ungraded: list[str] = []
    worst: dict[tuple[str, str], tuple[float, float]] = {}

    for kind, tag, path, z in runs:
        if len(path) < 2:
            continue
        if len(z) != len(path):
            ungraded.append(tag)
            continue
        radius = radii.get(tag, 0.0)
        for index in range(len(path) - 1):
            a, b = path[index], path[index + 1]
            za, zb = z[index], z[index + 1]
            segment = LineString([a, b])
            riser = segment.length <= VOID_BUFFER_M
            for ceiling, floor, plane, terminals, outline in graded:
                if _terminates_in_room(path, index, terminals.get(kind, ()), grace_m):
                    continue
                if ceiling.storey not in covers:
                    covers[ceiling.storey] = wall_cover(ctx, {ceiling.storey})
                if riser:
                    if not outline.covers(Point(a)):
                        continue
                    cover = covers[ceiling.storey]
                    if cover is not None and cover.covers(Point(a)):
                        continue
                    if soffits is not None and soffits.covers(Point(a)):
                        continue
                    low = max(min(za, zb) - radius, floor)
                    high = min(max(za, zb) + radius, plane)
                    if high - low <= tol:
                        continue
                    _record(worst, tag, ceiling.room_ref,
                            (high - low) * M_TO_FT, (plane - low) / M_PER_IN)
                    continue
                piece = outline.intersection(segment)
                if piece.is_empty or piece.length <= 0:
                    continue
                cover = covers[ceiling.storey]
                if cover is not None:
                    piece = piece.difference(cover)
                if soffits is not None:
                    piece = piece.difference(soffits)
                if piece.is_empty or piece.length <= 0:
                    continue
                span = segment.length
                parts = (piece.geoms if isinstance(piece, MultiLineString) else [piece])
                for part in parts:
                    if part.length <= 0:
                        continue
                    ts = sorted(segment.project(Point(xy)) / span for xy in part.coords)
                    air = _air_interval(za, zb, radius, floor, plane, tol)
                    if air is None:
                        continue
                    lo, hi = max(ts[0], air[0]), min(ts[-1], air[1])
                    if hi <= lo:
                        continue
                    exposure_ft = (hi - lo) * span * M_TO_FT
                    # Clamped to the band: the pipe's bottom can be below the storey
                    # datum (a drop on its way through the floor), and "116 inches below
                    # the ceiling" of a 107-inch room is not a number anybody can use.
                    # What is true is that it occupies the room's whole height.
                    deepest = plane - max(min(za + (zb - za) * lo,
                                              za + (zb - za) * hi) - radius, floor)
                    _record(worst, tag, ceiling.room_ref, exposure_ft, deepest / M_PER_IN)

    for (tag, room), (exposure_ft, intrusion_in) in sorted(worst.items()):
        if exposure_ft < rules.min_ceiling_exposure_ft:
            continue
        if intrusion_in < rules.ceiling_intrusion_in:
            continue
        out.append(advisory(
            cid,
            f"run {tag} hangs {intrusion_in:.1f}\" below {room}'s finished ceiling for "
            f"{exposure_ft:.2f} ft — that is inside the room, not above it",
            (tag, room), Result.FAIL,
            fix="reroute it out of the room, take it into a wall, or author a Soffit that "
                "boxes it out. Dropping the room's whole ceiling to hide one corridor is "
                "not the same fix: clear height is read by lighting, code.R305 and the "
                "takeoff"))

    if not any(finding.result is Result.FAIL for finding in out):
        out.append(passed(cid, f"{len(runs)} runs against {len(graded)} finished ceiling "
                               "plane(s): none hangs in a room's air", ()))
    if follow_roof:
        out.append(unknown(
            cid,
            f"{len(follow_roof)} room(s) resolve no flat ceiling plane (Room.ceiling is "
            "FollowRoof, so there is no single elevation to compare a run against) and are "
            f"NOT graded: {', '.join(sorted(follow_roof))}",
            tuple(sorted(follow_roof))))
    if ungraded:
        out.append(unknown(cid, f"{len(ungraded)} run(s) carry no resolved elevations and "
                                f"are not graded: {', '.join(sorted(ungraded)[:6])}",
                           tuple(sorted(ungraded))))
    return out


def _record(worst: dict, tag: str, room: str, exposure_ft: float,
            intrusion_in: float) -> None:
    """Keep one row per (run, room), ranked by DEPTH — see the module note.

    A run crossing a room in three segments is one defect with one fix, and reporting it
    three times teaches the reader to skim. The exposure accumulates; the intrusion is the
    worst of them, because that is the number the message leads with.
    """
    key = (tag, room)
    previous = worst.get(key)
    if previous is None:
        worst[key] = (exposure_ft, intrusion_in)
    else:
        worst[key] = (previous[0] + exposure_ft, max(previous[1], intrusion_in))
