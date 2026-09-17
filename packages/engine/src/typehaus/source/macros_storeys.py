"""Storey-level macros: copy one floor's layout onto another (→ plan Stage 2 P3).

Copies the wall graph a person redraws on every floor — nodes, walls, doors, windows, rooms —
under fresh plan-wide tags and no uids, each add pinned to the destination storey. Everything
that is floor-specific (structure, alarms, devices, MEP, stairs, placeables) is left behind with
a ``needs_review`` impact so the handoff lists it.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.base import Element
from typehaus.model.elements import Door, Node, Wall, Window
from typehaus.model.plan import PlanModel
from typehaus.model.remap import Impact, MutationResult
from typehaus.model.spatial import Room
from typehaus.source.macros_common import MacroError, _next_plan_tag, _storey_file_hint
from typehaus.source.ops import PatchOp, RawExpr
from typehaus.source.serialize import element_add_op

_PREFIX: dict[type[Element], str] = {
    Node: "N-", Wall: "W-", Door: "D-", Window: "WIN-", Room: "RM-"}
_LIST: dict[type[Element], str] = {
    Node: "NODES", Wall: "WALLS", Door: "OPENINGS", Window: "OPENINGS", Room: "ROOMS"}


def copy_storey_layout(plan: PlanModel, src: str, dst: str, *,
                       hint_file: str | None = None) -> MutationResult:
    """Copy ``src``'s nodes, walls, doors, windows and rooms onto the empty storey ``dst``."""
    if src == dst:
        raise MacroError("copy_storey_layout: source and destination are the same storey")
    src_storey, dst_storey = plan.storey(src), plan.storey(dst)
    if src_storey is None or dst_storey is None:
        raise MacroError(f"no storey {src if src_storey is None else dst!r}")
    if any(isinstance(e, (Node, Wall)) for e in plan.storey_elements(dst)):
        raise MacroError(f"storey {dst!r} already has walls; copy only onto an empty floor")
    hint_file = _storey_file_hint(plan, dst) or hint_file
    # An authored wall top belongs to its floor's ceiling; a different ceiling takes the default.
    same_ceiling = (src_storey.default_ceiling_height.meters
                    == dst_storey.default_ceiling_height.meters)
    source = plan.storey_elements(src)
    minted: set[str] = set()
    rename: dict[str, str] = {}
    for el in source:
        if type(el) in _PREFIX:
            rename[el.tag] = _next_plan_tag(plan, _PREFIX[type(el)], minted)

    ops: list[PatchOp] = []
    impacts: list[Impact] = []

    def add(el: Element, **fields: Any) -> PatchOp:
        copy = el.model_copy(update={"tag": rename[el.tag], **fields})
        op = element_add_op(copy, tag=copy.tag, hint_list=_LIST[type(el)], hint_file=hint_file)
        ops.append(PatchOp(op.op, op.type, op.tag, op.fields, hint_file=op.hint_file,
                           hint_list=op.hint_list, storey=dst))
        return ops[-1]

    def skip(el: Element, why: str) -> None:
        impacts.append(Impact(el.tag, "needs_review", f"{el.element_kind} {el.tag} {why}"))

    for el in source:
        if isinstance(el, Node):
            add(el)
    for el in source:
        if not isinstance(el, Wall):
            continue
        if el.start_node not in rename or el.end_node not in rename:
            skip(el, f"not copied: its nodes are not on {src!r}")
            rename.pop(el.tag, None)
            continue
        add(el, start_node=rename[el.start_node], end_node=rename[el.end_node],
            interior_room=rename.get(el.interior_room) if el.interior_room else None,
            stacks_on=None, bearing_refs=(), top=el.top if same_ceiling else None)
    for el in source:
        if isinstance(el, (Door, Window)):
            pos = el.position
            node = rename.get(pos.node or "") if pos.mode == "from_node" else None
            if el.host not in rename or (pos.mode == "from_node" and node is None):
                skip(el, "not copied: its host wall was not copied")
                continue
            # OpeningPosition is authored through its helper, never the bare constructor.
            add(el, host=rename[el.host]).fields["position"] = RawExpr(
                f'from_node("{node}", {pos.offset.to_source() if pos.offset else "ft(0)"})'
                if node is not None else "centered()")
        elif isinstance(el, Room):
            exceptions = tuple(x.model_copy(update={"wall_ref": rename[x.wall_ref]})
                               for x in el.wall_lining_exceptions if x.wall_ref in rename)
            add(el, wall_lining_exceptions=exceptions)
        elif type(el) not in _PREFIX:
            skip(el, f"not copied to {dst!r}: floor-specific, review it there")
    return MutationResult(ops=ops, impacts=tuple(impacts))

