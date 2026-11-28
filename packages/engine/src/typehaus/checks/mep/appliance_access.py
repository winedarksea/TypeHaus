"""``mep.attic_appliance_access`` - IMC 2018 306.3, appliances in attics.

Minnesota adopts the 2018 IMC (Minn. R. 1346.0050); part 1346.0306 amends only 306.5, so 306.3
stands as published. An attic holding an appliance that needs service takes:

* an opening at least 20 x 30 in. and a passageway at least 30 in. high and 22 in. wide, large
  enough to remove the largest appliance;
* a passageway at most 20 ft long along its centreline, or 50 ft where it is 6 ft or more high
  and 22 in. wide for its whole length (exception 2);
* continuous solid flooring at least 24 in. wide along the passageway;
* a level service space at least 30 x 30 in. at the service side.

An attic is a room whose ceiling is a ``FollowRoof`` and whose occupancy is not habitable; the
appliance is ``Equipment`` that is not a passive duct box or installed in another unit. The
route is the shortest path of a 22 in. disc over the floor deck, round every obstruction (what
stands in the first 30 in. over the floor, runs, a low roof; a roof's lining comes off its
headroom), from the room's door to a 30 in. square in front of the unit's required clearance,
measured from the unit's base (cabinet, pad, and what is piped to it where it enters the zone).
Not read: exception 1, a door leaf's swing, lighting and receptacle (306.3.1, see
``electrical.equipment_space_lighting``), and the route up to the attic (the stair).
"""

from __future__ import annotations

import heapq
import math
from functools import lru_cache
from typing import NamedTuple

from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.prepared import prep

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import EquipmentKind, Occupancy
from typehaus.model.refs import FollowRoof
from typehaus.resolve.overlay import difference, intersection, union_all

CID = "mep.attic_appliance_access"
CODE = "MN Mechanical Code (Minn. R. 1346.0050, IMC 2018) 306.3"

IN = 0.0254
FT = 0.3048
PASSAGE_H, PASSAGE_W = 30 * IN, 22 * IN
TALL_H = 72 * IN
MAX_LEN, MAX_LEN_TALL = 20 * FT, 50 * FT
FLOOR_W, SERVICE = 24 * IN, 30 * IN
OPEN_W, OPEN_H = 20 * IN, 30 * IN
#: A body this close over the floor (a flush grille, finish noise) is not an obstruction.
FLUSH_M = 0.5 * IN
_PASSIVE = frozenset({EquipmentKind.DUCT_MANIFOLD, EquipmentKind.PLENUM,
                      EquipmentKind.MIXING_BOX})
_HABITABLE = frozenset({
    Occupancy.BEDROOM, Occupancy.BATHROOM, Occupancy.KITCHEN, Occupancy.LIVING,
    Occupancy.DINING, Occupancy.MEDIA, Occupancy.OFFICE, Occupancy.HOBBY,
    Occupancy.STUDY_CLOSET, Occupancy.LAUNDRY, Occupancy.HALLWAY, Occupancy.FOYER,
    Occupancy.STAIR})
_SKIP_SOLIDS = frozenset({"ceiling", "insulation"})
_RUNS = ("pipe", "conduit")
_LATTICE_M, _MIN_CELL_M = 4 * IN, 0.5 * IN
_SNAP_M = 1e-4


class Route(NamedTuple):
    length_m: float          # opening -> appliance base along the centreline
    points: tuple            # centreline vertices, opening to service-square centre
    door: str = ""


def attic_rooms(ctx: CheckContext) -> dict[str, object]:
    """Plan rooms whose ceiling follows the roof and that nobody lives in."""
    return {r.tag: r for r in ctx.plan.all_elements()
            if r.element_kind == "Room" and isinstance(r.ceiling, FollowRoof)
            and r.occupancy not in _HABITABLE}


def _units(ctx: CheckContext, rooms: dict) -> list[tuple[object, object]]:
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    found = []
    for el in ctx.plan.all_elements():
        obj = objects.get(el.tag)
        if (el.element_kind == "Equipment" and el.kind not in _PASSIVE and obj is not None
                and not getattr(el, "installed_in_ref", None) and obj.room in rooms):
            found.append((el, obj))
    return sorted(found, key=lambda pair: pair[0].tag)


