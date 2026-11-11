"""A free wall end's board: gypsum on both faces, so the end is closed too (→ drywall_trims).

A free-standing partition is a hole in its room's face, so the ring walk never sees its ends.
Each ``open_end`` with gypsum on both faces takes a strip of the face's board across its
faces' outer planes, standing outboard of the end, and two outside-corner beads. Only the
height nothing else already occupies is boarded: a ceiling, a lining, a stair post.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Any

from shapely.geometry import Point, Polygon, box

from typehaus.resolve.coatings import COATING_SKIN_M
from typehaus.resolve.drywall_trims import TrimContext
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.model import ResolvedSolid, ResolvedWall
from typehaus.resolve.model_trim import ResolvedWallEnd
from typehaus.resolve.room_lookup import room_owning

_CATEGORY = "wall_end_board"
# Shorter than this between obstructions is a sliver of joist band, not a run of board.
_MIN_HEIGHT_M = 0.075
_OVERLAP_M2 = 1e-6
# Twice ``drywall_trims``' sliver clean-up, which can round a ring's corner by that much.
_ON_RING_M = 0.04


def wall_end_boards(ctx: TrimContext) -> None:
    """Emit each free end's board, film, quantity record and corner beads."""
    model = ctx.model
    model.solids[:] = [s for s in model.solids if s.category != _CATEGORY]
    model.wall_ends.clear()
    walls = {wall.tag: wall for wall in model.walls}
    for junction in sorted(model.junctions, key=lambda item: item.node_tag):
        if junction.kind != "open_end" or not junction.incidents:
            continue
        wall = walls.get(junction.incidents[0].wall_tag)
        faces = _gypsum_faces(ctx, wall) if wall is not None else None
        if faces is not None:
            _close_end(ctx, wall, junction, faces)


def _gypsum_faces(ctx: TrimContext, wall: ResolvedWall) -> tuple[Any, Any, str | None] | None:
    """``(first board, last board, face coat)`` when both faces are gypsum, else ``None``."""
    layers = wall.body_layers()
    boards = _boards(wall)
    if len(boards) < 2 or not all(
            getattr(ctx.materials.get(layer.material_ref), "gypsum_type", None)
            for layer in (boards[0], boards[-1])):
        return None
    return boards[0], boards[-1], layers[0].material_ref if layers[0].coating else None


def _boards(wall: ResolvedWall) -> list[Any]:
    """The non-coating layers, a cut layer's pieces (tee, pocket) collapsed to the first:
    its other pieces are slivers of band (``tee-above``) and would read as the board."""
    out, seen = [], set()
    for layer in wall.body_layers():
        if layer.coating or (layer.source_layer_name or "") in seen:
            continue
        if layer.source_layer_name:
            seen.add(layer.source_layer_name)
        out.append(layer)
    return out


def _close_end(ctx: TrimContext, wall: ResolvedWall, junction: Any,
               faces: tuple[Any, Any, str | None]) -> None:
    first, last, coating = faces
    is_start = junction.incidents[0].endpoint == "start"
    tail = wall.axis[1] if is_start else wall.axis[0]
    run = math.dist(junction.point, tail)
    if run <= 1e-9:
        return
    out = ((junction.point[0] - tail[0]) / run, (junction.point[1] - tail[1]) / run)
    normal = (-out[1], out[0])

    def along(point: tuple[float, float], axis: tuple[float, float]) -> float:
        return (point[0] - junction.point[0]) * axis[0] + (point[1] - junction.point[1]) * axis[1]

    corners = [p for layer in wall.body_layers() if not layer.coating for p in layer.polygon]
    plane = max(along(p, out) for p in corners)
    lo, hi = min(along(p, normal) for p in corners), max(along(p, normal) for p in corners)

    def ring(t0: float, t1: float) -> list[tuple[float, float]]:
        def at(t: float, n: float) -> tuple[float, float]:
            return (junction.point[0] + out[0] * t + normal[0] * n,
                    junction.point[1] + out[1] * t + normal[1] * n)
        return [at(t0, lo), at(t1, lo), at(t1, hi), at(t0, hi)]

    board = ring(plane, plane + first.thickness_m)
    bands = _clear_bands(ctx.model, wall, Polygon(board), _face_band(wall, first, last, is_start))
    if not bands:
        return
    end = "start" if is_start else "end"
    material, thickness = first.material_ref, first.thickness_m
    for index, (z0, z1) in enumerate(bands):
        key, tag = f"{wall.uid}-END{end[0].upper()}{index}", f"{wall.tag}-{end}-{index}"
        ctx.model.solids.append(ResolvedSolid(key, f"{tag}-board", wall.storey, _CATEGORY,
                                              board, z0, z1, material=material))
        if coating is not None:
            film = ring(plane + thickness, plane + thickness + COATING_SKIN_M)
            ctx.model.solids.append(ResolvedSolid(f"{key}P", f"{tag}-paint", wall.storey,
                                                  _CATEGORY, film, z0, z1, material=coating))
    height = sum(z1 - z0 for z0, z1 in bands)
    room = _room_tag(ctx, wall, Polygon(board))
    ctx.model.wall_ends.append(ResolvedWallEnd(
        wall=wall.tag, node=junction.node_tag, storey=wall.storey, room=room,
        material_ref=material, thickness_m=thickness, coating=coating,
        area_m2=(hi - lo) * height, height_m=height))
    if _on_room_ring(ctx.model, wall.storey, board[0]):
        return  # the ring walk has already beaded this end
    for z0, z1 in bands:
        for _corner in range(2):
            ctx.add("outside_corner", room, wall.storey, ctx.standard.outside_corner_ref,
                    z1 - z0, (wall.tag,))


