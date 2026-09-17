"""Room-shaped graph edits: draw a rectangle of walls with its room, and delete a wall with
everything that follows from it (P1).

Both build on a :class:`GraphView` so each step reads the previous one's result: a rectangle
may T-split the same wall twice, and a delete heals and merges on the post-delete graph.
"""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import LineString, Point, Polygon, box

from typehaus.model.enums import Occupancy
from typehaus.model.plan import PlanModel
from typehaus.model.remap import Impact, MutationResult, ReferenceRemap, remap_ops_for
from typehaus.model.spatial import Room
from typehaus.quantities.point import pt
from typehaus.source.macros_common import (
    _PLACEABLE_KINDS,
    ROOM_BOUNDARY_NODE_TOLERANCE_M,
    SNAP_M,
    XY,
    MacroError,
    _meters,
    _next_plan_tag,
    _nodes,
    _openings,
    _point_expr_m,
    _rooms,
    _round_len,
    _storey_file_hint,
    _walls,
)
from typehaus.source.macros_graph import (
    GraphView,
    axis_length,
    degree,
    references_to,
    station_map,
    station_of,
    wall_axis,
)
from typehaus.source.macros_split import heal_ops, opening_span, split_wall_ops, uncovered_refs
from typehaus.source.ops import PatchOp
from typehaus.source.serialize import element_add_op

MIN_SIDE_M = 0.3
# A corner this close to a node or wall, but not on it, would leave a sliver: refuse.
NEAR_MISS_M = 0.15


def _storey_faces(plan: PlanModel, storey: str) -> list[Polygon]:
    from typehaus.resolve.rooms import _storey_faces as faces

    return faces(plan, storey)


def _seg_distance(axis, p) -> tuple[float, float]:
    """(parameter t, distance) of ``p`` against the segment ``axis``."""
    length = axis_length(axis)
    t = station_of(axis, p) / length if length else 0.0
    return t, LineString(axis).distance(Point(p))


# --- draw_room_rect ----------------------------------------------------------

def draw_room_rect(plan: PlanModel, storey: str, a: XY, b: XY, assembly: str, occupancy: str,
                   *, floor_finish: str | None = None,
                   hint_file: str | None = None) -> MutationResult:
    """Four walls on the rectangle ``a``..``b`` plus a Room seeded at its centre.

    Corners reuse a node within ``SNAP_M``, T-split a wall they land on, and refuse a near
    miss; walls already lying on an edge are kept. A room whose seed the rectangle swallows is
    re-seeded into the largest seedless face left over.
    """
    try:
        occ = Occupancy(occupancy)
    except ValueError as exc:
        raise MacroError(f"unknown occupancy {occupancy!r}") from exc
    if not any(s.tag == storey for s in plan.storeys):
        raise MacroError(f"no storey {storey!r}")
    xs = sorted((_meters(a[0]), _meters(b[0])))
    ys = sorted((_meters(a[1]), _meters(b[1])))
    if xs[1] - xs[0] < MIN_SIDE_M or ys[1] - ys[0] < MIN_SIDE_M:
        raise MacroError(f"rectangle sides must be at least {MIN_SIDE_M} m")
    inner = box(xs[0], ys[0], xs[1], ys[1]).buffer(-SNAP_M)
    for wall in _walls(plan, storey):
        axis = wall_axis(plan, storey, wall)
        if axis is not None and LineString(axis).intersects(inner):
            raise MacroError(f"wall {wall.tag} runs inside the rectangle")
    hint_file = _storey_file_hint(plan, storey) or hint_file
    view = GraphView(plan, storey)
    node_list = "NODES" if hint_file is not None or _nodes(plan, storey) else None
    wall_list = "WALLS" if hint_file is not None or _walls(plan, storey) else None
    corners = [(xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1])]
    for corner in corners:
        _node_at(view, corner, hint_file, node_list)
    for i, p in enumerate(corners):
        _edge_walls(view, (p, corners[(i + 1) % 4]), assembly, hint_file, wall_list)
    centre = ((xs[0] + xs[1]) / 2, (ys[0] + ys[1]) / 2)
    _claim_room(view, centre, box(xs[0], ys[0], xs[1], ys[1]), occ, floor_finish, hint_file)
    return view.result()


