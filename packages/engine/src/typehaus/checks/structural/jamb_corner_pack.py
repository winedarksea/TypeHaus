"""``structural.jamb_corner_pack`` — a jamb pack sharing an L corner still does both jobs.

Where an opening's jack and king stand in an L corner's square, the framer builds one pack
(``resolve/framing/corner_jamb_packs.py``; D-S-BATH1 at N-S-BA1 is five studs). That pack
has to keep three duties, and each is read off the resolved members:

* **jack bearing** — a jack of the same wall under each header end, topped at the header's
  underside, carrying at least one stud thickness of it (R602.7.5's minimum is one jack);
* **king continuity** — a full-height king, corner or stud against the jack's outboard face,
  rising past the header's underside, so the header end and the jack have it to nail to;
* **corner backing** — the neighbour's end stud faces at least one stud thickness of the
  owner's full-height studs, for R602.3(1)'s corner-stud nailing and the inside-corner board.

``member_interference`` stays strict alongside it: sharing means the packs touch, never that
they overlap.
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.footprint import member_footprint

_CID = "structural.jamb_corner_pack"
_CODE = "IRC R602.7.5, R602.3(1)"
#: Faces within this read as touching; z ends within it as meeting.
_TOUCH_M = 0.125 * M_PER_IN
_FULL_HEIGHT = frozenset({"king", "corner", "stud"})
#: R602.7.5's minimum jack and the stud a corner nails through, both one 2x thickness.
_STUD_THICKNESS_M = 1.5 * M_PER_IN


def _along(point, origin, direction) -> float:
    return (point[0] - origin[0]) * direction[0] + (point[1] - origin[1]) * direction[1]


def _span(ring, origin, direction) -> tuple[float, float]:
    stations = [_along(p, origin, direction) for p in ring]
    return min(stations), max(stations)


def _pack_sides(wall, index: str):
    """``{side: (jacks, kings)}`` for opening ``index`` of ``wall`` (child keys)."""
    sides: dict[str, tuple[list, list]] = {}
    for member in wall.members:
        for role in ("jack", "king"):
            prefix = f"{role}-{index}-"
            if member.category == role and member.child_key.startswith(prefix):
                side = member.child_key[len(prefix)]
                sides.setdefault(side, ([], []))[role == "king"].append(member)
    return sides


def _grade_side(owner, neighbour, header, jacks, origin, direction) -> list[str]:
    """What this side of the shared pack fails to do; empty when it does all three."""
    problems: list[str] = []
    h_ring, h_lo, _h_hi = member_footprint(header)
    h_low, h_high = _span(h_ring, origin, direction)
    j_spans = [(_span(member_footprint(j)[0], origin, direction), j) for j in jacks]
    outboard = max if _along(jacks[0].p0, origin, direction) > (h_low + h_high) / 2 else min
    bearing = [j for (lo, hi), j in j_spans
               if abs(j.z1_m - h_lo) <= _TOUCH_M
               and min(hi, h_high) - max(lo, h_low) >= _STUD_THICKNESS_M - _TOUCH_M]
    if not bearing:
        problems.append(f"no jack carries {header.child_key}'s end (one stud thickness, "
                        "topped at its underside)")
    face = outboard(edge for (lo, hi), _j in j_spans for edge in (lo, hi))
    full = [m for wall in (owner, neighbour) for m in wall.members
            if m.category in _FULL_HEIGHT and m.p0 == m.p1]
    king_ok = False
    for member in full:
        ring, lo_z, hi_z = member_footprint(member)
        # Its category makes it plate to plate; it must also rise past the jack beside the
        # header end (a header may run up into the plates, D-G-SERVICE's LVL does).
        if lo_z > min(j.z0_m for j in jacks) + _TOUCH_M or hi_z < h_lo + _STUD_THICKNESS_M:
            continue
        lo, hi = _span(ring, origin, direction)
        if abs((lo if outboard is max else hi) - face) <= _TOUCH_M:
            king_ok = True
            break
    if not king_ok:
        problems.append("no full-height king, corner or stud stands against the jack's "
                        "outboard face")
    return problems


def _neighbour_backed(owner, neighbour, point) -> bool:
    """The neighbour's end stud faces >= one stud thickness of the owner's full studs."""
    ends = [m for m in neighbour.members if m.category in _FULL_HEIGHT and m.p0 == m.p1]
    if not ends:
        return False
    end = min(ends, key=lambda m: math.dist(m.p0, point))
    end_ring, end_lo, end_hi = member_footprint(end)
    face = Polygon(end_ring).exterior
    contact = 0.0
    for member in owner.members:
        if member.category not in _FULL_HEIGHT or member.p0 != member.p1:
            continue
        ring, lo, hi = member_footprint(member)
        if lo > end_lo + _TOUCH_M or hi < end_hi - _TOUCH_M:
            continue
        # The buffer adds about 2 x _TOUCH_M of side contact per stud; ignored at 1.5".
        contact += Polygon(ring).buffer(_TOUCH_M).intersection(face).length
    return contact >= _STUD_THICKNESS_M


@check(Tier.STRUCTURAL, _CID)
def jamb_corner_pack(ctx: CheckContext) -> list[Finding]:
    """Every opening whose jamb pack stands in an L corner's square, graded on both roles."""
    walls = {wall.tag: wall for wall in ctx.model.walls if wall.members}
    out: list[Finding] = []
    for junction in ctx.model.junctions:
        if junction.kind != "l" or junction.framing_owner not in walls:
            continue
        neighbour_tag = next((item.wall_tag for item in junction.incidents
                              if item.wall_tag != junction.framing_owner), None)
        owner, neighbour = walls[junction.framing_owner], walls.get(neighbour_tag)
        structure = next((layer for layer in getattr(neighbour, "layers", ())
                          if layer.function == "structure"), None)
        if neighbour is None or structure is None or not structure.polygon:
            continue
        origin = owner.axis[0]
        run = math.dist(owner.axis[0], owner.axis[1])
        direction = ((owner.axis[1][0] - origin[0]) / run, (owner.axis[1][1] - origin[1]) / run)
        square = _span(structure.polygon, origin, direction)
        for header in owner.members:
            if header.category != "header" or not header.child_key.startswith("header-"):
                continue
            index = header.child_key.split("-", 1)[1]
            for _side, (jacks, kings) in sorted(_pack_sides(owner, index).items()):
                spans = [_span(member_footprint(m)[0], origin, direction)
                         for m in (*jacks, *kings)]
                if not jacks or not any(min(hi, square[1]) - max(lo, square[0]) > _TOUCH_M
                                        for lo, hi in spans):
                    continue
                problems = _grade_side(owner, neighbour, header, jacks, origin, direction)
                if not _neighbour_backed(owner, neighbour, junction.point):
                    problems.append(f"{neighbour.tag}'s end stud is not backed by one stud "
                                    f"thickness of {owner.tag}'s full-height framing")
                what = header.opening_tag or f"{owner.tag}:{header.child_key}"
                where = (f"{what}'s jamb pack shares {owner.tag}'s corner with "
                         f"{neighbour.tag} at {junction.node_tag}")
                tags = tuple(t for t in (header.opening_tag, owner.tag, neighbour.tag) if t)
                if problems:
                    out.append(structural_advisory(
                        _CID, f"{where}: {'; '.join(problems)}", tags, Result.FAIL,
                        "frame the opening clear of the corner square, or let the pack "
                        "take the corner (resolve/framing/corner_jamb_packs.py)",
                        code=_CODE))
                else:
                    out.append(structural_advisory(
                        _CID, f"{where}: a jack under the header end, a full-height stud "
                              "against it, and the neighbour's end stud backed",
                        tags, Result.PASS, code=_CODE))
    if not out:
        return [_na(_CID, "no opening's jamb pack stands in an L corner's square", ())]
    return out
