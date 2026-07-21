"""Room macros + wall-draw — geometry-aware builders that emit :class:`MutationResult`s
(→ 21b §Room macros, §Mutation contract).

These are *server-side* helpers, not new grammar: each returns ordinary ``add|update|delete``
PatchOps that ride the standard :class:`~typehaus.source.coordinator.ProjectCoordinator`
patch/undo path, so undo/redo and revision-hash write safety come for free. Geometry math
lives here (the "server owns all geometry" rule, → 21b) — the client only sends screen intent
(draw endpoints, the wall to split, the drag delta). Node positions are read from the authored
:class:`~typehaus.model.plan.PlanModel`; new coordinates are emitted as :class:`RawExpr`
``pt(...)`` so no re-encoding round-trip can lose precision.
"""

from __future__ import annotations

from typing import Union

from typehaus.model.elements import Door, Node, Wall, Window
from typehaus.model.enums import Occupancy
from typehaus.model.plan import PlanModel
from typehaus.model.refs import from_node
from typehaus.model.remap import MutationResult, ReferenceRemap, remap_ops_for
from typehaus.model.spatial import Room
from typehaus.quantities import Length
from typehaus.quantities.length import ft, m
from typehaus.quantities.point import pt
from typehaus.source.ops import PatchOp, RawExpr
from typehaus.source.serialize import element_add_op

# Node coincidence tolerance — nodes closer than this fuse (T-junction heal), in meters.
SNAP_M = 0.02
# Collinearity tolerance for heal/merge (cross-product of unit axes), dimensionless.
COLLINEAR_TOL = 1e-3

XY = tuple[Union[float, str], Union[float, str]]


class MacroError(ValueError):
    """A macro could not be built (degenerate geometry, missing element, ambiguous heal)."""


# --- coordinate helpers ------------------------------------------------------

def _as_length(v: float | str) -> Length:
    return Length.parse(v) if isinstance(v, str) else m(float(v))


def _point_expr(x: float | str, y: float | str) -> RawExpr:
    return RawExpr(f"pt({_as_length(x).to_source()}, {_as_length(y).to_source()})")


def _meters(v: float | str) -> float:
    return _as_length(v).meters


def _nodes(plan: PlanModel, storey: str) -> list[Node]:
    return [e for e in plan.storey_elements(storey) if isinstance(e, Node)]


def _walls(plan: PlanModel, storey: str) -> list[Wall]:
    return [e for e in plan.storey_elements(storey) if isinstance(e, Wall)]


def _next_tag(existing: list, prefix: str) -> str:
    used = set()
    for el in existing:
        t = el.tag
        if t.startswith(prefix) and t[len(prefix):].isdigit():
            used.add(int(t[len(prefix):]))
    n = 1
    while n in used:
        n += 1
    return f"{prefix}{n}"


def _find_node_near(plan: PlanModel, storey: str, xy_m: tuple[float, float]) -> Node | None:
    for nd in _nodes(plan, storey):
        px, py = nd.position.xy_m
        if (px - xy_m[0]) ** 2 + (py - xy_m[1]) ** 2 <= SNAP_M ** 2:
            return nd
    return None


# --- wall-draw ---------------------------------------------------------------

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


# --- opening / room placement ------------------------------------------------

def _openings(plan: PlanModel, storey: str) -> list:
    kinds = {"Window", "Door", "RoughOpening"}
    return [e for e in plan.storey_elements(storey) if e.element_kind in kinds]


def _rooms(plan: PlanModel, storey: str) -> list:
    return [e for e in plan.storey_elements(storey) if e.element_kind == "Room"]


def place_opening(
    plan: PlanModel,
    storey: str,
    *,
    host: str,
    type_ref: str,
    along: float | str,
    is_door: bool,
    sill: float | str | None = None,
    hint_file: str | None = None,
    tag: str | None = None,
) -> MutationResult:
    """Add a window or door to a wall at ``along`` metres from the wall's start node (→ 21b).

    Position is authored as ``from_node(start, offset)`` so the opening tracks the wall's
    a-node under later stretches. The whole ``Window``/``Door`` declaration is serialized to
    source and added to the storey's ``OPENINGS`` list on ``hint_file`` (the host wall's file,
    passed by the client from its provenance so the op lands on the right storey).
    """
    wall = next((w for w in _walls(plan, storey) if w.tag == host), None)
    if wall is None:
        raise MacroError(f"no wall {host!r} on storey {storey!r}")
    offset = _as_length(along)
    position = from_node(wall.start_node, offset)
    if is_door:
        new_tag = tag or _next_tag(_openings(plan, storey), "D-")
        element: object = Door(
            tag=new_tag, host=host, type_ref=type_ref, position=position,
            sill_height=_as_length(sill) if sill is not None else None,
        )
    else:
        new_tag = tag or _next_tag(_openings(plan, storey), "WIN-")
        element = Window(
            tag=new_tag, host=host, type_ref=type_ref, position=position,
            sill_height=_as_length(sill) if sill is not None else ft(3),
        )
    op = element_add_op(element, tag=new_tag, hint_list="OPENINGS", hint_file=hint_file)
    # OpeningPosition is authored through its `from_node(...)` helper, not the bare model
    # constructor (which the plan dialect deliberately doesn't allow, → 10 §dialect).
    op.fields["position"] = RawExpr(
        f'from_node("{wall.start_node}", {offset.to_source()})'
    )
    return MutationResult(ops=[op])


