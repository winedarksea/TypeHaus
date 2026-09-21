"""A deck's ties to another structure, as horizontal springs — the ``deck_tie`` joints.

``engineering/deck_tie_basis.wall_ties`` is the one derivation of what ties a deck (the same
one ``pier_basis`` reads to make its columns lean), so this reads it and adds nothing: each
joint becomes a node ON the tied member's axis and two support springs there, DX and DY.
Nothing vertical — the tie block stands 1/4" off the concrete and carries no gravity.

**Where a joint lands.** A beam joint is split into its beam at the joint's plan station. A
joint on a wall standing on the deck (catlin's screen into ``W-G-W``) lands on the framing
member collinear with that wall — the sill it stands on — at the station nearest the joint,
clamped to the member: the N-S spring is exact, the E-W one moves a few inches of lever.

**Stiffness is claimed, and equal.** NDS 2018 §11.3.6's load/slip modulus for a dowel in
wood-to-metal, ``γ = 270,000 D^1.5`` lb/in at D = 1/2", times the parts at the joint. That
equality is the same assumption ``deck_tie`` distributes by, so the graph and the record
share it. Oracle: ``houses/catlin/notes/analytical_model_basis.md`` §1 and §3e.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.analytical.graph import SupportSpring

_FT = 0.3048
_LB_PER_IN_TO_N_PER_M = 4.4482216152605 / 0.0254
#: NDS 2018 §11.3.6: γ = 270,000 D^1.5 (lb/in) for a dowel-type fastener, wood to metal.
SLIP_MODULUS_LB_IN = 270_000.0 * 0.5 ** 1.5
#: A wall joint's sill is the framing member within this of the wall's line.
_COLLINEAR_FT = 0.5
_BASIS = ("deck tie {joint}: {parts} x {model} into {wall} (deck_tie/{deck}), a horizontal "
          "spring on {dof} at NDS 2018 §11.3.6's γ = 270,000 D^1.5 = {gamma:,.0f} lb/in per "
          "1/2\" bolt x {parts}; vertical free (the block stands off the concrete)")


def _tied(ctx: Any, scope: Any) -> list[tuple[Any, list[Any]]]:
    from typehaus.engineering.deck_tie_basis import wall_ties
    from typehaus.model.floors import FloorSystem

    out = []
    for item in scope.item_ids:
        if not item.startswith("deck_tie/"):
            continue
        deck = ctx.plan.by_tag(item.split("/", 1)[1])
        if isinstance(deck, FloorSystem):
            out.append((deck, wall_ties(ctx, deck)))
    return out


def _host(ctx: Any, joint: Any, axes: dict[str, Any]) -> str | None:
    """The axis the joint lands on: its own member's, or — for a wall on the deck — the
    highest member collinear with the wall and at or below its base (the sill it stands on).
    """
    if joint.member in axes:
        return joint.member
    wall = ctx.model.wall(joint.member)
    if wall is None:
        return None
    point = (joint.x_ft * _FT, joint.y_ft * _FT)
    best: tuple[float, str] | None = None
    for tag, axis in sorted(axes.items()):
        dx, dy = axis.p1[0] - axis.p0[0], axis.p1[1] - axis.p0[1]
        length = math.hypot(dx, dy)
        top = max(axis.p0[2], axis.p1[2])
        if length < 1e-9 or top > wall.z0_m + 0.05:
            continue
        off = abs((point[0] - axis.p0[0]) * dy - (point[1] - axis.p0[1]) * dx) / length / _FT
        if off <= _COLLINEAR_FT and (best is None or -top < best[0]):
            best = (-top, tag)
    return best[1] if best else None


def register(ctx: Any, scope: Any, axes: dict[str, Any], nodes: Any) -> dict[tuple, int]:
    """Add a node per tie joint on its host axis; ``{(deck, member, wall): node index}``."""
    out: dict[tuple, int] = {}
    for deck, joints in _tied(ctx, scope):
        for joint in joints:
            host = _host(ctx, joint, axes)
            if host is None:
                continue
            axis = axes[host]
            param = min(max(axis.param_of((joint.x_ft * _FT, joint.y_ft * _FT)), 0.0), 1.0)
            out[(deck.tag, joint.member, joint.wall)] = nodes.add(
                axis.at(param), f"{host}:tie:{joint.wall}")
    return out


def springs(ctx: Any, scope: Any, tie_node: dict[tuple, str]) -> tuple[SupportSpring, ...]:
    """DX and DY at every registered tie node."""
    out: list[SupportSpring] = []
    for deck, joints in _tied(ctx, scope):
        for joint in joints:
            node = tie_node.get((deck.tag, joint.member, joint.wall))
            if node is None:
                continue
            parts = len(joint.parts)
            stiffness = SLIP_MODULUS_LB_IN * parts * _LB_PER_IN_TO_N_PER_M
            for dof in ("DX", "DY"):
                out.append(SupportSpring(
                    node=node, dof=dof, stiffness_n_m=stiffness, direction=None,
                    basis=_BASIS.format(joint=f"{joint.member}/{joint.wall}", parts=parts,
                                        model=joint.model, wall=joint.wall, deck=deck.tag,
                                        dof=dof, gamma=SLIP_MODULUS_LB_IN)))
    return tuple(sorted(out, key=lambda s: (s.node, s.dof)))


def unplaced(ctx: Any, scope: Any, tie_node: dict[tuple, str]) -> tuple[str, ...]:
    """Gap lines for tie joints no axis in the graph could host."""
    return tuple(f"deck_tie/{deck.tag}: the tie {joint.member} -> {joint.wall} lands on no "
                 f"member in this graph, so it is not a spring here"
                 for deck, joints in _tied(ctx, scope) for joint in joints
                 if (deck.tag, joint.member, joint.wall) not in tie_node)
