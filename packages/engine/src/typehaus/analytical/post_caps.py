"""Post caps: a column top under a CONTINUOUS beam is a hinge in the beam's plane.

``members.py`` releases a beam's own END on a post top. A beam running continuous over a
post is not released (the cantilever past it would be a mechanism), and without this pass
the column top is then a rigid knee: fixed-base columns pick up a gravity base moment no
record carries. The adopted joint transmits no moment (``engineering/column_head_joint``,
``deck_post``'s k = 2.1 fixed base / free top), so the column's top end is released about
the horizontal axis ACROSS the beam and held about the beam's own axis — the cap's side
plates stop the beam rolling, the same claim ``supports.py`` makes for a beam on a wall.
Releasing both axes leaves the beam's roll held by nothing and the solver refuses it.

Left rigid, and named in the gaps, where the hinge cannot be claimed cleanly: two
non-parallel continuous beams on one cap, a beam oblique to the global axes, or a column
whose base is free about the hinge axis (a pin-pin column in the frame's plane is a
mechanism unless something else braces the frame, and this graph does not know that).
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from typehaus.analytical.graph import Member, Releases, Support

#: A beam within this of a global axis in plan hinges about the other one.
_AXIS_TOLERANCE_DEG = 5.0

_CAP_ASSUMPTION = (
    "post cap: a column top under a beam that runs CONTINUOUS over it is hinged about the "
    "horizontal axis across that beam (bending in the beam's plane transmits no moment) and "
    "held about the beam's own axis (the cap's side plates stop the beam rolling). A beam "
    "that ENDS on a post top is released at its own end instead")


def apply_post_caps(graph: Any, supports: tuple[Support, ...]) -> tuple[str, ...]:
    """Hinge each eligible column top in place on ``graph.members``; return the gap lines."""
    members = {m.id: m for m in graph.members}
    at_node: dict[str, list[Member]] = {}
    for member in graph.members:
        at_node.setdefault(member.n0, []).append(member)
        at_node.setdefault(member.n1, []).append(member)
    held = {s.node: s.restrained_rotations() for s in supports}
    z = {n.id: n.z_m for n in graph.nodes}
    gaps: list[str] = []
    for post, top in sorted(graph.post_top.items()):
        column = next((m for m in at_node.get(top, ())
                       if m.tag == post and m.is_vertical), None)
        if column is None:
            continue
        continuous = sorted({m.tag for m in at_node[top]
                             if not m.is_vertical and not _released_at(m, top)})
        if not continuous:
            continue
        axis, why = _hinge_axis(continuous, graph.beam_axis_xy)
        if axis is None:
            gaps.append(f"{post}: the post cap is left a RIGID knee — {why}; its frame "
                        f"moments are not a claim any record makes")
            continue
        if not _base_holds(graph.post_base.get(post), axis, held, at_node, z):
            gaps.append(f"{post}: the post cap is left a RIGID knee — its base is free about "
                        f"global {axis}, so a hinged cap would make the column pin-pin in "
                        f"{continuous[0]}'s plane; what braces that frame is not modelled")
            continue
        basis = (f"post cap under {', '.join(continuous)}: free in its plane, "
                 "held against its roll")
        caps = (replace(column.releases, basis=basis, j_hinge=axis) if column.n1 == top
                else replace(column.releases, basis=basis, i_hinge=axis))
        members[column.id] = replace(column, releases=caps)
        if _CAP_ASSUMPTION not in graph.assumptions:
            graph.assumptions = (*graph.assumptions, _CAP_ASSUMPTION)
    graph.members = tuple(sorted(members.values(), key=lambda m: m.id))
    return tuple(gaps)


def _released_at(member: Member, node: str) -> bool:
    r: Releases = member.releases
    return (r.i_moment if member.n0 == node else False) or (
        r.j_moment if member.n1 == node else False)


def _hinge_axis(beams: list[str], axis_xy: dict[str, tuple[float, float]]
                ) -> tuple[str | None, str]:
    """The one global axis every continuous beam here bends about, or why there is none."""
    found: set[str] = set()
    for tag in beams:
        dx, dy = axis_xy.get(tag, (0.0, 0.0))
        angle = math.degrees(math.atan2(abs(dy), abs(dx)))
        if angle <= _AXIS_TOLERANCE_DEG:
            found.add("Y")        # runs along X, bends about Y
        elif angle >= 90.0 - _AXIS_TOLERANCE_DEG:
            found.add("X")
        else:
            return None, f"{tag} runs oblique to the global axes ({angle:.0f} deg)"
    if len(found) > 1:
        return None, (f"{' and '.join(beams)} both run continuous over it in different "
                      f"directions, and a cap hinged in both planes holds neither beam")
    return found.pop(), ""


def _base_holds(node: str | None, axis: str, held: dict[str, tuple[bool, bool, bool]],
                at_node: dict[str, list[Member]], z: dict[str, float]) -> bool:
    """Whether rotation about ``axis`` is held at or below ``node``: by a support there, or
    by a column continuing rigidly DOWN to one (a post standing on another post)."""
    if node is None:
        return False
    if held.get(node, (False, False, False))["XYZ".index(axis)]:
        return True
    return any(_base_holds(other, axis, held, at_node, z)
               for member in at_node.get(node, ()) if member.is_vertical
               and not member.releases.any
               for other in (member.n0, member.n1) if z[other] < z[node])
