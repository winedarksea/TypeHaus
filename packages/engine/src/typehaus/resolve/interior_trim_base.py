"""Base runs: a room's finish-face ring, less everything the base dies into.

The ring is the room's ``clear_face`` turned counter-clockwise, so the room is on the left
of every edge, measured in arc length ``s`` (``room_perimeter``). It keeps only the arcs
on a wall whose room-side layer is a FINISH, and breaks those at:

* doors — the casing's outer edge, a trimless door's rough opening, a bookcase door's
  factory frame (``TrimScope.base_break_half_width``);
* floor openings and the stairs that start on this storey;
* what stands against the wall below the base's top (``TrimScope.fixed_footprints``):
  casework, a basin fixture or a wall-hung one (not a floor WC, which the base runs
  behind), an appliance. A floating vanity clears it and the base runs under;
* a raised platform (an enclosed tub deck);
* a non-wood paneling band from the floor (a tile surround). A wood band carries the base
  on its face instead, offset by its thickness.

A break is the box's own width along the face, so the base butts it rather than stopping short.

What survives is cut at every corner into straight pieces, butt-jointed: at an inside
corner the incoming piece runs to the far face and the outgoing one butts it; at an
outside corner the incoming one runs past by the outgoing one's depth.
"""

from __future__ import annotations

from typehaus.resolve import room_perimeter as rp
from typehaus.resolve.interior_trim_scope import TrimScope, base_kind, face_function, is_finish
from typehaus.resolve.model import ResolvedModel, ResolvedRoom
from typehaus.resolve.model_trim import ResolvedBaseRun, TrimPiece
from typehaus.resolve.room_corners import (
    corner_kind,
    corners_only,
    edge_direction,
    point_and_outward,
    ring_vertices,
)
from typehaus.resolve.room_walls import _TOUCH_M, bounding_wall_arcs

# How far a box may stand off the face and still be against it: a fridge's 1" air gap.
_AGAINST_M = 2 * 0.0254
# A stair-well ledge narrower than this is not floor a base could sit on.
_WELL_LEDGE_M = 4 * 0.0254
# Float slop between a box's face and the room ring it lands on: a nanometre, so the
# shared face is found and the base still stops at the box.
_MEETS_M = 1e-9
# A casing leg set off the face by a board-thickness change (1/2" over a 5/8" casing) still
# meets the base. Wider than this is another wall's casing, not this face's.
_CASING_STANDOFF_M = 0.25 * 0.0254
# A band starting this close to the floor is "from the floor".
_FROM_FLOOR_M = 0.01
# A finished piece shorter than this is corner noise, not a board anyone would cut.
_MIN_PIECE_M = 2 * 0.0254
# How far a non-board base stands off the face: porcelain + thinset; a 120-mil sheet; a
# 1/8" rubber cove base.
_SKIN_M = {"tile": 0.375 * 0.0254, "integral_cove": 0.125 * 0.0254,
           "resilient_base": 0.125 * 0.0254}


def resolve_base_runs(plan, model: ResolvedModel, scope: TrimScope) -> None:
    for room in sorted(scope.rooms.values(), key=lambda r: r.uid):
        kind = base_kind(scope, room)
        if kind == "none":
            continue
        model.base_runs.extend(_room_runs(plan, model, scope, room, kind))


def _room_runs(plan, model: ResolvedModel, scope: TrimScope, room: ResolvedRoom,
               kind: str) -> list[ResolvedBaseRun]:
    from shapely.geometry import LineString, Polygon
    from shapely.geometry.polygon import orient

    ring = corners_only(list(orient(Polygon(room.clear_face), 1.0).exterior.coords)[:-1])
    perimeter = rp.perimeter_length(ring)
    floor_z, _structural = scope.floors(model, room)
    height = scope.standard.base_height.meters
    arcs = bounding_wall_arcs(model, room, ring, scope.body)
    finish, bare, owned = finish_arcs(ring, perimeter, arcs, floor_z, height)

    breaks: list[tuple[float, float, str]] = [(a, b, "bare face") for a, b in bare]
    hosts = {wall.tag for wall, _span in arcs}
    for opening in model.openings:
        if opening.is_door and opening.host_wall in hosts:
            for a, b in _one_door(model, ring, room, scope, opening):
                breaks.append((a, b, opening.tag))
    for a, b in rp.floor_opening_intervals(plan, ring, room.storey, _WELL_LEDGE_M):
        breaks.append((a, b, "floor opening"))
    sides = [LineString([ring[i], ring[(i + 1) % len(ring)]]) for i in range(len(ring))]
    for tag, polygon in _obstacles(plan, model, scope, room, floor_z):
        breaks.extend((a, b, tag) for a, b in _butting(sides, polygon, _AGAINST_M))
    # A casing leg set off one face by a board-thickness change still stops the base there.
    for tag, polygon in _casing_footprints(model, room, floor_z, height):
        breaks.extend((a, b, tag) for a, b in _butting(sides, polygon, _CASING_STANDOFF_M))
    wood: list[tuple[float, float, float]] = []
    for band in model.panelings:
        if band.room != room.tag or band.band_z0_m > _FROM_FLOOR_M or not band.outline:
            continue
        material = scope.materials.get(band.material_ref)
        if band.retains_baseboard or getattr(material, "species", None):
            offset = 0.0 if band.replaces_wall_finish else band.thickness_m
            spans = rp.fronting_intervals(ring, [Polygon(band.outline)], _TOUCH_M)
            wood.extend((a, b, offset) for a, b in spans)
        else:
            spans = _butting(sides, Polygon(band.outline), _TOUCH_M)
            breaks.extend((a, b, band.tag) for a, b in spans)

    kept = _subtract(rp.merged_intervals(finish, perimeter),
                     rp.merged_intervals([(a, b) for a, b, _ in breaks], perimeter))
    pieces = _cut(ring, kept, wood, owned)
    return _runs(room, kind, scope, ring, perimeter, pieces, owned, breaks, floor_z, height)