class _Head:
    """Clear height over the walking surface at a point: structure, less the roof lining."""

    def __init__(self, ctx: CheckContext, room_tag: str, floor_z: float) -> None:
        from typehaus.resolve.coatings import layer_depth_m
        from typehaus.resolve.overhead import OverheadIndex
        from typehaus.resolve.roof_geometry import roof_slope_factor

        model = ctx.model
        self._floor_z = floor_z
        self._index = OverheadIndex(model)
        el = ctx.plan.by_tag(room_tag)
        roof = next((r for r in model.roofs if r.tag == el.ceiling.roof_ref), None)
        lining = sum(layer_depth_m(ctx.plan.library, layer)
                     for c in model.ceilings if c.room_ref == room_tag for layer in c.layers)
        self._lining = {el.ceiling.roof_ref: lining * roof_slope_factor(roof)} if roof else {}
        self.at = lru_cache(maxsize=None)(self._at)

    def _at(self, x: float, y: float) -> float:
        over = self._index.lowest_above(x, y, self._floor_z)
        if over is None:
            return math.inf
        return over.z_m - self._lining.get(over.tag, 0.0) - self._floor_z


def _low_headroom(head: _Head, bounds: tuple, level: float):
    """Plan region where the clear height is under ``level``; a 4 in. lattice, refined to
    1/2 in. along its edge (a feature narrower than the lattice is not seen)."""
    x0, y0, x1, y1 = bounds
    nx, ny = math.ceil((x1 - x0) / _LATTICE_M), math.ceil((y1 - y0) / _LATTICE_M)
    cells: list = []

    def visit(ax: float, ay: float, bx: float, by: float) -> None:
        low = [head.at(px, py) < level for px, py in ((ax, ay), (bx, ay), (ax, by), (bx, by))]
        if all(low):
            cells.append(box(ax, ay, bx, by))
        elif any(low):
            if bx - ax <= _MIN_CELL_M * 1.01:
                if head.at((ax + bx) / 2, (ay + by) / 2) < level:
                    cells.append(box(ax, ay, bx, by))
                return
            mx, my = (ax + bx) / 2, (ay + by) / 2
            for cx0, cy0, cx1, cy1 in ((ax, ay, mx, my), (mx, ay, bx, my),
                                       (ax, my, mx, by), (mx, my, bx, by)):
                visit(cx0, cy0, cx1, cy1)

    for i in range(nx):
        for j in range(ny):
            visit(x0 + i * _LATTICE_M, y0 + j * _LATTICE_M,
                  x0 + (i + 1) * _LATTICE_M, y0 + (j + 1) * _LATTICE_M)
    return union_all(cells)


def _footprint(ring) -> Polygon | None:
    poly = Polygon(ring)
    if len(ring) < 3 or poly.area < 1e-8:
        return None
    return poly if poly.is_valid else poly.buffer(0)


def _run_pieces(ctx: CheckContext):
    """(run, plan shape, z0, z1) of every pipe and conduit segment that has an elevation."""
    for run in (*ctx.model.pipe_runs, *ctx.model.conduits):
        diameter = (getattr(run, "bundle_diameter_m", None) or getattr(run, "diameter_m", None)
                    or getattr(run, "trade_size_m", 0.0))
        for i in range(len(run.path) - 1 if run.z_m else 0):
            z = (run.z_m[i], run.z_m[i + 1])
            yield (run, LineString(run.path[i:i + 2]).buffer(diameter / 2),
                   min(z) - diameter / 2, max(z) + diameter / 2)


