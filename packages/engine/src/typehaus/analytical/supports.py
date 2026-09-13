"""Boundary conditions, derived and claimed — never defaulted.

Owner decision, 2026-09-12: fixity is this engine's to derive, and every one of them
carries the prose a reviewer disagrees with. There are exactly three claims here.

* **A lateral-system column base is FIXED.** ``engineering/pier_basis`` already decides
  which cast columns ARE the lateral system — a freestanding deck with no knee brace and no
  beam landing in a wall — and it decides it because ``deck_post`` grades a base moment on
  exactly those and on nothing else. Reading that same flag here is what keeps the
  analytical model and the calculation package answering the same question the same way;
  deriving it a second time would be two answers about the balcony's whole lateral system.
  The basis quotes ``_Pier.moment_basis`` verbatim, wind and all.
* **Every other post base is PINNED.** A post on a bell or a pad is set on an anchor that
  transfers no moment, and claiming otherwise would invent a restraint the connector cannot
  deliver — the unconservative direction.
* **A beam bearing on a wall or a foundation is a PINNED support node.** The wall is not a
  member in this version (see ``scope.py``); the bearing is real and is where the load goes
  to ground.

**Rotations are part of the claim, not a consequence of the fixity.** A pin that freed all
three rotations would let a beam roll about its own axis and spin about Z, and a solver
reports that as an instability rather than as the modelling mistake it is. A bearing plate
holds a beam against roll; a post base connector holds a post against twist. Both are
restraints a builder would recognise, so both are stated here in ``Support.rotations``
rather than worked around by pretending an end is fixed. The other half of the same rule
lives in ``members.py``: a member end AT a support carries no moment release, because the
support is what says which rotation is free.

Nothing else is a support. A member end that reaches no support and no other member is
left alone, and the gap register says so — a fabricated restraint is how a model comes back
stable and wrong.
"""

from __future__ import annotations

from typing import Any

from typehaus.analytical.graph import Fixity, Support


def derive_supports(ctx: Any, scope: Any, graph: Any) -> tuple[Support, ...]:
    """Every restrained node, with the claim it is restrained under."""
    from typehaus.engineering.pier_basis import cast_piers
    from typehaus.model.elements import Wall
    from typehaus.model.structure import Footing, Pad, Post

    piers = {pier.tag: pier for pier in cast_piers(ctx)}
    out: list[Support] = []
    seen: set[str] = set()
    for tag in scope.posts:
        node = graph.post_base.get(tag)
        post = ctx.plan.by_tag(tag)
        if node is None or not isinstance(post, Post) or node in seen:
            continue
        seen.add(node)
        items = scope.items_for(tag)
        item_id = next((i for i in items if i.startswith("deck_post/")), items[0] if items
                       else None)
        pier = piers.get(tag)
        if pier is not None and pier.lateral_system:
            out.append(Support(
                node=node, fixity=Fixity.FIXED, element_tag=tag, item_id=item_id,
                basis=(f"lateral system: {tag} is doweled into its base and is the only "
                       f"thing resisting storey shear — {pier.moment_basis}")))
            continue
        base = _base_of(ctx, tag)
        carried = graph.post_carries.get(tag, ())
        rotations, braced = _base_rotations(
            [graph.beam_axis_xy.get(beam, (0.0, 0.0)) for beam in carried])
        out.append(Support(
            node=node, fixity=Fixity.PINNED, element_tag=tag, item_id=item_id,
            rotations=rotations,
            basis=(f"post on {base}: the base connector transfers no bending moment and "
                   f"the column is free to lean in the plane of the frame. It is held "
                   f"against twist about its own axis, and {braced}")))

    for (beam_tag, ref), node in sorted(graph.bearing_node.items()):
        support = ctx.plan.by_tag(ref)
        if not isinstance(support, Wall | Footing | Pad) or node in seen:
            continue
        seen.add(node)
        items = scope.items_for(beam_tag, ref)
        rotations, roll = _bearing_rotations(graph.beam_axis_xy.get(beam_tag, (1.0, 0.0)))
        out.append(Support(
            node=node, fixity=Fixity.PINNED, element_tag=ref,
            item_id=items[0] if items else None, rotations=rotations,
            basis=(f"{beam_tag} bears on {ref}: pinned — free to rotate in bending over "
                   f"the bearing — and the bearing plate holds the beam against ROLL about "
                   f"its own axis (global {roll}). {ref} is not a member in this model")))
    return tuple(sorted(out, key=lambda s: (s.node, s.element_tag)))


def _base_rotations(carried: list[tuple[float, float]]
                    ) -> tuple[tuple[bool, bool, bool], str]:
    """A pinned post base's rotational restraint, and the sentence that claims it.

    Two restraints, and neither is the pin the name suggests it is not:

    * **Twist about the post's own axis (global Z).** A base connector that let a column
      spin on itself does not exist, and a beam released over the top of one would have
      nothing else holding it.
    * **Roll about the axis of the beam the column carries.** This is the one place the
      graph leans on something it does not model: the deck plane, which
      ``loads.py`` carries as a line load and not as members, is what braces a deck column
      out of the frame's plane. Without it a pair of pin-based columns under one beam is a
      rigid-body rotation about the line joining their bases — an instability of the
      drawing, not of the building. The reaction moment it develops is a check on the
      claim: under gravity it comes back at essentially zero.

    Bending in the plane of the frame — about the axis ACROSS the beam — stays free, which
    is what makes it a pin at all.
    """
    restrain_x = any(abs(direction[0]) >= abs(direction[1]) and any(direction)
                     for direction in carried)
    restrain_y = any(abs(direction[1]) > abs(direction[0]) for direction in carried)
    braced = ("the deck plane braces it against rolling with "
              + " and ".join(axis for axis, on in (("X", restrain_x), ("Y", restrain_y))
                             if on) + "-running beams it carries") if (
        restrain_x or restrain_y) else "carries no beam this graph models"
    return (restrain_x, restrain_y, True), braced


def _bearing_rotations(direction: tuple[float, float]) -> tuple[tuple[bool, bool, bool], str]:
    """``(rotations, the axis named in the basis)`` for a beam end on a wall or a seat.

    One rotation is restrained: the beam's OWN axis, the roll a bearing plate stops. Both
    bending rotations stay free, which is what makes it a pin and not a fixed end — and it
    is why the member end at a support carries no release: a released end on a pinned
    support contributes no rotational stiffness in any axis, and the node then has nothing
    holding it. A skew beam is taken on its dominant plan axis; a seat is not a torsion
    connection and half a degree of skew does not change which way the member rolls.
    """
    if abs(direction[0]) >= abs(direction[1]):
        return (True, False, False), "X"
    return (False, True, False), "Y"


def _base_of(ctx: Any, tag: str) -> str:
    """What the post lands on, named as the author named it."""
    from typehaus.model.structure import Footing

    post = ctx.plan.by_tag(tag)
    for element in ctx.plan.all_elements():
        if isinstance(element, Footing) and element.under == tag:
            return element.tag
    return getattr(post, "supported_by", None) or "its base"
