"""Which faces a joist end's sill ties take: closely spaced ends are one pack.

An A35 lies beside its member, 1/8" clear (``plate_angle``). Parallel members whose ends sit
together with a clear gap narrower than a tie's slot (its width and 1/8" each side) are one
pack: no tie fits between them, so the pack is tied on its two outer faces (C-C-2026 p. 310
fn. 1 allows angles on each side of a joist 3" thick or more; each outer tie here nails a
different ply, and every pack is wider than 3"). The outermost tied member at each side
owns that face's tie; a lone member takes the first clear side. Each tie names the framing
over its flat leaf, so a blocked tie is reported, never drawn through wood.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN

#: Clear of the member or block the leaf sits beside.
GAP_M = 0.125 * M_PER_IN
#: How far a partner's or rim's end may sit from the tied end and still be at it.
NEAR_M = 6.0 * M_PER_IN
#: Members that land on a sill beside a joist end and so close its slot.
_PACKED = frozenset({"joist", "sister_joist", "trimmer"})
#: A member standing within this of the end's underside stands on the same sill.
_Z_TOL_M = 0.5 * M_PER_IN


@dataclass(frozen=True)
class SillTie:
    side: float  # -1/+1 across the member, in its (end -> far) left-normal frame
    centre: tuple  # the heel's plan point
    inward: tuple  # the flat leaf's direction off the heel
    blocked_by: tuple  # framing under the flat leaf


@dataclass(frozen=True)
class SillPack:
    ties: tuple  # SillTie, the ones this member owns
    extent_m: tuple  # (lo, hi) of the pack, plan coordinate across the support
    members: int  # tied members in the pack


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    run = math.hypot(dx, dy) or 1.0
    return dx / run, dy / run


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _width(member) -> float:
    from typehaus.resolve.framing.profiles import cross_section

    return member.plan_width_m or cross_section(member.profile).width_m


def _blocked(floors, spot, z_m) -> tuple:
    """Framing standing at ``z_m`` (the sill top) over ``spot``."""
    from shapely.geometry import LineString

    x0, y0, x1, y1 = spot.bounds
    out = []
    for floor in floors:
        for m in floor.members:
            if m.category == "rim" or not m.z0_m - _Z_TOL_M <= z_m < m.z1_m:
                continue
            r = _width(m) / 2.0
            if (max(m.p0[0], m.p1[0]) + r <= x0 or min(m.p0[0], m.p1[0]) - r >= x1
                    or max(m.p0[1], m.p1[1]) + r <= y0 or min(m.p0[1], m.p1[1]) - r >= y1):
                continue
            if LineString([m.p0[:2], m.p1[:2]]).buffer(r, cap_style=2).intersection(
                    spot).area > 1e-7:
                out.append(m.child_key or m.category)
    return tuple(sorted(set(out)))


def sill_pack(member, point, floor, floors, dims, tied=frozenset({"joist"})) -> SillPack:
    """The ties ``member``'s end at ``point`` owns, and the pack it stands in.

    An I-joist or LSL end ties on its end rim's inboard face; a truss or sawn end on its
    own side face (``floor`` holds the rim)."""
    from typehaus.hardware.plan_geometry import distance_point_to_segment
    from typehaus.resolve.connector_geometry.plate_angle import footprint
    from typehaus.resolve.framing.profiles import cross_section

    end, far = ((member.p0, member.p1) if math.dist(point, member.p0)
                <= math.dist(point, member.p1) else (member.p1, member.p0))
    u = _unit(end, far)
    a = (-u[1], u[0])
    slot = dims.width_m + 2.0 * GAP_M
    found = []  # (lo, hi, tied?, is self)
    for f in floors:
        for s in f.members:
            if (s.category not in _PACKED or abs(_dot(_unit(s.p0, s.p1), a)) > 0.01
                    or not s.z0_m - _Z_TOL_M <= member.z0_m < s.z1_m):
                continue
            near = min((s.p0, s.p1), key=lambda p: abs(_dot((p[0] - end[0], p[1] - end[1]),
                                                             u)))
            off = _dot((s.p0[0] - end[0], s.p0[1] - end[1]), a)
            if (abs(_dot((near[0] - end[0], near[1] - end[1]), u)) > NEAR_M
                    or abs(off) > 4.0 * slot + _width(member)):
                continue
            half = _width(s) / 2.0
            found.append((off - half, off + half, s.category in tied, s is member))
    me = next(f for f in found if f[3]) if any(f[3] for f in found) else (
        -_width(member) / 2.0, _width(member) / 2.0, True, True)
    lo, hi, grown = me[0], me[1], True
    while grown:
        grown = False
        for f in found:
            if f[0] < hi + slot - 1e-9 and f[1] > lo - slot + 1e-9 \
                    and (f[0] < lo - 1e-9 or f[1] > hi + 1e-9):
                lo, hi, grown = min(lo, f[0]), max(hi, f[1]), True
    pack = [f for f in found if f[0] >= lo - 1e-9 and f[1] <= hi + 1e-9] or [me]
    centres = sorted(((f[0] + f[1]) / 2.0, f[3]) for f in pack if f[2] or f[3])
    sides = []
    if centres[0][1]:
        sides.append(-1.0)
    if centres[-1][1] and (len(pack) > 1 or not sides):
        sides.append(1.0)
    if len(pack) > 1 and len(sides) == 2 and (me[0] + me[1]) / 2.0 > (lo + hi) / 2.0:
        sides.reverse()  # the member's own exposed face first
    face = None
    if cross_section(member.profile).shape == "i_joist" or "lsl" in member.profile.lower():
        rims = [r for r in floor.members if r.category == "rim"
                and abs(_dot(_unit(r.p0, r.p1), u)) < 0.01
                and distance_point_to_segment(end, r.p0, r.p1) <= NEAR_M]
        face = 0.0
        if rims:
            rim = min(rims, key=lambda r: distance_point_to_segment(end, r.p0, r.p1))
            face = _dot((rim.p0[0] - end[0], rim.p0[1] - end[1]), u) + _width(rim) / 2.0
    half = dims.width_m / 2.0

    def tie(side):
        across = hi if side > 0 else lo
        if face is not None:
            lateral = across + side * (GAP_M + half)
            centre = (end[0] + u[0] * face + a[0] * lateral,
                      end[1] + u[1] * face + a[1] * lateral)
            inward = u
        else:
            along = GAP_M + half
            centre = (end[0] + a[0] * across + u[0] * along,
                      end[1] + a[1] * across + u[1] * along)
            inward = (a[0] * side, a[1] * side)
        spot = footprint(centre, inward, dims)
        return SillTie(side, centre, inward, _blocked(floors, spot, member.z0_m))

    if len(pack) == 1:  # a lone member: the first clear side
        options = [tie(-1.0), tie(1.0)]
        ties = (next((t for t in options if not t.blocked_by), options[0]),)
    else:
        ties = tuple(tie(side) for side in sides)
    across = 0 if abs(a[0]) >= abs(a[1]) else 1
    ends = sorted(end[across] + a[across] * v for v in (lo, hi))
    return SillPack(ties, (ends[0], ends[1]), sum(1 for f in pack if f[2] or f[3]))
