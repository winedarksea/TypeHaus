"""Sheet goods by the sheet — wall, roof, subfloor and ceiling panels, net of openings.

Split out of ``takeoff/framing.py``. The sheet SIZE is each layer's ``sheet_length``, read
through ``resolve/sheet_stock`` — the same reading the R602.10 blocking factor uses.
"""

from __future__ import annotations

from collections import defaultdict

from shapely.geometry import Polygon

from typehaus.model.enums import LayerFunction
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Room
from typehaus.resolve.ceiling_over import (
    ceiling_regions,
    deck_structure_underside_m,
    deck_void_face,
)
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import length, polygon_area, sub
from typehaus.resolve.geometry_walls import cuts_layer
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.sheet_stock import (
    layer_sheet_length_in,
    order_sheet_length_in,
    sheet_label,
    sheets_for,
    wall_sheathing,
)
from typehaus.takeoff.sheet_rips import rip_sheet_rows, rip_stock

_M2_TO_FT2 = 10.7639104167
_M_TO_FT = 3.280839895013123


def sheet_goods_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Return net-area and whole-sheet quantities for wall, roof, and subfloor sheathing.

    Every row is explicitly tied to its material, thickness and sheet size; this makes a
    sheet estimate auditable instead of silently grouping unlike panel products. The size is
    the layer's ``sheet_length`` (``resolve/sheet_stock``), 4x8 where it states none.
    """
    from typehaus.takeoff.stairs import separate_stair_wear_members

    areas: dict[tuple[str, str, float, float | None], float] = defaultdict(float)
    for member in separate_stair_wear_members(model):
        section = cross_section(member.profile)
        areas[("stair wear surface", member.material, section.depth_m, None)] += (
            member.length_m * section.width_m)
    openings_by_wall: dict[str, list] = defaultdict(list)
    for opening in model.openings:
        openings_by_wall[opening.host_wall].append(opening)

    for wall in model.walls:
        exterior = any(layer.function == "cladding" for layer in wall.layers)
        if not exterior:
            continue
        gross = length(sub(wall.axis[1], wall.axis[0])) * (
            ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2 - wall.z0_m
        )
        stated = dict(wall_sheathing(model.plan, wall))
        for layer in wall.layers:
            if layer.function != "sheathing":
                continue
            # A BLIND recess deducts a sheet only where it reaches the sheathing: a hydrant
            # bore from the yard does, a firebox pocket from the living room does not.
            wall_area = gross - sum(
                op.width_m * op.height_m for op in openings_by_wall[wall.tag]
                if cuts_layer(wall, layer.name, op))
            areas[("exterior wall", layer.material_ref, layer.thickness_m,
                   stated.get(layer.name))] += max(
                0.0, wall_area)

    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            continue
        for layer in assembly.layers:
            if layer.function is LayerFunction.SHEATHING:
                areas[("roof", layer.material_ref, layer.thickness.meters,
                       layer_sheet_length_in(layer))] += roof.surface_area_m2

    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem) or system.subfloor is None:
                continue
            floor = next((item for item in model.floors if item.tag == system.tag), None)
            if floor is None or not floor.members:
                continue
            points = [point for member in floor.members for point in (member.p0, member.p1)]
            # The FRAMING's own bounding box — joist tip to joist tip, behind the rim.
            framed = (max(point[0] for point in points) - min(point[0] for point in points)) * (
                max(point[1] for point in points) - min(point[1] for point in points)
            )
            # ``deck_voids``, not the authored ``FloorOpening`` outlines: a wall passing
            # through the deck takes plywood out too and nobody authors that cut
            # (``resolve/through_deck.py``).
            openings = sum(abs(polygon_area(list(ring))) for ring in floor.deck_voids)
            # **The SHEET bills off the sheet, not off the framing.** This read the member
            # bounding box for both, which understates every deck by a rim thickness at each
            # end and — once ``FloorSystem.subfloor_outline`` existed — would have let a
            # plank oversail its rim, draw wide, pass R311.3 and still bill the joist field.
            # ``deck_outline`` is the one polygon the geometry, the drawings and the checks
            # already agree on, so it is what the order reads too.
            sheet = abs(polygon_area(list(floor.deck_outline))) if floor.deck_outline else framed
            areas[("subfloor", system.subfloor.material_ref,
                   system.subfloor.thickness.meters, None)] += sheet - openings
            # ``FloorSystem.ceiling_below`` is the same kind of sheet on the underside of
            # the same deck — and it is nailed to the JOISTS, so it keeps the framed extent
            # whatever the sheet above does.
            #
            # It does NOT take the same opening deduction, though. The subfloor above is
            # genuinely cut around everything that passes through the deck; the ceiling below
            # is only cut where you can see up into it. A chase full of brick takes plywood
            # out and leaves the gypsum whole, so the ceiling asks `deck_void_face` — the one
            # place that rule lives — instead of re-summing every opening.
            under = deck_structure_underside_m(storey, system)
            voids = deck_void_face(model.plan, storey.tag, system, model.walls, under)
            ceiling = framed - (0.0 if voids is None else voids.area)
            for layer in system.ceiling_below:
                areas[("ceiling", layer.material_ref, layer.thickness.meters,
                       layer_sheet_length_in(layer))] += ceiling

    # A structural Slab's own ceiling_below (a room sitting under a cast deck) bills the
    # same way, net of its floor openings — meaningless, and left unauthored, on a
    # slab-on-grade with no occupied space below it.
    for storey in model.plan.storeys:
        for slab in model.plan.storey_elements(storey.tag):
            if (not isinstance(slab, Slab) or not slab.ceiling_below
                    or slab.datum != "structure"):
                continue
            net = max(0.0, abs(polygon_area([point.xy_m for point in slab.outline])) - sum(
                abs(polygon_area([point.xy_m for point in opening.outline]))
                for opening in model.plan.storey_elements(storey.tag)
                if isinstance(opening, FloorOpening) and opening.tag in slab.openings))
            for layer in slab.ceiling_below:
                areas[("ceiling", layer.material_ref, layer.thickness.meters,
                       layer_sheet_length_in(layer))] += net

    # A room's own ``ceiling_lining`` override replaces the covering deck's generic
    # billing over just its own clear face — the same clip-and-rebill ``FinishZone``/
    # ``WallPaneling.replaces_wall_finish`` apply to a base billing they only partly cover.
    for room in model.rooms:
        plan_room = model.plan.by_tag(room.tag)
        if not isinstance(plan_room, Room) or not plan_room.ceiling_lining:
            continue
        face = Polygon(room.clear_face)
        # Per REGION, not per deck: a room straddling two decks takes only its own share
        # out of each one's blanket billing, or the second subtraction credits back area
        # that deck never billed (catlin's RM-B-GYM is 234 SF of FS-M-EAST and 90 of
        # SL-M-DECK, not 324 of each).
        for region in ceiling_regions(model.plan, room.storey, face, model.walls):
            for layer in region.deck.ceiling_below:
                areas[("ceiling", layer.material_ref, layer.thickness.meters,
                       layer_sheet_length_in(layer))] -= region.face.area
        for layer in plan_room.ceiling_lining:
            areas[("ceiling", layer.material_ref, layer.thickness.meters,
                   layer_sheet_length_in(layer))] += room.area_m2

    rows = [
        {"scope": scope, "material": material, "thickness_in": round(thickness / 0.0254, 3),
         "net_area_sqft": round(area * _M2_TO_FT2, 1),
         "sheet": sheet_label(order_sheet_length_in(sheet)),
         "sheets": sheets_for(area * _M2_TO_FT2, order_sheet_length_in(sheet))}
        for (scope, material, thickness, sheet), area in sorted(
            areas.items(), key=lambda item: (item[0][:3], item[0][3] or 0.0))
    ]
    # The panel-profile MEMBERS — a window buck, a web stiffener, a plywood furring rip. Every
    # row above is a layer bought as a flat sheet and hung; these are bought as the same sheet
    # and cut up, which is a different order and (until this existed) was billed as 8-ft
    # STICKS of a profile no lumber yard has ever stocked. ``framing_takeoff`` drops exactly
    # this set, so nothing is billed twice.
    rips = [(member, stock, member.length_m * _M_TO_FT)
            for member in model.all_members()
            if (stock := rip_stock(member.profile, member.material)) is not None]
    return sorted(rows + rip_sheet_rows(rips),
                  key=lambda row: (str(row["scope"]), str(row["material"]),
                                   float(str(row["thickness_in"]))))