def _node_at(view: GraphView, p, hint_file, node_list) -> str:
    storey = view.storey
    nodes = _nodes(view.plan, storey)
    if nodes:
        near = min(nodes, key=lambda n: Point(n.position.xy_m).distance(Point(p)))
        d = Point(near.position.xy_m).distance(Point(p))
        if d <= SNAP_M:
            return near.tag
        if d < NEAR_MISS_M:
            raise MacroError(f"corner is {d:.3f} m from node {near.tag}; snap to it or move away")
    for wall in _walls(view.plan, storey):
        axis = wall_axis(view.plan, storey, wall)
        if axis is None:
            continue
        t, d = _seg_distance(axis, p)
        if d >= NEAR_MISS_M:
            continue
        if d > SNAP_M:
            raise MacroError(f"corner is {d:.3f} m off wall {wall.tag}; snap to it or move away")
        station, length = t * axis_length(axis), axis_length(axis)
        for op in _openings(view.plan, storey):
            span = opening_span(view.plan, op, wall, length) if op.host == wall.tag else None
            if span is not None and span[0] - SNAP_M < station < span[0] + span[1] + SNAP_M:
                raise MacroError(f"a wall would tee into opening {op.tag} on {wall.tag}")
        mid = _next_plan_tag(view.plan, "N-", view.minted)
        new_wall = _next_plan_tag(view.plan, "W-", view.minted)
        view.absorb(split_wall_ops(view.plan, storey, wall, t, mid, new_wall,
                                   hint_file=hint_file))
        return mid
    tag = _next_plan_tag(view.plan, "N-", view.minted)
    view.emit([PatchOp("add", "Node", tag, {"position": _point_expr_m(*p)},
                       hint_file=hint_file, hint_list=node_list, storey=storey)])
    return tag


def _edge_walls(view: GraphView, edge, assembly, hint_file, wall_list) -> None:
    """Walls for each gap between consecutive nodes on ``edge`` not already joined."""
    storey, length = view.storey, axis_length(edge)
    on_edge = sorted(
        (station_of(edge, n.position.xy_m), n.tag) for n in _nodes(view.plan, storey)
        if LineString(edge).distance(Point(n.position.xy_m)) <= SNAP_M)
    on_edge = [(s, tag) for s, tag in on_edge if -SNAP_M <= s <= length + SNAP_M]
    pairs = {frozenset((w.start_node, w.end_node)) for w in _walls(view.plan, storey)}
    for (_s1, n1), (_s2, n2) in zip(on_edge, on_edge[1:], strict=False):
        if n1 == n2 or frozenset((n1, n2)) in pairs:
            continue
        tag = _next_plan_tag(view.plan, "W-", view.minted)
        view.emit([PatchOp("add", "Wall", tag,
                           {"start_node": n1, "end_node": n2, "assembly": assembly},
                           hint_file=hint_file, hint_list=wall_list, storey=storey)])


def _claim_room(view: GraphView, centre, rect: Polygon, occ: Occupancy, floor_finish,
                hint_file) -> None:
    storey = view.storey
    faces = _storey_faces(view.plan, storey)
    face = next((f for f in faces if f.contains(Point(centre))), None)
    if face is None:
        raise MacroError("the rectangle does not close a face")

    def displaced(seed: Point) -> bool:
        # Swallowed by the new face, or left inside a new wall's body (a centred seed under
        # a partition drawn through the middle of its room) where no face claims it.
        return face.contains(seed) or (rect.buffer(ROOM_BOUNDARY_NODE_TOLERANCE_M).contains(seed)
                                       and not any(f.contains(seed) for f in faces))

    claim = True
    for room in [r for r in _rooms(view.plan, storey) if displaced(Point(r.seed.xy_m))]:
        seeds = [Point(r.seed.xy_m) for r in _rooms(view.plan, storey)]
        seedless = [f for f in faces
                    if not f.equals(face) and not any(f.contains(s) for s in seeds)]
        if not seedless:
            claim = False
            view.impacts.append(Impact(room.tag, "needs_review",
                                       f"{room.tag} already claims the rectangle; no room added"))
            continue
        spot = max(seedless, key=lambda f: f.area).representative_point()
        view.emit([PatchOp("update", "Room", room.tag, {"seed": _point_expr_m(spot.x, spot.y)})])
        view.impacts.append(Impact(room.tag, "carried",
                                   f"{room.tag} re-seeded outside the new rectangle"))
    if not claim:
        return
    tag = _next_plan_tag(view.plan, "RM-", view.minted)
    room = Room(tag=tag, seed=pt(_round_len(centre[0]), _round_len(centre[1])),
                occupancy=occ, floor_finish=floor_finish or None)
    view.emit([replace(element_add_op(room, tag=tag, hint_list="ROOMS", hint_file=hint_file),
                       storey=storey)])


