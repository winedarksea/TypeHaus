"""Electrical checks — symbols-only coverage (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from typehaus.checks._authoring import advisory, passed as _pass, unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.intervals import merge as _merge_intervals

_HABITABLE = {Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.KITCHEN, Occupancy.DINING,
             Occupancy.OFFICE}


# WARN severity + FAIL result, deliberately: the permit integrity gate only blocks on ERROR
# severity, and this finding is advisory, not a hard blocker.
def _warn_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return advisory(cid, msg, tags, Result.FAIL)


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


_RECEPTACLE_KINDS = {"receptacle", "gfci"}  # the 125V 15/20A devices 210.52 counts
# A 240V kind still counts if its *type* offers a 125V port — the combination 5-20R/6-20R
# device is one box with two receptacles in it, and the 5-20R half is a 210.52 receptacle
# like any other. (This is the DeviceKind precedent: the kind stays flat, the type
# differentiates.)
_COMBINATION_RECEPTACLE_KIND = "receptacle_240"
_MAX_TO_RECEPTACLE_M = 6 * 0.3048  # no point along the wall line > 6' from a receptacle
_MIN_WALL_SPACE_M = 2 * 0.3048  # wall spaces under 2' are exempt
_NEAR_WALL_M = 0.5  # how close to the room boundary a device must sit to serve it
# How much floor may survive between a floor opening and the wall face behind it and still
# count as standing room. 12" of ledge along a stair well is not somewhere you plug a lamp in.
_FLOOR_OPENING_LEDGE_M = 12 * 0.0254
# How far a cabinet's base may sit above the floor and still meet the floor line: a toe-kick
# tolerance, which an upper cabinet is nowhere near.
_FIXED_CABINET_FLOOR_CONTACT_M = 6 * 0.0254


def _counts_as_a_125v_receptacle(ctx: CheckContext, device) -> bool:
    if device.kind.value in _RECEPTACLE_KINDS:
        return True
    if device.kind.value != _COMBINATION_RECEPTACLE_KIND or device.type_ref is None:
        return False
    device_type = next((t for t in ctx.plan.library.electrical_device_types
                        if t.tag == device.type_ref), None)
    return device_type is not None and any(
        port.service.value == "power_120" for port in device_type.ports)


def _perimeter_position(ring: list, point: tuple) -> tuple[float, float]:
    """(arc-length coordinate of the nearest boundary point, distance to the boundary)."""
    best_s, best_d = 0.0, float("inf")
    s = 0.0
    for index in range(len(ring)):
        (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % len(ring)]
        ex, ey = x1 - x0, y1 - y0
        length = (ex * ex + ey * ey) ** 0.5
        if length < 1e-9:
            continue
        t = max(0.0, min(1.0, ((point[0] - x0) * ex + (point[1] - y0) * ey) / (length * length)))
        px, py = x0 + ex * t, y0 + ey * t
        d = ((point[0] - px) ** 2 + (point[1] - py) ** 2) ** 0.5
        if d < best_d:
            best_s, best_d = s + t * length, d
        s += length
    return best_s, best_d


def _point_at(ring: list, s: float) -> tuple[float, float]:
    total = 0.0
    for index in range(len(ring)):
        (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % len(ring)]
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if total + length >= s or index == len(ring) - 1:
            t = 0.0 if length < 1e-9 else (s - total) / length
            return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
        total += length
    return ring[0]


def _door_intervals(ctx: CheckContext, ring: list, storey_tag: str) -> list[tuple[float, float]]:
    """Perimeter intervals occupied by door openings on walls bounding this room."""
    walls = {w.tag: w for w in ctx.model.walls if w.storey == storey_tag}
    intervals = []
    for opening in ctx.model.openings:
        if not opening.is_door:
            continue
        host = walls.get(opening.host_wall)
        if host is None:
            continue
        center = opening_center(host, opening) or host.axis[0]
        s, d = _perimeter_position(ring, center)
        if d <= _NEAR_WALL_M:
            half = opening.width_m / 2.0
            intervals.append((s - half, s + half))
    return intervals


def _floor_opening_intervals(ctx: CheckContext, ring: list,
                             storey_tag: str) -> list[tuple[float, float]]:
    """Perimeter intervals where the boundary fronts a floor opening rather than floor.

    210.52(A)(2)'s subject is *wall space*, and its yardstick is "measured horizontally along
    the floor line". Where a stair well runs up against the wall there is no floor line to
    measure along — the boundary looks like wall on plan, but standing in front of it means
    standing over the drop, and the only way to satisfy the 6' rule there is to hang a
    receptacle above a stairwell. So a well breaks the measurement the same way a doorway
    does; the spaces either side of it are still measured in full.

    ``_FLOOR_OPENING_LEDGE_M`` is how much floor may survive between the well edge and the
    wall face and still count as somewhere to stand. It is deliberately small: a foot of
    concrete ledge along a 9' drop is not a place a lamp gets plugged in.
    """
    from shapely.geometry import LineString, Point, Polygon

    boundary = LineString(list(ring) + [ring[0]])
    intervals: list[tuple[float, float]] = []
    for element in ctx.plan.storey_elements(storey_tag):
        # A chase is boxed and decked over — there is floor on it, so it breaks nothing. Only
        # an opening you could step into takes the floor line away.
        if element.element_kind != "FloorOpening" or element.purpose.value == "chase":
            continue
        well = Polygon([point.xy_m for point in element.outline])
        if not well.is_valid or well.is_empty:
            continue
        fronting = boundary.intersection(well.buffer(_FLOOR_OPENING_LEDGE_M))
        for piece in getattr(fronting, "geoms", (fronting,)):
            if piece.is_empty or piece.length <= 0:
                continue
            offsets = [boundary.project(Point(coord)) for coord in piece.coords]
            intervals.append((min(offsets), max(offsets)))
    return intervals


def _fixed_cabinet_intervals(ctx: CheckContext, ring: list,
                             storey_tag: str) -> list[tuple[float, float]]:
    """Perimeter intervals occupied by fixed cabinets that have no work surface.

    210.52(A)(2)(1) names them alongside doorways and fireplaces as the things wall space is
    unbroken by, and for the same reason: a run of floor-to-ceiling pantry has no floor line
    in front of it and nowhere to put a lamp, so requiring a receptacle within 6' of its
    middle would put one behind a cabinet. A base run is the opposite case — its countertop
    is exactly what the receptacle is for — which is why the type has to say which it is
    (``FurnitureType.work_surface``) rather than the check guessing from height.
    """
    from shapely.geometry import LineString, Point, Polygon

    boundary = LineString(list(ring) + [ring[0]])
    floor_z = next((s.elevation.meters for s in ctx.plan.storeys if s.tag == storey_tag), 0.0)
    types = {t.tag: t for t in ctx.plan.library.furniture_types}
    intervals: list[tuple[float, float]] = []
    for item in ctx.model.canvas_objects:
        if item.storey != storey_tag or item.type_ref is None:
            continue
        item_type = types.get(item.type_ref)
        if item_type is None or item_type.work_surface is not False:
            continue
        # An upper cabinet is also a fixed cabinet with no counter, but 210.52(A)(2) measures
        # along the floor line and an upper does not reach it.
        if item.z_m - floor_z > _FIXED_CABINET_FLOOR_CONTACT_M:
            continue
        carcass = Polygon(item.footprint)
        if not carcass.is_valid or carcass.is_empty:
            continue
        if carcass.distance(boundary) > _NEAR_WALL_M:
            continue
        # Projected rather than buffered: a buffer wide enough to reach the boundary (which
        # is the room polygon, not the drywall face — see _NEAR_WALL_M) would also run that
        # far past each end of the carcass and swallow the wall either side of it.
        offsets = [boundary.project(Point(coord)) for coord in carcass.exterior.coords]
        intervals.append((min(offsets), max(offsets)))
    return intervals


def _merged_intervals(intervals: list[tuple[float, float]],
                      perimeter: float) -> list[tuple[float, float]]:
    """Clamp the breaks to the ring, sort them, and union any that overlap.

    The wall-space builder pairs each break's end with the next break's start, which only
    describes wall space while the breaks are disjoint: a doorway opening straight onto a
    stair well would otherwise manufacture a negative-length "space" between the two.
    """
    return _merge_intervals([(max(0.0, a), min(perimeter, b)) for a, b in intervals])


def _coverage_gaps(space: tuple[float, float], positions: list[float]) -> list[float]:
    """Perimeter coordinates of points in a linear wall space > 6' from any receptacle."""
    a, b = space
    inside = sorted(p for p in positions if a - 0.05 <= p <= b + 0.05)
    if not inside:
        # A qualifying wall space with no receptacle at all always fails: 210.52(A)(1)
        # counts only receptacles within the space (doorways break the measurement).
        return [(a + b) / 2.0]
    gaps = []
    if inside[0] - a > _MAX_TO_RECEPTACLE_M:
        gaps.append(a)
    for left, right in zip(inside, inside[1:]):
        if right - left > 2 * _MAX_TO_RECEPTACLE_M:
            gaps.append((left + right) / 2.0)
    if b - inside[-1] > _MAX_TO_RECEPTACLE_M:
        gaps.append(b)
    return gaps


