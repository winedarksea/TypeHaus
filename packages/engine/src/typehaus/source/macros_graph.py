"""Shared plumbing for the graph-editing macros (split, heal, draw_room_rect, delete_wall):
wall axes and station maps, a reference walker, a plan view that applies ops as they are
emitted, and op coalescing so one element gets one update per patch.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from pydantic import BaseModel

from typehaus.model.base import Element
from typehaus.model.plan import PlanModel
from typehaus.model.remap import Impact, MutationResult, ReferenceRemap
from typehaus.source.macros_common import _nodes, _walls
from typehaus.source.ops import PatchOp

XYm = tuple[float, float]
Axis = tuple[XYm, XYm]


def wall_axis(plan: PlanModel, storey: str, wall) -> Axis | None:
    """Node-to-node axis — the frame ``resolve/topology`` gives ``ResolvedWall.axis``."""
    by_tag = {n.tag: n for n in _nodes(plan, storey)}
    a, b = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    return (a.position.xy_m, b.position.xy_m) if a is not None and b is not None else None


def axis_length(axis: Axis) -> float:
    (x0, y0), (x1, y1) = axis
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


def station_map(old: Axis, new: Axis) -> tuple[float, bool]:
    """(shift, reversed) taking a station on ``old`` to the same point on collinear ``new``:
    ``d' = d + shift``, or ``d' = shift - d`` when ``new`` runs the other way."""
    (ox, oy), (nx, ny) = old[0], new[0]
    ln = axis_length(new) or 1.0
    ux, uy = (new[1][0] - nx) / ln, (new[1][1] - ny) / ln
    lo = axis_length(old) or 1.0
    reversed_ = ((old[1][0] - ox) * ux + (old[1][1] - oy) * uy) / lo < 0
    return (ox - nx) * ux + (oy - ny) * uy, reversed_


def station_of(axis: Axis, p: XYm) -> float:
    (x0, y0), (x1, y1) = axis
    ln = axis_length(axis) or 1.0
    return ((p[0] - x0) * (x1 - x0) + (p[1] - y0) * (y1 - y0)) / ln


def _holds(value: object, tag: str) -> bool:
    if isinstance(value, str):
        return value == tag
    if isinstance(value, BaseModel):
        return any(_holds(getattr(value, n), tag) for n in type(value).model_fields)
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_holds(v, tag) for v in value)
    return False


def references_to(plan: PlanModel, tag: str) -> list[tuple[Element, str]]:
    """Every (element, top-level field) whose value names ``tag``, nested records included."""
    out: list[tuple[Element, str]] = []
    for el in plan.all_elements():
        for name in type(el).model_fields:
            if name not in ("tag", "uid") and _holds(getattr(el, name), tag):
                out.append((el, name))
    return out


def degree(plan: PlanModel, storey: str, node: str) -> int:
    return sum(node in (w.start_node, w.end_node) for w in _walls(plan, storey))


def coalesce(ops: list[PatchOp]) -> list[PatchOp]:
    """Fold repeated updates of one element into its add or first update (later fields win);
    a delete closes the element."""
    out: list[PatchOp] = []
    open_op: dict[tuple[str, str], int] = {}
    for op in ops:
        key = (op.type, op.tag)
        if op.op == "update" and key in open_op:
            first = out[open_op[key]]
            out[open_op[key]] = replace(first, fields={**first.fields, **op.fields})
            continue
        if op.op == "delete":
            open_op.pop(key, None)
        else:
            open_op[key] = len(out)
        out.append(op)
    return out


@dataclass
class GraphView:
    """The plan as the ops emitted so far leave it, plus the accumulated outcome."""

    plan: PlanModel
    storey: str
    ops: list[PatchOp] = field(default_factory=list)
    minted: set[str] = field(default_factory=set)
    impacts: list[Impact] = field(default_factory=list)
    deleted_tags: list[str] = field(default_factory=list)
    renamed: dict[str, str] = field(default_factory=dict)
    deleted: set[str] = field(default_factory=set)
    rehost: dict[str, str] = field(default_factory=dict)
    shift: dict[str, float] = field(default_factory=dict)
    reversed: set[str] = field(default_factory=set)

    def emit(self, ops: list[PatchOp]) -> None:
        from typehaus.source.inmemory import apply_ops_to_plan

        if ops:
            self.plan = apply_ops_to_plan(self.plan, ops)[0]
            self.ops.extend(ops)

    def absorb(self, result: MutationResult) -> None:
        self.emit(result.ops)
        self.impacts.extend(result.impacts)
        self.deleted_tags.extend(result.deleted_tags)
        self.renamed.update(result.remap.renamed)
        self.deleted |= result.remap.deleted
        self.rehost.update(result.remap.rehost)
        # Compose station maps: d' = s + (-d if r else d), applied in emit order.
        for tag in set(result.remap.shift) | result.remap.reversed:
            s2, r2 = result.remap.shift.get(tag, 0.0), tag in result.remap.reversed
            s1 = self.shift.get(tag, 0.0)
            self.shift[tag] = s2 - s1 if r2 else s2 + s1
            self.reversed ^= {tag} if r2 else set()

    def result(self) -> MutationResult:
        remap = ReferenceRemap(renamed=self.renamed, deleted=frozenset(self.deleted),
                               rehost=self.rehost, shift=self.shift,
                               reversed=frozenset(self.reversed))
        return MutationResult(ops=coalesce(self.ops), remap=remap,
                              deleted_tags=tuple(self.deleted_tags),
                              impacts=tuple(self.impacts))
