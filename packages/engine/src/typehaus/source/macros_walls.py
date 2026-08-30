"""Wall topology macros: draw, rubber-band stretch, split, and heal.

Split out of :mod:`typehaus.source.macros` along its ``# --- wall-draw``,
``# --- rubber-band stretch``, ``# --- split``, and ``# --- heal / merge`` bands. They share
one subject — the node/wall graph — and one hazard: every one of them changes identity or
connectivity, so they are the macros that emit a :class:`ReferenceRemap` and the ones whose
edits have to carry hosted openings, room seeds, and room contents along with them.
"""

from __future__ import annotations

from typehaus.model.elements import Wall
from typehaus.model.plan import PlanModel
from typehaus.model.remap import MutationResult, ReferenceRemap, remap_ops_for
from typehaus.source.macros_common import (
    _PLACEABLE_KINDS,
    ROOM_BOUNDARY_NODE_TOLERANCE_M,
    SNAP_M,
    XY,
    MacroError,
    _find_node_near,
    _meters,
    _next_tag,
    _nodes,
    _point_expr,
    _point_expr_m,
    _rooms,
    _walls,
)
from typehaus.source.macros_geometry import _collinear, _dist, _project_param
from typehaus.source.ops import PatchOp


def draw_wall(
    plan: PlanModel,
    storey: str,
    start: XY,
    end: XY,
    assembly: str,
    *,
    hint_file: str | None = None,
    tag: str | None = None,
) -> MutationResult:
    """Draw one wall between two points — the fundamental UI add flow (→ 21b).

    Endpoints snap to existing nodes within ``SNAP_M`` (automatic T-junction heal); otherwise
    a fresh ``Node`` is added. Emits at most two node adds + one wall add, all in one patch so
    undo removes the whole stroke atomically.
    """
    sx, sy = _meters(start[0]), _meters(start[1])
    ex, ey = _meters(end[0]), _meters(end[1])
    if (sx - ex) ** 2 + (sy - ey) ** 2 < SNAP_M ** 2:
        raise MacroError("degenerate wall: endpoints coincide")

    ops: list[PatchOp] = []
    node_list = "NODES" if any(_nodes(plan, storey)) else None
    minted_tags: list[str] = []

    def node_at(pt: XY, at_m: tuple[float, float]) -> str:
        existing = _find_node_near(plan, storey, at_m)
        if existing is not None:
            return existing.tag
        pending = _pending_nodes(plan, storey, minted_tags)
        new_tag = _next_tag(pending, "N-")
        minted_tags.append(new_tag)
        ops.append(PatchOp("add", "Node", new_tag,
                           {"position": _point_expr(pt[0], pt[1])},
                           hint_file=hint_file, hint_list=node_list))
        return new_tag

    a = node_at(start, (sx, sy))
    b = node_at(end, (ex, ey))
    wall_tag = tag or _next_tag(_walls(plan, storey), "W-")
    ops.append(PatchOp("add", "Wall", wall_tag,
                       {"start_node": a, "end_node": b, "assembly": assembly},
                       hint_file=hint_file, hint_list=_wall_list(plan, storey)))
    return MutationResult(ops=ops)


def _pending_nodes(plan: PlanModel, storey: str, minted: list[str]) -> list:
    class _T:
        def __init__(self, tag: str) -> None:
            self.tag = tag

    return [*_nodes(plan, storey), *(_T(t) for t in minted)]


def _wall_list(plan: PlanModel, storey: str) -> str | None:
    return "WALLS" if any(_walls(plan, storey)) else None


# --- rubber-band stretch -----------------------------------------------------

