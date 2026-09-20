"""Split and heal cores: the identity-changing edits on one wall, and everything that has to
follow them — hosted openings (host + a position that keeps its world station), wall-attached
placeables (P8: ``rehost`` + ``shift``), and the refs no handler carries (``needs_review``).

Both take pre-minted tags and a plan *view*, so a macro that splits twice (draw_room_rect)
reads the first split's result before building the second.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.plan import PlanModel
from typehaus.model.remap import (
    Impact,
    MutationResult,
    ReferenceRemap,
    registered_ref_fields,
    remap_ops_for,
)
from typehaus.source.macros_common import (
    _PLACEABLE_KINDS,
    MacroError,
    _nodes,
    _openings,
    _point_expr_m,
    _round_len,
    _walls,
)
from typehaus.source.macros_geometry import _collinear
from typehaus.source.macros_graph import (
    Axis,
    axis_length,
    references_to,
    station_map,
    station_of,
    wall_axis,
)
from typehaus.source.ops import PatchOp, RawExpr
from typehaus.source.serialize import value_source

_EPS = 1e-6
# Wall fields a new segment must not inherit: identity, topology, and the stack tiebreaker
# (two segments naming one wall below is the ambiguity it exists to break).
_SEGMENT_SKIP = {"uid", "tag", "start_node", "end_node", "stacks_on"}


def opening_span(plan: PlanModel, opening, wall, length: float) -> tuple[float, float] | None:
    """(near-jamb station, width) of an opening on ``wall``, or None if the type is missing."""
    from typehaus.source.macros_openings import _opening_start_offset, _opening_width

    try:
        width = _opening_width(plan, opening)
    except MacroError:
        return None
    return _opening_start_offset(opening, wall, length, width), width


def _from_node(node: str, station: float) -> RawExpr:
    return RawExpr(f'from_node("{node}", {_round_len(round(max(0.0, station), 6)).to_source()})')


def _placeable_station(el, wall_tag: str, axis: Axis) -> float | None:
    att = getattr(getattr(el, "location", None), "attachment", None)
    if att is not None:
        return att.distance_from_start.meters if att.wall_ref == wall_tag else None
    pos = getattr(el, "position", None)
    return station_of(axis, pos.xy_m) if pos is not None else None


def uncovered_refs(plan: PlanModel, tag: str, *, carried: set[str]) -> list[tuple[object, str]]:
    """Refs to ``tag`` outside the openings' ``host``, the placeables' P8 fields, and any
    ``carried`` kind's registered handler fields."""
    handled = registered_ref_fields()
    out = []
    for el, name in references_to(plan, tag):
        kind = el.element_kind
        if name == "host" and kind in ("Door", "Window", "RoughOpening"):
            continue
        if isinstance(el, _PLACEABLE_KINDS) and name in ("wall_ref", "location"):
            continue
        if kind in carried and name in handled.get(kind, ()):
            continue
        out.append((el, name))
    return out


