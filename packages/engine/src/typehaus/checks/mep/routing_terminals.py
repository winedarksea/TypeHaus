"""Connection versus transit for ``mep.run_in_finished_volume``.

A run's own end at a thing in the room is the connection to it, not a run through the room:
the terminal grace (an end leg within reach of a terminal) and the fixture trim (end legs
inside a served fixture's body) decide which legs the check skips.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, Point, Polygon

from typehaus.checks.registry import CheckContext
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


def terminates_in_room(path: tuple[tuple[float, float], ...], index: int,
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


def fixture_trim(ctx: CheckContext, tag: str, path: tuple[tuple[float, float], ...],
                 z: tuple[float, ...], radius: float) -> set[int]:
    """Legs from a run's end inside a served fixture's footprint and under its top: its trap
    and drop. Neither a long leg nor a riser climbing out of it to the ceiling qualifies."""
    run = next((r for r in ctx.model.pipe_runs if r.tag == tag), None)
    if run is None or not run.serves:
        return set()
    bodies = [(Polygon(c.footprint).buffer(1e-3), c.body_z1_m)
              for c in ctx.model.canvas_objects
              if c.tag in run.serves and len(c.footprint) >= 3 and c.body_z1_m is not None]
    if not bodies:
        return set()

    def inside(index: int) -> bool:
        piece = LineString([path[index], path[index + 1]])
        top = max(z[index], z[index + 1]) + radius
        return any(shape.covers(piece) and top <= body_top + 1e-3
                   for shape, body_top in bodies)

    out: set[int] = set()
    for order in (range(len(path) - 1), reversed(range(len(path) - 1))):
        for index in order:
            if not inside(index):
                break
            out.add(index)
    return out
