"""Where a wall's studs actually are, asked once.

``structural.window_framing_module`` grew this arithmetic first and owned all of it; a door
check needs the same four answers and must not re-derive them, because a check that disagrees
with the solver about where the studs are reports legal stations nobody frames.

The one behavioural change moving it here makes is :func:`wall_module`. ``solver.py`` lays a
STAGGERED partition out on **half** its authored spacing — the two stud rows interleave, so
the combined rhythm a jamb pack has to clear is 8" on a 16" wall — and the window check read
``framing.spacing`` straight, so on a staggered wall the two disagreed by a factor of two.
Nothing in catlin surfaced it: no window sits on a staggered wall. Four DOORS do, and the
moment doors are graded the disagreement goes live, which is why it is fixed before the door
check exists rather than after.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.enums import LayerFunction, PartitionLayout

_IN_M = 0.0254

#: ``integrity.opening_fits``' edge distance, in metres. An opening whose jamb lands closer
#: than this to a node is an ERROR-severity integrity failure, so a "legal station" that
#: violates it is not legal — it is one hard finding traded for another. Duplicated as a
#: constant rather than imported to keep ``checks/structural`` off ``checks/integrity``; the
#: name of the check that owns it is in the message every consumer prints.
MIN_EDGE_M = 0.05


def structure_framing(assembly: Any) -> Any:
    """The STRUCTURE layer's ``FramingSpec``, or None for concrete/masonry.

    An opening in a poured wall consumes no stud bays, and every caller wants the same
    early-out rather than its own ``next(...)`` over the layers.
    """
    if assembly is None:
        return None
    return next((layer.framing for layer in assembly.layers
                 if layer.function is LayerFunction.STRUCTURE), None)


def wall_module(framing: Any, fallback_in: float) -> float:
    """The module in inches a wall is **framed** on, not the one it is authored with.

    Mirrors ``resolve/framing/solver.py``'s ``module_spacing = spacing / 2.0 if staggered``.
    A STAGGERED partition's two rows of studs interleave on the shared plate, so a jamb pack
    — and therefore any question about which stations an opening may occupy — sees half the
    authored o.c. Read the authored number instead and every verdict on such a wall is
    against a grid with twice the pitch of the one built.
    """
    spacing_in = (framing.spacing.inches if getattr(framing, "spacing", None) is not None
                  else fallback_in)
    if getattr(framing, "layout", None) is PartitionLayout.STAGGERED:
        return spacing_in / 2.0
    return spacing_in


def segment_residue_in(wall: Any, module_in: float) -> float:
    """Where a wall segment's stud grid starts, as a residue in inches mod the module.

    The framing solver lays a segment's studs out from **its own start node**
    (``resolve.framing.stud_module`` measures every opening from 0 = that node), so the set
    of stations an opening may legally occupy on a wall is a property of that node and not of
    the facade. Two segments are in phase only when their start nodes share this residue; a
    column between storeys needs the same residue, a mirror pair needs residues summing to
    0 mod the module. Reporting it turns "this window is 4" off" into the answer: a facade
    near-miss is almost always an out-of-phase *segment*, which no opening move can fix.

    True only while the assembly lays out from the wall — see :func:`module_origin`, which is
    what an opt-in ``FramingSpec.layout_origin="line"`` changes and which every consumer must
    follow, or it would report legal stations the solver does not frame.
    """
    (x0, y0), (x1, y1) = wall.axis
    # Project the start node onto the segment's own dominant axis — the direction the grid
    # runs — so the residue is comparable between two segments on the same facade.
    along_m = float(x0 if abs(x1 - x0) >= abs(y1 - y0) else y0)
    return (along_m / _IN_M) % module_in


def module_origin(ctx: Any, wall: Any, framing: Any,
                  spacing_m: float) -> tuple[float, str]:
    """``(phase in metres, how to describe it)`` for this wall's stud grid.

    The framing solver's own arithmetic, asked the same question — the check and the framing
    it checks must never disagree about where the studs are.
    """
    from typehaus.resolve.layout_lines import layout_phase, lines_by_wall

    line = lines_by_wall(ctx.model.layout_lines).get(wall.tag)
    phase = layout_phase(framing, line, wall.tag, spacing_m)
    if getattr(framing, "layout_origin", "wall-start") != "line" or line is None:
        return phase, "segment"
    return phase, line.tag


def feasible_stations(width_m: float, axis_len_m: float, spacing_m: float,
                      stud_thickness_m: float, phase_m: float) -> list[float]:
    """Every station on this wall an opening of this width could legally occupy.

    "Legally" is three conditions, and the last two are the ones a hand survey misses:

    1. It costs the **minimum** number of interrupted studs — which is what "on the module"
       means. Both families of candidate are enumerated, stud lines and bay centres, exactly
       as ``opening_stud_module`` does, rather than a closed form that could drift from the
       counting rule.
    2. Both jambs clear :data:`MIN_EDGE_M` of the wall's ends. A 24" opening in a 28" wall has
       a perfectly good module station and no room at all for it: ``integrity.opening_fits``
       is an ERROR, so naming that station would trade a soft advisory for a hard failure.
    3. The **jamb pack** clears the ends too, not just the rough opening. This is the one that
       cost real damage before it was here. An opening carries a king and a jack each side —
       two stud thicknesses beyond the RO — and a corner carries a three-stud pack of its own.
       ``D-S-BED3`` at centre 32" on a 50" wall leaves its RO 3" from the node, which passes
       ``opening_fits`` comfortably and drives its king stud straight through the neighbouring
       wall's end stud. Moving it there traded a one-stud advisory for nine new
       ``structural.member_interference`` overlaps, none of which ``opening_fits`` can see.
       So the edge a station must clear is ``MIN_EDGE_M`` PLUS the pack.

    Returning the list rather than a boolean is the point. A check that can name the nearest
    legal centre gives an instruction; one that cannot only makes an accusation — and, when
    the list comes back **empty**, it has learned something a bare "off the module" never
    says: that no move of this opening on this wall will do, and the fix is the node, the
    layout origin, or a narrower leaf.
    """
    from typehaus.resolve.framing.stud_module import studs_interrupted

    if spacing_m <= 0.0 or axis_len_m <= 0.0:
        return []
    half = width_m / 2.0
    ideal = min(studs_interrupted(phase_m + offset, half, spacing_m, stud_thickness_m,
                                  phase_m)
                for offset in (0.0, spacing_m / 2.0))
    # King + jack each side of the RO, then the integrity margin beyond that — see (3).
    edge = MIN_EDGE_M + 2.0 * stud_thickness_m
    low, high = half + edge, axis_len_m - half - edge
    if low > high:
        return []
    out: list[float] = []
    for offset in (0.0, spacing_m / 2.0):
        # Walk the grid from the first candidate at or after ``low`` to the last at or
        # before ``high``. n is an integer count of modules off the phase, so the stations
        # are the solver's, not a resampling of them.
        base = phase_m + offset
        first = int((low - base) // spacing_m)
        station = base + first * spacing_m
        while station < low - 1e-9:
            station += spacing_m
        while station <= high + 1e-9:
            if studs_interrupted(station, half, spacing_m, stud_thickness_m,
                                 phase_m) == ideal:
                out.append(station)
            station += spacing_m
    out.sort()
    # A station reachable from both families is one station, not two.
    deduped: list[float] = []
    for station in out:
        if not deduped or abs(station - deduped[-1]) > 1e-9:
            deduped.append(station)
    return deduped


def nearest_station(stations: list[float], center_along_m: float) -> float | None:
    """The legal station an opening should move to — the closest one, in metres along."""
    if not stations:
        return None
    return min(stations, key=lambda station: abs(station - center_along_m))


# --- how well the upper storeys stack on the lower ------------------------------------------

#: Member categories that mean a wall's STRUCTURE layer resolved to sticks of lumber. A
#: concrete or masonry wall carries no studs to stand over, so it is not a carrier.
#:
#: The opening categories are in the set deliberately: a wall that is almost entirely rough
#: opening frames a jamb pack and no module stud at all. ``W-M-N3`` is 4'-0" long and 3'-2" of
#: that is ``D-M-ENTRY``, leaving 3 3/4" at each end that the king and jack fill between them
#: — a framed wall by any reading, and invisible to a ``stud``-only test.
FRAMED_STRUCTURE_CATEGORIES = frozenset({
    "stud", "plate", "raked_plate", "corner", "king", "jack", "cripple", "header", "sill",
})

#: How far apart two studs may be and still count as stacked. Half an inch is a third of a
#: stud's own thickness — near enough that the load path is continuous through the plate,
#: far enough that a stud on the next module station is never mistaken for the same one.
STACK_TOLERANCE_M = 0.5 * _IN_M


def orphan_studs(model: Any) -> tuple[int, dict[str, int]]:
    """``(stacked studs walked, {upper wall tag: studs standing over nothing})``.

    "Orphaned" is not "wrong". A module stud suppressed under a window on one storey and not
    the other, and jamb packs at differing stations because the openings differ, are both
    correct framing — the count will never go to zero and is a **ceiling, not a target**. What
    it is good for is comparison: it moves when a grid re-phases, and the direction it moves
    is the whole verdict on a phase edit.

    Lives here rather than in the test that first computed it, and rather than in the report
    that prints it, because the pin and the report must not be able to disagree about what the
    number means (``haus explain module``, ``test_upper_storey_studs_stand_over_studs``).
    """
    import math

    walls = {wall.tag: wall for wall in model.walls}

    def studs(wall: Any) -> list[Any]:
        return [member for member in wall.members if member.category == "stud"]

    def framed(wall: Any) -> bool:
        return any(member.category in FRAMED_STRUCTURE_CATEGORIES for member in wall.members)

    carriers: dict[str, list[str]] = {}
    for edge in model.stack_edges:
        lower, upper = walls.get(edge.lower_wall), walls.get(edge.upper_wall)
        if lower is None or upper is None or not framed(lower):
            continue
        carriers.setdefault(edge.upper_wall, []).append(edge.lower_wall)

    total = 0
    per_wall: dict[str, int] = {}
    for upper_tag, lower_tags in sorted(carriers.items()):
        upper = walls[upper_tag]
        (ax, ay), (bx, by) = upper.axis
        span = math.dist((ax, ay), (bx, by))
        if span <= 0:
            continue
        dx, dy = (bx - ax) / span, (by - ay) / span

        def station(member: Any, ax: float = ax, ay: float = ay,
                    dx: float = dx, dy: float = dy) -> float:
            return float((member.p0[0] - ax) * dx + (member.p0[1] - ay) * dy)

        below = [station(stud) for tag in lower_tags for stud in studs(walls[tag])]
        for stud in studs(upper):
            total += 1
            if not any(abs(station(stud) - other) <= STACK_TOLERANCE_M for other in below):
                per_wall[upper_tag] = per_wall.get(upper_tag, 0) + 1
    return total, per_wall