def rehost_along_wall(view: PlanModel, storey: str, wall, new_tag: str, mid_tag: str,
                      axis: Axis, split_len: float) -> tuple[list[PatchOp], ReferenceRemap,
                                                            list[Impact]]:
    """Carry openings and attached/wet-wall placeables on a split wall to the segment their
    station falls in; the b-side segment starts at ``mid_tag``, ``split_len`` along."""
    ops: list[PatchOp] = []
    impacts: list[Impact] = []
    rehost: dict[str, str] = {}
    shift: dict[str, float] = {}
    length = axis_length(axis)
    for op in _openings(view, storey):
        if op.host != wall.tag:
            continue
        span = opening_span(view, op, wall, length)
        if span is None:
            impacts.append(Impact(op.tag, "needs_review", f"opening {op.tag} has no width; "
                                  f"left on {wall.tag}"))
            continue
        s, w = span
        b_side = s + w / 2 > split_len
        if s + _EPS < split_len < s + w - _EPS:
            impacts.append(Impact(op.tag, "needs_review",
                                  f"opening {op.tag} straddles the split of {wall.tag}"))
        if b_side:
            rehost[op.tag] = new_tag
            ops.append(PatchOp("update", op.element_kind, op.tag,
                               {"host": new_tag, "position": _from_node(mid_tag, s - split_len)}))
            impacts.append(Impact(op.tag, "carried", f"opening {op.tag} re-hosted to {new_tag}"))
        elif op.position.mode == "centered" or op.position.node == wall.end_node:
            ops.append(PatchOp("update", op.element_kind, op.tag,
                               {"position": _from_node(wall.start_node, s)}))
    for el in view.storey_elements(storey):
        if not isinstance(el, _PLACEABLE_KINDS):
            continue
        att = getattr(getattr(el, "location", None), "attachment", None)
        on_att = att is not None and att.wall_ref == wall.tag
        on_ref = getattr(el, "wall_ref", None) == wall.tag
        if not (on_att or on_ref):
            continue
        if on_ref and att is not None and not on_att:
            impacts.append(Impact(el.tag, "needs_review", f"{el.tag} names {wall.tag} as its "
                                  "wet wall but hangs on another; wall_ref left on the a-side"))
            continue
        station = _placeable_station(el, wall.tag, axis)
        if station is not None and station > split_len + _EPS:
            rehost[el.tag] = new_tag
            if on_att:
                shift[el.tag] = -split_len
            impacts.append(Impact(el.tag, "carried", f"{el.tag} re-hosted to {new_tag}"))
    remap = ReferenceRemap(rehost=rehost, shift=shift)
    for el in view.storey_elements(storey):
        if isinstance(el, _PLACEABLE_KINDS) and el.tag in rehost:
            ops.extend(remap_ops_for(el, remap))
    for el, name in uncovered_refs(view, wall.tag, carried=set()):
        if el.tag != wall.tag:
            impacts.append(Impact(el.tag, "needs_review",
                                  f"{el.tag}.{name} names split wall {wall.tag}; not carried"))
    return ops, remap, impacts


def split_wall_ops(view: PlanModel, storey: str, wall, t: float, mid_tag: str,
                   new_wall_tag: str, *, hint_file: str | None = None) -> MutationResult:
    """Split ``wall`` at parameter ``t``; the a-side keeps the uid (#33), tags pre-minted."""
    axis = wall_axis(view, storey, wall)
    if axis is None:
        raise MacroError(f"wall {wall.tag!r} has an unresolved node")
    (ax, ay), (bx, by) = axis
    fields: dict[str, object] = {"start_node": mid_tag, "end_node": wall.end_node}
    for name, fld in type(wall).model_fields.items():
        value = getattr(wall, name)
        if name in _SEGMENT_SKIP or (not fld.is_required() and value == fld.get_default(
                call_default_factory=True)):
            continue
        fields[name] = value if type(value) is str else RawExpr(value_source(value))
    ops = [
        PatchOp("add", "Node", mid_tag,
                {"position": _point_expr_m(ax + t * (bx - ax), ay + t * (by - ay))},
                hint_file=hint_file, hint_list="NODES", storey=storey),
        PatchOp("update", wall.element_kind, wall.tag, {"end_node": mid_tag}),
        PatchOp("add", wall.element_kind, new_wall_tag, fields, hint_file=hint_file,
                hint_list="WALLS", storey=storey),
    ]
    refit, remap, impacts = rehost_along_wall(view, storey, wall, new_wall_tag, mid_tag, axis,
                                              t * axis_length(axis))
    ops.extend(refit)
    return MutationResult(ops=ops, remap=remap, impacts=tuple(impacts),
                          warnings=tuple(i.reason for i in impacts))


