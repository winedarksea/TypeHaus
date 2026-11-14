"""NEC 210.52(A) wall-space receptacle spacing; (C) counters via ``electrical_counters``."""

from __future__ import annotations

from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.electrical import _HABITABLE, _counts_toward_210_52, _warn_fail
from typehaus.checks.mep.electrical_counters import counter_findings
from typehaus.checks.mep.electrical_wall_space import (
    definite_coverage_gaps,
    facing_well_intervals,
    floor_line_ring,
    uncertain_wall_space,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve import room_perimeter
from typehaus.resolve.placeables import placed_xy

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
            s, d = _perimeter_position(ring, placed_xy(ctx.model, device))
            floor_mounted = device.mount is not None and device.mount.kind.value == "floor"
            reach = _FLOOR_RECEPTACLE_WALL_REACH_M if floor_mounted else _NEAR_WALL_M
            if d <= reach + _RECEPTACLE_DISTANCE_TOLERANCE_M:
                positions.append(s)
        breaks = (_door_intervals(ctx, ring, room.storey)
                  + _floor_opening_intervals(ctx, ring, room.storey)
                  + _fixed_cabinet_intervals(ctx, ring, room.storey))
        uncertainty = uncertain_wall_space(ctx.model, room, ring)
        gaps = definite_coverage_gaps(perimeter, positions, breaks, uncertainty.intervals)
        if gaps:
            worst = _point_at(ring, sum(gaps[0]) / 2.0)
            out.append(_warn_fail(
                cid, f"room {room.tag}: wall space > 6' from a receptacle near "
                     f"({worst[0] / 0.3048:.1f}', {worst[1] / 0.3048:.1f}') "
                     f"[{len(gaps)} gap(s)]", (room.tag,)))
        if uncertainty.intervals:
            hosts = ", ".join(uncertainty.hosts) or "unresolved boundary"
            reasons = "; ".join(uncertainty.reasons)
            out.append(_unknown(
                cid, f"room {room.tag}: {reasons} ({hosts}); "
                     "spacing evaluated with these spans both included and excluded; "
                     "complete compliance is unresolved",
                (room.tag, *uncertainty.hosts)))
        elif not gaps:
            out.append(_pass(cid, f"room {room.tag} meets the 6' receptacle rule",
                             (room.tag,)))
    out.extend(counter_findings(ctx, cid))
    return out
