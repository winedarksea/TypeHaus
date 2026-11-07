"""The undercut a hung leaf actually has, read off its resolved doorway.

``door_sizing`` hangs the leaf; this reads what came out: the gap from the leaf's bottom to
each adjacent finished floor. The higher floor's gap is the one the leaf clears as it swings
and the tightest under the closed leaf (the doorway's joint sits under it), so it is the
undercut ``advisory.door_undercut`` grades and ``mep.door_transfer_air`` takes as free area.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Products that sit under the closed leaf and so set the gap over the lower floor.
_UNDER_LEAF_ROLES = frozenset({"sill", "track", "transition"})


@dataclass(frozen=True)
class RealizedUndercut:
    higher_m: float  # over the higher finished floor: the graded undercut
    lower_m: float  # over the lower one, out in the room
    higher_finish: str | None
    lower_finish: str | None
    lower_room: str | None
    # A documented threshold or reducer under the leaf closes the step to the lower floor.
    bridged: bool


def realized_undercut(opening) -> RealizedUndercut | None:
    """None where the leaf bottom or either adjacent finished floor is not known."""
    assembly = opening.doorway
    if assembly is None or assembly.leaf_bottom_z_m is None:
        return None
    floors = assembly.adjacent_floors
    if len(floors) != 2 or any(f is None or f.surface_m is None for f in floors):
        return None
    lower, higher = sorted(floors, key=lambda f: f.surface_m)
    leaf = assembly.leaf_bottom_z_m
    return RealizedUndercut(
        higher_m=leaf - higher.surface_m, lower_m=leaf - lower.surface_m,
        higher_finish=higher.finish_ref, lower_finish=lower.finish_ref,
        lower_room=lower.room_tag,
        bridged=any(c.specification.role in _UNDER_LEAF_ROLES for c in assembly.components))
