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
* a non-wood paneling band from the floor (a tile surround). A wood band carries the base
  on its face instead, offset by its thickness.

What survives is cut at every corner into straight pieces, butt-jointed: at an inside
corner the incoming piece runs to the far face and the outgoing one butts it; at an
outside corner the incoming one runs past by the outgoing one's depth.
"""

from __future__ import annotations

from typehaus.resolve import room_perimeter as rp
from typehaus.resolve.interior_trim_scope import TrimScope, base_kind, face_function, is_finish
from typehaus.resolve.model import ResolvedModel, ResolvedRoom
from typehaus.resolve.model_trim import ResolvedBaseRun, TrimPiece
from typehaus.resolve.room_walls import _TOUCH_M, bounding_wall_arcs

# How far a box may stand off the face and still be against it: a fridge's 1" air gap.
_AGAINST_M = 2 * 0.0254
# A stair-well ledge narrower than this is not floor a base could sit on.
_WELL_LEDGE_M = 4 * 0.0254
# A band starting this close to the floor is "from the floor".
_FROM_FLOOR_M = 0.01
# A finished piece shorter than this is corner noise, not a board anyone would cut.
_MIN_PIECE_M = 2 * 0.0254


def resolve_base_runs(plan, model: ResolvedModel, scope: TrimScope) -> None:
    for room in sorted(scope.rooms.values(), key=lambda r: r.uid):
        kind = base_kind(scope, room)
        if kind == "none":
            continue
        model.base_runs.extend(_room_runs(plan, model, scope, room, kind))


def _room_runs(plan, model: ResolvedModel, scope: TrimScope, room: ResolvedRoom,
               kind: str) -> list[ResolvedBaseRun]:
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient

    ring = _corners_only(list(orient(Polygon(room.clear_face), 1.0).exterior.coords)[:-1])
    perimeter = rp.perimeter_length(ring)
    floor_z, _structural = scope.floors(model, room)
    height = scope.standard.base_height.meters
    arcs = bounding_wall_arcs(model, room, ring, scope.body)

    finish, bare, owned = [], [], []
    for wall, (s0, s1) in arcs:
        # Trim each arc back by the touch band so a bare neighbour cannot nick a corner. An
        # end at the ring's seam is where cyclic_span split one run in two, not a run's end.
        a = s0 if s0 <= 1e-9 else s0 + _TOUCH_M
        b = s1 if s1 >= perimeter - 1e-9 else s1 - _TOUCH_M
        if b <= a:
            continue
        owned.append((wall, (a, b)))
        mid = (a + b) / 2.0
        point, outward = _point_and_outward(ring, mid)
        function = face_function(wall, point, outward, floor_z, floor_z + height)
        (finish if is_finish(function) else bare).append((a, b))

    breaks: list[tuple[float, float, str]] = [(a, b, "bare face") for a, b in bare]
    hosts = {wall.tag for wall, _span in arcs}
    for opening in model.openings:
        if opening.is_door and opening.host_wall in hosts:
            for a, b in _one_door(model, ring, room, scope, opening):
                breaks.append((a, b, opening.tag))
    for a, b in rp.floor_opening_intervals(plan, ring, room.storey, _WELL_LEDGE_M):
        breaks.append((a, b, "floor opening"))
    for tag, polygon in _obstacles(plan, model, scope, room, floor_z):
        for a, b in rp.fronting_intervals(ring, [polygon], _AGAINST_M):
            breaks.append((a, b, tag))
    wood: list[tuple[float, float, float]] = []
    for band in model.panelings:
        if band.room != room.tag or band.band_z0_m > _FROM_FLOOR_M or not band.outline:
            continue
        material = scope.materials.get(band.material_ref)
        spans = rp.fronting_intervals(ring, [Polygon(band.outline)], _TOUCH_M)
        if getattr(material, "species", None):
            offset = 0.0 if band.replaces_wall_finish else band.thickness_m
            wood.extend((a, b, offset) for a, b in spans)
        else:
            breaks.extend((a, b, band.tag) for a, b in spans)

    kept = _subtract(rp.merged_intervals(finish, perimeter),
                     rp.merged_intervals([(a, b) for a, b, _ in breaks], perimeter))
    pieces = _cut(ring, kept, wood, owned)
    return _runs(room, kind, scope, ring, perimeter, pieces, owned, breaks, floor_z, height)


def _one_door(model, ring, room, scope: TrimScope, opening) -> list[tuple[float, float]]:
    return rp.door_intervals(model, ring, room.storey,
                             lambda o: scope.base_break_half_width(o)
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


def _subtract(keep, cut):
    out = []
    for a, b in keep:
        pieces = [(a, b)]
        for c, d in cut:
            pieces = [part for (p, q) in pieces
                      for part in ((p, min(q, c)), (max(p, d), q)) if part[1] - part[0] > 1e-9]
        out.extend(pieces)
    return out


def _vertices(ring) -> list[float]:
    s, out = 0.0, []
    for i in range(len(ring)):
        out.append(s)
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % len(ring)]
        s += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return out


def _corners_only(ring: list) -> list:
    """``ring`` without its collinear vertices: a straight face is one board, not two."""
    out = []
    for i, (bx, by) in enumerate(ring):
        (ax, ay), (cx, cy) = ring[i - 1], ring[(i + 1) % len(ring)]
        u = ((bx - ax), (by - ay))
        v = ((cx - bx), (cy - by))
        nu, nv = (u[0] ** 2 + u[1] ** 2) ** 0.5, (v[0] ** 2 + v[1] ** 2) ** 0.5
        if nu < 1e-9 or nv < 1e-9:
            continue
        if abs(u[0] * v[1] - u[1] * v[0]) / (nu * nv) > 1e-4 or u[0] * v[0] + u[1] * v[1] < 0:
            out.append((bx, by))
    return out if len(out) >= 3 else ring


def _cut(ring, kept, wood, owned):
    """Split ``kept`` at every vertex, wall end and wood-band edge: ``(s0, s1, offset)``."""
    stations = (_vertices(ring) + [s for a, b, _ in wood for s in (a, b)]
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


def _point_and_outward(ring, s):
    """The point at ``s`` and the unit vector from it into the wall (right of a CCW edge)."""
    x, y = rp.point_at(ring, s)
    ex, ey = _edge_direction(ring, s)
    return (x, y), (ey, -ex)


def _edge_direction(ring, s):
    vertices = _vertices(ring)
    index = max(i for i, v in enumerate(vertices) if v <= s + 1e-9)
    (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % len(ring)]
    length = max(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5, 1e-12)
    return (x1 - x0) / length, (y1 - y0) / length


def _corner(ring, s_vertex) -> str:
    """``inside`` at a convex vertex of the room (a left turn of a CCW ring), else outside."""
    vertices = _vertices(ring)
    index = min(range(len(vertices)), key=lambda i: abs(vertices[i] - s_vertex))
    (ax, ay), (bx, by), (cx, cy) = (ring[index - 1], ring[index],
                                    ring[(index + 1) % len(ring)])
    cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
    return "inside" if cross > 0 else "outside"


def _runs(room, kind, scope: TrimScope, ring, perimeter, pieces, arcs, breaks, floor_z,
          height) -> list[ResolvedBaseRun]:
    vertices = _vertices(ring) + [perimeter]

    def at_vertex(s: float) -> bool:
        return any(abs(s - v) < 1e-6 for v in vertices)

    t = scope.thickness_m
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
            start_corner = _corner(ring, s0)
            # Inside: butt the incoming board's face. Outside: reach back to its face.
            lead = -(prev[2] + t) if start_corner == "inside" else prev[2]
        if nxt is not None and _meets(s1, nxt[0], perimeter) and at_vertex(s1):
            end_corner = _corner(ring, s1 % perimeter)
            trail = -nxt[2] if end_corner == "inside" else nxt[2] + t
        wall = _wall_at(arcs, (s0 + s1) / 2.0)
        if wall is None:
            continue
        p0, p1 = rp.point_at(ring, s0), rp.point_at(ring, s1)
        ex, ey = _edge_direction(ring, (s0 + s1) / 2.0)
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
        material = scope.standard.material_ref if kind == "trim" else room.floor_finish
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