def _obstructions(ctx: CheckContext, floor_z: float, height: float, room: Polygon) -> list:
    """Footprints of everything standing in ``floor_z .. floor_z + height`` over the room."""
    ceiling_z = floor_z + height
    zone = room.buffer(0.01)
    found: list = []

    def take(poly, z0, z1) -> None:
        z0 = floor_z if z0 is None else z0
        if poly is not None and z1 is not None and z1 > floor_z + FLUSH_M \
                and z0 < ceiling_z and poly.intersects(zone):
            found.append(poly)

    for obj in ctx.model.canvas_objects:
        take(_footprint(obj.footprint), obj.body_z0_m, obj.body_z1_m)
    for solid in ctx.model.solids:
        # A run's sweep outline is its bounding box; the runs below are read per segment.
        if solid.category not in _SKIP_SOLIDS and not solid.category.startswith(_RUNS):
            take(_footprint(solid.outline), solid.z0_m, solid.z1_m)
    for _run, poly, z0, z1 in _run_pieces(ctx):
        take(poly, z0, z1)
    return found


def _floor_region(ctx: CheckContext, floor, floor_z: float):
    """The solid flooring: the deck less its open voids and any flush grille through it."""
    deck = Polygon(floor.deck_outline, holes=[list(v) for v in floor.open_voids])
    grilles = [p for o in ctx.model.canvas_objects if o.kind == "Register"
               and o.body_z1_m is not None and abs(o.body_z1_m - floor_z) <= FLUSH_M
               and (p := _footprint(o.footprint)) is not None]
    return _polygonal(difference(deck, _polygonal(grilles))) if grilles else deck


def _reflex_vertices(poly: Polygon) -> list[tuple[float, float]]:
    out = []
    shaped = orient(poly)
    for ring in (shaped.exterior, *shaped.interiors):
        pts = list(ring.coords)[:-1]
        for i, p in enumerate(pts):
            a, b = pts[i - 1], pts[(i + 1) % len(pts)]
            if (p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0]) < -1e-12:
                out.append(p)
    return out


def _shortest(region, start: tuple, goals: list[tuple]):
    """A* over the reflex vertices: ``(vertices, length)`` to the nearest reachable goal in the
    part of ``region`` holding ``start``, else ``None``."""
    part = next((g for g in getattr(region, "geoms", [region])
                 if g.buffer(_SNAP_M).covers(Point(start))), None)
    if part is None:
        return None
    cover = prep(part.buffer(_SNAP_M))
    goals = [g for g in goals if cover.covers(Point(g))]
    if not goals:
        return None
    nodes = [start, *goals, *_reflex_vertices(part)]
    ends = set(range(1, 1 + len(goals)))

    def estimate(i: int) -> float:
        return min(math.dist(nodes[i], nodes[k]) for k in ends)

    best, came = {0: 0.0}, {}
    queue = [(estimate(0), 0.0, 0)]
    while queue:
        _f, dist, i = heapq.heappop(queue)
        if i in ends:
            path = [i]
            while path[-1] != 0:
                path.append(came[path[-1]])
            return [nodes[k] for k in reversed(path)], dist
        if dist > best.get(i, math.inf):
            continue
        for j in range(len(nodes)):
            step = math.dist(nodes[i], nodes[j])
            if j != i and dist + step < best.get(j, math.inf) and cover.covers(
                    LineString([nodes[i], nodes[j]])):
                best[j], came[j] = dist + step, i
                heapq.heappush(queue, (dist + step + estimate(j), dist + step, j))
    return None


def _service_frame(obj, zone_ring):
    """(u, v, zone polygon): u points from the unit out of its service side; ``None`` if the
    zone is not a rectangle."""
    zone = Polygon(zone_ring)
    pts = list(zone.exterior.coords)[:-1]
    if len(pts) != 4 or zone.area < 1e-6:
        return None
    e1 = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
    e2 = (pts[2][0] - pts[1][0], pts[2][1] - pts[1][1])
    if abs(e1[0] * e2[0] + e1[1] * e2[1]) > 1e-6 * math.hypot(*e1) * math.hypot(*e2):
        return None
    norm = math.hypot(*e1)
    axes = [(e1[0] / norm, e1[1] / norm), (-e1[1] / norm, e1[0] / norm)]
    toward = (zone.centroid.x - obj.position[0], zone.centroid.y - obj.position[1])
    u = max(axes, key=lambda a: abs(a[0] * toward[0] + a[1] * toward[1]))
    if u[0] * toward[0] + u[1] * toward[1] < 0:
        u = (-u[0], -u[1])
    return u, (-u[1], u[0]), zone


