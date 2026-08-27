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

from typehaus.checks._authoring import advisory, passed as _pass, unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import EquipmentKind
from typehaus.quantities import inch

# The owner's enclosure standard: 5/8" Type X on the interior face of the closet, the same
# membrane R302.6 asks for over a garage. Reuses ``fire_separation``'s reader so "is this
# layer Type X" has one answer in the engine.
_MIN_TYPE_X_MEMBRANE = inch(0.625)


# WARN severity + FAIL result, deliberately: the permit integrity gate only blocks on ERROR
# severity, and this finding is advisory, not a hard blocker.
def _warn(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return advisory(cid, msg, tags, Result.FAIL)


# Structural materials that are the enclosure by themselves. Read off the material's own
# tag rather than the wall's, for the same reason ``_gypsum_grade`` reads gypsum_type: a
# house that spells its concrete differently should still be gradeable, and this list is
# the honest minimum of what this engine can currently tell apart.
_MASS_NONCOMBUSTIBLE_MATERIALS = frozenset({"concrete", "concrete-icf", "cmu"})


def _is_mass_noncombustible(ctx: CheckContext, layer) -> bool:
    from typehaus.model.enums import LayerFunction

    if getattr(layer, "function", None) is not LayerFunction.STRUCTURE:
        return False
    return getattr(layer, "material_ref", None) in _MASS_NONCOMBUSTIBLE_MATERIALS


def _panel_tags(ctx: CheckContext) -> set:
    """Tags of the PANEL-kind electrical devices — read off ``DeviceKind``, not the type
    name: ``ED-T-LT-PANEL`` is a flat ceiling luminaire, and matching on "PANEL" in a type
    tag files it as switchgear."""
    return {element.tag for element in ctx.plan.all_elements()
            if element.element_kind == "ElectricalDevice"
            and getattr(getattr(element, "kind", None), "value", None) == "panel"}


def _is_separable_device(obj, panels: set) -> bool:
    """Is this placeable one of the "other devices" the 3' separation is measured from?"""
    # A panel is the one electrical device with a bus in it; every other kind on a wall is
    # a switch, an outlet or a light, and a battery is not kept away from those.
    return obj.kind == "Equipment" or obj.tag in panels


def _paired_conversion_equipment(ctx: CheckContext, battery) -> set:
    """The battery's own power-conversion equipment, which is not an "other device".

    A hybrid inverter and the pack it charges are one listed ESS, not two appliances that
    happened to be hung near each other: they are sold as a pair, the manufacturer's
    install instructions govern the gap between them, and the DC conductors between them
    carry enough current that *separating* them is its own hazard — every inch of
    separation is voltage drop on the highest-amperage run in the house. Applying a
    separation rule written about foreign heat sources to the battery's own inverter would
    make the model worse by enforcing it.

    The link is the circuit both elements declare. That is an authored fact, not an
    inference from tag spelling: catlin's ``CKT-ESS-GRID`` is the EG4 12kPV's grid port
    (a source, not a branch), and ``EQ-B-ESS-BATT`` names it too. A battery with no
    circuit, or an inverter on a different one, exempts nothing.
    """
    circuit = getattr(battery, "circuit", None)
    if not circuit:
        return set()
    return {element.tag for element in ctx.plan.all_elements()
            if element.element_kind == "Equipment"
            and getattr(element, "kind", None) is EquipmentKind.INVERTER
            and getattr(element, "circuit", None) == circuit}


def _batteries(ctx: CheckContext) -> list:
    return [element for element in ctx.plan.all_elements()
            if element.element_kind == "Equipment"
            and getattr(element, "kind", None) is EquipmentKind.BATTERY]


@check(Tier.ADVISORY, "advisory.ess_enclosure")
def ess_enclosure(ctx: CheckContext) -> list[Finding]:
    """The ESS closet's walls carry at least 5/8" Type X on the interior face.

    Measured off the assembly's own layers, through ``fire_separation._gypsum_grade`` — the
    material states its gypsum grade, so a library that spells the product differently
    still grades correctly. Walls bounding the ESS room are found from the room's resolved
    face, not by tag prefix: a wall counts when most of its own length runs along the
    room's boundary, which keeps out the wall that merely touches a corner from the far
    side of a partition.

    A wall of solid non-combustible mass passes outright. The owner's rule is about what
    the enclosure is made of, and 12" of concrete is not improved by gypsum: demanding a
    membrane on it would report a defect that no builder would fix and that no reader would
    believe twice.
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
        bounding = []
        for wall in ctx.model.walls:
            if wall.storey != room.storey:
                continue
            axis = LineString([wall.axis[0], wall.axis[1]])
            if axis.length <= 1e-9:
                continue
            if axis.intersection(band).length >= 0.5 * axis.length:
                bounding.append(wall)
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
            if any(_is_mass_noncombustible(ctx, layer) for layer in layers):
                continue
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
    """The battery declares a REQUIRED separation zone, and nothing stands in it.

    The owner's rule is "keep a 3' clearance from other devices" (plans/TODO.md) — a
    *separation* from neighbouring equipment, not a working space in front of a face. That
    distinction decides how this is measured, and it is why the check exists alongside the
    resolver's own clearance test rather than duplicating it.

    ``integrity.placeable_required_clearance_conflict`` already reports a peer body standing
    in a REQUIRED zone — but it exempts peers in a *different room*, on the sound reasoning
    that a partition stops a use zone. A stud wall does not stop the thing this zone is
    about. So this check asks the same question with that exemption removed: any placeable
    on the storey whose footprint enters the zone is reported, wall or no wall.

    "Other devices" is read narrowly and deliberately: placed ``Equipment`` and panel-kind
    enclosures. The concern behind the rule is another heat source or another live bus
    beside a lithium pack — not the ceiling light panel two rooms away, not a switch, not
    the water closet on the far side of a foot of concrete. Reporting those would be
    literally true of a 3' sphere and useless to the person reading it, which is how an
    advisory finding gets ignored.

    The battery's **own** inverter is not an other device either, and that exemption is the
    one worth arguing for: see ``_paired_conversion_equipment``. It is named in the PASS
    message rather than dropped silently, so the reader can disagree with it.

    It also reports a battery that declares no REQUIRED zone at all. A separation nobody
    authored is a separation nothing defends.
    """
    from shapely.geometry import Polygon

    cid = "advisory.ess_clearance"
    batteries = _batteries(ctx)
    if not batteries:
        return []
    canvas = {obj.tag: obj for obj in ctx.model.canvas_objects}
    panels = _panel_tags(ctx)

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
                     "standard is a 3' separation from other devices, and a zone nobody "
                     "authored is a separation nothing defends",
                (battery.tag,)))
            continue
        own = Polygon(obj.footprint)
        paired = _paired_conversion_equipment(ctx, battery)
        intruders: list[str] = []
        for zone in obj.required_clearances:
            shape = Polygon(zone)
            if shape.is_valid and own.is_valid:
                shape = shape.difference(own)
            if shape.is_empty:
                continue
            for peer in ctx.model.canvas_objects:
                if peer.uid == obj.uid or peer.storey != obj.storey:
                    continue
                if not _is_separable_device(peer, panels):
                    continue
                if peer.tag in paired:
                    continue
                if shape.intersection(Polygon(peer.footprint)).area > 1e-3:
                    intruders.append(peer.tag)
        if intruders:
            out.append(_warn(
                cid, f"{battery.tag}'s 3' separation zone holds "
                     + ", ".join(sorted(set(intruders)))
                     + " — the wall between them does not make the distance",
                tuple([battery.tag] + sorted(set(intruders)))))
        else:
            note = ""
            if paired:
                note = (f" ({', '.join(sorted(paired))} is its own power-conversion "
                        f"equipment on {battery.circuit}, not an other device)")
            out.append(_pass(
                cid, f"nothing stands in {battery.tag}'s REQUIRED separation zone, in its "
                     f"room or through the walls of it{note}",
                tuple([battery.tag] + sorted(paired))))
    return out
