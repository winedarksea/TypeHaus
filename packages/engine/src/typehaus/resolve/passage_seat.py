"""A leafless through hole whose sill still lands on its rooms' floors.

``sill_m`` is measured off the wall's base, so a passage whose wall starts below the finished
floor carries a sill and is still walked through. It counts when its sill is no more than a
threshold above the higher adjoining finished floor. With no room on either side nothing can
be said, and only a zero sill reads as a passage.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.resolve.room_lookup import room_owning

_THRESHOLD_M = 0.5 * M_PER_IN
_ROOM_PROBE_M = 0.15


def mark_seated_passages(model: ResolvedModel) -> None:
    """Set ``seated_passage`` on each opening it applies to; call after rooms and floors."""
    walls = {wall.tag: wall for wall in model.walls}
    for index, opening in enumerate(model.openings):
        wall = walls.get(opening.host_wall)
        if wall is None or not opening.is_leafless_through or opening.sill_m <= 1e-9:
            continue
        floors = _side_floors(model, wall, opening)
        if floors and wall.base_ref_z_m + opening.sill_m <= max(floors) + _THRESHOLD_M:
            model.openings[index] = replace(opening, seated_passage=True)


def _side_floors(model: ResolvedModel, wall, opening) -> list[float]:
    origin, tangent, normal, _length = wall_frame(wall)
    cx = origin[0] + tangent[0] * opening.center_along_m
    cy = origin[1] + tangent[1] * opening.center_along_m
    reach = wall.thickness_m / 2.0 + _ROOM_PROBE_M
    floors = []
    for side in (1.0, -1.0):
        room = room_owning(model, wall.storey,
                           (cx + normal[0] * side * reach, cy + normal[1] * side * reach))
        if room is not None:
            floors.append(room_finished_floor_elevation(model, room))
    return floors