@check(Tier.ADVISORY, "electrical.receptacle_spacing")
def receptacle_spacing(ctx: CheckContext) -> list[Finding]:
    """NEC 210.52(A)-style 6' rule along every habitable room's wall line (advisory).

    Geometry-based, unlike ``room_lighting``'s tag matching: the room's resolved
    ``clear_face`` ring is unrolled into an arc-length coordinate (so corners measure
    correctly), doorways, floor openings and counterless fixed cabinets break it into wall
    spaces, spaces under 2' are exempt, and every remaining point must be within 6' of a
    receptacle projected onto the boundary.
    The kitchen-counter rule (210.52(C)) is not evaluated — counters are casework, not
    resolved geometry — and reports UNKNOWN so the gap stays visible.
    """
    cid = "electrical.receptacle_spacing"
    devices_by_storey: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        devices_by_storey[storey.tag] = [
            element for element in ctx.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"]
    if not any(devices_by_storey.values()):
        return [_unknown(cid, "electrical not modeled")]

    habitable = {occupancy.value for occupancy in _HABITABLE}
    out: list[Finding] = []
    for room in ctx.model.rooms:
        if room.occupancy not in habitable:
            continue
        ring = [tuple(point) for point in room.clear_face]
        if len(ring) < 3:
            continue
        perimeter = sum(
            ((ring[(i + 1) % len(ring)][0] - ring[i][0]) ** 2
             + (ring[(i + 1) % len(ring)][1] - ring[i][1]) ** 2) ** 0.5
            for i in range(len(ring)))
        positions = []
        for device in devices_by_storey.get(room.storey, []):
            if not _counts_as_a_125v_receptacle(ctx, device):
                continue
            s, d = _perimeter_position(ring, device.position.xy_m)
            if d <= _NEAR_WALL_M:
                positions.append(s)
        breaks = (_door_intervals(ctx, ring, room.storey)
                  + _floor_opening_intervals(ctx, ring, room.storey)
                  + _fixed_cabinet_intervals(ctx, ring, room.storey))
        doors = _merged_intervals(breaks, perimeter)
        # Wall spaces: the perimeter minus the spans that break it. A room with no break at
        # all is one circular space, where coverage means the largest receptacle-to-receptacle
        # arc.
        gaps: list[float] = []
        if not doors:
            if not positions:
                gaps.append(0.0)
            else:
                ordered = sorted(positions)
                for left, right in zip(ordered, ordered[1:] + [ordered[0] + perimeter]):
                    if right - left > 2 * _MAX_TO_RECEPTACLE_M:
                        gaps.append(((left + right) / 2.0) % perimeter)
        else:
            spaces = []
            for index, (a, b) in enumerate(doors):
                next_a = doors[index + 1][0] if index + 1 < len(doors) else doors[0][0] + perimeter
                if next_a - b >= _MIN_WALL_SPACE_M:
                    spaces.append((b, next_a))
            for space in spaces:
                wrapped = [p + perimeter if p < space[0] - 0.05 else p for p in positions]
                gaps.extend(g % perimeter for g in _coverage_gaps(space, wrapped))
        if gaps:
            worst = _point_at(ring, gaps[0])
            out.append(_warn_fail(
                cid, f"room {room.tag}: wall space > 6' from a receptacle near "
                     f"({worst[0] / 0.3048:.1f}', {worst[1] / 0.3048:.1f}') "
                     f"[{len(gaps)} gap(s)]", (room.tag,)))
        else:
            out.append(_pass(cid, f"room {room.tag} meets the 6' receptacle rule",
                             (room.tag,)))
    out.append(_unknown(cid, "kitchen counter rule (210.52(C)) not evaluated — counter "
                             "casework is not resolved geometry; counter receptacles are "
                             "authored at 42\" in plan/mep.py"))
    return out


# How far past an island's carcass a receptacle may sit and still be serving it: an end-
# or side-mounted device projects an inch or two off the face, and anything much farther
# out is a wall receptacle that happens to be nearby. Kept well under _NEAR_WALL_M so a
# freestanding island (> _NEAR_WALL_M from every boundary) can never borrow one.
_ISLAND_RECEPTACLE_MARGIN_M = 12 * 0.0254


@check(Tier.ADVISORY, "electrical.island_receptacle")
def island_receptacle(ctx: CheckContext) -> list[Finding]:
    """Every freestanding work-surface island has a receptacle at its footprint.

    2023 NEC 210.52(C)(2) stopped *requiring* an island or peninsular countertop
    receptacle, but where none is installed it requires provisions for adding one, and
    210.52(C)(3) confines any receptacle that serves the countertop to on/above/in the
    counter surface. An island with nothing at all — no receptacle, no provision — is the
    thing worth flagging: the appliance ends up on an extension cord across the aisle.

    Population: ``FurnitureType.work_surface is True`` (the same type attribute
    ``_fixed_cabinet_intervals`` reads for the opposite purpose), sitting on the floor,
    standing free of every room boundary by more than ``_NEAR_WALL_M`` — a base run
    against a wall is the wall receptacles' problem and ``receptacle_spacing``'s beat. A
    peninsula (attached to a wall at one end) reads as near-wall here and is not graded.
    """
    from shapely.geometry import LineString, Point, Polygon

    cid = "electrical.island_receptacle"
    furniture_types = {t.tag: t for t in ctx.plan.library.furniture_types}
    if not furniture_types:
        return [_unknown(cid, "no furniture types in the library")]

    boundaries_by_storey: dict[str, list] = {}
    for room in ctx.model.rooms:
        ring = [tuple(point) for point in room.clear_face]
        if len(ring) >= 3:
            boundaries_by_storey.setdefault(room.storey, []).append(
                LineString(ring + [ring[0]]))
    receptacles_by_storey: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        receptacles_by_storey[storey.tag] = [
            element for element in ctx.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"
            and _counts_as_a_125v_receptacle(ctx, element)]

    floor_z = {s.tag: s.elevation.meters for s in ctx.plan.storeys}
    out: list[Finding] = []
    islands = 0
    for item in ctx.model.canvas_objects:
        item_type = furniture_types.get(item.type_ref or "")
        if item_type is None or item_type.work_surface is not True:
            continue
        if item.z_m - floor_z.get(item.storey, 0.0) > _FIXED_CABINET_FLOOR_CONTACT_M:
            continue
        carcass = Polygon(item.footprint)
        if not carcass.is_valid or carcass.is_empty:
            continue
        near_wall = any(carcass.distance(boundary) <= _NEAR_WALL_M
                        for boundary in boundaries_by_storey.get(item.storey, []))
        if near_wall:
            continue
        islands += 1
        reach = carcass.buffer(_ISLAND_RECEPTACLE_MARGIN_M)
        served = any(reach.contains(Point(device.position.xy_m))
                     for device in receptacles_by_storey.get(item.storey, []))
        if served:
            out.append(_pass(cid, f"island {item.tag} has a receptacle at its footprint",
                             (item.tag,)))
        else:
            out.append(_warn_fail(
                cid, f"island {item.tag} has no receptacle within its footprint — "
                     f"NEC 210.52(C)(2) wants one (or provisions for one), and "
                     f"210.52(C)(3) wants any that serves the countertop on/above/in "
                     f"the counter surface", (item.tag,)))
    if not islands:
        return [_unknown(cid, "no freestanding work-surface casework modeled")]
    return out


@check(Tier.ADVISORY, "electrical.circuit_refs")
def circuit_refs(ctx: CheckContext) -> list[Finding]:
    """Every ``circuit`` reference resolves, every panel_ref is a panel, poles match ports."""
    cid = "electrical.circuit_refs"
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    if not circuits:
        return [_unknown(cid, "no circuits authored")]

    # Alarms are consumers too: R314.4 puts them on a branch circuit, so a detector naming a
    # circuit that does not exist is the same defect as a receptacle doing it.
    consumers = [element for element in ctx.plan.all_elements()
                 if element.element_kind in ("ElectricalDevice", "Equipment", "Register",
                                             "Alarm")]
    panels = {element.tag for element in consumers
              if element.element_kind == "ElectricalDevice" and element.kind.value == "panel"}
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}

    out: list[Finding] = []
    for circuit in circuits.values():
        if circuit.panel_ref not in panels:
            out.append(_warn_fail(cid, f"circuit {circuit.tag} names missing panel "
                                       f"{circuit.panel_ref}", (circuit.tag,)))
    _required = {1: "power_120", 2: "power_240"}
    for element in consumers:
        ref = element.circuit
        if not ref:
            continue
        circuit = circuits.get(ref)
        if circuit is None:
            out.append(_warn_fail(cid, f"{element.tag} references unknown circuit {ref}",
                                  (element.tag,)))
            continue
        # A 2-pole circuit's device must offer a POWER_240 port (and 1-pole a POWER_120);
        # multi-port types (e.g. a two-gang 5-20R/6-20R) satisfy either.
        product_type = types.get(getattr(element, "type_ref", None))
        required = _required.get(circuit.poles)
        if (element.element_kind == "ElectricalDevice" and product_type is not None
                and product_type.ports and required is not None
                and required not in {port.service.value for port in product_type.ports}):
            out.append(_warn_fail(
                cid, f"{element.tag} on {circuit.poles}-pole circuit {ref} has no "
                     f"{required} port", (element.tag, ref),
            ))
    if not out:
        out.append(_pass(cid, f"{len(circuits)} circuits reconcile with their devices"))
    return out


