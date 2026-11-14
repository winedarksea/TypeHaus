"""CODE-tier electrical rules — NEC 210.8 GFCI and 210.12 AFCI protection.

Kept apart from ``electrical.py``, which is five hundred lines of ADVISORY rules about
layout quality (receptacle spacing, lighting controls, panel spaces, service load). What is
here is different in kind: a missing GFCI is not a suggestion, it is the single most common
electrical correction written on a residential rough-in, and it fails the inspection.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy, Service
from typehaus.model.nec import NEC, cite
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

# 2026 NEC 210.8(A): the locations where a 125-250 V receptacle, at any amperage, must be
# GFCI-protected. Bathrooms, garages, accessory buildings, outdoors, crawl spaces, basements
# (finished or not), kitchens, laundry areas, 6' of a sink (9) or a tub/shower (11).
_GFCI_OCCUPANCIES = {
    Occupancy.BATHROOM.value: f"{NEC.GFCI_BATHROOM} (bathroom)",
    Occupancy.GARAGE.value: f"{NEC.GFCI_GARAGE} (garage)",
    Occupancy.KITCHEN.value: f"{NEC.GFCI_KITCHEN} (kitchen)",
    Occupancy.LAUNDRY.value: f"{NEC.GFCI_LAUNDRY} (laundry area)",
}
_SINK_REACH_M = 6 * 0.3048  # 210.8(A): within 6' of the top inside edge of a sink bowl
# How much of the receptacle-to-sink segment may lie inside a wall before the path counts as
# PIERCING that wall. Not zero: a receptacle's plan point sits on (and sometimes a fraction
# of an inch inside) the wall face it is mounted to, and a fixture pushed hard against its
# own wall does the same, so a same-room pair routinely shares a hair of wall footprint.
# A real wall crossing is the wall's whole thickness — 4 3/4" is the thinnest in this house.
_PIERCE_TOL_M = 1 * 0.0254


@check(Tier.CODE, "code.E3902_gfci_locations")
def gfci_locations(ctx: CheckContext) -> list[Finding]:
    """NEC 210.8 — every receptacle in a wet, outdoor or basement location is GFCI-protected.

    Protection is satisfied two ways and both count: a ``RECEPTACLE_GFCI`` device (the
    self-protecting outlet) or an ordinary receptacle on a ``Circuit`` with ``gfci=True``
    (a breaker protecting the whole run). A receptacle that is neither, and names no
    circuit at all, is UNKNOWN rather than FAIL — breaker protection cannot be ruled out
    from an unassigned device, and an inspector would ask rather than write it up.
    """
    from shapely.geometry import Point

    from typehaus.checks.code.mn_residential._common import _storey_is_below_grade
    from typehaus.checks.mep.electrical_gfci_appliances import (
        appliance_receptacles,
        outdoor_outlets,
    )

    cid, code = "code.E3902_gfci_locations", cite(NEC.GFCI_DWELLING)
    # Everything here is per storey. A plan-frame point test across the whole building puts
    # a second-floor receptacle inside the basement bathroom it happens to sit above, which
    # is both wrong and confidently wrong — it reports a citation and a room name.
    devices: list[tuple[object, str]] = []
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if (element.element_kind == "ElectricalDevice"
                    and _is_a_gfci_receptacle(ctx, element)):
                devices.append((element, storey.tag))
    if not devices:
        return [by_result(cid, Result.UNKNOWN, "no 125-250 V receptacles are modeled", (),
                          code)]
    # Circuits are schedule data in the library, not storey elements — they have no
    # position and never appear in an element list.
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    guards = {element.tag: element for storey in ctx.plan.storeys
              for element in ctx.plan.storey_elements(storey.tag)
              if element.element_kind == "ElectricalDevice"}
    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append((room, axis_polygon(room)))
    below_grade = {storey.tag: _storey_is_below_grade(ctx, storey)
                   for storey in ctx.plan.storeys}
    sinks = _sink_points(ctx)
    barriers = _wall_barrier(ctx)
    appliance, appliance_gaps = appliance_receptacles(ctx, devices)

    by_tag = {room.tag: room for room in ctx.model.rooms}
    out: list[Finding] = []
    for device, storey_tag in devices:
        point = Point(placed_xy(ctx.model, device))
        room = _room_of(ctx.model, device, point, rooms.get(storey_tag, ()), by_tag)
        reasons = [r for r in (_why_gfci_required(ctx, device, room, point,
                                                  sinks.get(storey_tag, ()), below_grade,
                                                  barriers.get(storey_tag)),
                               appliance.get(device.tag)) if r]
        if not reasons:
            if room is not None and below_grade.get(room.storey) is None:
                out.append(by_result(cid, Result.UNKNOWN,
                                     f"{device.tag}: storey {room.storey} has no grade datum, so "
                                     f"{NEC.GFCI_BASEMENT} (basement) cannot be ruled out",
                                     (device.tag, room.tag), code,
                                     "author the site grade the storey is measured against"))
            continue
        reason = "; ".join(reasons)
        tags = (device.tag,) + ((room.tag,) if room is not None else ())
        if device.kind.value == "gfci":
            out.append(by_result(cid, Result.PASS,
                                 f"{device.tag} is a GFCI device — {reason}", (), code))
            continue
        circuit = circuits.get(device.circuit) if device.circuit else None
        if device.gfci_ref:
            guard = guards.get(device.gfci_ref)
            if guard is not None and guard.kind.value == "gfci" and guard.circuit == device.circuit:
                out.append(by_result(cid, Result.PASS,
                                     f"{device.tag} is fed from the load side of GFCI "
                                     f"{guard.tag} — {reason}", (), code))
            else:
                out.append(by_result(cid, Result.FAIL,
                                     f"{device.tag} names gfci_ref {device.gfci_ref}, which is "
                                     f"not a GFCI device on {device.circuit} — {reason}",
                                     tags, code, "point gfci_ref at a GFCI device on the "
                                     "same circuit"))
            continue
        if circuit is None:
            out.append(by_result(cid, Result.UNKNOWN,
                                 f"{device.tag} requires GFCI protection — {reason} — and "
                                 "names no circuit, so breaker protection cannot be "
                                 "confirmed", tags, code,
                                 "assign the device to a circuit, or make it a GFCI device"))
        elif getattr(circuit, "gfci", False) and getattr(circuit, "gfci_class", "A") == "C":
            out.append(by_result(cid, Result.FAIL,
                                 f"{device.tag} requires GFCI protection — {reason} — but "
                                 f"{circuit.tag} is a Class C SPGFCI, not personnel "
                                 "protection", tags, code,
                                 f"make {circuit.tag} a Class A GFCI"))
        elif getattr(circuit, "gfci", False):
            out.append(by_result(cid, Result.PASS,
                                 f"{device.tag} is protected by GFCI breaker "
                                 f"{circuit.tag} — {reason}", (), code))
        else:
            out.append(by_result(cid, Result.FAIL,
                                 f"{device.tag} requires GFCI protection — {reason} — but is "
                                 f"an ordinary receptacle on non-GFCI circuit {circuit.tag}",
                                 tags, code,
                                 "make it a RECEPTACLE_GFCI device, or set gfci=True on "
                                 f"{circuit.tag}"))
    if not out:
        out.append(by_result(cid, Result.PASS, f"no receptacle sits in a {NEC.GFCI_DWELLING} "
                             "location (bath, kitchen, garage, laundry, outdoors, basement, "
                             "or within 6' of a sink)", (), code))
    return out + appliance_gaps + outdoor_outlets(ctx, _outdoor_consumers(ctx, barriers))


def _is_a_gfci_receptacle(ctx: CheckContext, device) -> bool:
    """A 125-250 V receptacle of any amperage — 210.8(A)'s population since the 2020 NEC.

    A 240 V kind is a receptacle unless its type states a NEMA spec with no receptacle in it.
    """
    from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle

    if _counts_as_a_125v_receptacle(ctx, device):
        return True
    if device.kind.value != "receptacle_240":
        return False
    product = next((t for t in ctx.plan.library.electrical_device_types
                    if t.tag == device.type_ref), None) if device.type_ref else None
    nema = getattr(product, "nema", None)
    return not getattr(product, "deadfront", False) and (nema is None or "R" in nema)


def _outdoor_consumers(ctx: CheckContext, barriers) -> dict[str, tuple[str, str]]:
    """{tag: (circuit, kind)} for each Equipment outdoors — 210.8(F)'s.

    Outdoors by its own placement: no authored room, its point in no room polygon and off
    every wall (a wall-hung indoor unit sits on its wall). No room-face tolerance, which
    would pull a condenser on a pad beside the house indoors.
    """
    from shapely.geometry import Point

    polygons: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            polygons.setdefault(room.storey, []).append(axis_polygon(room))
    out: dict[str, tuple[str, str]] = {}
    for storey in ctx.plan.storeys:
        walls = barriers.get(storey.tag)
        walls = walls.buffer(_WALL_HUNG_M) if walls is not None else None
        for element in ctx.plan.storey_elements(storey.tag):
            circuit = getattr(element, "circuit", None)
            if not circuit or element.element_kind != "Equipment" or element.room:
                continue
            xy = placed_xy(ctx.model, element)
            if xy is None:
                continue
            point = Point(xy)
            if any(poly.covers(point) for poly in polygons.get(storey.tag, ())):
                continue
            if walls is not None and walls.covers(point):
                continue
            out[element.tag] = (circuit, getattr(element.kind, "value", ""))
    return out


_WALL_HUNG_M = 2 * 0.0254  # a wall-hung unit's point may stand just off the wall face


# How far outside a room's axis cell an UNHOSTED element may sit and still be in that room.
# A wall-hosted one never reads this: its own face says which side it is on.
_IN_ROOM_TOL_M = 0.5
# How far past its host face a wall-mounted device is probed for the room it faces.
_FACE_PROBE_M = 0.15


def _room_of(model, device, point, storey_rooms, by_tag):
    """The room this element is in: authored if it says, else the room its host face looks
    into, else the axis cell covering (or nearest within tolerance of) its point.

    A tolerance alone is wrong on a thick exterior wall: a receptacle on its outer face sits
    inches off the room's axis cell and was counted indoors. ``getattr`` because the AFCI
    rule walks every circuit consumer, and they share no base promising ``room``.
    """
    authored = getattr(device, "room", None)
    if authored and authored in by_tag:
        return by_tag[authored]
    hosted = _host_of(model, device)
    if hosted is not None:
        wall, attachment = hosted
        from shapely.geometry import Point

        from typehaus.resolve.wall_hosting import face_frame

        (x, y), _, (nx, ny) = face_frame(wall, attachment, None)
        probe = Point(x + nx * _FACE_PROBE_M, y + ny * _FACE_PROBE_M)
        return next((room for room, poly in storey_rooms if poly.covers(probe)), None)
    covering = [room for room, poly in storey_rooms if poly.covers(point)]
    if covering:
        return covering[0]
    near = [(poly.distance(point), room) for room, poly in storey_rooms]
    if near:
        distance, room = min(near, key=lambda pair: pair[0])
        if distance <= _IN_ROOM_TOL_M:
            return room
    return None


def _host_of(model, element):
    """(wall, attachment) when ``element`` is wall-hosted on a resolved wall, else None."""
    attachment = getattr(getattr(element, "location", None), "attachment", None)
    wall = model.wall(attachment.wall_ref) if attachment is not None else None
    return None if wall is None else (wall, attachment)


def _why_gfci_required(ctx, device, room, point, sinks, below_grade, barrier) -> str | None:
    """The 210.8(A) item that puts this receptacle in scope, or None."""
    if room is None:
        # Outside every resolved room face: an exterior receptacle.
        return f"{NEC.GFCI_OUTDOORS} (outdoors)"
    if room.occupancy in _GFCI_OCCUPANCIES:
        return _GFCI_OCCUPANCIES[room.occupancy]
    # Every basement room, finished or not, since the 2020 NEC.
    if below_grade.get(room.storey) is True:
        return f"{NEC.GFCI_BASEMENT} (basement)"
    for kind, item, what in (("sink", NEC.GFCI_SINK, "a sink"),
                             ("bathing", NEC.GFCI_TUB_SHOWER, "a bathtub or shower")):
        reach = [poly for poly, k in sinks if k == kind
                 and not _pierces_a_wall(point, poly, barrier)]
        near = min((point.distance(poly) for poly in reach), default=None)
        if near is not None and near <= _SINK_REACH_M:
            return f"{item} (within 6' of {what} — {near / .3048:.1f}')"
    return None


def _pierces_a_wall(point: Any, sink: Any, barrier: Any) -> bool:
    """True when a cord run straight from receptacle to sink would go THROUGH a wall.

    ** 210.8(A)'s 6 ft is a CORD PATH, not a plan-frame straight line. ** NEC 210.8 is
    explicit: the distance "shall be measured as the shortest path the supply cord of an appliance
    connected to the receptacle would follow WITHOUT PIERCING a floor, wall, ceiling, or
    fixed barrier." A receptacle in a bedroom 5'-4" from a vanity on the far side of the
    bathroom wall was being written up for a sink it cannot reach with a cord at all.

    Doors, doorways and windows are deliberately NOT barriers: the printed 2026 list is floor,
    wall, ceiling and fixed barrier only (the opening clause left the code before 2026), so
    ``_wall_barrier`` punches every through opening out of its wall; a blind niche stays wall.

    The honest limit: when the straight line IS blocked, the real cord path is some longer
    way round, and this returns True rather than computing it. So the check can under-report
    a receptacle whose path around a doorway still comes in under 6 ft. Straight-line
    distance is only ever a LOWER bound on that path, so nothing here reports a distance it
    has not actually measured, which is the failure mode worth avoiding.
    """
    from shapely.geometry import LineString
    from shapely.ops import nearest_points

    if barrier is None or barrier.is_empty:
        return False
    # ``sink`` is a polygon, so the segment to test is the one to its NEAREST point — the
    # same point ``point.distance(sink)`` reports against.
    segment = LineString(nearest_points(point, sink))
    if not segment.intersects(barrier):
        return False
    inside = segment.intersection(barrier)
    return getattr(inside, "length", 0.0) > _PIERCE_TOL_M


def _wall_barrier(ctx: CheckContext) -> dict[str, Any]:
    """Per storey, the wall footprints a cord may not pass through, openings punched out."""
    from shapely.geometry import LineString
    from shapely.ops import substring

    from typehaus.resolve.overlay import union_all

    axes: dict[str, tuple[Any, float, str]] = {}
    solids: dict[str, list[Any]] = {}
    for wall in ctx.model.walls:
        if len(wall.axis) < 2:
            continue
        axis = LineString(wall.axis)
        if axis.length <= 0:
            continue
        axes[wall.tag] = (axis, wall.thickness_m, wall.storey)
        solids.setdefault(wall.storey, []).append(
            axis.buffer(wall.thickness_m / 2.0, cap_style=2))
    holes: dict[str, list[Any]] = {}
    for opening in ctx.model.openings:
        host = getattr(opening, "host_wall", None)
        entry = axes.get(host) if isinstance(host, str) else None
        if entry is None:
            continue
        axis, thickness, storey = entry
        centre = getattr(opening, "center_along_m", None)
        width = getattr(opening, "width_m", None)
        if centre is None or not width or getattr(opening, "depth_m", None) is not None:
            continue
        lo = max(0.0, centre - width / 2.0)
        hi = min(axis.length, centre + width / 2.0)
        if hi - lo <= 0:
            continue
        # Buffered by the full thickness, not half: the hole has to reach past both faces
        # or a sliver of wall is left standing in the doorway.
        holes.setdefault(storey, []).append(
            substring(axis, lo, hi).buffer(thickness, cap_style=2))
    out: dict[str, Any] = {}
    for storey, parts in solids.items():
        solid = union_all(parts)
        cut = holes.get(storey)
        if cut:
            solid = solid.difference(union_all(cut))
        out[storey] = solid
    return out


def _fixture_reach_kind(fixture_type: Any) -> str | None:
    """210.8(A)(9) "sink", (A)(11) "bathing" (tub or shower), or None (toilet, floor drain).

    A draining type nothing classifies counts as a sink, the conservative reading.
    """
    if getattr(fixture_type, "basin", None):
        return "sink"
    symbol = getattr(fixture_type, "plan_symbol", None) or ""
    if "tub" in symbol or "shower" in symbol or symbol.startswith("kohler-underscore"):
        return "bathing"
    if any(word in symbol for word in ("sink", "lavatory", "vanity")) or not symbol:
        return "sink"
    return None


def _sink_points(ctx: CheckContext) -> dict[str, list]:
    """Per storey, (footprint, kind) for every sink and bathtub/shower (``_fixture_reach_kind``).

    Keyed by storey for the same reason the room lookup is: the 6' sink reach is a
    reach across a countertop, not through a floor assembly.

    Polygons, not points: the sink reach is measured to the *outside edge* of the sink, which is
    what the resolved footprint gives directly — ``point.distance(polygon)`` is edge
    distance for free. A centroid point understates distance by up to half a fixture.
    """
    from shapely.geometry import Polygon

    kinds = {
        t.tag: _fixture_reach_kind(t) for t in ctx.plan.library.fixture_types
        if any(getattr(need, "value", need) == Service.DRAIN.value
               for need in getattr(t, "needs", ()))
    }
    out: dict[str, list] = {}
    for obj in ctx.model.canvas_objects:
        if obj.kind != "Fixture" or not kinds.get(obj.type_ref):
            continue
        if len(obj.footprint) < 3:
            continue
        out.setdefault(obj.storey, []).append((Polygon(obj.footprint), kinds[obj.type_ref]))
    return out


# NEC 210.12: AFCI protection on the 120V 15/20A branch circuits serving these rooms. The
# list is close to "everywhere people live" — the exclusions are bathrooms, garages, and
# unfinished basements, which is to say the places 210.8 already sends to GFCI instead.
_AFCI_OCCUPANCIES = frozenset({
    Occupancy.KITCHEN.value, Occupancy.LIVING.value, Occupancy.DINING.value,
    Occupancy.BEDROOM.value, Occupancy.HALLWAY.value, Occupancy.LAUNDRY.value,
    Occupancy.MEDIA.value, Occupancy.OFFICE.value, Occupancy.HOBBY.value, Occupancy.STORAGE.value,
    Occupancy.STUDY_CLOSET.value,  # "similar rooms or areas"
})

# ...and only on the circuits the section actually reaches. NEC 210.12 is written
# for "120-volt, single-phase, 15- and 20-ampere branch circuits", which is the ordinary
# lighting-and-receptacle wiring and nothing else: a 240V range, dryer, heat-pump or EV
# circuit is outside it, and so is a 120V circuit over 20A. Screening on the *rooms* alone
# wrote up eight breakers in this house that no AFCI device is even made for.
_AFCI_MAX_AMPS = 20


def _afci_applies(circuit) -> bool:
    """Is this circuit one of the 120V 15/20A branch circuits 210.12 covers?"""
    return (getattr(circuit, "poles", 1) == 1
            and getattr(circuit, "breaker_amps", 0) <= _AFCI_MAX_AMPS)


@check(Tier.CODE, "code.E3902_16_afci")
def afci_branch_circuits(ctx: CheckContext) -> list[Finding]:
    """NEC 210.12 — branch circuits serving habitable rooms are AFCI-protected.

    Evaluated per *circuit*, not per outlet, because that is where the protection lives: a
    single breaker covers every device on the run, so one circuit reaching one bedroom puts
    the whole circuit in scope. That also makes the finding actionable — it names the
    breaker to change, not the eleven receptacles downstream of it.

    Two screens, both necessary: the circuit must reach a room on the section's list *and*
    be one of the 120V 15/20A branch circuits the section is written for (``_afci_applies``).
    A 2-pole range or heat-pump circuit lands in a living room like every other circuit does
    and is not what 210.12 is about.
    """
    from shapely.geometry import Point

    cid, code = "code.E3902_16_afci", cite(NEC.AFCI_DWELLING)
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    if not circuits:
        return [by_result(cid, Result.UNKNOWN, "the plan states no circuits", (), code)]

    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append((room, axis_polygon(room)))
    by_tag = {room.tag: room for room in ctx.model.rooms}

    # Which rooms each circuit reaches, via every consumer that names it.
    served: dict[str, set[str]] = {}
    unplaced: dict[str, set[str]] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            circuit_tag = getattr(element, "circuit", None)
            if not circuit_tag or circuit_tag not in circuits:
                continue
            xy = placed_xy(ctx.model, element)
            if xy is None:
                continue
            room = _room_of(ctx.model, element, Point(xy), rooms.get(storey.tag, ()), by_tag)
            if room is None:
                # A hosted face that looks into no room is outdoors: out of 210.12's scope.
                if _host_of(ctx.model, element) is None:
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
                out.append(by_result(cid, Result.UNKNOWN,
                                     f"{tag} feeds {', '.join(sorted(unplaced[tag]))}, none of "
                                     "which resolves to a room, so whether "
                                     f"{NEC.AFCI_DWELLING} reaches it cannot be decided",
                                     (tag,), code))
            continue
        habitable = occupancies & _AFCI_OCCUPANCIES
        if not habitable:
            continue
        where = ", ".join(sorted(habitable))
        if getattr(circuit, "afci", False):
            out.append(by_result(cid, Result.PASS, f"{tag} is AFCI-protected ({where})",
                                 (), code))
        else:
            out.append(by_result(cid, Result.FAIL,
                                 f"{tag} serves {where} space and is not AFCI-protected",
                                 (tag,), code,
                                 f"set afci=True on {tag} in the circuit schedule"))
    if not out:
        return [by_result(cid, Result.PASS,
                          f"no circuit serves a room {NEC.AFCI_DWELLING} covers", (), code)]
    return out
