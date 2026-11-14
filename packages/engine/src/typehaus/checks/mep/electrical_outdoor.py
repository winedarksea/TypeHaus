"""CODE-tier electrical rule — NEC 210.52(E)(3), a receptacle on each balcony, deck or porch.

A balcony, deck or porch within 4 in. horizontally of the dwelling unit carries at least one
receptacle accessible from it, not more than 6 1/2 ft above its walking surface.

"The dwelling unit" is the walls of every storey whose ``Building.kind`` is "dwelling" (all
walls in a house that authors no buildings). A surface qualifies when it lies mostly outside
the dwelling's rooms and its outline comes within ``_REACH_M`` of those walls in plan. No door
is required. Catlin's court structure stands 5 in. off the house, but its porch and balcony
decks reach 2.4 in. and 1.7 in. from the house walls, so both are graded. A receptacle on
the house wall counts when it is within ``_PERIMETER_M`` of the surface's outline.
A surface under ``_MIN_SPAN_M`` across is read as a stoop or landing, not
a porch or deck (the engine's reading; the code gives no size).
"""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.electrical import _counts_toward_210_52
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CID, _CODE = "code.NEC_210_52_E3_balcony_receptacles", cite(NEC.BALCONY_RECEPTACLE)
_REACH_M = 4 * 0.0254 + 1e-3  # 4 in., plus a millimetre of round-off
_PERIMETER_M = 18 * 0.0254
_MAX_HEIGHT_M = 6.5 * 0.3048
_MIN_SPAN_M = 4 * 0.3048


def _dwelling_storeys(ctx: CheckContext) -> set[str]:
    plan = ctx.plan
    if not plan.project.buildings:
        return {storey.tag for storey in plan.storeys}
    return {storey.tag for storey in plan.storeys
            if getattr(plan.building(plan.building_of(storey.tag)), "kind", None) == "dwelling"}


@check(Tier.CODE, _CID)
def balcony_deck_porch_receptacles(ctx: CheckContext) -> list[Finding]:
    """Each balcony, deck or porch within 4 in. of the dwelling has a counting receptacle."""
    from shapely.geometry import LineString, Point, Polygon

    from typehaus.resolve.overlay import union_all

    model = ctx.model
    dwelling = _dwelling_storeys(ctx)
    rooms: dict[str, list] = {}
    for room in model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append(axis_polygon(room))
    walls = [LineString(w.axis).buffer(w.thickness_m / 2.0, cap_style=2)
             for w in model.walls if w.storey in dwelling and len(w.axis) >= 2]
    if not walls:
        return [by_result(_CID, Result.NOT_APPLICABLE, "no dwelling walls resolve", (), _CODE)]
    shell = union_all(walls)
    indoors = union_all([poly for storey in dwelling for poly in rooms.get(storey, ())])

    reached: dict[str, float] = {}
    surfaces = {}
    for floor in model.floors:
        poly = Polygon(floor.deck_outline).buffer(0)
        if poly.is_empty or poly.area <= 0:
            continue
        if not indoors.is_empty and poly.intersection(indoors).area > 0.5 * poly.area:
            continue  # a floor of the dwelling itself
        gap = poly.distance(shell)
        if gap <= _REACH_M:
            surfaces[floor.tag] = (floor, poly)
            reached[floor.tag] = gap

    objects = {obj.tag: obj for obj in model.canvas_objects}
    out: list[Finding] = []
    for tag, gap in sorted(reached.items()):
        floor, poly = surfaces[tag]
        x0, y0, x1, y1 = poly.bounds
        if min(x1 - x0, y1 - y0) < _MIN_SPAN_M:
            continue
        serving = []
        for element in ctx.plan.all_elements():
            if (element.element_kind != "ElectricalDevice"
                    or not _counts_toward_210_52(ctx, element, height_limit=False)):
                continue
            xy, obj = placed_xy(model, element), objects.get(element.tag)
            if xy is None or obj is None or obj.z_m is None:
                continue
            if any(room.contains(Point(xy)) for room in rooms.get(obj.storey, ())):
                continue  # indoors: a receptacle on the room face is not on the deck
            if (poly.distance(Point(xy)) <= _PERIMETER_M
                    and -0.1 <= obj.z_m - floor.deck_z1_m <= _MAX_HEIGHT_M):
                serving.append(element.tag)
        label = f"{tag} ({gap / 0.0254:.1f} in. from the dwelling)"
        if serving:
            out.append(by_result(_CID, Result.PASS, f"{label}: {', '.join(sorted(serving))}",
                                 (), _CODE))
        else:
            out.append(by_result(_CID, Result.FAIL,
                                 f"{label} has no receptacle within its perimeter at or below "
                                 "6 1/2 ft above the surface", (tag,), _CODE,
                                 "add a weather-resistant GFCI receptacle on the house wall "
                                 "beside the door, within reach of the surface"))
    if not out:
        out.append(by_result(_CID, Result.NOT_APPLICABLE,
                             "no balcony, deck or porch lies within 4 in. of the dwelling",
                             (), _CODE))
    return out
