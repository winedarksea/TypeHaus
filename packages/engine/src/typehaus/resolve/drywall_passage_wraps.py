"""A leafless passage's drywall wrap (owner decision 2026-11-07; → drywall_trims).

A walk-through ``is_passage`` opening with no leaf takes no casing: each gypsum face's board
returns into the reveal, and the face's outside corners take the standard's corner bead up
both jambs and across the head. Nothing runs along the floor, so a floor transition under
the passage (oak to tile) changes nothing. A face without gypsum (a brick reveal) is skipped.

Each gypsum face also bills its share of the reveal's return strips (board and coatings,
half the core depth each, all of it when the other face is bare), the way window returns
bill theirs (``takeoff/passage_wraps.py``).

Known limits: the jamb probe reads 0.3-1.0 m above the floor and the finish run comes from the
wall-wide ``depth_layers()``, so a tile or wainscot band can mislead either; the bead runs to
the RO head at the full RO width, ~1.5" a face over the wrapped opening.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.resolve.drywall_trims import TrimContext, room_floor
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.interior_trim_scope import face_is_gypsum
from typehaus.resolve.room_lookup import room_owning

_ROOM_PROBE_M = 0.15
_JAMB_PROBE_M = 0.05
# The face over the head is probed in this band above it.
_HEAD_PROBE = (0.02, 0.10)
_JAMB_PROBE = (0.3, 1.0)


@dataclass(frozen=True)
class PassageWrapFace:
    """One gypsum face of a leafless passage: its bead and its share of the return."""

    opening: str
    storey: str
    room: str | None
    height_m: float  # finished floor on this side to the head
    width_m: float
    jambs: int  # jambs with board beside them on this face
    head: bool
    depth_m: float  # this face's share of the reveal between the two faces' boards
    finish: tuple[tuple[str, float], ...]  # (material, thickness): board and coatings

    @property
    def bead_length_m(self) -> float:
        return self.jambs * self.height_m + (self.width_m if self.head else 0.0)

    @property
    def return_area_m2(self) -> float:
        return self.bead_length_m * self.depth_m


def passage_wrap_faces(model, materials: dict) -> list[PassageWrapFace]:
    walls = {wall.tag: wall for wall in model.walls}
    out: list[PassageWrapFace] = []
    for opening in sorted(model.openings, key=lambda o: o.uid):
        wall = walls.get(opening.host_wall)
        if not opening.is_passage or opening.is_door or wall is None:
            continue
        out.extend(_faces(model, materials, opening, wall))
    return out


def _faces(model, materials, opening, wall) -> list[PassageWrapFace]:
    origin, tangent, normal, axis_length = wall_frame(wall)
    faces = finish_faces(wall)
    if axis_length <= 1e-9 or faces is None:
        return []
    cx = origin[0] + tangent[0] * opening.center_along_m
    cy = origin[1] + tangent[1] * opening.center_along_m
    head_z = wall.base_ref_z_m + opening.sill_m + opening.height_m
    runs = _finish_runs(wall, materials, origin, normal)
    core = (faces[1] - faces[0]) - sum(t for run in runs.values() for _m, t in run)
    found = []
    for side, face in ((1, faces[1]), (-1, faces[0])):
        lift = face + side * _ROOM_PROBE_M
        room = room_owning(model, wall.storey, (cx + normal[0] * lift, cy + normal[1] * lift))
        floor_z = (room_floor(model, room) if room is not None
                   else wall.base_ref_z_m + opening.sill_m)
        into = (-normal[0] * side, -normal[1] * side)

        def gypsum(along: float, z0: float, z1: float, face=face, into=into) -> bool:
            point = (cx + tangent[0] * along + normal[0] * face,
                     cy + tangent[1] * along + normal[1] * face)
            return face_is_gypsum(wall, point, into, z0, z1, materials)

        jamb = opening.width_m / 2.0 + _JAMB_PROBE_M
        jambs = sum(gypsum(sign * jamb, floor_z + _JAMB_PROBE[0], floor_z + _JAMB_PROBE[1])
                    for sign in (-1.0, 1.0))
        head = gypsum(0.0, head_z + _HEAD_PROBE[0], head_z + _HEAD_PROBE[1])
        if jambs or head:
            found.append((side, room, head_z - floor_z, jambs, head))
    return [PassageWrapFace(
        opening=opening.tag, storey=wall.storey, room=room.tag if room else None,
        height_m=height, width_m=opening.width_m, jambs=jambs, head=head,
        depth_m=max(core, 0.0) / len(found), finish=runs[side])
        for side, room, height, jambs, head in found]


def _finish_runs(wall, materials, origin, normal) -> dict[int, tuple[tuple[str, float], ...]]:
    """Each face's board and coatings, read inward from that face until the first layer
    that is neither."""
    def offset(layer) -> float:
        return sum((p[0] - origin[0]) * normal[0] + (p[1] - origin[1]) * normal[1]
                   for p in layer.polygon) / max(len(layer.polygon), 1)

    layers = sorted((layer for layer in wall.depth_layers() if len(layer.polygon) >= 3),
                    key=offset)
    runs: dict[int, tuple[tuple[str, float], ...]] = {}
    for side, ordered in ((1, layers[::-1]), (-1, layers)):
        run = []
        for layer in ordered:
            material = materials.get(layer.material_ref)
            if not (getattr(material, "coating", False)
                    or getattr(material, "gypsum_type", None) is not None):
                break
            run.append((layer.material_ref, layer.thickness_m))
        runs[side] = tuple(run)
    return runs


def passage_beads(ctx: TrimContext) -> None:
    for face in passage_wrap_faces(ctx.model, ctx.materials):
        ctx.add("outside_corner", face.room, face.storey, ctx.standard.outside_corner_ref,
                face.bead_length_m, (face.opening, face.room or ""))