@check(Tier.ADVISORY, "electrical.panel_spaces")
def panel_spaces(ctx: CheckContext) -> list[Finding]:
    """Breaker spaces required per panel vs. the enclosure, plus slot-map integrity.

    Spaces required = Σ poles over the panel's circuits. Where circuits author ``slot``
    positions, the physical map is checked too: a 2-pole breaker occupies ``slot`` and
    ``slot + 2`` (same column — odd left, even right), no two breakers may share a
    position, and no position may sit past the enclosure's ``spaces``.
    """
    cid = "electrical.panel_spaces"
    circuits = list(ctx.plan.library.circuits)
    if not circuits:
        return [_unknown(cid, "no circuits authored")]

    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    panels = {element.tag: element for element in ctx.plan.all_elements()
              if element.element_kind == "ElectricalDevice" and element.kind.value == "panel"}

    by_panel: dict[str, list] = {}
    for circuit in circuits:
        by_panel.setdefault(circuit.panel_ref, []).append(circuit)

    out: list[Finding] = []
    for panel_ref, group in sorted(by_panel.items()):
        required = sum(circuit.poles for circuit in group)
        panel = panels.get(panel_ref)
        product_type = types.get(getattr(panel, "type_ref", None)) if panel else None
        spaces = getattr(product_type, "spaces", None)
        if spaces is None:
            out.append(_unknown(
                cid, f"panel {panel_ref} needs {required} spaces but its type declares "
                     f"no ``spaces``", (panel_ref,)))
        elif required > spaces:
            out.append(_warn_fail(
                cid, f"panel {panel_ref} needs {required} breaker spaces but the "
                     f"enclosure has {spaces} — swap to a larger panel or shed circuits",
                (panel_ref,)))
        else:
            out.append(_pass(
                cid, f"panel {panel_ref}: {required} spaces required fits the "
                     f"{spaces}-space enclosure", (panel_ref,)))
        # Slot-map integrity — only over circuits that author a slot.
        occupied: dict[int, str] = {}
        for circuit in group:
            if circuit.slot is None:
                continue
            positions = (circuit.slot,) if circuit.poles == 1 else (circuit.slot,
                                                                    circuit.slot + 2)
            for position in positions:
                if position in occupied:
                    out.append(_warn_fail(
                        cid, f"panel {panel_ref}: slot {position} assigned to both "
                             f"{occupied[position]} and {circuit.tag}",
                        (occupied[position], circuit.tag)))
                else:
                    occupied[position] = circuit.tag
            if spaces is not None and positions[-1] > spaces:
                out.append(_warn_fail(
                    cid, f"panel {panel_ref}: {circuit.tag} occupies slot "
                         f"{positions[-1]}, past the {spaces}-space enclosure",
                    (circuit.tag,)))
    return out