def _service_squares(base: Polygon, u, v, zone: Polygon):
    """30 in. squares in front of the unit's base, slid along the service face."""
    proj = lambda p, a: p[0] * a[0] + p[1] * a[1]  # noqa: E731
    front = max(proj(p, u) for p in base.exterior.coords)
    lat = [proj(p, v) for p in zone.exterior.coords]
    lo, hi = min(lat) + SERVICE / 2, max(lat) - SERVICE / 2
    centres = [(lo + hi) / 2] if hi < lo else [lo + k * (hi - lo) / 20 for k in range(21)]
    squares = []
    for c in centres:
        near, far, left, right = front, front + SERVICE, c - SERVICE / 2, c + SERVICE / 2
        ring = [(u[0] * a + v[0] * b, u[1] * a + v[1] * b)
                for a, b in ((near, left), (near, right), (far, right), (far, left))]
        mid = (u[0] * (front + SERVICE / 2) + v[0] * c, u[1] * (front + SERVICE / 2) + v[1] * c)
        squares.append((Polygon(ring), mid))
    return squares


def _seed(eroded, door_xy, room: Polygon):
    """(point on the room's face by the door, first centreline point 11 in. inside it)."""
    from shapely.ops import nearest_points

    centre = Point(door_xy)
    edge = room.exterior.interpolate(room.exterior.project(centre))
    gap = math.dist((edge.x, edge.y), door_xy)
    if gap < 1e-9 or room.contains(centre):
        return None
    inward = ((edge.x - door_xy[0]) / gap, (edge.y - door_xy[1]) / gap)
    reach = PASSAGE_W / 2 + 0.01 * IN
    seed = Point(edge.x + inward[0] * reach, edge.y + inward[1] * reach)
    if not eroded.buffer(_SNAP_M).covers(seed):
        near = min(getattr(eroded, "geoms", [eroded]), key=lambda g: g.distance(seed))
        if near.distance(seed) > PASSAGE_W / 2:
            return None
        seed = nearest_points(near, seed)[0]
    return (edge.x, edge.y), (seed.x, seed.y)


def _route(free, floor_core, door_xy, room: Polygon, squares) -> Route | None:
    """Best route from the door to one of ``squares`` through ``free``, on 24 in. flooring
    when ``floor_core`` (the deck eroded by half that) is given."""
    eroded = free.buffer(-PASSAGE_W / 2, quad_segs=4)
    if floor_core is not None and not eroded.is_empty:
        eroded = intersection(eroded, floor_core)
    if eroded.is_empty:
        return None
    seeded = _seed(eroded, door_xy, room)
    if seeded is None:
        return None
    face, seed = seeded
    goals = [mid for square, mid in squares if free.buffer(_SNAP_M).covers(square)]
    hit = _shortest(eroded, seed, goals)
    if hit is None:
        return None
    points, length = hit
    # Opening to the base: the lead-in, the path, and the square's near half.
    return Route(math.dist(face, seed) + length + SERVICE / 2, (face, *points))


def _polygonal(geometry):
    """Only the area of ``geometry`` (an overlay can leave lines and points); never a
    collection, which the overlay refuses to mix."""
    if isinstance(geometry, list):
        geometry = union_all(geometry)
    parts = [g for item in getattr(geometry, "geoms", [geometry])
             for g in getattr(item, "geoms", [item]) if isinstance(g, Polygon) and not g.is_empty]
    return union_all(parts) if parts else Polygon()


def _inches(m: float) -> str:
    return f"{m / IN:.1f} in"


def _feet(m: float) -> str:
    return f"{m / FT:.1f} ft"


def _opening_clear(opening) -> tuple[float | None, float | None]:
    sizing = getattr(opening, "sizing", None)
    if opening is None:
        return None, None
    if sizing is not None and sizing.clear_w_m is not None:
        return sizing.clear_w_m, sizing.clear_h_m
    return opening.width_m, getattr(opening, "height_m", None)


