"""Connection versus transit for ``mep.run_in_finished_volume``.

A run's own end at a thing in the room is the connection to it, not a run through the room:
the terminal grace (an end leg within reach of a terminal, clipped to that reach), the
fixture trim (end legs inside a served fixture's body) and casework cover (a run behind a
cabinet is boxed in) decide what of a run the check grades.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import LineString, Point, Polygon

from typehaus.checks.registry import CheckContext
from typehaus.quantities import M_PER_IN
from typehaus.resolve.overlay import union_all
from typehaus.resolve.placeables import placed_xy

#: What each trade can actually terminate at, by run kind. **Per trade, not one list**, and
#: that is what makes the grace rule mean something: a drain ending near a light switch has
#: not connected to anything, and a one-list version excused ``PR-A-STUBATH-DRAIN``'s
#: dog-leg because ``ED-S-SUITEBATH-SW`` happened to sit 8.9" from the stack head.
#:
#: ``Equipment`` is in all three because it genuinely is: an air handler takes duct, an ERV
#: takes a condensate line, and both take power. ``Furniture`` is in none — a sofa is not a
#: terminal, and 127 of them would excuse most of the house. ``Luminaire`` is not a kind at
#: all; a light fixture is an ``ElectricalDevice``.
TERMINAL_KINDS = {
    "pipe": frozenset({"Fixture", "Appliance", "Equipment"}),
    "duct": frozenset({"Register", "Equipment"}),
    "conduit": frozenset({"ElectricalDevice", "Alarm", "Equipment"}),
}


def terminals_in(ctx: CheckContext, storey: str,
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
    out: dict[str, list[tuple[float, float]]] = {kind: [] for kind in TERMINAL_KINDS}
    for element in ctx.plan.storey_elements(storey):
        kinds = [trade for trade, allowed in TERMINAL_KINDS.items()
                 if element.element_kind in allowed]
        if not kinds:
            continue
        xy = placed_xy(ctx.model, element)
        if xy is None or not outline.covers(Point(xy)):
            continue
        for trade in kinds:
            out[trade].append(xy)
    return out


def terminal_leg(path: tuple[tuple[float, float], ...], z: tuple[float, ...], index: int,
                 terminals: Any, grace_m: float) -> tuple | None:
    """``None`` when leg ``index`` is not a terminal leg, else ``(a, za, b, zb)``: what of it
    lies beyond ``grace_m`` of the terminal vertex (``a == b`` when nothing does).

    A run's own first or last leg whose end vertex lands within ``grace_m`` of a terminal in
    the room *is* the connection to it, but only for ``grace_m`` of plan length: the rest is
    transit, so a long leg out of a fixture is still graded from there on. A pure riser
    stays whole. An interior segment is never a connection.
    """
    a, b = path[index], path[index + 1]
    za, zb = z[index], z[index + 1]
    near = [index == 0 and _near(a, terminals, grace_m),
            index == len(path) - 2 and _near(b, terminals, grace_m)]
    if not any(near):
        return None
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    cut_a, cut_b = (grace_m if n else 0.0 for n in near)
    if length <= cut_a + cut_b:
        return a, za, a, za
    t0, t1 = cut_a / length, 1.0 - cut_b / length
    lerp = lambda t: ((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),  # noqa: E731
                      za + (zb - za) * t)
    (pa, qa), (pb, qb) = lerp(t0), lerp(t1)
    return pa, qa, pb, qb


def _near(vertex: tuple[float, float], terminals: Any, grace_m: float) -> bool:
    return any((vertex[0] - x) ** 2 + (vertex[1] - y) ** 2 <= grace_m * grace_m
               for x, y in terminals)


#: Gap closed between butted cabinet carcasses (0.1-0.2" seams) so they read as one body.
CASEWORK_SNAP_M = 0.5 * M_PER_IN
#: A cabinet stands on the floor, not hangs from the wall, within this of the storey datum.
CASEWORK_FLOOR_M = 6.0 * M_PER_IN


def casework_bodies(model: Any, floors: dict[str, float]) -> list[tuple[str, Any, float]]:
    """``[(storey, footprint, top)]`` of each floor-standing cabinet a countertop sits on."""
    hosts = {tag for top in model.countertops for tag in top.hosts}
    return [(c.storey, Polygon(c.footprint).buffer(CASEWORK_SNAP_M), c.body_z1_m)
            for c in model.canvas_objects
            if c.tag in hosts and len(c.footprint) >= 3 and c.body_z0_m is not None
            and c.body_z1_m is not None
            and c.body_z0_m <= floors.get(c.storey, 0.0) + CASEWORK_FLOOR_M]


def casework_cover(bodies: list[tuple[str, Any, float]], storey: str, cover: Any,
                   leg: Any, top: float) -> Any:
    """``cover`` plus the cabinets on ``storey`` that touch ``leg`` and stand over ``top``
    (the pipe's crown): a run behind a sink base is boxed in, like a run in a wall."""
    hit = [shape for s, shape, z1 in bodies if s == storey and z1 >= top
           and shape.intersects(leg)]
    if not hit:
        return cover
    return union_all(hit if cover is None else [cover, *hit])


def fixture_trim(ctx: CheckContext, tag: str, path: tuple[tuple[float, float], ...],
                 z: tuple[float, ...], radius: float) -> set[int]:
    """Legs from a run's end inside a served fixture's footprint and under its top: its trap
    and drop. Neither a long leg nor a riser climbing out of it to the ceiling qualifies."""
    from typehaus.resolve.riser_cover import in_body, served_bodies

    run = next((r for r in ctx.model.pipe_runs if r.tag == tag), None)
    if run is None or not run.serves:
        return set()
    bodies = served_bodies(ctx.model, run.serves)  # one predicate with the router's
    if not bodies:
        return set()

    def inside(index: int) -> bool:
        piece = LineString([path[index], path[index + 1]])
        return in_body(bodies, piece, max(z[index], z[index + 1]) + radius)

    out: set[int] = set()
    for order in (range(len(path) - 1), reversed(range(len(path) - 1))):
        for index in order:
            if not inside(index):
                break
            out.add(index)
    return out