def move_nodes(
    plan: PlanModel, storey: str, node_tags: list[str], dx: float | str, dy: float | str
) -> MutationResult:
    """Translate a rigid node set by (dx, dy) — the atomic op behind stretch + driven dims.

    Every connected wall stretches/shrinks for free (walls reference nodes, not coordinates).
    Anchor-pinned nodes never move (§Driven dimensions); moving *only* pinned nodes is a
    rejected op, never a silent no-op.
    """
    dxm, dym = _meters(dx), _meters(dy)
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    movable = [t for t in node_tags if not getattr(by_tag.get(t), "anchored", False)]
    pinned = [t for t in node_tags if t not in movable]
    if not movable:
        raise MacroError(
            f"all requested nodes are anchor-pinned ({', '.join(pinned)}); nothing to move"
        )
    ops: list[PatchOp] = []
    for tag in movable:
        nd = by_tag.get(tag)
        if nd is None:
            raise MacroError(f"no node {tag!r} on storey {storey!r}")
        px, py = nd.position.xy_m
        ops.append(PatchOp("update", "Node", tag,
                           {"position": _point_expr_m(px + dxm, py + dym)}))
    # A completed room-boundary translation is a rigid move; a partial boundary selection
    # is a resize and intentionally leaves contents at their project coordinates.
    translated_rooms = _rooms_with_moved_boundaries(plan, storey, set(movable))
    for room in _rooms(plan, storey):
        if room.tag not in translated_rooms:
            continue
        x, y = room.seed.xy_m
        ops.append(PatchOp("update", "Room", room.tag,
                           {"seed": _point_expr_m(x + dxm, y + dym)}))
    for item in plan.storey_elements(storey):
        if (not isinstance(item, _PLACEABLE_KINDS)
                or getattr(item, "room", None) not in translated_rooms):
            continue
        location = getattr(item, "location", None)
        if location is not None and location.attachment is not None:
            continue
        x, y = item.position.xy_m
        ops.append(PatchOp("update", item.element_kind, item.tag,
                           {"position": _point_expr_m(x + dxm, y + dym)}))
    warnings = (f"pinned nodes held: {', '.join(pinned)}",) if pinned else ()
    return MutationResult(ops=ops, warnings=warnings)


def _rooms_with_moved_boundaries(plan: PlanModel, storey: str, moved_nodes: set[str]) -> set[str]:
    """Return rooms whose complete authored boundary node set participates in this move."""
    try:
        from shapely.geometry import Point, Polygon

        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        nodes = _nodes(plan, storey)
        translated: set[str] = set()
        for room in model.rooms:
            if room.storey != storey or len(room.clear_face) < 3:
                continue
            boundary = Polygon(room.clear_face).boundary
            boundary_nodes = {
                node.tag for node in nodes
                if boundary.distance(Point(node.position.xy_m))
                <= ROOM_BOUNDARY_NODE_TOLERANCE_M}
            if boundary_nodes and boundary_nodes <= moved_nodes:
                translated.add(room.tag)
        return translated
    except Exception:  # noqa: BLE001 - a half-authored room must not make node edits fail
        return set()


# --- split -------------------------------------------------------------------

def split_wall(plan: PlanModel, storey: str, wall_tag: str, at: XY) -> MutationResult:
    """Split a wall at a point — 1 wall → 2, the original uid staying with the a-side (#33).

    The survivor keeps ``wall_tag``; a fresh segment is added. A midnode is inserted, openings
    re-host to whichever segment their position falls in, and a :class:`ReferenceRemap` reports
    the identity change so hosted openings and stack refs carry through.
    """
    wall = next((w for w in _walls(plan, storey) if w.tag == wall_tag), None)
    if wall is None:
        raise MacroError(f"no wall {wall_tag!r} on storey {storey!r}")
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    a, b = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    if a is None or b is None:
        raise MacroError(f"wall {wall_tag!r} has an unresolved node")
    ax, ay = a.position.xy_m
    bx, by = b.position.xy_m
    px, py = _meters(at[0]), _meters(at[1])
    t = _project_param((ax, ay), (bx, by), (px, py))
    if not (SNAP_M < t < 1 - SNAP_M):
        raise MacroError("split point is at or beyond a wall end")

    mid_tag = _next_tag(_nodes(plan, storey), "N-")
    new_wall_tag = _next_tag(_walls(plan, storey), "W-")
    seg_fields = {"start_node": mid_tag, "end_node": wall.end_node, "assembly": wall.assembly}
    ops = [
        PatchOp("add", "Node", mid_tag,
                {"position": _point_expr_m(ax + t * (bx - ax), ay + t * (by - ay))},
                hint_list="NODES"),
        # survivor keeps the a-side: its end becomes the midnode
        PatchOp("update", "Wall", wall_tag, {"end_node": mid_tag}),
        PatchOp("add", "Wall", new_wall_tag, seg_fields, hint_list="WALLS"),
    ]
    remap, refit_ops, warnings = _rehost_openings(
        plan, storey, wall, new_wall_tag, t
    )
    ops.extend(refit_ops)
    return MutationResult(ops=ops, remap=remap, warnings=warnings)


