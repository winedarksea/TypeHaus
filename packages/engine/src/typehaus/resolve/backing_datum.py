"""A backing band authored above the finished floor, lifted onto its wall's sill datum.

``WallBacking.datum="finished-floor"`` lets a grab-bar course be written the way CRC
R328.1.1 writes it, 32" AFF, instead of as a sill-datum literal that lands 3/4"-1 1/2" low
under a subfloor and tile. Rooms resolve after framing, so the band frames on the sill datum
and this pass lifts its members by the finished floor of the room on its face. The checks
read the same offset through :func:`band_datum_offset_m`, so model and grade agree.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.backing_panels import BackingBand, backing_bands
from typehaus.resolve.model import ResolvedModel, ResolvedRoom, ResolvedWall
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.resolve.room_lookup import room_owning

__all__ = ["apply_backing_datums", "band_datum_offset_m", "face_room"]

#: How far past the wall's outermost layer the face's room is sampled.
_SAMPLE_PAST_FACE_M = 0.05


def face_room(model: ResolvedModel, wall: ResolvedWall, face: str,
              station: float) -> ResolvedRoom | None:
    """The room standing past ``face`` ("left"/"right") of ``wall`` at ``station``."""
    (x0, y0), (x1, y1) = wall.axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if length <= 0.0:
        return None
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    nx, ny = -uy, ux
    sign = -1.0 if face == "right" else 1.0
    across = [sign * ((px - x0) * nx + (py - y0) * ny)
              for layer in wall.layers for px, py in layer.polygon]
    reach = (max(across) if across else 0.0) + _SAMPLE_PAST_FACE_M
    point = (x0 + ux * station + sign * nx * reach, y0 + uy * station + sign * ny * reach)
    return room_owning(model, wall.storey, point)


def band_datum_offset_m(model: ResolvedModel, wall: ResolvedWall,
                        band: BackingBand) -> float | None:
    """How far the band's datum stands above the wall's sill datum.

    ``0`` for a sill-datum band; ``None`` for a finished-floor band with no room on its face,
    which ``integrity.wall_backing_ref`` reports rather than guessing a floor.
    """
    if band.datum != "finished-floor":
        return 0.0
    (x0, y0), (x1, y1) = wall.axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    start = band.start_m or 0.0
    end = length if band.length_m is None else min(length, start + band.length_m)
    room = face_room(model, wall, band.face, (start + end) / 2.0)
    if room is None:
        return None
    return room_finished_floor_elevation(model, room) - wall.base_ref_z_m


def apply_backing_datums(plan: PlanModel, model: ResolvedModel) -> None:
    """Lift every finished-floor band's members by its datum offset. After rooms resolve."""
    bands = backing_bands(plan)
    for index, wall in enumerate(model.walls):
        ordered = sorted(bands.get(wall.tag, ()), key=lambda b: (b.elevation_m, b.tag))
        lifts: dict[str, float] = {}
        for ordinal, band in enumerate(ordered):
            offset = band_datum_offset_m(model, wall, band)
            if offset:
                lifts[f"backing-{ordinal}-"] = offset
        if not lifts:
            continue
        members = []
        for member in wall.members:
            prefix = next((key for key in lifts if member.child_key.startswith(key)), None)
            if prefix is not None:
                member = replace(member, z0_m=member.z0_m + lifts[prefix],
                                 z1_m=member.z1_m + lifts[prefix])
            members.append(member)
        model.walls[index] = replace(wall, members=tuple(members))
