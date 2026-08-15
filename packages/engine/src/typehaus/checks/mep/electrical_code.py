"""CODE-tier electrical rules — E3902 GFCI protection.

Kept apart from ``electrical.py``, which is five hundred lines of ADVISORY rules about
layout quality (receptacle spacing, lighting controls, panel spaces, service load). What is
here is different in kind: a missing GFCI is not a suggestion, it is the single most common
electrical correction written on a residential rough-in, and it fails the inspection.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy, Service

# E3902: the locations where a 125V 15/20A receptacle must be GFCI-protected. Bathrooms,
# garages and accessory buildings, outdoors, crawl spaces, unfinished basements, kitchens,
# laundry areas, and anything within 6' of a sink.
_GFCI_OCCUPANCIES = {
    Occupancy.BATHROOM.value: "E3902.1 (bathroom)",
    Occupancy.GARAGE.value: "E3902.2 (garage/accessory building)",
    Occupancy.KITCHEN.value: "E3902.6 (kitchen)",
    Occupancy.LAUNDRY.value: "E3902.9 (laundry area)",
}
# E3902.11: unfinished basement receptacles. Read as the below-grade rooms whose occupancy
# says nobody finished them — a finished basement bedroom is not in scope, a below-grade
# mechanical or storage room is.
_UNFINISHED_OCCUPANCIES = {Occupancy.UTILITY.value, Occupancy.STORAGE.value,
                           Occupancy.MECHANICAL.value}
_SINK_REACH_M = 6 * 0.3048  # E3902.10: within 6' of the top inside edge of a sink bowl


def _finding(cid: str, result: Result, message: str, tags: tuple[str, ...],
             code: str, fix: str | None = None) -> Finding:
    if result is Result.PASS:
        return passed(cid, message, tags, code=code)
    if result is Result.UNKNOWN:
        return unknown(cid, message, tags, code=code, fix=fix)
    return failed(cid, message, tags, code=code, fix=fix)


@check(Tier.CODE, "code.E3902_gfci_locations")
def gfci_locations(ctx: CheckContext) -> list[Finding]:
    """E3902 — every receptacle in a wet, outdoor or below-grade location is GFCI-protected.

    Protection is satisfied two ways and both count: a ``RECEPTACLE_GFCI`` device (the
    self-protecting outlet) or an ordinary receptacle on a ``Circuit`` with ``gfci=True``
    (a breaker protecting the whole run). A receptacle that is neither, and names no
    circuit at all, is UNKNOWN rather than FAIL — breaker protection cannot be ruled out
    from an unassigned device, and an inspector would ask rather than write it up.
    """
    from shapely.geometry import Point, Polygon

    from typehaus.checks.code.mn_residential._common import _storey_is_below_grade
    from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle

    cid, code = "code.E3902_gfci_locations", "E3902"
    # Everything here is per storey. A plan-frame point test across the whole building puts
    # a second-floor receptacle inside the basement bathroom it happens to sit above, which
    # is both wrong and confidently wrong — it reports a citation and a room name.
    devices: list[tuple[object, str]] = []
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if (element.element_kind == "ElectricalDevice"
                    and _counts_as_a_125v_receptacle(ctx, element)):
                devices.append((element, storey.tag))
    if not devices:
        return [_finding(cid, Result.UNKNOWN, "no 125V receptacles are modeled", (), code)]
    # Circuits are schedule data in the library, not storey elements — they have no
    # position and never appear in an element list.
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(room.clear_face) >= 3:
            rooms.setdefault(room.storey, []).append((room, Polygon(room.clear_face)))
    below_grade = {storey.tag: _storey_is_below_grade(ctx, storey)
                   for storey in ctx.plan.storeys}
    sinks = _sink_points(ctx)

    by_tag = {room.tag: room for room in ctx.model.rooms}
    out: list[Finding] = []
    for device, storey_tag in devices:
        point = Point(device.position.xy_m)
        room = _room_of(device, point, rooms.get(storey_tag, ()), by_tag)
        reason = _why_gfci_required(ctx, device, room, point,
                                    sinks.get(storey_tag, ()), below_grade)
        if reason is None:
            continue
        tags = (device.tag,) + ((room.tag,) if room is not None else ())
        if device.kind.value == "gfci":
            out.append(_finding(cid, Result.PASS,
                                f"{device.tag} is a GFCI device — {reason}", (), code))
            continue
        circuit = circuits.get(device.circuit) if device.circuit else None
        if circuit is None:
            out.append(_finding(cid, Result.UNKNOWN,
                                f"{device.tag} requires GFCI protection — {reason} — and "
                                "names no circuit, so breaker protection cannot be "
                                "confirmed", tags, code,
                                "assign the device to a circuit, or make it a GFCI device"))
        elif getattr(circuit, "gfci", False):
            out.append(_finding(cid, Result.PASS,
                                f"{device.tag} is protected by GFCI breaker "
                                f"{circuit.tag} — {reason}", (), code))
        else:
            out.append(_finding(cid, Result.FAIL,
                                f"{device.tag} requires GFCI protection — {reason} — but is "
                                f"an ordinary receptacle on non-GFCI circuit {circuit.tag}",
                                tags, code,
                                "make it a RECEPTACLE_GFCI device, or set gfci=True on "
                                f"{circuit.tag}"))
    if not out:
        return [_finding(cid, Result.PASS, "no receptacle sits in an E3902 location "
                         "(bath, kitchen, garage, laundry, outdoors, unfinished basement, "
                         "or within 6' of a sink)", (), code)]
    return out


# How far outside a room's finish face a device may sit and still be in that room. A
# receptacle is mounted *on* the wall, so its point lands on or just past the clear face —
# a plain point-in-polygon test calls half the receptacles in the house outdoors.
_IN_ROOM_TOL_M = 0.5


def _room_of(device, point, storey_rooms, by_tag):
    """The room this element is in: authored if it says, else the nearest face it touches.

    ``getattr`` rather than attribute access because the AFCI rule walks every circuit
    consumer, and Equipment, Registers and devices do not share a base that promises a
    ``room`` field.
    """
    authored = getattr(device, "room", None)
    if authored and authored in by_tag:
        return by_tag[authored]
    covering = [room for room, poly in storey_rooms if poly.covers(point)]
    if covering:
        return covering[0]
    near = [(poly.distance(point), room) for room, poly in storey_rooms]
    if near:
        distance, room = min(near, key=lambda pair: pair[0])
        if distance <= _IN_ROOM_TOL_M:
            return room
    return None


def _why_gfci_required(ctx, device, room, point, sinks, below_grade) -> str | None:
    """The E3902 clause that puts this receptacle in scope, or None."""
    if room is None:
        # Outside every resolved room face: an exterior receptacle. E3902.3.
        return "E3902.3 (outdoors)"
    if room.occupancy in _GFCI_OCCUPANCIES:
        return _GFCI_OCCUPANCIES[room.occupancy]
    if (room.occupancy in _UNFINISHED_OCCUPANCIES
            and below_grade.get(room.storey) is True):
        return "E3902.11 (unfinished basement)"
    near = min((point.distance(sink) for sink in sinks), default=None)
    if near is not None and near <= _SINK_REACH_M:
        return f"E3902.10 (within 6' of a sink — {near / .3048:.1f}')"
    return None


def _sink_points(ctx: CheckContext) -> dict[str, list]:
    """Per storey, the plan points of every fixture that drains.

    Keyed by storey for the same reason the room lookup is: the 6' reach of E3902.10 is a
    reach across a countertop, not through a floor assembly.
    """
    from shapely.geometry import Point

    out: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = next((t for t in ctx.plan.library.fixture_types
                                 if t.tag == fixture.type_ref), None)
            if fixture_type is None:
                continue
            needs = getattr(fixture_type, "needs", ())
            if any(getattr(need, "value", need) == Service.DRAIN.value for need in needs):
                out.setdefault(storey.tag, []).append(Point(fixture.position.xy_m))
    return out


# E3902.16: AFCI protection on the 120V 15/20A branch circuits serving these rooms. The list
# is close to "everywhere people live" — the exclusions are bathrooms, garages, and
# unfinished basements, which is to say the places E3902 already sends to GFCI instead.
_AFCI_OCCUPANCIES = frozenset({
    Occupancy.KITCHEN.value, Occupancy.LIVING.value, Occupancy.DINING.value,
    Occupancy.BEDROOM.value, Occupancy.HALLWAY.value, Occupancy.LAUNDRY.value,
    Occupancy.MEDIA.value, Occupancy.OFFICE.value, Occupancy.STORAGE.value,
})

# ...and only on the circuits the section actually reaches. E3902.16 (NEC 210.12) is written
# for "120-volt, single-phase, 15- and 20-ampere branch circuits", which is the ordinary
# lighting-and-receptacle wiring and nothing else: a 240V range, dryer, heat-pump or EV
# circuit is outside it, and so is a 120V circuit over 20A. Screening on the *rooms* alone
# wrote up eight breakers in this house that no AFCI device is even made for.
_AFCI_MAX_AMPS = 20


def _afci_applies(circuit) -> bool:
    """Is this circuit one of the 120V 15/20A branch circuits E3902.16 covers?"""
    return (getattr(circuit, "poles", 1) == 1
            and getattr(circuit, "breaker_amps", 0) <= _AFCI_MAX_AMPS)


@check(Tier.CODE, "code.E3902_16_afci")
def afci_branch_circuits(ctx: CheckContext) -> list[Finding]:
    """E3902.16 — branch circuits serving habitable rooms are AFCI-protected.

    Evaluated per *circuit*, not per outlet, because that is where the protection lives: a
    single breaker covers every device on the run, so one circuit reaching one bedroom puts
    the whole circuit in scope. That also makes the finding actionable — it names the
    breaker to change, not the eleven receptacles downstream of it.

    Two screens, both necessary: the circuit must reach a room on the section's list *and*
    be one of the 120V 15/20A branch circuits the section is written for (``_afci_applies``).
    A 2-pole range or heat-pump circuit lands in a living room like every other circuit does
    and is not what E3902.16 is about.
    """
    from shapely.geometry import Point, Polygon

    cid, code = "code.E3902_16_afci", "E3902.16"
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    if not circuits:
        return [_finding(cid, Result.UNKNOWN, "the plan states no circuits", (), code)]

    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(room.clear_face) >= 3:
            rooms.setdefault(room.storey, []).append((room, Polygon(room.clear_face)))
    by_tag = {room.tag: room for room in ctx.model.rooms}

    # Which rooms each circuit reaches, via every consumer that names it.
    served: dict[str, set[str]] = {}
    unplaced: dict[str, set[str]] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            circuit_tag = getattr(element, "circuit", None)
            if not circuit_tag or circuit_tag not in circuits:
                continue
            position = getattr(element, "position", None)
            if position is None:
                continue
            room = _room_of(element, Point(position.xy_m), rooms.get(storey.tag, ()), by_tag)
            if room is None:
                unplaced.setdefault(circuit_tag, set()).add(element.tag)
            else:
                served.setdefault(circuit_tag, set()).add(room.occupancy)

    out: list[Finding] = []
    for tag, circuit in sorted(circuits.items()):
        if not _afci_applies(circuit):
            continue
        occupancies = served.get(tag, set())
        if not occupancies:
            if tag in unplaced:
                out.append(_finding(cid, Result.UNKNOWN,
                                    f"{tag} feeds {', '.join(sorted(unplaced[tag]))}, none of "
                                    "which resolves to a room, so whether E3902.16 reaches "
                                    "it cannot be decided", (tag,), code))
            continue
        habitable = occupancies & _AFCI_OCCUPANCIES
        if not habitable:
            continue
        where = ", ".join(sorted(habitable))
        if getattr(circuit, "afci", False):
            out.append(_finding(cid, Result.PASS, f"{tag} is AFCI-protected ({where})",
                                (), code))
        else:
            out.append(_finding(cid, Result.FAIL,
                                f"{tag} serves {where} space and is not AFCI-protected",
                                (tag,), code,
                                f"set afci=True on {tag} in the circuit schedule"))
    if not out:
        return [_finding(cid, Result.PASS, "no circuit serves a room E3902.16 covers",
                         (), code)]
    return out