def _rehost_openings(
    plan: PlanModel, storey: str, wall: Wall, new_tag: str, split_t: float
) -> tuple[ReferenceRemap, list[PatchOp], tuple[str, ...]]:
    """Re-host openings on the split wall onto the segment their position falls in."""
    rehost: dict[str, str] = {}
    warnings: list[str] = []
    for el in plan.storey_elements(storey):
        if getattr(el, "host", None) != wall.tag:
            continue
        along = _opening_param(el, wall, plan, storey)
        if along is not None and along > split_t:
            rehost[el.tag] = new_tag
            warnings.append(f"opening {el.tag} re-hosted to {new_tag}")
    remap = ReferenceRemap(renamed={}, rehost=rehost)
    ops: list[PatchOp] = []
    for el in plan.storey_elements(storey):
        if getattr(el, "host", None) == wall.tag:
            ops.extend(remap_ops_for(el, remap))
    return remap, ops, tuple(warnings)


def _opening_param(el: object, wall: Wall, plan: PlanModel, storey: str) -> float | None:
    """Fractional position (0..1) of an opening along its host wall, if determinable."""
    pos = getattr(el, "position", None)
    if pos is None or getattr(pos, "mode", None) != "from_node":
        return 0.5 if pos is not None else None  # centered → keeps a-side
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    a, b = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    anchor = by_tag.get(pos.node or wall.start_node)
    if a is None or b is None or anchor is None or pos.offset is None:
        return None
    length = _dist(a.position.xy_m, b.position.xy_m)
    if length == 0:
        return None
    base = 0.0 if anchor.tag == wall.start_node else 1.0
    frac = pos.offset.meters / length
    return base + frac if base == 0.0 else base - frac


# --- heal / merge ------------------------------------------------------------

def heal_walls(plan: PlanModel, storey: str, node_tag: str) -> MutationResult:
    """Fuse two collinear walls meeting at ``node_tag`` back into one edge (inverse of split).

    The survivor is the wall contributing the fused edge's a-node (#33). The shared node and
    the second wall are deleted; a :class:`ReferenceRemap` renames the absorbed wall to the
    survivor so hosted openings and refs follow.
    """
    incident = [w for w in _walls(plan, storey)
                if node_tag in (w.start_node, w.end_node)]
    if len(incident) != 2:
        raise MacroError(
            f"heal needs exactly two walls at {node_tag!r}, found {len(incident)}"
        )
    w1, w2 = incident
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    if not _collinear(w1, w2, node_tag, by_tag):
        raise MacroError(f"walls at {node_tag!r} are not collinear; cannot heal")
    # Survivor is the wall whose a-node is not the shared node (keeps its start).
    survivor, absorbed = (w1, w2) if w1.start_node != node_tag else (w2, w1)
    far_end = absorbed.end_node if absorbed.start_node == node_tag else absorbed.start_node
    remap = ReferenceRemap(renamed={absorbed.tag: survivor.tag},
                           deleted=frozenset({node_tag}))
    ops = [
        PatchOp("update", "Wall", survivor.tag, {"end_node": far_end}),
        PatchOp("delete", "Wall", absorbed.tag, {}),
        PatchOp("delete", "Node", node_tag, {}),
    ]
    warnings: list[str] = []
    for el in plan.storey_elements(storey):
        if getattr(el, "host", None) == absorbed.tag:
            ops = remap_ops_for(el, remap) + ops
            warnings.append(f"opening {el.tag} re-hosted to {survivor.tag}")
    return MutationResult(ops=ops, remap=remap,
                          deleted_tags=(absorbed.tag, node_tag), warnings=tuple(warnings))
