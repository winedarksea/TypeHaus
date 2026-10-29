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

**The attic is graded against the roof.** A ``FollowRoof`` room has no flat plane, so its
ceiling is the roof structure's underside less the lining (:mod:`.routing_sloped`), cut at
the ridge, and only where that finished ceiling clears R304.3's 5'-0" over the floor. A run
under a lower rake is not graded but NAMED in an UNKNOWN: with no knee wall the eave is
still finished room, and only an unmodeled box would hide it — unless the room declares
``exposed_services``, whose PASS then names it. A room whose roof cannot be resolved is
named in an UNKNOWN too.

**The terminal grace is blind to length**: ``PR-A-STUBATH-VENT`` crossed the bath for 6'-4"
from the shower, excused whole. The fixture's trim is the bounded version: legs from a pipe
run's end inside a served fixture's footprint and under its top (an open sink's trap and
drop) are its connection, not transit.

**A room may answer this in words.** Boxing a run out with a ``Soffit`` was the only
authored answer until 2026-09-13, which made a soffit the engine's idea of a ceiling
rather than the owner's: three of catlin's existed for no other reason, and all three were
retired the same week once their rooms could say it instead. ``Room.exposed_services``
is the other answer — a sentence saying the room's ceiling is deliberately open — and it is
positive evidence, not a suppression: the PASS quotes it back, so the report carries the
decision instead of a silence. It retires the ceiling comparison for that room and **only**
that comparison; every run crossing it is measured again against
``MepPreferences.exposed_service_headroom_ft``, because nothing else in the engine asks
whether somebody walks into the pipe (``code.R305_ceiling_height`` measures the structure
overhead and has never seen a run).

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
from typehaus.checks.mep.routing_sloped import SlopedPlane, sloped_plane
from typehaus.checks.mep.routing_terminals import (
    fixture_trim,
    terminals_in,
    terminates_in_room,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import EXPOSED_SERVICE_OCCUPANCIES, Occupancy
from typehaus.quantities import M_PER_IN


def _soffit_union(ctx: CheckContext, storey: str) -> Any:
    """The plan union of ``storey``'s resolved soffits — a run inside a bulkhead is boxed out.

    A soffit is the authored answer to exactly this finding, so a route that has already
    been covered by one must stop being reported, or the fix cannot be verified.

    ** PER STOREY, AND NOT AS A REFINEMENT. ** This unioned the whole house until 2026-09-07,
    which reads a bulkhead as covering every room stacked over and under it. Catlin found it
    the day a basement bathroom got one: SF-B-BATH took 6.8 SF out of RM-S-SUITEBATH's
    ceiling two floors up and shortened a run's reported exposure by a foot and a quarter.
    ``wall_cover`` beside it was already keyed this way; this is the same rule.
    """
    from typehaus.resolve.overlay import union_all

    polygons = [Polygon(soffit.outline) for soffit in ctx.model.soffits
                if soffit.storey == storey and len(soffit.outline) >= 3]
    valid = [poly for poly in polygons if poly.is_valid and not poly.is_empty]
    return union_all(valid) if valid else None


def _air_interval(za: float, zb: float, radius: float, floor: float, pa: float, pb: float,
                  tol: float) -> tuple[float, float] | None:
    """The ``t`` sub-interval of a segment where the pipe's OUTSIDE is in the room's air.

    ``bottom(t) = z(t) - radius`` must be under the ceiling plane (``pa`` to ``pb`` along the
    segment; equal for a flat ceiling) by more than ``tol``, and ``top(t) = z(t) + radius``
    must be over the storey's floor. Both are linear in ``t``, so each is a half-line and the
    answer is their intersection with ``[0, 1]``.
    """
    lo, hi = 0.0, 1.0
    for coefficient, offset, want_below in (
            (zb - za - (pb - pa), pa - tol + radius - za, True),   # z(t) < plane(t) - tol + r
            (zb - za, floor - radius - za, False)):                # z(t) > floor - r
        if abs(coefficient) < 1e-12:
            if (offset > 0.0) != want_below:
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


def _segment_rows(a: tuple[float, float], za: float, zb: float, radius: float,
                  segment: LineString, riser: bool, outline: Any, cover: Any,
                  soffits: Any, floor: float, plane: float | tuple[float, float],
                  tol: float) -> list[tuple[float, float]]:
    """``(exposure_ft, intrusion_in)`` for one segment against one ``plane``.

    ``plane`` is a height, or the ``(start, end)`` heights of a ceiling that slopes along
    this segment (:mod:`.routing_sloped`).

    Lifted out of the grading loop so the plane is an ARGUMENT: a room whose ceiling is
    closed is graded against the ceiling, and a room whose ``exposed_services`` says it is
    open is graded against its headroom line by the same arithmetic. Two planes, one
    measurement — a second copy of this would be two things to keep agreeing.
    """
    pa, pb = plane if isinstance(plane, tuple) else (plane, plane)
    if riser:
        if not outline.covers(Point(a)):
            return []
        if cover is not None and cover.covers(Point(a)):
            return []
        if soffits is not None and soffits.covers(Point(a)):
            return []
        low = max(min(za, zb) - radius, floor)
        high = min(max(za, zb) + radius, pa)
        if high - low <= tol:
            return []
        return [((high - low) * M_TO_FT, (pa - low) / M_PER_IN)]

    piece = outline.intersection(segment)
    if piece.is_empty or piece.length <= 0:
        return []
    if cover is not None:
        piece = piece.difference(cover)
    if soffits is not None:
        piece = piece.difference(soffits)
    if piece.is_empty or piece.length <= 0:
        return []
    span = segment.length
    rows: list[tuple[float, float]] = []
    for part in (piece.geoms if isinstance(piece, MultiLineString) else [piece]):
        if part.length <= 0:
            continue
        ts = sorted(segment.project(Point(xy)) / span for xy in part.coords)
        air = _air_interval(za, zb, radius, floor, pa, pb, tol)
        if air is None:
            continue
        lo, hi = max(ts[0], air[0]), min(ts[-1], air[1])
        if hi <= lo:
            continue
        # Clamped to the band: the pipe's bottom can be below the storey datum (a drop on
        # its way through the floor), and "116 inches below the ceiling" of a 107-inch room
        # is not a number anybody can use. What is true is that it occupies the whole height.
        deepest = max(pa + (pb - pa) * t - max(za + (zb - za) * t - radius, floor)
                      for t in (lo, hi))
        rows.append(((hi - lo) * span * M_TO_FT, deepest / M_PER_IN))
    return rows


@check(Tier.ADVISORY, "mep.run_in_finished_volume")
def run_in_finished_volume(ctx: CheckContext) -> list[Finding]:
    """A pipe, duct or raceway may not hang in the open air of a finished room.

    ADVISORY: no IRC section says a duct may not cross a living room, and there is no
    citation to hang a ``PermitItemSpec`` on. It is the buildability twin of
    ``mep.run_over_void``, and ``CheckReport.counts()`` counts a FAIL regardless of
    severity, so it holds a clean house to the same standard a code check would.

    A room whose ``Room.exposed_services`` states a reason is not graded against its
    ceiling plane at all — its ceiling is authored as deliberately open — but every run
    crossing it is still held to the headroom line. See the module note.

    A room is finished unless its occupancy is in
    :data:`~typehaus.model.enums.EXPOSED_SERVICE_OCCUPANCIES` — a mechanical room's ceiling
    is a service plane and pipe hangs there by design — unless ``Room.closed_to_services``
    says why this one is not (a walk-in closet somebody dresses in). Everything else is
    graded, hallways and stairwells included: those are the rooms people look *up* in.
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
    closed = {room.tag for room in ctx.model.rooms if room.closed_to_services}
    declared = {room.tag: room.exposed_services for room in ctx.model.rooms
                if room.exposed_services}
    storey_z = {storey.tag: storey.elevation.meters for storey in ctx.plan.storeys}
    radii = run_radii(ctx)
    soffit_covers: dict[str, Any] = {}
    tol = rules.ceiling_intrusion_in * M_PER_IN
    grace_m = rules.terminal_grace_in * M_PER_IN
    headroom_m = rules.exposed_service_headroom_ft / M_TO_FT

    #: ``(ceiling, floor, plane, terminals, outline, declared reason, is the low eave)``
    graded: list[tuple[Any, float, Any, dict, Any, str | None, bool]] = []
    follow_roof: set[str] = set()
    for ceiling in ctx.model.ceilings:
        plane: float | SlopedPlane | None = ceiling.z0_m
        if plane is None:
            plane = sloped_plane(ctx.model, ctx.plan, ceiling)
        if plane is None:
            follow_roof.add(ceiling.room_ref)
            continue
        occupancy = occupancies.get(ceiling.room_ref)
        if (occupancy is not None and Occupancy(occupancy) in EXPOSED_SERVICE_OCCUPANCIES
                and ceiling.room_ref not in closed):
            continue
        if len(ceiling.outline) < 3:
            continue
        outline = Polygon(ceiling.outline)
        if not outline.is_valid or outline.is_empty:
            continue
        floor = storey_z.get(ceiling.storey, 0.0)
        zones = [(outline, False)]
        if isinstance(plane, SlopedPlane):
            standing = plane.standing_part(outline, floor)
            zones = [(standing, False), (outline.difference(standing), True)]
        terminals = terminals_in(ctx, ceiling.storey, outline)
        graded.extend((ceiling, floor, plane, terminals, zone, declared.get(ceiling.room_ref),
                       eave) for zone, eave in zones if zone.area > 1e-6)

    out: list[Finding] = []
    covers: dict[str, Any] = {}
    ungraded: list[str] = []
    worst: dict[tuple[str, str], tuple[float, float]] = {}
    #: (run, room) rows under a rake too low to stand under: named, not graded.
    eaves: dict[tuple[str, str], tuple[float, float]] = {}
    #: (run, room) rows for a DECLARED room, measured against its headroom line instead.
    low: dict[tuple[str, str], tuple[float, float]] = {}
    #: What each declared room's PASS gets to say it actually saw.
    crossings: dict[str, set[str]] = {room: set() for room in declared}
    eave_seen: dict[str, set[str]] = {room: set() for room in declared}

    for kind, tag, path, z in runs:
        if len(path) < 2:
            continue
        if len(z) != len(path):
            ungraded.append(tag)
            continue
        radius = radii.get(tag, 0.0)
        trim = fixture_trim(ctx, tag, path, z, radius) if kind == "pipe" else set()
        for index in range(len(path) - 1):
            a, b = path[index], path[index + 1]
            za, zb = z[index], z[index + 1]
            segment = LineString([a, b])
            riser = segment.length <= VOID_BUFFER_M
            for ceiling, floor, plane, terminals, outline, reason, eave in graded:
                if index in trim or terminates_in_room(path, index, terminals.get(kind, ()),
                                                        grace_m):
                    continue
                if ceiling.storey not in covers:
                    covers[ceiling.storey] = wall_cover(ctx, {ceiling.storey})
                    soffit_covers[ceiling.storey] = _soffit_union(ctx, ceiling.storey)
                if isinstance(plane, SlopedPlane):
                    # A riser has no length to cut, so it reads the plane at its own point.
                    pieces = ([(a, za, zb, segment, plane.z_at(a), plane.z_at(a))] if riser
                              else plane.pieces(a, b, za, zb))
                else:
                    pieces = [(a, za, zb, segment, plane, plane)]
                for start, pza, pzb, piece, pa, pb in pieces:
                    args = (start, pza, pzb, radius, piece, riser, outline,
                            covers[ceiling.storey], soffit_covers[ceiling.storey], floor)
                    rows = _segment_rows(*args, (pa, pb), tol)
                    if eave and reason is not None:
                        # A declared room's eave: the run is the design, and nobody stands
                        # under 5'-0" for a headroom line to protect.
                        if rows:
                            eave_seen[ceiling.room_ref].add(tag)
                        continue
                    if eave or reason is None:
                        for exposure_ft, intrusion_in in rows:
                            _record(eaves if eave else worst, tag, ceiling.room_ref,
                                    exposure_ft, intrusion_in)
                        continue
                    # Declared open. The crossing is the DESIGN, so it is evidence for the
                    # pass rather than a finding — and the run is then measured again against
                    # the headroom line, with no intrusion allowance, because a pipe somebody
                    # walks into is a different defect and this is the only check that can
                    # see it. Over a flight the flat line is the wrong datum:
                    # code.R311_7_2 grades the sloped nosing line there.
                    if rows:
                        crossings[ceiling.room_ref].add(tag)
                    head = (min(pa, floor + headroom_m), min(pb, floor + headroom_m))
                    for exposure_ft, intrusion_in in _segment_rows(*args, head, 0.0):
                        _record(low, tag, ceiling.room_ref, exposure_ft, intrusion_in)

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
            fix="reroute it out of the room, take it into a wall, author a Soffit that "
                "boxes it out. Dropping the room's whole ceiling to hide one corridor is "
                "not the same fix: clear height is read by lighting, code.R305 and the "
                "takeoff. If the ceiling is meant to be open, say so on the Room: "
                "`exposed_services=\"<why>\"` is an answer this check reads and quotes"))

    head_label = _feet_inches(rules.exposed_service_headroom_ft)
    for (tag, room), (exposure_ft, intrusion_in) in sorted(low.items()):
        if exposure_ft < rules.min_ceiling_exposure_ft:
            continue
        out.append(advisory(
            cid,
            f"run {tag} hangs {intrusion_in:.1f}\" below the {head_label} headroom line "
            f"in {room} for {exposure_ft:.2f} ft — {room}'s services are deliberately "
            "exposed, but this one is in the way of somebody's head, which is a different "
            "question",
            (tag, room), Result.FAIL,
            fix="lift it, reroute it, or box THIS run out. Declaring the ceiling open is "
                "not an answer to head height: code.R305_ceiling_height measures the "
                "structure overhead and never sees a run"))

    for room in sorted(declared):
        if room in follow_roof:
            continue
        if not any(ceiling.room_ref == room for ceiling, *_ in graded):
            out.append(unknown(
                cid,
                f"{room} declares its services deliberately exposed (\"{declared[room]}\") "
                "but resolves no finished ceiling plane here, so the declaration grades "
                "nothing and no run was measured against it",
                (room,)))
            continue
        if any(key[1] == room and exposure_ft >= rules.min_ceiling_exposure_ft
               for key, (exposure_ft, _depth) in low.items()):
            continue  # reported above; a row under the threshold does not void the PASS
        seen = crossings[room]
        # An empty set is not a quiet pass: it says the declaration is not what is carrying
        # this room today — a Soffit or a wall still covers everything crossing it — and a
        # reader deciding whether that box can go needs to be told which of the two answered.
        evidence = (f"so the {len(seen)} run(s) under its ceiling are the design, not a "
                    "defect "
                    f"({', '.join(sorted(seen))}), and each still clears the {head_label} "
                    "headroom line"
                    if seen else
                    "though nothing currently hangs in its open air: a Soffit or a wall "
                    "still covers every run that crosses it")
        if eave_seen[room]:
            evidence += (f"; in its eave, under 5'-0\" of head, "
                         f"{', '.join(sorted(eave_seen[room]))} lie open by the same choice")
        out.append(passed(
            cid, f"{room}: services are deliberately exposed — \"{declared[room]}\" — "
                 + evidence,
            (room,) + tuple(sorted(seen | eave_seen[room]))))

    if not any(finding.result is Result.FAIL for finding in out):
        planes = len({id(entry[0]) for entry in graded})
        out.append(passed(cid, f"{len(runs)} runs against {planes} finished ceiling "
                               "plane(s): none hangs in a room's air", ()))
    if follow_roof:
        out.append(unknown(
            cid,
            f"{len(follow_roof)} room(s) follow a roof that does not resolve (Room.ceiling is "
            "FollowRoof, so there is no plane to compare a run against) and are "
            f"NOT graded: {', '.join(sorted(follow_roof))}",
            tuple(sorted(follow_roof))))
    in_eaves = sorted(key for key, (exposure_ft, intrusion_in) in eaves.items()
                      if exposure_ft >= rules.min_ceiling_exposure_ft
                      and intrusion_in >= rules.ceiling_intrusion_in)
    if in_eaves:
        out.append(unknown(
            cid,
            f"{len(in_eaves)} run(s) lie in a finished room's eave, under less than R304.3's "
            "5'-0\" of head, which is not graded (a boxed eave chase is not modeled, and an "
            f"open one is still in the room): {', '.join(f'{t} in {r}' for t, r in in_eaves)}",
            tuple(sorted({part for key in in_eaves for part in key}))))
    if ungraded:
        out.append(unknown(cid, f"{len(ungraded)} run(s) carry no resolved elevations and "
                                f"are not graded: {', '.join(sorted(ungraded)[:6])}",
                           tuple(sorted(ungraded))))
    return out


def _feet_inches(feet: float) -> str:
    """``6.667`` -> ``6'-8"``. The headroom line is a dimension and reads as one."""
    total = round(feet * 12)
    return f"{total // 12}'-{total % 12}\""


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