# --- delete_wall -------------------------------------------------------------

def delete_wall(plan: PlanModel, storey: str, wall: str, *,
                keep_room: str | None = None) -> MutationResult:
    """Delete a wall: its openings go with it, attached placeables move to the nearest
    collinear survivor, orphaned nodes go, straight-through nodes heal, and rooms that now
    share a face merge into ``keep_room`` (or the larger)."""
    target = next((w for w in _walls(plan, storey) if w.tag == wall), None)
    if target is None:
        raise MacroError(f"no wall {wall!r} on storey {storey!r}")
    if keep_room is not None and keep_room not in {r.tag for r in _rooms(plan, storey)}:
        raise MacroError(f"no room {keep_room!r} on storey {storey!r}")
    for el, name in uncovered_refs(plan, wall, carried=set()):
        raise MacroError(f"{el.tag}.{name} names {wall}; re-point it before deleting")
    hosted = [o for o in _openings(plan, storey) if o.host == wall]
    for op in hosted:
        for el, name in references_to(plan, op.tag):
            raise MacroError(f"{el.tag}.{name} names opening {op.tag} on {wall}")
    faces = _storey_faces(plan, storey)
    before = {r.tag: next((f.area for f in faces if f.contains(Point(r.seed.xy_m))), 0.0)
              for r in _rooms(plan, storey)}
    view = GraphView(plan, storey)
    _rehost_off(view, target)
    view.absorb(MutationResult(
        ops=[*(PatchOp("delete", o.element_kind, o.tag, {}) for o in hosted),
             PatchOp("delete", "Wall", wall, {})],
        remap=ReferenceRemap(deleted=frozenset({wall, *(o.tag for o in hosted)})),
        deleted_tags=(*(o.tag for o in hosted), wall),
        impacts=tuple(Impact(o.tag, "left_behind", f"opening {o.tag} deleted with {wall}")
                      for o in hosted)))
    for node in (target.start_node, target.end_node):
        if degree(view.plan, storey, node) == 0 and not references_to(view.plan, node):
            view.absorb(MutationResult(ops=[PatchOp("delete", "Node", node, {})],
                                       remap=ReferenceRemap(deleted=frozenset({node})),
                                       deleted_tags=(node,)))
        elif degree(view.plan, storey, node) == 2:
            _try_heal(view, node)
    _merge_rooms(view, before, keep_room)
    return view.result()