def move_opening(
    plan: PlanModel,
    storey: str,
    *,
    tag: str,
    along: float | str,
) -> MutationResult:
    """Move an opening along its existing host wall without inventing a second geometry solver.

    ``OpeningPosition`` is an authored structured value, so a normal scalar patch cannot
    safely express it.  Re-emitting ``from_node`` keeps the opening attached to the wall's
    start node as that wall is stretched later.
    """
    opening = next((item for item in _openings(plan, storey) if item.tag == tag), None)
    if opening is None:
        raise MacroError(f"no opening {tag!r} on storey {storey!r}")
    wall = next((item for item in _walls(plan, storey) if item.tag == opening.host), None)
    if wall is None:
        raise MacroError(f"opening {tag!r} hosts on missing wall {opening.host!r}")
    offset = _as_length(along)
    return MutationResult(ops=[PatchOp(
        "update", opening.element_kind, tag,
        {"position": RawExpr(f'from_node("{wall.start_node}", {offset.to_source()})')},
    )])


def place_room(
    plan: PlanModel,
    storey: str,
    *,
    seed: XY,
    occupancy: str,
    floor_finish: str | None = None,
    hint_file: str | None = None,
    tag: str | None = None,
) -> MutationResult:
    """Claim a room by dropping a seed point in an enclosed area (→ 11 §Room, → 21b).

    The clear-face polygon is derived server-side from the wall graph on the next resolve;
    the macro only authors the seed + occupancy. Added to the storey's ``ROOMS`` list.
    """
    try:
        occ = Occupancy(occupancy)
    except ValueError as exc:
        raise MacroError(f"unknown occupancy {occupancy!r}") from exc
    new_tag = tag or _next_tag(_rooms(plan, storey), "RM-")
    room = Room(
        tag=new_tag, seed=pt(_as_length(seed[0]), _as_length(seed[1])), occupancy=occ,
        floor_finish=floor_finish or None,
    )
    op = element_add_op(room, tag=new_tag, hint_list="ROOMS", hint_file=hint_file)
    return MutationResult(ops=[op])


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
    warnings = (f"pinned nodes held: {', '.join(pinned)}",) if pinned else ()
    return MutationResult(ops=ops, warnings=warnings)


def _point_expr_m(x_m: float, y_m: float) -> RawExpr:
    """Emit a point from meters, snapping near-round inch values to authored ft-in."""
    return RawExpr(f"pt({_round_len(x_m).to_source()}, {_round_len(y_m).to_source()})")


def _round_len(x_m: float) -> Length:
    inches = x_m / 0.0254
    nearest = round(inches * 16) / 16  # 1/16" grid
    if abs(nearest - inches) < 1e-6:
        feet, rem = divmod(nearest, 12)
        return ft(feet, rem)
    return m(x_m)


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
        plan, storey, wall, wall_tag, new_wall_tag, t
    )
    ops.extend(refit_ops)
    return MutationResult(ops=ops, remap=remap, warnings=warnings)


def _rehost_openings(
    plan: PlanModel, storey: str, wall: Wall, keep_tag: str, new_tag: str, split_t: float
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


# --- geometry primitives -----------------------------------------------------

def _dist(p: tuple[float, float], q: tuple[float, float]) -> float:
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


def _project_param(
    a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]
) -> float:
    abx, aby = b[0] - a[0], b[1] - a[1]
    denom = abx * abx + aby * aby
    if denom == 0:
        return 0.0
    return ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / denom


def _collinear(w1: Wall, w2: Wall, shared: str, by_tag: dict[str, Node]) -> bool:
    def other(w: Wall) -> str:
        return w.end_node if w.start_node == shared else w.start_node

    s = by_tag.get(shared)
    e1, e2 = by_tag.get(other(w1)), by_tag.get(other(w2))
    if s is None or e1 is None or e2 is None:
        return False
    (sx, sy) = s.position.xy_m
    v1 = (e1.position.xy_m[0] - sx, e1.position.xy_m[1] - sy)
    v2 = (e2.position.xy_m[0] - sx, e2.position.xy_m[1] - sy)
    l1 = (v1[0] ** 2 + v1[1] ** 2) ** 0.5
    l2 = (v2[0] ** 2 + v2[1] ** 2) ** 0.5
    if l1 == 0 or l2 == 0:
        return False
    cross = (v1[0] * v2[1] - v1[1] * v2[0]) / (l1 * l2)
    return abs(cross) < COLLINEAR_TOL
