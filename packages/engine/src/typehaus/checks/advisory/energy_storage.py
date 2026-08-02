"""ADVISORY — owner hardening around the energy storage system.

These two are deliberately *not* CODE, and the line is worth stating because both look like
code requirements at a glance. R327 permits an ESS in a utility closet, a basement, or a
storage/utility space without demanding a rated enclosure around it; NFPA 855 and the
manufacturer's instructions are where separation and clearance rules of this shape live,
and neither is the adopted residential code this profile encodes (see
``checks/code/mn_residential/profile.py``'s coverage statement).

So they are owner decisions with arithmetic behind them: a 5/8" Type X membrane and three
feet of working space around a 14 kWh lithium pack in a basement is what the owner asked
for, and these checks hold the model to what was asked rather than to what is required.

Both no-op when no ESS is placed.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import EquipmentKind
from typehaus.quantities import inch

# The owner's enclosure standard: 5/8" Type X on the interior face of the closet, the same
# membrane R302.6 asks for over a garage. Reuses ``fire_separation``'s reader so "is this
# layer Type X" has one answer in the engine.
_MIN_TYPE_X_MEMBRANE = inch(0.625)


def _warn(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.PASS)


def _unknown(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {msg}",
                   element_tags=tags, result=Result.UNKNOWN)


def _batteries(ctx: CheckContext) -> list:
    return [element for element in ctx.plan.all_elements()
            if element.element_kind == "Equipment"
            and getattr(element, "kind", None) is EquipmentKind.BATTERY]


@check(Tier.ADVISORY, "advisory.ess_enclosure")
def ess_enclosure(ctx: CheckContext) -> list[Finding]:
    """The ESS closet's walls carry at least 5/8" Type X on the interior face.

    Measured off the assembly's own layers, through ``fire_separation._gypsum_grade`` — the
    material states its gypsum grade, so a library that spells the product differently
    still grades correctly. Walls bounding the ESS room are found the way the garage
    separation check finds its shared walls: by the room's resolved face, not by tag prefix.
    """
    from shapely.geometry import LineString, Polygon

    from typehaus.checks.code.mn_residential.fire_separation import _gypsum_grade

    cid = "advisory.ess_enclosure"
    batteries = _batteries(ctx)
    if not batteries:
        return []
    rooms = {room.tag: room for room in ctx.model.rooms}
    assemblies = {a.tag: a for a in ctx.plan.library.assemblies}

    out: list[Finding] = []
    for room_tag in sorted({getattr(b, "room", None) for b in batteries} - {None}):
        room = rooms.get(room_tag)
        if room is None or len(room.clear_face) < 3:
            out.append(_unknown(cid, f"ESS room {room_tag} has no resolved face, so its "
                                     "enclosure cannot be measured", (str(room_tag),)))
            continue
        face = Polygon(room.clear_face)
        band = face.boundary.buffer(inch(12).meters)
        bounding = [wall for wall in ctx.model.walls
                    if wall.storey == room.storey
                    and band.intersects(LineString([wall.axis[0], wall.axis[1]]))]
        if not bounding:
            out.append(_unknown(cid, f"no wall bounds ESS room {room_tag}",
                                (str(room_tag),)))
            continue
        thin = []
        for wall in bounding:
            assembly = assemblies.get(wall.assembly)
            if assembly is None:
                continue
            layers = tuple(assembly.layers) + tuple(assembly.default_lining)
            type_x = sum(layer.thickness.meters for layer in layers
                         if _gypsum_grade(ctx, layer) == "type-x"
                         and layer.thickness is not None)
            if type_x + 1e-9 < _MIN_TYPE_X_MEMBRANE.meters:
                thin.append((wall.tag, type_x))
        if thin:
            out.append(_warn(
                cid, f"ESS room {room_tag} is enclosed by "
                     + ", ".join(f"{tag} ({value / .0254:.2f}\" Type X)"
                                 for tag, value in sorted(thin))
                     + f"; the owner's ESS closet standard is "
                       f"{_MIN_TYPE_X_MEMBRANE.inches:.3g}\" Type X on the interior face",
                tuple([str(room_tag)] + [tag for tag, _ in sorted(thin)])))
        else:
            out.append(_pass(
                cid, f"all {len(bounding)} walls bounding ESS room {room_tag} carry at "
                     f"least {_MIN_TYPE_X_MEMBRANE.inches:.3g}\" Type X", (str(room_tag),)))
    return out


@check(Tier.ADVISORY, "advisory.ess_clearance")
def ess_clearance(ctx: CheckContext) -> list[Finding]:
    """The battery declares a REQUIRED working-clearance zone, and it fits its room.

    Two things the resolver does not already say. The resolver reports a REQUIRED zone that
    another *placeable body* stands in (``integrity.placeable_required_clearance_conflict``)
    — that half is covered and this check does not duplicate it. What is left is the zone
    that runs *through a wall*: a 3' clearance authored on a battery in a 3'x4' closet is
    satisfied on paper and impossible in the room, and no placeable overlaps to reveal it.

    So: the zone must exist and be REQUIRED (an ESS clearance the owner asked for and
    nobody authored is the failure that matters), and it must lie inside the room's clear
    face.
    """
    from shapely.geometry import Polygon

    cid = "advisory.ess_clearance"
    batteries = _batteries(ctx)
    if not batteries:
        return []
    rooms = {room.tag: room for room in ctx.model.rooms}
    canvas = {obj.tag: obj for obj in ctx.model.canvas_objects}

    out: list[Finding] = []
    for battery in sorted(batteries, key=lambda e: e.tag):
        obj = canvas.get(battery.tag)
        if obj is None:
            out.append(_unknown(cid, f"{battery.tag} did not resolve to a placed object",
                                (battery.tag,)))
            continue
        if not obj.required_clearances:
            out.append(_warn(
                cid, f"{battery.tag} declares no REQUIRED clearance zone; the owner's ESS "
                     "standard is a 3' working clearance, and a zone nobody authored is a "
                     "clearance nothing defends",
                (battery.tag,)))
            continue
        room = rooms.get(obj.room or "")
        if room is None or len(room.clear_face) < 3:
            out.append(_unknown(cid, f"{battery.tag} resolved to no room, so its clearance "
                                     "cannot be tested against one", (battery.tag,)))
            continue
        face = Polygon(room.clear_face)
        spill = sum(max(Polygon(zone).difference(face).area, 0.0)
                    for zone in obj.required_clearances)
        if spill > 1e-3:
            out.append(_warn(
                cid, f"{battery.tag}'s required clearance runs {spill * 10.7639:.2f} sf "
                     f"past the walls of {room.tag}; the clearance the owner asked for does "
                     "not fit the room it is drawn in",
                (battery.tag, room.tag)))
        else:
            out.append(_pass(
                cid, f"{battery.tag}'s required clearance zone lies inside {room.tag}",
                (battery.tag, room.tag)))
    return out