def finish_arcs(ring, perimeter: float, arcs, floor_z: float, height: float):
    """``(finish, bare, owned)``: the wall arcs whose face over the base band is a FINISH,
    those that are not, and every arc with its wall."""
    finish, bare, owned = [], [], []
    for wall, (s0, s1) in arcs:
        # Trim each arc back by the touch band so a bare neighbour cannot nick a corner. An
        # end at the ring's seam is where cyclic_span split one run in two, not a run's end.
        a = s0 if s0 <= 1e-9 else s0 + _TOUCH_M
        b = s1 if s1 >= perimeter - 1e-9 else s1 - _TOUCH_M
        if b <= a:
            continue
        owned.append((wall, (a, b)))
        point, outward = point_and_outward(ring, (a + b) / 2.0)
        function = face_function(wall, point, outward, floor_z, floor_z + height)
        (finish if is_finish(function) else bare).append((a, b))
    return finish, bare, owned


def _butting(sides, polygon, max_standoff: float) -> list[tuple[float, float]]:
    """Ring intervals where ``polygon`` stands within ``max_standoff`` of a side.

    Each side reaches by its own standoff, so the break is the polygon's own width along that
    face: a buffer by the full allowance would stop the base that much short of it as well.
    """
    from shapely.geometry import Point

    if not polygon.is_valid or polygon.is_empty:
        return []
    out, s = [], 0.0
    for side in sides:
        standoff = side.distance(polygon)
        if standoff <= max_standoff:
            hit = side.intersection(polygon.buffer(standoff + _MEETS_M))
            for piece in getattr(hit, "geoms", (hit,)):
                if piece.is_empty or piece.length <= 0:
                    continue
                offsets = [side.project(Point(coord)) for coord in piece.coords]
                out.append((s + min(offsets), s + max(offsets)))
        s += side.length
    return out


def _one_door(model, ring, room, scope: TrimScope, opening) -> list[tuple[float, float]]:
    return rp.door_intervals(model, ring, room.storey,
                             lambda o: scope.base_break_half_width(o, room.tag)
                             if o.tag == opening.tag else None, {opening.host_wall})


def _obstacles(plan, model: ResolvedModel, scope: TrimScope, room: ResolvedRoom,
               floor_z: float):
    """``(tag, footprint)`` for each floor-standing thing a base stops at, in this room."""
    from shapely.geometry import Polygon

    from typehaus.resolve.room_lookup import owns

    top = floor_z + scope.standard.base_height.meters
    for tag, footprint, z0, _z1 in scope.fixed_footprints(plan, model, room.storey):
        if z0 >= top:
            continue  # a floating vanity, an upper: the base runs under it
        if owns(room, (footprint.centroid.x, footprint.centroid.y)):
            yield tag, footprint
    for stair in model.stairs:
        if stair.storey == room.storey and len(stair.outline) >= 3:
            yield stair.tag, Polygon(stair.outline)
    yield from stair_skirt_footprints(model, room.storey)
    # A raised platform (an enclosed tub deck, a bench) is a box the base never runs behind.
    for solid in model.solids:
        if (solid.category == "slab_platform" and solid.storey == room.storey
                and solid.z1_m > top and len(solid.outline) >= 3):
            yield solid.tag, Polygon(solid.outline)


def stair_skirt_footprints(model: ResolvedModel, storey: str):
    """``(stair tag, plan footprint)`` of each skirt board on ``storey``: its toe runs past
    the stair outline, and the base butts it there."""
    from shapely.geometry import Polygon

    from typehaus.resolve.framing.footprint import member_footprint

    for stair in model.stairs:
        if stair.storey != storey:
            continue
        for member in stair.members:
            if member.category == "stair_skirt":
                yield stair.tag, Polygon(member_footprint(member)[0])


