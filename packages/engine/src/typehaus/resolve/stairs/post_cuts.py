"""Landing framing meets an authored column: it stops at the column's faces.

A landing rim or joist whose run reaches an authored ``Post`` standing through the landing
framing is cut at the column faces; a run through a column becomes two pieces. Every cut end
then hangs on that face (``joints/column_hung.py`` derives a concealed-flange hanger), so no
rim runs into a post or rests on nothing. Hand check:
houses/catlin/notes/stair_landing_post_hangers.md.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.model.structure import Post
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedModel

# A leftover shorter than two hanger seats (2 x 1 3/4") is no member worth hanging.
_MIN_PIECE_M = inch(3.5).meters
_TOL = 1e-6

PostSpan = tuple[tuple[float, float, float, float], float, float]


def _authored_post_spans(model: ResolvedModel) -> list[PostSpan]:
    """Each authored ``Post`` as (plan box, z0, z1), read off the plan.

    Posts resolve after the stairs, so their extent is derived here the way
    ``envelope._resolve_post`` does it, less connector insets. A post whose support has
    not resolved yet is left out: it claims no corner it cannot be shown to reach.
    """
    tops = {solid.tag: solid.z1_m for solid in model.solids}
    spans = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Post):
                continue
            height = (element.height.meters if element.height is not None
                      else storey.default_ceiling_height.meters)
            if element.supported_by:
                if element.supported_by not in tops:
                    continue
                z0 = tops[element.supported_by]
                z1 = z0 + height
            else:
                z1 = storey.elevation.meters
                z0 = z1 - height
            section = cross_section(element.size)
            x, y = element.position.xy_m
            half_w, half_d = section.width_m / 2.0, section.depth_m / 2.0
            spans.append(((x - half_w, y - half_d, x + half_w, y + half_d), z0, z1))
    return spans


def frame_landing_to_posts(model: ResolvedModel, members: tuple[FramedMember, ...]
                           ) -> tuple[FramedMember, ...]:
    """``members`` with every level landing rim/joist cut back to the authored posts' faces."""
    spans = _authored_post_spans(model)
    if not spans:
        return members
    out: list[FramedMember] = []
    for member in members:
        if (member.category != "landing_framing" or member.p0 == member.p1
                or "winder" in member.child_key):
            out.append(member)
            continue
        out.extend(_cut_at_posts(member, spans))
    return tuple(out)


def _cut_at_posts(member: FramedMember, spans: list[PostSpan]) -> list[FramedMember]:
    if abs(member.p1[1] - member.p0[1]) < _TOL:
        run_axis = 0
    elif abs(member.p1[0] - member.p0[0]) < _TOL:
        run_axis = 1
    else:
        return [member]  # only axis-aligned landing framing is generated
    cross = 1 - run_axis
    half = (member.plan_width_m or cross_section(member.profile).width_m) / 2.0
    centre = member.p0[cross]
    s0, s1 = member.p0[run_axis], member.p1[run_axis]
    pieces = [tuple(sorted((s0, s1)))]
    for box, z0, z1 in spans:
        if member.z0_m >= z1 - _TOL or member.z1_m <= z0 + _TOL:
            continue
        if centre + half <= box[cross] + _TOL or centre - half >= box[cross + 2] - _TOL:
            continue
        lo, hi = box[run_axis], box[run_axis + 2]
        kept = []
        for a, b in pieces:
            if b <= lo + _TOL or a >= hi - _TOL:
                kept.append((a, b))
                continue
            if lo - a >= _MIN_PIECE_M:
                kept.append((a, lo))
            if b - hi >= _MIN_PIECE_M:
                kept.append((hi, b))
        pieces = kept
    if pieces == [tuple(sorted((s0, s1)))]:
        return [member]
    out = []
    for index, (a, b) in enumerate(pieces):
        start, end = (a, b) if s0 <= s1 else (b, a)
        p0, p1 = list(member.p0), list(member.p1)
        p0[run_axis], p1[run_axis] = start, end
        key = member.child_key if len(pieces) == 1 else f"{member.child_key}-seg{index}"
        out.append(replace(member, child_key=key, p0=(p0[0], p0[1]), p1=(p1[0], p1[1]),
                           length_m=b - a))
    return out
