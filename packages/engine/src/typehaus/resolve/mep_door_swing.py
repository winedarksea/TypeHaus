"""A swinging door's leaf sweep as a volume a run must stay out of.

Beside :mod:`typehaus.resolve.mep_envelopes` (which owns the rough-opening prism) so the check
and the router read one derivation. The sector is ``ResolvedOpening.swing_clearance`` -- hinge,
side and radius already resolved for the plan sheets and ``integrity.door_swing_conflict``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typehaus.resolve.model import ResolvedModel


def door_swing_prisms(
        model: ResolvedModel) -> list[tuple[str, str, Any, float, float, tuple[str, ...]]]:
    """Each swinging door as ``(tag, host, plan sector, floor z, head z, penetration_for)``.

    A slider, pocket or overhead door has no sector. As in ``door_swing_conflict`` the leaf
    stops at the head: a run above it is clear, a run below it stops the door.
    """
    from shapely.geometry import Polygon

    walls = {wall.tag: wall for wall in model.walls}
    out = []
    for opening in model.openings:
        wall = walls.get(opening.host_wall)
        if wall is None or len(opening.swing_clearance) < 3:
            continue
        sector = Polygon(opening.swing_clearance)
        if sector.is_empty or not sector.is_valid:
            continue
        low = wall.base_ref_z_m + opening.sill_m
        out.append((opening.tag, wall.tag, sector, low, low + opening.height_m,
                    tuple(opening.penetration_for or ())))
    return out
