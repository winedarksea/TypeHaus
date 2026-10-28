"""Wall-mounted electrical bodies need solid wall beside doors and windows."""

from __future__ import annotations

from math import hypot, isfinite

from typehaus.checks._authoring import advisory_fail, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model import ElectricalDevice, MountKind
from typehaus.resolve.model import ResolvedOpening

_CHECK_ID = "electrical.wall_device_opening"
# Numerical noise at a shared edge is not penetration into an opening.
_OVERLAP_TOLERANCE_M = 1e-9


def _overlaps(first_low: float, first_high: float,
              second_low: float, second_high: float) -> bool:
    return min(first_high, second_high) - max(first_low, second_low) > _OVERLAP_TOLERANCE_M


@check(Tier.ADVISORY, _CHECK_ID)
def wall_device_opening(ctx: CheckContext) -> list[Finding]:
    """Compare complete body envelopes in their host wall's station/elevation plane.

    A finish-face plate stands outside the wall's thickness, even when it is mounted
    over a doorway. A solid-intersection test therefore misses precisely this defect.
    This does not grade casing, framing bays, pocket travel, or door swings.
    """
    devices = [element for element in ctx.plan.all_elements()
               if isinstance(element, ElectricalDevice) and element.mount is not None
               and element.mount.kind == MountKind.WALL]
    if not devices:
        return [not_applicable(_CHECK_ID, "no wall-mounted electrical devices")]
    bodies = {body.tag: body for body in ctx.model.canvas_objects}
    walls = {wall.tag: wall for wall in ctx.model.walls}
    openings_by_wall: dict[str, list[ResolvedOpening]] = {}
    for opening in ctx.model.openings:
        if opening.kind in {"door", "window"}:
            openings_by_wall.setdefault(opening.host_wall, []).append(opening)

    findings: list[Finding] = []
    for device in devices:
        body = bodies.get(device.tag)
        if (body is None or len(body.footprint) < 3 or body.body_z0_m is None
                or body.body_z1_m is None
                or not all(isfinite(value) for point in body.footprint for value in point)
                or not isfinite(body.body_z0_m) or not isfinite(body.body_z1_m)
                or body.body_z1_m <= body.body_z0_m):
            findings.append(unknown(_CHECK_ID, f"{device.tag}: body envelope is unresolved",
                                    (device.tag,)))
            continue
        wall = walls.get(body.attachment_wall or "")
        if wall is None or wall.storey != body.storey:
            findings.append(unknown(_CHECK_ID, f"{device.tag}: attachment wall is unresolved",
                                    (device.tag,)))
            continue
        (start_x, start_y), (end_x, end_y) = wall.axis
        axis_length = hypot(end_x - start_x, end_y - start_y)
        if not isfinite(axis_length) or axis_length <= _OVERLAP_TOLERANCE_M:
            findings.append(unknown(_CHECK_ID, f"{wall.tag}: wall axis is unresolved",
                                    (device.tag, wall.tag)))
            continue
        tangent_x = (end_x - start_x) / axis_length
        tangent_y = (end_y - start_y) / axis_length
        stations = [(x - start_x) * tangent_x + (y - start_y) * tangent_y
                    for x, y in body.footprint]
        device_low, device_high = min(stations), max(stations)
        if device_high - device_low <= _OVERLAP_TOLERANCE_M:
            findings.append(unknown(_CHECK_ID, f"{device.tag}: body has no resolved wall width",
                                    (device.tag, wall.tag)))
            continue
        device_findings: list[Finding] = []
        for opening in openings_by_wall.get(wall.tag, []):
            tags = (device.tag, opening.tag, wall.tag)
            bottom = wall.base_ref_z_m + opening.sill_m
            if (not all(isfinite(value) for value in (
                    bottom, opening.height_m, opening.width_m, opening.center_along_m,
                    opening.arch_rise_m)) or opening.width_m <= 0 or opening.height_m <= 0):
                device_findings.append(unknown(
                    _CHECK_ID, f"{opening.tag}: opening envelope is unresolved", tags))
                continue
            if (not _overlaps(device_low, device_high,
                              opening.center_along_m - opening.width_m / 2,
                              opening.center_along_m + opening.width_m / 2)
                    or not _overlaps(body.body_z0_m, body.body_z1_m,
                                     bottom, bottom + opening.height_m)):
                continue
            if opening.arch_rise_m != 0:
                device_findings.append(unknown(
                    _CHECK_ID, f"{device.tag}: possible overlap with arched opening "
                    f"{opening.tag}; its curved head is not evaluated", tags))
                continue
            device_findings.append(advisory_fail(
                _CHECK_ID, f"{device.tag}'s full body overlaps {opening.kind} "
                f"{opening.tag} in {wall.tag}; move it onto solid wall", tags))
        findings.extend(device_findings or [passed(
            _CHECK_ID, f"{device.tag}: body clears host-wall door and window openings",
            (device.tag, wall.tag))])
    return findings
