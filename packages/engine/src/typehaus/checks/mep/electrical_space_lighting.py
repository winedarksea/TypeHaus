"""``electrical.equipment_space_lighting`` — 2026 NEC 210.70(C): light where equipment is serviced.

A utility, mechanical, storage or unconditioned room (an attic's unfinished bay, a basement's
furnace room) that holds equipment needing service takes a lighting outlet with a switch,
a point of control at each entry, and a light at or near the equipment. Equipment is an
``Equipment`` element (ducts' manifolds and plenums are not serviced) or a panel. Per room:

* no luminaire, or none with a wall switch or integral switch: FAIL (advisory);
* an entry (a door, or a leafless floor-level opening) with no controlling switch within
  6 ft, an equipment footprint with no luminaire within 6 ft, or no modelled entry (a
  stair): UNKNOWN, since "entry that permits access" and "near" are judgement the plan
  cannot settle.

(C)(3): where every switched light in the room answers only to automatic controls (a
switch type whose ``control`` is ``occupancy`` or ``timer``) and none has an integral switch,
the room is UNKNOWN, since a manual bypass is not modelled.
Finished basement rooms (a gym) are 210.70(A)(1)/(A)(3) rooms and are outside this scope.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.mep.electrical_working_space import AUTOMATIC_ONLY_CONTROLS
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DeviceKind, Occupancy
from typehaus.model.nec import NEC, cite

_CID = "electrical.equipment_space_lighting"
_NEAR_M = 6 * 0.3048
_SPACES = frozenset(o.value for o in (Occupancy.UTILITY, Occupancy.MECHANICAL,
                                      Occupancy.STORAGE, Occupancy.CLOSET,
                                      Occupancy.UNCONDITIONED))
_NOT_SERVICED = frozenset({"duct_manifold", "plenum"})


def _serviced(ctx: CheckContext, objects: dict, room_of) -> dict[str, list[str]]:
    """Room tag -> tags of the equipment and panels in it that need servicing."""
    held: dict[str, list[str]] = {}
    for el in ctx.plan.all_elements():
        kind = getattr(getattr(el, "kind", None), "value", None)
        is_equipment = el.element_kind == "Equipment" and kind not in _NOT_SERVICED
        if not (is_equipment or (el.element_kind == "ElectricalDevice" and kind == "panel")):
            continue
        obj = objects.get(el.tag)
        room = room_of(obj) if obj is not None else None
        if room is not None and room.occupancy in _SPACES:
            held.setdefault(room.tag, []).append(el.tag)
    return held


def _manual(light, switches: dict, types: dict) -> bool:
    """A light with an integral switch or at least one switch that is not automatic-only."""
    if getattr(types.get(light.type_ref), "integral_switch", False):
        return True
    kinds = [getattr(types.get(switches[s].type_ref or ""), "control", None)
             for s in light.controlled_by if s in switches]
    return any(kind not in AUTOMATIC_ONLY_CONTROLS for kind in kinds)


def _closet_door(door, room: str, doors_of: dict[str, set[str]]) -> bool:
    """The door leads to another room that has no other door: a dead end off ``room``."""
    beyond = [tag for tag, doors in doors_of.items() if tag != room and door.tag in doors]
    return bool(beyond) and all(doors_of[tag] == {door.tag} for tag in beyond)


@check(Tier.ADVISORY, _CID)
def equipment_space_lighting(ctx: CheckContext) -> list[Finding]:
    """Each room with serviced equipment has a switched light, a control per door, a light near."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.geometry import opening_center
    from typehaus.resolve.room_lookup import room_owning
    from typehaus.resolve.room_openings import room_doors, room_passages

    code = cite(NEC.EQUIPMENT_SPACE_LIGHTING)
    objects = {o.tag: o for o in ctx.model.canvas_objects}

    def room_of(obj):
        return room_owning(ctx.model, obj.storey, obj.position)

    held = _serviced(ctx, objects, room_of)
    if not held:
        return [not_applicable(_CID, "no utility, mechanical, storage or unconditioned room "
                                     "holds equipment or a panel", code=code)]
    lights = [e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"
              and e.kind is DeviceKind.LIGHT and e.tag in objects]
    switches = {e.tag: e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"
                and e.kind is DeviceKind.SWITCH and e.tag in objects}
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    rooms = {r.tag: r for r in ctx.model.rooms}
    entries = {r.tag: room_doors(ctx.model, r) + room_passages(ctx.model, r)
               for r in ctx.model.rooms}
    doors_of = {tag: {d.tag for d in found} for tag, found in entries.items()}
    out: list[Finding] = []
    for tag in sorted(held):
        room = rooms[tag]
        mine = [e for e in lights if room_of(objects[e.tag]) is not None
                and room_of(objects[e.tag]).tag == tag]
        tags = (tag, *held[tag])
        if not mine:
            out.append(advisory(_CID, f"{tag} holds {', '.join(held[tag])} and has no lighting "
                                      "outlet", tags, Result.FAIL, code=code,
                                fix="add a luminaire with a wall switch"))
            continue
        switched = [e for e in mine if getattr(types.get(e.type_ref), "integral_switch", False)
                    or any(s in switches for s in e.controlled_by)]
        if not switched:
            out.append(advisory(_CID, f"{tag}: no luminaire has a switch ({mine[0].tag} names "
                                      "none)", tags, Result.FAIL, code=code,
                                fix="control a luminaire by a wall switch"))
            continue
        controls = [objects[s].position for e in mine for s in e.controlled_by if s in switches]
        gaps: list[str] = []
        if not any(_manual(e, switches, types) for e in switched):
            gaps.append(f"every switched light answers only to automatic control, and "
                        f"{NEC.EQUIPMENT_SPACE_AUTOMATIC} wants a manual bypass the model does "
                        "not hold")
        doors = [d for d in entries[tag] if not _closet_door(d, tag, doors_of)]
        if not doors:
            gaps.append("no entry is modelled (a stair?)")
        for door in doors:
            wall = ctx.model.wall(door.host_wall)
            centre = opening_center(wall, door) if wall is not None else None
            if centre is not None and not any(math.dist(centre, c) <= _NEAR_M for c in controls):
                gaps.append(f"door {getattr(door, 'tag', door.host_wall)} has no switch of this "
                            "room's lights within 6 ft")
        for eq in held[tag]:
            obj = objects[eq]
            shape = Polygon(obj.footprint) if len(obj.footprint) >= 3 else Point(obj.position)
            if not any(shape.distance(Point(objects[e.tag].position)) <= _NEAR_M for e in mine):
                gaps.append(f"no luminaire within 6 ft of {eq}")
        if gaps:
            out.append(unknown(_CID, f"{tag}: " + "; ".join(gaps) + "; what 'at each entry' and "
                               "'near' mean is the inspector's", tags, code=code,
                               fix="a switch at each entry and a light by the equipment"))
        else:
            out.append(passed(_CID, f"{tag} has a switched light, a control at each of its "
                                    f"{len(doors)} doors and a light near {', '.join(held[tag])}",
                              tags, code=code))
    return out
