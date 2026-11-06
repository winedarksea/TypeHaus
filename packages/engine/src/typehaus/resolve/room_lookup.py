"""Which room owns a plan point — read off the room's AXIS cell, not its clear face.

The clear face stops at the finish plane, so a device set into a wall, a register in a
jamb, or a column foot straddling a partition lies outside every clear face. Ownership is
the question "whose side of the centreline is this on", and the axis cells tile the storey.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.resolve.model import ResolvedModel, ResolvedRoom


def room_owning(model: ResolvedModel, storey: str | None,
                xy: tuple[float, float]) -> ResolvedRoom | None:
    """The room on ``storey`` whose axis cell covers ``xy`` (any storey when ``None``)."""
    point = Point(xy[0], xy[1])
    for room in model.rooms:
        if storey is not None and room.storey != storey:
            continue
        ring = axis_ring(room)
        if len(ring) >= 3 and Polygon(ring).covers(point):
            return room
    return None


def owns(room: ResolvedRoom, xy: tuple[float, float]) -> bool:
    """Whether ``xy`` lies in ``room``'s axis cell."""
    ring = axis_ring(room)
    return len(ring) >= 3 and Polygon(ring).covers(Point(xy[0], xy[1]))


def axis_polygon(room: ResolvedRoom) -> Polygon:
    """``room``'s axis cell as a polygon — the ownership shape."""
    return Polygon(axis_ring(room))


def axis_ring(room) -> list:
    """``room``'s axis cell ring, falling back to the clear face (hand-built stand-ins)."""
    return getattr(room, "axis_face", None) or room.clear_face


def opening_rooms(model: ResolvedModel, opening,
                  reach_m: float = 0.15) -> tuple[ResolvedRoom | None, ResolvedRoom | None]:
    """The rooms ``reach_m`` off each finish face of an opening's wall, at its centre:
    ``(left-normal side, right-normal side)``. ``None`` is outdoors or no room."""
    from typehaus.resolve.geometry import wall_frame
    from typehaus.resolve.geometry_door_products import finish_faces

    wall = model.wall(opening.host_wall)
    if wall is None:
        return None, None
    origin, tangent, normal, _ = wall_frame(wall)
    faces = finish_faces(wall) or (-wall.thickness_m / 2, wall.thickness_m / 2)

    def probe(side: int) -> ResolvedRoom | None:
        reach = (faces[1] if side > 0 else faces[0]) + side * reach_m
        return room_owning(model, wall.storey, tuple(
            origin[i] + tangent[i] * opening.center_along_m + normal[i] * reach
            for i in (0, 1)))

    return probe(1), probe(-1)