@check(Tier.ADVISORY, "electrical.service_load")
def service_load(ctx: CheckContext) -> list[Finding]:
    """The 220.82 demand estimate vs. the authored service, with load management credited.

    A ``LoadManagement`` (EMS per NEC 625.42, interlock, ...) caps what its managed
    circuits can draw together, so the group's connected excess over
    ``max_simultaneous_va`` comes off the demand — *in the 220.82 term the load was counted
    in*, which ``takeoff/electrical.py`` now does rather than subtracting it flat off the
    total. With none authored this reports the honest state: the levers are an EMS, an
    interlock, or a bigger service.
    """
    from typehaus.takeoff.electrical import service_load_summary

    cid = "electrical.service_load"
    if not ctx.plan.library.circuits:
        return [_unknown(cid, "no circuits authored")]

    summary = service_load_summary(ctx.model)
    demand_va = float(summary["demand_va"])  # type: ignore[arg-type]
    service_amps = float(summary["service_amps"])  # type: ignore[arg-type]
    credit_va = float(summary["load_management_credit_va"])  # type: ignore[arg-type]

    out: list[Finding] = []
    for credit in summary["load_management"]:  # type: ignore[union-attr]
        tag = str(credit["tag"])
        missing = list(credit["missing_circuits"])  # type: ignore[arg-type]
        if missing:
            out.append(_warn_fail(
                cid, f"{tag} manages unknown circuits: {', '.join(sorted(missing))}", (tag,)))
            continue
        if float(credit["excess_va"]):  # type: ignore[arg-type]
            managed_tags = ", ".join(credit["managed_circuits"])  # type: ignore[arg-type]
            out.append(_pass(
                cid, f"{tag} ({credit['strategy']}) caps {managed_tags} at "
                     f"{float(credit['cap_va']):.0f} VA — "
                     f"{float(credit['excess_va']):.0f} VA of connected load never reaches "
                     "the service", (tag,)))

    managed_amps = demand_va / 240.0
    where = ("" if summary["service_amps_source"] == "default"
             else f" ({summary['service_amps_source']})")
    if managed_amps <= service_amps:
        out.append(_pass(
            cid, f"demand {managed_amps:.1f}A (after a {credit_va:.0f} VA load-management "
                 f"credit) fits the {service_amps:.0f}A service{where}"))
    else:
        out.append(_warn_fail(
            cid, f"estimated demand {managed_amps:.1f}A exceeds the {service_amps:.0f}A "
                 f"service{where} — options: an EMS per NEC 625.42 on the EV circuits, an "
                 f"interlock between competing loads, or a service upgrade", ()))
    return out