def _fits(section: tuple[float, float], width: float, height: float) -> bool:
    a, b = sorted(section)
    return (a <= width and b <= height) or (b <= width and a <= height)


def _samples(points, step: float = 0.05):
    line = LineString(points)
    return [line.interpolate(d) for d in
            [k * step for k in range(int(line.length / step))] + [line.length]]


def _grade_side(ctx, el, obj, room, zone_ring, floor, floor_z, head, doors):
    """(Result, message) for one service side of one unit."""
    tag = el.tag
    frame = _service_frame(obj, zone_ring)
    if frame is None:
        return Result.UNKNOWN, (f"{tag}: its service clearance is not a rectangle, so the "
                                "service side cannot be derived")
    u, v, zone = frame
    outline = Polygon(room.clear_face)
    footprint = _footprint(obj.footprint)
    # The base is what the unit stands on and what is piped to it where it enters the zone.
    own = {el.tag, getattr(el, "pan_drain_ref", None)}
    piped = [poly for run, poly, _z0, _z1 in _run_pieces(ctx)
             if (own & {run.tag, *getattr(run, "serves", ())}) and poly.intersects(zone)]
    standing = [p for s in ctx.model.solids if s.category not in _SKIP_SOLIDS
                and not s.category.startswith(_RUNS)
                and s.z0_m <= floor_z + FLUSH_M and s.z1_m > floor_z + FLUSH_M
                and (p := _footprint(s.outline)) is not None and p.intersects(footprint)]
    base = _polygonal([footprint, *standing, *piped]).convex_hull
    squares = _service_squares(base, u, v, zone)
    deck = _floor_region(ctx, floor, floor_z)
    core = deck.buffer(-FLOOR_W / 2)

    def free_at(level: float):
        blocked = _polygonal(_obstructions(ctx, floor_z, level, outline))
        low = _low_headroom(head, outline.bounds, level)
        return _polygonal(difference(difference(intersection(outline, deck), blocked),
                                     _polygonal(low)))

    free30 = free_at(PASSAGE_H)
    routes: dict[str, Route] = {}
    floorless = False
    for door_tag, xy in doors:
        hit = _route(free30, core, xy, outline, squares)
        floorless |= hit is None and _route(free30, None, xy, outline, squares) is not None
        if hit is not None:
            routes[door_tag] = hit._replace(door=door_tag)
    if not routes:
        why = ("the flooring under it is under 24 in. wide" if floorless else
               "a 22 in. wide, 30 in. high route is blocked, or no 30 x 30 in. level "
               "service space is clear")
        return Result.FAIL, f"{tag}: no passageway reaches the service side: {why}"
    route = min(routes.values(), key=lambda r: r.length_m)
    min_head = min(head.at(p.x, p.y) for p in _samples(route.points))
    facts = (f"route from {route.door} {_feet(route.length_m)} long, at least 22 in. wide "
             f"on 24 in. flooring, {_inches(min_head)} high at its lowest")
    fails: list[str] = []
    if route.length_m > MAX_LEN:
        # Exception 2: 6 ft high and 22 in. wide for its whole length allows 50 ft.
        free72 = free_at(TALL_H)
        tall = [r for _t, xy in doors if (r := _route(free72, core, xy, outline, squares))]
        shortest = min((r.length_m for r in tall), default=None)
        if shortest is None or shortest > MAX_LEN_TALL:
            fails.append(f"longer than 20 ft ({_feet(route.length_m)}) and no 6 ft high "
                         "route within 50 ft")
        else:
            facts += f"; the 6 ft x 22 in. route is {_feet(shortest)} (limit 50 ft)"
    opening = next((d for d in doors_by_tag(ctx, room) if d.tag == route.door), None)
    gaps: list[str] = []
    clear_w, clear_h = _opening_clear(opening)
    if clear_w is None or clear_h is None:
        gaps.append(f"the size of {route.door} is not resolved")
    elif clear_w < OPEN_W or clear_h < OPEN_H:
        fails.append(f"opening {route.door} clear {_inches(clear_w)} x {_inches(clear_h)}, "
                     "under 20 x 30 in.")
    if obj.body_z0_m is None or obj.body_z1_m is None:
        gaps.append("the appliance height is not modelled")
    else:
        pts = list(footprint.exterior.coords)
        sides = sorted((math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2])))
        section = (sides[0], obj.body_z1_m - obj.body_z0_m)
        size = f"{_inches(section[0])} x {_inches(section[1])}"
        if clear_w is not None and clear_h is not None and not _fits(section, clear_w, clear_h):
            fails.append(f"the appliance's {size} section does not fit {route.door}")
        if not _fits(section, PASSAGE_W, min_head):
            fails.append(f"the appliance's {size} section does not fit the passageway")
    if fails:
        return Result.FAIL, f"{tag}: {'; '.join(fails)} ({facts})"
    if gaps:
        return Result.UNKNOWN, f"{tag}: {'; '.join(gaps)} ({facts})"
    return Result.PASS, f"{tag}: IMC 306.3 met: {facts}; 30 x 30 in. level service space clear"


