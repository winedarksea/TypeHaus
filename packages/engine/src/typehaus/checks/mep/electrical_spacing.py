"""NEC 210.52(A) wall-space receptacle spacing; (C) counters via ``electrical_counters``."""

from __future__ import annotations

from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.electrical import _HABITABLE, _counts_toward_210_52, _warn_fail
from typehaus.checks.mep.electrical_code import _room_of
from typehaus.checks.mep.electrical_counters import counter_findings
from typehaus.checks.mep.electrical_wall_space import (
    definite_coverage_gaps,
    facing_well_intervals,
    floor_line_ring,
    uncertain_wall_space,
    uncovered_wall_intervals,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC
from typehaus.resolve import room_perimeter
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_NEAR_WALL_M = room_perimeter.NEAR_WALL_M  # how close a device must sit to serve the wall
_FLOOR_RECEPTACLE_WALL_REACH_M = 18 * 0.0254  # NEC 210.52(A)(3)
_RECEPTACLE_DISTANCE_TOLERANCE_M = 1e-9  # Include exact limits after polygon projection.
# How much floor may survive between a floor opening and the wall face behind it and still
# count as standing room. 12" of ledge along a stair well is not somewhere you plug a lamp in.
_FLOOR_OPENING_LEDGE_M = 12 * 0.0254
# How far a cabinet's base may sit above the floor and still meet the floor line: a toe-kick
# tolerance, which an upper cabinet is nowhere near.
_FIXED_CABINET_FLOOR_CONTACT_M = room_perimeter.FLOOR_CONTACT_M

_perimeter_position = room_perimeter.perimeter_position
_point_at = room_perimeter.point_at
_cyclic_span = room_perimeter.cyclic_span
_merged_intervals = room_perimeter.merged_intervals


def _door_intervals(ctx: CheckContext, ring: list, storey_tag: str) -> list[tuple[float, float]]:
    """Perimeter intervals occupied by door openings on walls bounding this room."""
    return room_perimeter.door_intervals(ctx.model, ring, storey_tag)


def _floor_opening_intervals(ctx: CheckContext, ring: list,
                             storey_tag: str) -> list[tuple[float, float]]:
    """Perimeter intervals where the boundary fronts a floor opening rather than floor.

    210.52(A)(2)'s subject is *wall space*, measured "horizontally along the floor line".
    Where a stair well runs up against the wall there is no floor line to measure along, and
    the only way to satisfy the 6' rule there is to hang a receptacle above a stairwell. So a
    well breaks the measurement the same way a doorway does. ``_FLOOR_OPENING_LEDGE_M`` is
    deliberately small: a foot of ledge along a 9' drop is not where a lamp gets plugged in.
    """
    return facing_well_intervals(ctx.plan, ring, storey_tag, _FLOOR_OPENING_LEDGE_M)


def _fixed_cabinet_intervals(ctx: CheckContext, ring: list,
                             storey_tag: str) -> list[tuple[float, float]]:
    """Perimeter intervals occupied by fixed cabinets, with or without a work surface.

    2026 210.52(A)(2)(1) breaks wall space at every fixed cabinet (before, only counterless
    ones); a countertop is 210.52(C)'s. Fixed cabinetry answers ``work_surface`` at all
    (``None`` is a bookcase); an appliance set into the run (dishwasher, range) is part of it.
    """
    return room_perimeter.fixed_cabinet_intervals(
        ctx.model, ctx.plan, ring, storey_tag, lambda t: t.work_surface is not None,
        run_appliances=True)


# The engine's symbol for a fireplace: 210.52(A)(2) names fireplaces among the breaks.
_FIREPLACE_SYMBOLS = frozenset({"fireplace-insert"})


def _is_fireplace(product) -> bool:
    representation = getattr(product, "model_representation", None)
    return bool({getattr(product, "plan_symbol", None),
                 getattr(representation, "symbol", None)} & _FIREPLACE_SYMBOLS)


def _stationary_intervals(ctx: CheckContext, ring: list, room) -> list[tuple[float, float]]:
    """Perimeter intervals held by stationary appliances and fireplaces (210.52(A)(2)).

    An appliance or piece of equipment breaks the wall line where it stands on the floor
    within ``_NEAR_WALL_M`` of it, in this room (its ``room``, else its centroid); a
    fireplace breaks it at any height, since the code names it outright.
    """
    from shapely.geometry import LineString, Point, Polygon

    lib = ctx.plan.library
    types = {t.tag: t for t in (*lib.appliance_types, *lib.equipment_types)}
    boundary = LineString(list(ring) + [ring[0]])
    area = Polygon(ring)
    floor_z = next((s.elevation.meters for s in ctx.plan.storeys if s.tag == room.storey), 0.0)
    out: list[tuple[float, float]] = []
    for obj in ctx.model.canvas_objects:
        if (obj.kind not in ("Appliance", "Equipment") or obj.storey != room.storey
                or len(obj.footprint) < 3):
            continue
        body = Polygon(obj.footprint)
        if not body.is_valid or body.is_empty:
            continue
        mine = obj.room == room.tag if obj.room else area.contains(body.centroid)
        fireplace = _is_fireplace(types.get(obj.type_ref or ""))
        if (not mine or body.distance(boundary) > _NEAR_WALL_M
                or (not fireplace and obj.z_m - floor_z > _FIXED_CABINET_FLOOR_CONTACT_M)):
            continue
        offsets = sorted(boundary.project(Point(c)) for c in body.exterior.coords)
        out.extend(_cyclic_span(offsets, boundary.length))
    return out


@check(Tier.ADVISORY, "electrical.receptacle_spacing")
def receptacle_spacing(ctx: CheckContext) -> list[Finding]:
    """NEC 210.52(A)-style 6' rule along every habitable room's wall line (advisory).

    Geometry-based, unlike ``room_lighting``'s tag matching: the room's resolved
    ``clear_face`` ring is unrolled into an arc-length coordinate (so corners measure
    correctly), doorways, floor openings and fixed cabinets break it into wall
    spaces, spaces under 2' are exempt, and every remaining point must be within 6' of a
    receptacle projected onto the boundary. Roof-to-floor plate boundaries are evaluated
    both as wall space and as breaks, with their interpretation explicitly UNKNOWN.
    Kitchen counters (210.52(C)) are graded off the resolved countertops by
    ``electrical_counters.counter_findings``.
    """
    from shapely.geometry import Point

    cid = "electrical.receptacle_spacing"
    devices_by_storey: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        devices_by_storey[storey.tag] = [
            element for element in ctx.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"]
    if not any(devices_by_storey.values()):
        return [_unknown(cid, "electrical not modeled")]

    habitable = {occupancy.value for occupancy in _HABITABLE}
    storey_rooms: dict[str, list] = {}
    for other in ctx.model.rooms:
        if len(axis_ring(other)) >= 3:
            storey_rooms.setdefault(other.storey, []).append((other, axis_polygon(other)))
    by_tag = {other.tag: other for other in ctx.model.rooms}
    out: list[Finding] = []
    for room in ctx.model.rooms:
        if room.occupancy not in habitable:
            continue
        ring = floor_line_ring(ctx.model, room)
        if len(ring) < 3:
            out.append(_unknown(cid, f"room {room.tag}: boundary geometry is unresolved",
                                (room.tag,)))
            continue
        perimeter = room_perimeter.perimeter_length(ring)
        positions = []
        for device in devices_by_storey.get(room.storey, []):
            if not _counts_toward_210_52(ctx, device):
                continue
            xy = placed_xy(ctx.model, device)
            # A receptacle on the wall's other face serves the room behind it, not this one.
            owner = _room_of(ctx.model, device, Point(xy), storey_rooms.get(room.storey, ()),
                             by_tag)
            if owner is None or owner.tag != room.tag:
                continue
            s, d = _perimeter_position(ring, xy)
            floor_mounted = device.mount is not None and device.mount.kind.value == "floor"
            reach = _FLOOR_RECEPTACLE_WALL_REACH_M if floor_mounted else _NEAR_WALL_M
            if d <= reach + _RECEPTACLE_DISTANCE_TOLERANCE_M:
                positions.append(s)
        breaks = (_door_intervals(ctx, ring, room.storey)
                  + _floor_opening_intervals(ctx, ring, room.storey)
                  + _fixed_cabinet_intervals(ctx, ring, room.storey)
                  + _stationary_intervals(ctx, ring, room))
        uncertainty = uncertain_wall_space(ctx.model, room, ring)
        gaps = definite_coverage_gaps(perimeter, positions, breaks, uncertainty.intervals)
        if gaps:
            worst = _point_at(ring, sum(gaps[0]) / 2.0)
            out.append(_warn_fail(
                cid, f"room {room.tag}: wall space > 6' from a receptacle near "
                     f"({worst[0] / 0.3048:.1f}', {worst[1] / 0.3048:.1f}') "
                     f"[{len(gaps)} gap(s)]", (room.tag,)))
        included = (uncovered_wall_intervals(perimeter, positions, breaks)
                    if uncertainty.intervals else [])
        hosts = ", ".join(uncertainty.hosts) or "unresolved boundary"
        if uncertainty.intervals and not included and not gaps:
            out.append(_pass(cid, f"room {room.tag} meets the 6' receptacle rule whether or "
                                  f"not {hosts} counts as wall space", (room.tag,)))
        elif uncertainty.intervals:
            reasons = "; ".join(uncertainty.reasons)
            open_ft = sum(hi - lo for lo, hi in included) / 0.3048
            out.append(_unknown(
                cid, f"room {room.tag}: {reasons} ({hosts}); counted as wall space, "
                     f"{open_ft:.1f} ft of the room's wall line is more than 6' from a "
                     "receptacle; not counted,"
                     + (" gaps remain" if gaps else " the room passes")
                     + f" — whether {NEC.WALL_SPACE} wall space includes it is unresolved",
                (room.tag, *uncertainty.hosts),
                fix="a floor receptacle within 18\" of it (210.52(A)(3)) settles both readings"))
        elif not gaps:
            out.append(_pass(cid, f"room {room.tag} meets the 6' receptacle rule",
                             (room.tag,)))
    out.extend(counter_findings(ctx, cid))
    return out
