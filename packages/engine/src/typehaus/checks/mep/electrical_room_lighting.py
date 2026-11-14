"""NEC 210.70(A): a light and a switch in every habitable room and equipment space."""

from __future__ import annotations

from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.electrical import _HABITABLE, _warn_fail
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.electrical import luminaire_types
from typehaus.model.enums import Occupancy
from typehaus.model.nec import NEC
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring, owns


@check(Tier.ADVISORY, "electrical.room_lighting")
def room_lighting(ctx: CheckContext) -> list[Finding]:
    """Every habitable room needs >= 1 light + >= 1 switch (symbols-only, decision 1).

    NEC 210.70(A)(3) adds utility, laundry and mechanical rooms, and a storage room with
    equipment in it: a light, switched in the room, by a switch it names, or at the fixture.
    """
    cid = "electrical.room_lighting"
    all_devices = [element for storey in ctx.plan.storeys
                   for element in ctx.plan.storey_elements(storey.tag)
                   if element.element_kind == "ElectricalDevice"]
    if not all_devices:
        return [_unknown(cid, "electrical not modeled")]
    switch_tags = {d.tag for d in all_devices if d.kind.value == "switch"}
    integral = {tag for tag, product in luminaire_types(ctx.plan.library).items()
                if product.integral_switch}

    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        for room in ctx.plan.storey_elements(storey.tag):
            if room.element_kind != "Room":
                continue
            habitable = room.occupancy in _HABITABLE
            if not habitable and not _is_equipment_space(ctx, storey.tag, room):
                continue
            nearby = _devices_in_room(ctx, storey.tag, room)
            lights = [d for d in nearby if d.kind.value == "light"]
            switches = [d for d in nearby if d.kind.value == "switch"]
            if not habitable and not switches:
                switches = [d for d in lights if d.type_ref in integral
                            or set(d.controlled_by) & switch_tags]
            if lights and switches:
                out.append(_pass(cid, f"room {room.tag} has a light and a switch", (room.tag,)))
                continue
            missing = ", ".join(kind for kind, present in (("light", lights),
                                                           ("switch", switches))
                                if not present)
            label = "habitable room" if habitable else (
                f"{room.occupancy.value} room (NEC {NEC.STORAGE_EQUIPMENT_LIGHTING})")
            out.append(_warn_fail(cid, f"{label} {room.tag} is missing: {missing}",
                                  (room.tag,)))
    return out


# NEC 210.70(A)(3): spaces that hold equipment needing service; storage only with some.
_EQUIPMENT_SPACES = {Occupancy.UTILITY, Occupancy.LAUNDRY, Occupancy.MECHANICAL}


def _is_equipment_space(ctx: CheckContext, storey_tag: str, room) -> bool:
    if room.occupancy in _EQUIPMENT_SPACES:
        return True
    if room.occupancy is not Occupancy.STORAGE:
        return False
    resolved = next((r for r in ctx.model.rooms if r.tag == room.tag), None)
    for element in ctx.plan.storey_elements(storey_tag):
        if element.element_kind != "Equipment":
            continue
        if element.room == room.tag:
            return True
        xy = placed_xy(ctx.model, element) if resolved is not None else None
        if xy is not None and owns(resolved, xy):
            return True
    return False


# How far outside a room's clear face a device may sit and still be in it: a wall-mounted
# switch stands on the finish face, which lies a few inches off the clear face.
_IN_ROOM_TOLERANCE_M = 0.15


def _devices_in_room(ctx: CheckContext, storey_tag: str, room) -> list:
    """The storey's devices whose position lies in the resolved room's clear face."""
    from shapely.geometry import Point

    resolved = next((r for r in ctx.model.rooms if r.tag == room.tag), None)
    if resolved is None or len(axis_ring(resolved)) < 3:
        return []
    face = axis_polygon(resolved)
    return [
        element for element in ctx.plan.storey_elements(storey_tag)
        if element.element_kind == "ElectricalDevice"
        and face.distance(Point(placed_xy(ctx.model, element))) <= _IN_ROOM_TOLERANCE_M
    ]
