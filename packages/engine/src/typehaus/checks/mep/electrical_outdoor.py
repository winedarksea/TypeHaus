"""CODE-tier electrical rule — NEC 210.52(E)(3), a receptacle on each balcony, deck or porch.

Balconies, decks and porches reached from inside the dwelling carry at least one receptacle
within their perimeter, not more than 6 1/2 ft above the surface (2026 number UNCONFIRMED,
``model/nec.py``).

"Reached from inside" is read off the door, not the structure: a walkable ``FloorSystem`` that
lies a door's width of reach (``_REACH_M`` past the wall axis) outside an exterior door, on
the door's own level (``_LEVEL_M`` of the storey datum). The court stands 5 in. off the house
yet its porch and balcony both land at their doors, so no gap is tested. A receptacle on the
house wall counts when it is within ``_PERIMETER_M`` of the surface's outline. A surface under
``_MIN_SPAN_M`` across is a stoop or landing, not a porch or deck, and is not graded.
The official text reaches surfaces within 4 in. horizontally of the dwelling unit, so grading
the court, 5 in. off, is stricter than the rule.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CID, _CODE = "code.NEC_210_52_E3_balcony_receptacles", cite(NEC.BALCONY_RECEPTACLE)
_REACH_M = 24 * 0.0254
_LEVEL_M = 12 * 0.0254
_PERIMETER_M = 18 * 0.0254
_MAX_HEIGHT_M = 6.5 * 0.3048
_MIN_SPAN_M = 4 * 0.3048


@check(Tier.CODE, _CID)
def balcony_deck_porch_receptacles(ctx: CheckContext) -> list[Finding]:
    """Each balcony, deck or porch a dwelling door opens onto has a counting receptacle."""
    from shapely.geometry import Point, Polygon

    model = ctx.model
    elevation = {storey.tag: storey.elevation.meters for storey in ctx.plan.storeys}
    walls = {wall.tag: wall for wall in model.walls}
    rooms: dict[str, list] = {}
    for room in model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append(axis_polygon(room))
    surfaces = {}
    for floor in model.floors:
        poly = Polygon(floor.deck_outline).buffer(0)
        if not poly.is_empty:
            surfaces[floor.tag] = (floor, poly)

    reached: dict[str, list[str]] = {}
    for opening in model.openings:
        wall = walls.get(opening.host_wall)
        if not opening.is_door or wall is None or wall.storey not in elevation:
            continue
        (x0, y0), (x1, y1) = wall.axis
        run = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / run, (y1 - y0) / run
        cx, cy = x0 + ux * opening.center_along_m, y0 + uy * opening.center_along_m
        probes = [Point(cx - uy * _REACH_M * s, cy + ux * _REACH_M * s) for s in (1, -1)]
        inside = [any(poly.contains(p) for poly in rooms.get(wall.storey, ())) for p in probes]
        if inside.count(True) != 1:
            continue  # an interior door, or a door with no room behind it
        outside = probes[inside.index(False)]
        for tag, (floor, poly) in surfaces.items():
            if (poly.contains(outside)
                    and abs(floor.deck_z1_m - elevation[wall.storey]) <= _LEVEL_M):
                reached.setdefault(tag, []).append(opening.tag)

    objects = {obj.tag: obj for obj in model.canvas_objects}
    out: list[Finding] = []
    for tag, doors in sorted(reached.items()):
        floor, poly = surfaces[tag]
        x0, y0, x1, y1 = poly.bounds
        if min(x1 - x0, y1 - y0) < _MIN_SPAN_M:
            continue
        serving = []
        for element in ctx.plan.all_elements():
            if (element.element_kind != "ElectricalDevice"
                    or not _counts_as_a_125v_receptacle(ctx, element)):
                continue
            xy, obj = placed_xy(model, element), objects.get(element.tag)
            if xy is None or obj is None or obj.z_m is None:
                continue
            if any(room.contains(Point(xy)) for room in rooms.get(obj.storey, ())):
                continue  # indoors: a receptacle on the room face is not on the deck
            if (poly.distance(Point(xy)) <= _PERIMETER_M
                    and -0.1 <= obj.z_m - floor.deck_z1_m <= _MAX_HEIGHT_M):
                serving.append(element.tag)
        label = f"{tag} (reached from {', '.join(sorted(set(doors)))})"
        if serving:
            out.append(by_result(_CID, Result.PASS, f"{label}: {', '.join(sorted(serving))}",
                                 (), _CODE))
        else:
            out.append(by_result(_CID, Result.FAIL,
                                 f"{label} has no receptacle within its perimeter at or below "
                                 "6 1/2 ft above the surface", (tag, *sorted(set(doors))), _CODE,
                                 "add a weather-resistant GFCI receptacle on the house wall "
                                 "beside the door, within reach of the surface"))
    if not out:
        out.append(by_result(_CID, Result.NOT_APPLICABLE,
                             "no balcony, deck or porch is reached from inside the dwelling",
                             (), _CODE))
    return out
