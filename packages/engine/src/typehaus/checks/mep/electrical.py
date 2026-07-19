"""Electrical checks — symbols-only coverage (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import Occupancy

_HABITABLE = {Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.KITCHEN, Occupancy.DINING,
             Occupancy.OFFICE}


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.PASS)


def _warn_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _unknown(cid: str, reason: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {reason}",
                   element_tags=tags, result=Result.UNKNOWN)


@check(Tier.ADVISORY, "electrical.room_lighting")
def room_lighting(ctx: CheckContext) -> list[Finding]:
    """Every habitable room needs >= 1 light + >= 1 switch (symbols-only, decision 1)."""
    all_devices = [element for storey in ctx.plan.storeys
                   for element in ctx.plan.storey_elements(storey.tag)
                   if element.element_kind == "ElectricalDevice"]
    if not all_devices:
        return [_unknown("electrical.room_lighting", "electrical not modeled")]

    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        for room in ctx.plan.storey_elements(storey.tag):
            if room.element_kind != "Room" or room.occupancy not in _HABITABLE:
                continue
            nearby = _devices_in_room(ctx, storey.tag, room)
            lights = [d for d in nearby if d.kind.value == "light"]
            switches = [d for d in nearby if d.kind.value == "switch"]
            if lights and switches:
                out.append(_pass(
                    "electrical.room_lighting",
                    f"room {room.tag} has a light and a switch", (room.tag,),
                ))
            else:
                missing = ", ".join(
                    kind for kind, present in (("light", lights), ("switch", switches))
                    if not present
                )
                out.append(_warn_fail(
                    "electrical.room_lighting",
                    f"habitable room {room.tag} is missing: {missing}", (room.tag,),
                ))
    return out


def _devices_in_room(ctx: CheckContext, storey_tag: str, room) -> list:
    """Symbols-only proximity match: nearest room seed by tag suffix (→ ED-<room-suffix>-*)."""
    suffix = room.tag[3:]  # "RM-M-BED" -> "M-BED"
    return [
        element for element in ctx.plan.storey_elements(storey_tag)
        if element.element_kind == "ElectricalDevice" and element.tag.startswith(f"ED-{suffix}-")
    ]
