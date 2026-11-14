"""What 210.52 counts as a receptacle, shared by every electrical check.

The checks themselves live in ``electrical_room_lighting``, ``electrical_spacing``,
``electrical_island`` and ``electrical_circuit_refs``.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy

# 210.52(A)'s rooms; MEDIA is the family/recreation room.
_HABITABLE = {Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.KITCHEN, Occupancy.DINING,
             Occupancy.OFFICE, Occupancy.HOBBY, Occupancy.STUDY_CLOSET, Occupancy.MEDIA}


# WARN severity + FAIL result, deliberately: the permit integrity gate only blocks on ERROR
# severity, and this finding is advisory, not a hard blocker.
def _warn_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return advisory(cid, msg, tags, Result.FAIL)


_RECEPTACLE_KINDS = {"receptacle", "gfci"}  # the 125V 15/20A devices 210.52 counts
# A 240V kind still counts if its *type* offers a 125V port — the combination 5-20R/6-20R
# device is one box with two receptacles in it, and the 5-20R half is a 210.52 receptacle
# like any other. (This is the DeviceKind precedent: the kind stays flat, the type
# differentiates.)
_COMBINATION_RECEPTACLE_KIND = "receptacle_240"


def _counts_as_a_125v_receptacle(ctx: CheckContext, device) -> bool:
    device_type = next((t for t in ctx.plan.library.electrical_device_types
                        if t.tag == device.type_ref), None) if device.type_ref else None
    if device.kind.value in _RECEPTACLE_KINDS:
        return not getattr(device_type, "deadfront", False)
    if device.kind.value != _COMBINATION_RECEPTACLE_KIND:
        return False
    return device_type is not None and any(
        port.service.value == "power_120" for port in device_type.ports)


_REQUIRED_MAX_HEIGHT_M = 5.5 * 0.3048


def _counts_toward_210_52(ctx: CheckContext, device, *, height_limit: bool = True) -> bool:
    """A 125 V receptacle 210.52 may count as REQUIRED: not switched (``controlled_by``) and,
    with ``height_limit``, not more than 5 1/2 ft above the floor (the lead-in). (E) sets its
    own 6 1/2 ft and passes ``height_limit=False``. 210.8 GFCI scope uses the plain test."""
    if not _counts_as_a_125v_receptacle(ctx, device) or getattr(device, "controlled_by", ()):
        return False
    mount = getattr(device, "mount", None)
    elevation = getattr(mount, "elevation", None)
    return not (height_limit and elevation is not None
                and elevation.meters > _REQUIRED_MAX_HEIGHT_M + 1e-9)