def _rehost_off(view: GraphView, wall) -> None:
    """Move placeables naming ``wall`` onto the nearest collinear wall that survives."""
    storey, plan = view.storey, view.plan
    axis = wall_axis(plan, storey, wall)
    survivors = []
    for other in _walls(plan, storey):
        oa = wall_axis(plan, storey, other)
        if other.tag != wall.tag and oa is not None and all(
                _line_distance(axis, p) <= SNAP_M for p in oa):
            survivors.append((other, oa))
    rehost: dict[str, str] = {}
    shift: dict[str, float] = {}
    flipped: set[str] = set()
    ops: list[PatchOp] = []
    for el in plan.storey_elements(storey):
        if not isinstance(el, _PLACEABLE_KINDS):
            continue
        att = getattr(getattr(el, "location", None), "attachment", None)
        on_att = att is not None and att.wall_ref == wall.tag
        on_ref = getattr(el, "wall_ref", None) == wall.tag
        if not (on_att or on_ref):
            continue
        if on_att:
            d = max(0.0, min(axis_length(axis), att.distance_from_start.meters))
            (x0, y0), (x1, y1) = axis
            f = d / (axis_length(axis) or 1.0)
            point = (x0 + f * (x1 - x0), y0 + f * (y1 - y0))
        else:
            point = el.position.xy_m if getattr(el, "position", None) is not None else None
        best = min(survivors, key=lambda s: LineString(s[1]).distance(Point(point)),
                   default=None) if point is not None else None
        if best is None:
            view.impacts.append(Impact(el.tag, "needs_review",
                                       f"{el.tag} names deleted wall {wall.tag}; no collinear "
                                       "wall survives to carry it"))
            continue
        other, oa = best
        if on_att:
            rehost[el.tag] = other.tag
            shift[el.tag], rev = station_map(axis, oa)
            if rev:
                flipped.add(el.tag)
        if on_ref and not on_att and att is not None:
            ops.append(PatchOp("update", el.element_kind, el.tag, {"wall_ref": other.tag}))
        elif on_ref:
            rehost[el.tag] = other.tag
        view.impacts.append(Impact(el.tag, "carried", f"{el.tag} re-hosted to {other.tag}"))
        if LineString(oa).distance(Point(point)) > SNAP_M:
            view.impacts.append(Impact(el.tag, "needs_review",
                                       f"{el.tag} now sits past the end of {other.tag}"))
    remap = ReferenceRemap(rehost=rehost, shift=shift, reversed=frozenset(flipped))
    for el in plan.storey_elements(storey):
        if el.tag in rehost:
            ops.extend(remap_ops_for(el, remap))
    view.absorb(MutationResult(ops=ops, remap=remap))


def _line_distance(axis, p) -> float:
    """Distance from ``p`` to the infinite line through ``axis``."""
    (x0, y0), (x1, y1) = axis
    length = axis_length(axis) or 1.0
    return abs((x1 - x0) * (y0 - p[1]) - (x0 - p[0]) * (y1 - y0)) / length


_SAME_WALL_SKIP = {"uid", "tag", "start_node", "end_node", "stacks_on"}


def _try_heal(view: GraphView, node: str) -> None:
    """Heal a straight-through node when both walls are the same wall in all but extent and
    nothing would be left for review."""
    storey = view.storey
    w1, w2 = [w for w in _walls(view.plan, storey) if node in (w.start_node, w.end_node)]
    if w1.model_dump(exclude=_SAME_WALL_SKIP) != w2.model_dump(exclude=_SAME_WALL_SKIP):
        return
    try:
        result = heal_ops(view.plan, storey, node)
    except MacroError:
        return
    if any(i.kind == "needs_review" for i in result.impacts):
        view.impacts.append(Impact(node, "needs_review", f"{node} left unhealed: "
                                   + "; ".join(i.reason for i in result.impacts)))
        return
    view.absorb(result)


def _merge_rooms(view: GraphView, area_before: dict[str, float], keep: str | None) -> None:
    storey = view.storey
    faces = _storey_faces(view.plan, storey)
    groups: dict[int, list] = {}
    for room in _rooms(view.plan, storey):
        index = next((i for i, f in enumerate(faces) if f.contains(Point(room.seed.xy_m))), None)
        if index is None:
            view.impacts.append(Impact(room.tag, "needs_review",
                                       f"{room.tag} no longer encloses a face"))
            continue
        groups.setdefault(index, []).append(room)
    for rooms in groups.values():
        if len(rooms) < 2:
            continue
        tags = [r.tag for r in rooms]
        survivor = keep if keep in tags else max(tags, key=lambda t: area_before.get(t, 0.0))
        for tag in tags:
            if tag == survivor:
                continue
            ops: list[PatchOp] = []
            for el, name in references_to(view.plan, tag):
                if name != "room":
                    raise MacroError(f"{el.tag}.{name} names room {tag}; cannot merge it")
                ops.append(PatchOp("update", el.element_kind, el.tag, {"room": survivor}))
            ops.append(PatchOp("delete", "Room", tag, {}))
            view.absorb(MutationResult(
                ops=ops, remap=ReferenceRemap(renamed={tag: survivor}), deleted_tags=(tag,),
                impacts=(Impact(tag, "left_behind", f"{tag} merged into {survivor}"),
                         *(Impact(o.tag, "carried", f"{o.tag} moved to {survivor}")
                           for o in ops[:-1]))))