def _face_band(wall: ResolvedWall, first: Any, last: Any, is_start: bool) -> tuple[float, float]:
    """The height both faces' board reaches at this end, from the subfloor up."""
    (a0, a1), (b0, b1) = first.band(wall), last.band(wall)
    top = min(a1, b1)
    raked = wall.top_z0_m if is_start else wall.top_z1_m
    return max(a0, b0, wall.frame_base_z_m), top if raked is None else min(top, raked)


def _room_tag(ctx: TrimContext, wall: ResolvedWall, board: Polygon) -> str | None:
    authored = getattr(ctx.model.plan.by_tag(wall.tag), "interior_room", None)
    if authored is not None:
        return authored
    room = room_owning(ctx.model, wall.storey, (board.centroid.x, board.centroid.y))
    return room.tag if room is not None else None


def _on_room_ring(model: Any, storey: str, point: tuple[float, float]) -> bool:
    """Does any room's outer face on ``storey`` pass through this end's corner?"""
    return any(Polygon(room.clear_face).exterior.distance(Point(point)) <= _ON_RING_M
               for room in model.rooms if room.storey == storey and len(room.clear_face) >= 3)


def _clear_bands(model: Any, wall: ResolvedWall, board: Polygon,
                 band: tuple[float, float]) -> list[tuple[float, float]]:
    """``band`` less the height of everything standing in ``board``'s plan."""
    taken = sorted((z0, z1) for shape, z0, z1 in _occupants(model, wall, board)
                   if z1 > band[0] and z0 < band[1]
                   and shape.intersection(board).area > _OVERLAP_M2)
    free, low = [], band[0]
    for z0, z1 in taken:
        if z0 - low >= _MIN_HEIGHT_M:
            free.append((low, z0))
        low = max(low, z1)
    if band[1] - low >= _MIN_HEIGHT_M:
        free.append((low, band[1]))
    return free


def _occupants(model: Any, wall: ResolvedWall,
               board: Polygon) -> Iterator[tuple[Polygon, float, float]]:
    """Plan shape and height of every wall layer, member and solid near ``board``."""
    near = box(*board.bounds).buffer(0.05)
    for other in model.walls:
        if other.tag == wall.tag:
            continue
        for layer in other.layers:
            if len(layer.polygon) >= 3 and not layer.coating:
                yield (Polygon(layer.polygon), *layer.band(other))
    own = {id(member) for member in wall.members}
    for member in model.all_members():
        if id(member) in own:
            continue
        span = box(min(member.p0[0], member.p1[0]), min(member.p0[1], member.p1[1]),
                   max(member.p0[0], member.p1[0]), max(member.p0[1], member.p1[1]))
        if span.distance(near) > 0.15:
            continue
        ring, z0, z1 = member_footprint(member)
        yield Polygon(ring), z0, z1
    for solid in model.solids:
        if len(solid.outline) >= 3 and solid.category != _CATEGORY:
            shape = Polygon(solid.outline, [list(void) for void in solid.voids])
            if shape.is_valid:
                yield shape, solid.z0_m, solid.z1_m