def _casing_footprints(model: ResolvedModel, room: ResolvedRoom, floor_z: float, height: float):
    """``(tag, footprint)`` for each casing piece on this storey that stands in the base band.

    Any room's casing, not only this room's: a closet's base butts the mud room's casing
    on the far side of the shared door.
    """
    from shapely.geometry import Polygon

    top = floor_z + height
    for casing in model.door_casings:
        if casing.storey != room.storey:
            continue
        for piece in casing.pieces:
            if len(piece.outline) >= 3 and piece.z0_m < top and piece.z1_m > floor_z:
                yield casing.opening_ref, Polygon(piece.outline)


def _subtract(keep, cut):
    out = []
    for a, b in keep:
        pieces = [(a, b)]
        for c, d in cut:
            pieces = [part for (p, q) in pieces
                      for part in ((p, min(q, c)), (max(p, d), q)) if part[1] - part[0] > 1e-9]
        out.extend(pieces)
    return out


def _cut(ring, kept, wood, owned):
    """Split ``kept`` at every vertex, wall end and wood-band edge: ``(s0, s1, offset)``."""
    stations = (ring_vertices(ring) + [s for a, b, _ in wood for s in (a, b)]
                + [s for _wall, (a, b) in owned for s in (a, b)])
    pieces = []
    for a, b in kept:
        cuts = sorted({a, b, *(s for s in stations if a < s < b)})
        for p, q in zip(cuts, cuts[1:], strict=False):
            if q - p < 1e-6:
                continue
            mid = (p + q) / 2.0
            offset = max((o for c, d, o in wood if c <= mid <= d), default=0.0)
            pieces.append((p, q, offset))
    return pieces


def _runs(room, kind, scope: TrimScope, ring, perimeter, pieces, arcs, breaks, floor_z,
          height) -> list[ResolvedBaseRun]:
    vertices = ring_vertices(ring) + [perimeter]

    def at_vertex(s: float) -> bool:
        return any(abs(s - v) < 1e-6 for v in vertices)

    t = _SKIN_M.get(kind, scope.thickness_m)
    out: list[ResolvedBaseRun] = []
    count: dict[str, int] = {}
    n = len(pieces)
    # Pieces wrap: the ring's last piece may meet its first at the seam vertex.
    for i, (s0, s1, offset) in enumerate(pieces):
        prev = pieces[i - 1] if n > 1 else None
        nxt = pieces[(i + 1) % n] if n > 1 else None
        start_corner = end_corner = None
        lead = trail = 0.0
        if prev is not None and _meets(prev[1], s0, perimeter) and at_vertex(s0):
            start_corner = corner_kind(ring, s0)
            # Inside: butt the incoming board's face. Outside: reach back to its face.
            lead = -(prev[2] + t) if start_corner == "inside" else prev[2]
        if nxt is not None and _meets(s1, nxt[0], perimeter) and at_vertex(s1):
            end_corner = corner_kind(ring, s1 % perimeter)
            trail = -nxt[2] if end_corner == "inside" else nxt[2] + t
        wall = _wall_at(arcs, (s0 + s1) / 2.0)
        if wall is None:
            continue
        p0, p1 = rp.point_at(ring, s0), rp.point_at(ring, s1)
        ex, ey = edge_direction(ring, (s0 + s1) / 2.0)
        start = (p0[0] - ex * lead, p0[1] - ey * lead)
        end = (p1[0] + ex * trail, p1[1] + ey * trail)
        nx, ny = -ey, ex  # into the room
        ring_out = (
            (start[0] + nx * offset, start[1] + ny * offset),
            (end[0] + nx * offset, end[1] + ny * offset),
            (end[0] + nx * (offset + t), end[1] + ny * (offset + t)),
            (start[0] + nx * (offset + t), start[1] + ny * (offset + t)),
        )
        length = (s1 - s0) + lead + trail
        if length < _MIN_PIECE_M:
            continue
        index = count.get(wall.tag, 0)
        count[wall.tag] = index + 1
        touching = tuple(sorted({tag for a, b, tag in breaks
                                 if abs(a - s1) < 1e-6 or abs(b - s0) < 1e-6}))
        material = (scope.standard.base_material_for(room.tag) if kind == "trim"
                    else room.floor_finish)
        out.append(ResolvedBaseRun(
            uid=f"{room.uid}-base-{wall.uid}-{index}",
            tag=f"BASE-{room.tag}-{wall.tag}-{index}",
            storey=room.storey, room=room.tag, wall_tag=wall.tag, kind=kind,
            material_ref=material or "", thickness_m=t, height_m=height,
            piece=TrimPiece(name="base", outline=ring_out, z0_m=floor_z,
                            z1_m=floor_z + height, length_m=length, width_m=height),
            start_corner=start_corner, end_corner=end_corner, breaks=touching,
            offset_m=offset, profile=scope.standard.profile))
    return out


def _meets(a: float, b: float, perimeter: float) -> bool:
    return abs(a - b) < 1e-6 or abs(abs(a - b) - perimeter) < 1e-6


def _wall_at(arcs, s):
    best = None
    for wall, (a, b) in arcs:
        if a - 1e-9 <= s <= b + 1e-9 and (best is None or b - a > best[1][1] - best[1][0]):
            best = (wall, (a, b))
    return best[0] if best is not None else None