def heal_ops(view: PlanModel, storey: str, node_tag: str) -> MutationResult:
    """Fuse the two collinear walls at ``node_tag``; the survivor keeps its uid and every
    station on either wall is mapped onto the fused axis (the inverse of a split)."""
    incident = [w for w in _walls(view, storey) if node_tag in (w.start_node, w.end_node)]
    if len(incident) != 2:
        raise MacroError(f"heal needs exactly two walls at {node_tag!r}, found {len(incident)}")
    w1, w2 = incident
    by_tag = {nd.tag: nd for nd in _nodes(view, storey)}
    if not _collinear(w1, w2, node_tag, by_tag):
        raise MacroError(f"walls at {node_tag!r} are not collinear; cannot heal")
    survivor, absorbed = (w1, w2) if w1.start_node != node_tag else (w2, w1)
    far_end = absorbed.end_node if absorbed.start_node == node_tag else absorbed.start_node
    if survivor.start_node == node_tag:  # both walls start here: the fused wall starts far
        ends, update = (far_end, survivor.end_node), {"start_node": far_end}
    else:
        ends, update = (survivor.start_node, far_end), {"end_node": far_end}
    fused_axis = (by_tag[ends[0]].position.xy_m, by_tag[ends[1]].position.xy_m)
    fused = SimpleNamespace(tag=survivor.tag, start_node=ends[0], end_node=ends[1])
    fused_len = axis_length(fused_axis)
    ops: list[PatchOp] = []
    impacts: list[Impact] = []
    shift: dict[str, float] = {}
    flipped: set[str] = set()
    for wall in (survivor, absorbed):
        axis = wall_axis(view, storey, wall)
        s0, rev = station_map(axis, fused_axis)
        for op in _openings(view, storey):
            if op.host != wall.tag:
                continue
            span = opening_span(view, op, wall, axis_length(axis))
            if span is None:
                continue
            s, w = span
            new_s = s0 - s - w if rev else s0 + s
            keeps = (wall is survivor and op.position.mode != "centered"
                     and op.position.node in ends
                     and abs(opening_span(view, op, fused, fused_len)[0] - new_s) < _EPS)
            if not keeps:
                fields: dict[str, object] = {"position": _from_node(ends[0], new_s)}
                if wall is absorbed:
                    fields["host"] = survivor.tag
                    impacts.append(Impact(op.tag, "carried",
                                          f"opening {op.tag} re-hosted to {survivor.tag}"))
                ops.append(PatchOp("update", op.element_kind, op.tag, fields))
        for el in view.storey_elements(storey):
            att = getattr(getattr(el, "location", None), "attachment", None)
            if isinstance(el, _PLACEABLE_KINDS) and att is not None and att.wall_ref == wall.tag \
                    and (abs(s0) > _EPS or rev):
                shift[el.tag] = s0
                if rev:
                    flipped.add(el.tag)
    remap = ReferenceRemap(renamed={absorbed.tag: survivor.tag}, deleted=frozenset({node_tag}),
                           shift=shift, reversed=frozenset(flipped))
    seen: set[str] = set()
    for el, _name in references_to(view, absorbed.tag) + [
            (e, "") for e in view.storey_elements(storey) if e.tag in shift]:
        if el.tag in seen or el.element_kind in ("Door", "Window", "RoughOpening"):
            continue
        seen.add(el.tag)
        ops.extend(remap_ops_for(el, remap))
    for tag in (absorbed.tag, node_tag):
        for el, name in uncovered_refs(view, tag, carried={"Wall", "Stair"}):
            if el.tag in (survivor.tag, absorbed.tag) or (
                    name == "position" and getattr(el, "host", None) in (survivor.tag,
                                                                         absorbed.tag)):
                continue
            impacts.append(Impact(el.tag, "needs_review",
                                  f"{el.tag}.{name} names {tag}, removed by the heal"))
    ops += [PatchOp("update", survivor.element_kind, survivor.tag, update),
            PatchOp("delete", absorbed.element_kind, absorbed.tag, {}),
            PatchOp("delete", "Node", node_tag, {})]
    return MutationResult(ops=ops, remap=remap, deleted_tags=(absorbed.tag, node_tag),
                          impacts=tuple(impacts), warnings=tuple(i.reason for i in impacts))
