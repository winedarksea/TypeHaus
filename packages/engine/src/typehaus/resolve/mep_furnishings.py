"""The volume a STORAGE furnishing claims, read by a check and by the router alike.

A walk-in closet is ``Occupancy.STORAGE``, and storage is a room whose ceiling is a service
plane (``EXPOSED_SERVICE_OCCUPANCIES``): ``mep.run_in_finished_volume`` leaves pipe hanging
in one by design. That is right for a bare store room and wrong for a closet with a
shelf-and-rod in it — catlin's suite stack and both suite supply risers stood in the open
through ``FURN-M-CLOSET-SHELF`` and nothing said so. What separates the two is the
furnishing, so the furnishing is what answers.

**Only in a STORAGE room**, because that is the only exemption this closes: a finished
room is graded by ``run_in_finished_volume`` already, and a kitchen's sink base is storage
furniture that plumbing belongs inside. **A storage furnishing there claims its plan
footprint from the floor to the ceiling.** Coats
hang from the rod to the floor and boxes sit on the shelf up to the ceiling, so the column
is in use at every height; a closet that holds none stays open to services. The top is the
room's ceiling plane, else its storey datum plus ``Room.clear_height``; a room with neither
(an attic room under a raked roof) claims nothing rather than a guessed height.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class FurnishingColumn:
    tag: str
    room: str | None
    footprint: Any  # shapely Polygon
    z0_m: float
    z1_m: float


def furnishing_columns(model: ResolvedModel) -> list[FurnishingColumn]:
    """Every storage furnishing's claimed column — see the module note."""
    from shapely.geometry import Polygon

    types = {ft.tag: ft for ft in model.plan.library.furniture_types}
    datum = {s.tag: s.elevation.meters for s in model.plan.storeys}
    rooms = {room.tag: room for room in model.rooms}
    ceilings = {c.room_ref: c.z0_m for c in model.ceilings if c.z0_m is not None}
    out: list[FurnishingColumn] = []
    for obj in model.canvas_objects:
        ftype = types.get(obj.type_ref or "")
        if obj.domain != "furniture" or ftype is None or not ftype.storage:
            continue
        if len(obj.footprint) < 3 or obj.storey not in datum:
            continue
        room = rooms.get(obj.room or "")
        if room is None or room.occupancy != "storage":
            continue
        top = ceilings.get(obj.room or "")
        if top is None and room.clear_height_m:
            top = datum[obj.storey] + room.clear_height_m
        if top is None:
            continue
        out.append(FurnishingColumn(tag=obj.tag, room=obj.room,
                                    footprint=Polygon(obj.footprint),
                                    z0_m=datum[obj.storey], z1_m=top))
    return out