def doors_by_tag(ctx, room) -> list:
    from typehaus.resolve.room_openings import room_doors, room_passages

    return room_doors(ctx.model, room) + room_passages(ctx.model, room)


@check(Tier.CODE, CID)
def attic_appliance_access(ctx: CheckContext) -> list[Finding]:
    """IMC 306.3 - every appliance in an attic has an opening, a passage, floor and space."""
    from typehaus.resolve.geometry import opening_center
    from typehaus.resolve.walking_surface import surfaces_at

    rooms = attic_rooms(ctx)
    units = _units(ctx, rooms)
    if not units:
        return [by_result(CID, Result.NOT_APPLICABLE, "no appliance stands in a room under "
                          "the roof that is not lived in", (), CODE)]
    resolved = {r.tag: r for r in ctx.model.rooms}
    out: list[Finding] = []
    heads: dict[str, _Head] = {}
    for el, obj in units:
        room = resolved.get(obj.room)
        tags = (el.tag, obj.room)
        floors = {f.tag: f for f in ctx.model.floors if f.storey == obj.storey}
        landed = [s for s in surfaces_at(ctx.model, obj.position) if s.deck_tag in floors]
        if room is None or not room.clear_face or not landed:
            out.append(by_result(CID, Result.UNKNOWN, f"{el.tag}: the room or the floor "
                                 "under it is not resolved", tags, CODE))
            continue
        surface = min(landed, key=lambda s: s.deck_top_m)
        if surface.surface_m is None:
            out.append(by_result(CID, Result.UNKNOWN, f"{el.tag}: the floor finish depth "
                                 "is not stated, so the walking surface is not known",
                                 tags, CODE))
            continue
        doors = []
        for opening in doors_by_tag(ctx, room):
            wall = ctx.model.wall(opening.host_wall)
            centre = opening_center(wall, opening) if wall is not None else None
            if centre is not None:
                doors.append((opening.tag, centre))
        if not doors:
            out.append(by_result(CID, Result.UNKNOWN, f"{el.tag}: {obj.room} has no modelled "
                                 "door or opening to start the passageway", tags, CODE))
            continue
        if not obj.required_clearances:
            out.append(by_result(CID, Result.UNKNOWN, f"{el.tag}: its type declares no "
                                 "required clearance, so the service side is not known",
                                 tags, CODE))
            continue
        head = heads.setdefault(obj.room, _Head(ctx, obj.room, surface.surface_m))
        floor = floors[surface.deck_tag]
        verdicts = [_grade_side(ctx, el, obj, room, ring, floor, surface.surface_m, head, doors)
                    for ring in obj.required_clearances]
        rank = (Result.FAIL, Result.UNKNOWN, Result.PASS).index
        result = min((r for r, _ in verdicts), key=rank)
        message = " | ".join(m for r, m in verdicts if r is result)
        out.append(by_result(CID, result, message, tags, CODE))
    return out
