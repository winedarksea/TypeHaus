"""ADVISORY — sound isolation at sleeping rooms (decision #50's promised advisory).

A wall is graded only where it separates a sleeping room from a noisy room (or from another
sleeping room) AND no door or opening joins that pair. A door is the weakest element in the
wall: an undercut door leaks more than an upgraded partition saves, so a pair joined by
one would be graded on a board that buys nothing. The target is the house's own
``[acoustics] min_partition_stc``; ``Assembly.stc`` is always a published test (#50).
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import advisory_fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import SLEEPING_OCCUPANCIES, Occupancy
from typehaus.resolve.room_lookup import room_owning

CHECK_ID = "advisory.acoustic_adjacency"

_SLEEPING = frozenset(o.value for o in SLEEPING_OCCUPANCIES)
_NOISY = frozenset(o.value for o in (Occupancy.BATHROOM, Occupancy.LAUNDRY, Occupancy.LIVING,
                                     Occupancy.KITCHEN, Occupancy.MECHANICAL))
_STEP_M = 0.3     # sample spacing along a wall
_PROBE_M = 0.02   # off the axis, into each side's axis cell


def _sides(model, wall, station: float):
    """The rooms either side of ``wall`` at ``station`` metres along its axis."""
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    if length <= 1e-9:
        return None, None
    tx, ty = (x1 - x0) / length, (y1 - y0) / length
    px, py = x0 + tx * station, y0 + ty * station
    left = room_owning(model, wall.storey, (px - ty * _PROBE_M, py + tx * _PROBE_M))
    right = room_owning(model, wall.storey, (px + ty * _PROBE_M, py - tx * _PROBE_M))
    return left, right


def _pairs_along(model, wall) -> set[tuple[str, str]]:
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    count = max(1, int(length / _STEP_M))
    pairs = set()
    for i in range(count):
        left, right = _sides(model, wall, (i + 0.5) * length / count)
        if left is not None and right is not None and left.tag != right.tag:
            pairs.add(tuple(sorted((left.tag, right.tag))))
    return pairs


def _joined(model) -> set[tuple[str, str]]:
    """Room pairs a door or opening connects directly."""
    joined = set()
    for opening in model.openings:
        if opening.kind == "window":
            continue
        wall = model.wall(opening.host_wall)
        if wall is None:
            continue
        left, right = _sides(model, wall, opening.center_along_m)
        if left is not None and right is not None:
            joined.add(tuple(sorted((left.tag, right.tag))))
    return joined


def _graded(a: str, b: str) -> bool:
    return (a in _SLEEPING and (b in _NOISY or b in _SLEEPING)) or (
        b in _SLEEPING and a in _NOISY)


@check(Tier.ADVISORY, CHECK_ID)
def acoustic_adjacency(ctx: CheckContext) -> list[Finding]:
    """A doorless wall between a sleeping room and a noisy one meets the house's STC."""
    model = ctx.model
    occupancy = {room.tag: room.occupancy for room in model.rooms}
    joined = _joined(model)
    target = ctx.preferences.min_partition_stc
    out: list[Finding] = []
    for wall in model.walls:
        if wall.is_foundation:
            continue
        pairs = [p for p in sorted(_pairs_along(model, wall))
                 if p not in joined and _graded(occupancy[p[0]], occupancy[p[1]])]
        if not pairs:
            continue
        rooms = " / ".join(f"{a}-{b}" for a, b in pairs)
        tags = (wall.tag, *sorted({t for p in pairs for t in p}))
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        stc = getattr(assembly, "stc", None)
        if target is None:
            out.append(_unknown(CHECK_ID, f"{wall.tag} ({wall.assembly}) separates {rooms} "
                                "with no door; preferences.toml states no [acoustics] "
                                "min_partition_stc to grade it against", tags))
        elif stc is None:
            out.append(_unknown(CHECK_ID, f"{wall.tag} ({wall.assembly}) separates {rooms} "
                                f"with no door, and the assembly cites no tested STC "
                                f"(target {target:g})", tags))
        elif stc < target:
            out.append(advisory_fail(
                CHECK_ID, f"{wall.tag} ({wall.assembly}, STC {stc}) separates {rooms} with "
                f"no door: below the house's STC {target:g}", tags,
                fix="retype to a tested assembly that meets the target (e.g. INT_2X4_RC)"))
        else:
            out.append(_pass(CHECK_ID, f"{wall.tag} ({wall.assembly}, STC {stc}) separates "
                             f"{rooms}: meets STC {target:g}", tags))
    if not out:
        return [_na(CHECK_ID, "no wall separates a sleeping room from a noisy or sleeping "
                              "room without a door between them")]
    return out
