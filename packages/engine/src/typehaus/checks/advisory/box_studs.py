"""ADVISORY — a flush device box that lands on a stud, king or jack (geometry review M3-106).

A nail-on box fixes to the side of a stud, so its body must sit beside the framing, never
over it. Each flush box (``resolve/device_boxes.py``, decision #93) is read against the
upright members of its own wall that share its depth and height. A clash names the
smallest station move that lands the box clear, beside the member, without entering an
opening, a pocket cavity or another box's cavity. A surface box sits on concrete and is
not graded. A box whose ``BoxRow.block_profile`` derived no block is reported too.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.checks._authoring import not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory
from typehaus.resolve.geometry_members import member_box

CHECK_ID = "advisory.box_on_stud"
_IN_M = 0.0254
_TOL_M = 0.125 * _IN_M  # an overlap under 1/8" is a box touching the stud face


@dataclass(frozen=True)
class StudClash:
    overlap_m: float  # along the wall, the deepest member intrusion into the box
    members: tuple[str, ...]  # child keys of the members the box sits over
    shift_m: float | None  # signed station move that clears it, None when none does


def _span(points: list[tuple[float, float]], origin: tuple[float, float],
          axis: tuple[float, float]) -> tuple[float, float]:
    values = [(x - origin[0]) * axis[0] + (y - origin[1]) * axis[1] for x, y in points]
    return min(values), max(values)


def stud_clash(model: object, box: object) -> StudClash | None:
    """The box against its wall's upright framing, or None for a surface box / no wall."""
    if box.mounting == "surface":
        return None
    wall = model.wall(box.wall_tag)
    if wall is None:
        return None
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    tangent = ((x1 - x0) / length, (y1 - y0) / length)  # stations run along it
    s_lo, s_hi = _span(list(box.footprint), (x0, y0), tangent)
    n_lo, n_hi = _span(list(box.footprint), box.face_point, box.normal)
    members: list[tuple[float, float, str]] = []
    for member in wall.members:
        if member.p0 != member.p1 or member.plan_outline is not None:
            continue
        if member.z1_m <= box.z0_m + _TOL_M or member.z0_m >= box.z1_m - _TOL_M:
            continue
        solid = member_box(member)
        if solid is None:
            continue
        ring = [(x, y) for x, y, _z in solid.corners_bottom]
        m_lo, m_hi = _span(ring, box.face_point, box.normal)
        if min(m_hi, n_hi) - max(m_lo, n_lo) <= _TOL_M:
            continue  # the other face's stud in a staggered wall
        members.append((*_span(ring, (x0, y0), tangent), member.child_key))
    voids = [(o.center_along_m - o.width_m / 2 - (o.pocket_run_m if o.pocket_sign < 0 else 0),
              o.center_along_m + o.width_m / 2 + (o.pocket_run_m if o.pocket_sign > 0 else 0),
              o.tag)
             for o in model.openings if o.host_wall == wall.tag
             and o.sill_m < box.z1_m and o.sill_m + o.height_m > box.z0_m]
    for other in model.device_boxes:  # a back-to-back box shares the cavity
        if (other is box or other.wall_tag != wall.tag or other.mounting == "surface"
                or other.z1_m <= box.z0_m or other.z0_m >= box.z1_m):
            continue
        o_lo, o_hi = _span(list(other.footprint), box.face_point, box.normal)
        if min(o_hi, n_hi) - max(o_lo, n_lo) > _TOL_M:
            voids.append((*_span(list(other.footprint), (x0, y0), tangent), other.device_tag))
    hits = [(a, b, key) for a, b, key in members if min(b, s_hi) - max(a, s_lo) > _TOL_M]
    if not hits:
        return StudClash(0.0, (), 0.0)
    overlap = max(min(b, s_hi) - max(a, s_lo) for a, b, _ in hits)
    obstacles = members + voids + [(-1.0, 0.0, "start"), (length, length + 1.0, "end")]
    moves = [m for m in (_clear(obstacles, s_lo, s_hi, +1), _clear(obstacles, s_lo, s_hi, -1))
             if m is not None]
    return StudClash(overlap, tuple(sorted(key for _a, _b, key in hits)),
                     min(moves, key=abs) if moves else None)


def _clear(obstacles: list[tuple[float, float, str]], lo: float, hi: float,
           sense: int) -> float | None:
    """Walk the box one way until nothing overlaps it; the move, or None after 12"."""
    shift = 0.0
    for _ in range(len(obstacles) + 1):
        hit = [(a, b) for a, b, _ in obstacles
               if min(b, hi + shift) - max(a, lo + shift) > _TOL_M]
        if not hit:
            return shift
        shift = (max(b for _a, b in hit) - lo if sense > 0
                 else min(a for a, _b in hit) - hi)
        if abs(shift) > 12 * _IN_M:
            return None
    return None


@check(Tier.ADVISORY, CHECK_ID)
def box_on_stud(ctx: CheckContext) -> list[Finding]:
    """Each flush device box against the studs, kings and jacks of its wall."""
    out: list[Finding] = []
    blocked = {(row.box_product_ref, row.mounting) for el in ctx.plan.all_elements()
               if el.element_kind == "BoxStandard" for row in el.rows if row.block_profile}
    for box in sorted(ctx.model.device_boxes, key=lambda b: b.device_tag):
        clash = stud_clash(ctx.model, box)
        if clash is None:
            continue
        tags = (box.device_tag, box.wall_tag)
        what = f"{box.device_tag}'s {box.box_product} box on {box.wall_tag}"
        if (box.box_product, box.mounting) in blocked and box.block_key is None:
            out.append(advisory(
                CHECK_ID, f"{what}: its row asks a block behind the box and none fits "
                          "(no stud each side, or too shallow a cavity)", tags,
                Result.ADVISORY, fix="re-station the box in a full stud bay"))
        if not clash.members:
            out.append(passed(CHECK_ID, f"{what} clears the wall's upright framing", tags))
            continue
        move = ("no station within 12 in. clears it" if clash.shift_m is None else
                f"move its station {clash.shift_m / _IN_M:+.2f} in. to land it beside the "
                "framing")
        out.append(advisory(
            CHECK_ID, f"{what} sits {clash.overlap_m / _IN_M:.2f} in. over "
                      f"{', '.join(clash.members)}; {move}", tags, Result.ADVISORY,
            fix="re-station the device so its nail-on box fixes to the side of a stud"))
    if not out:
        return [not_applicable(CHECK_ID, "no device sits on a flush box")]
    return out
