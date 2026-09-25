"""``structural.bearing_wall_footing`` — a framed bearing wall on a slab has a footing under it.

A slab-on-grade (R506.1, 3 1/2" minimum) is not a footing. IRC R403.1 sends a bearing wall's
load to the soil through a footing sized per R403.1.1, so each bearing point of a framed
bearing wall standing on a slab-on-grade — every stud, king, jack and corner stud the framing
resolved — must stand on a footing (or pad) whose top is the wall's base. A point may overhang
the footing by 1/4" (``_OVERHANG_TOL_M``) of its 1 1/2" and still bear; past that it FAILs.

What the check REPORTS but does not grade is the footing's reach past each point along the
wall. R403.1.1's projection P ("not less than 2 inches") is written for the strip's faces;
a strip's END has no code number, so the least margin is printed, flagged under 2", and left
to the reader.

Where a door breaks the wall, the header delivers the load to its jamb packs; the opening
itself needs nothing under it, and this check asks nothing of it (no member stands there).

In scope: a ``Wall`` (not a ``FoundationWall``) that something names as its bearing — a floor
system's joists, a roof, a stair, a floor opening or a wall above (``bearing_refs``) — whose
base sits on a slab ``slabs_on_grade`` counts as bearing on the ground. N/A is earned only by
reading every such wall and finding none on a slab-on-grade.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.floors import FloorSystem
from typehaus.model.structure import FoundationWall
from typehaus.resolve.framing.footprint import member_footprint

_CID = "structural.bearing_wall_footing"
_CODE = "IRC R403.1, R403.1.1"
_IN = 0.0254
# R403.1.1's face projection P, used only to flag a thin END margin.
_PROJECTION_M = 2.0 * _IN
# How far a bearing point may hang past the footing edge and still count as on it.
_OVERHANG_TOL_M = 0.25 * _IN
# A top within this of the wall base is the plane the wall stands on.
_Z_TOL_M = 0.5 * _IN
_BEARING_MEMBERS = frozenset({"stud", "king", "jack", "corner"})


def _named_bearings(plan) -> set[str]:
    """Every wall tag something in the plan says it bears on."""
    tags: set[str] = set()
    for element in plan.all_elements():
        tags.update(getattr(element, "bearing_refs", ()) or ())
        if isinstance(element, FloorSystem):
            tags.update(element.joists.bearing_refs)
    # Not ``stacks_on``: it is a layout tiebreaker, and a partition stacks on a partition.
    return tags


def _station_in(wall, point) -> float:
    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
    return ((point[0] - x0) * (x1 - x0) + (point[1] - y0) * (y1 - y0)) / run / _IN


def _grade_wall(wall, on: list[str], members, ground, footing_tags) -> Finding:
    from shapely.geometry import Polygon

    tags = (wall.tag, *on, *footing_tags)
    bare: list[str] = []
    margins: list[tuple[float, str]] = []
    for member in sorted(members, key=lambda m: _station_in(wall, m.p0)):
        ring, _z0, _z1 = member_footprint(member)
        seat = Polygon(ring)
        where = f"{member.child_key} at {_station_in(wall, member.p0):.1f}\""
        # Shrinking the seat by the tolerance on every edge = allowing that much overhang.
        core = seat.buffer(-_OVERHANG_TOL_M, join_style=2)
        if ground is None or core.difference(ground).area > 1e-9:
            bare.append(where)
            continue
        margin = ground.boundary.distance(seat) if seat.within(ground) else 0.0
        margins.append((margin, where))
    if bare:
        return failed(
            _CID,
            f"{wall.tag} stands on {', '.join(on)} (a slab-on-grade, not a footing) at "
            f"{len(bare)} of {len(members)} bearing points: {'; '.join(bare)} — stations are "
            "inches from its start node",
            tags, code=_CODE,
            fix=("lengthen the footing under the neighbouring run "
                 "(Footing.start_extension / end_extension) past each jamb pack, or give the "
                 "wall its own footing"),
        )
    least, where = min(margins)
    note = (f"; {where} has only {least / _IN:.2f}\" of footing past it, under the 2\" "
            "R403.1.1 sets for a face projection (an end margin has no code number)"
            if least < _PROJECTION_M - 1e-9 else
            f"; least footing past any point {least / _IN:.2f}\" ({where})")
    return passed(_CID, f"{wall.tag}: all {len(members)} bearing points stand on "
                        f"{', '.join(footing_tags) or 'a footing'}{note}", tags, code=_CODE)


@check(Tier.STRUCTURAL, _CID)
def bearing_wall_footing(ctx: CheckContext) -> list[Finding]:
    """Grade each framed bearing wall on a slab-on-grade for a footing under every bearing point."""
    if ctx.plan is None:
        return []
    from shapely.geometry import LineString, Polygon

    # The foundation sheet's own reading of "bears on grade"; one definition, two readers.
    from typehaus.emit.draw.foundation_schedule import slabs_on_grade
    from typehaus.resolve.overlay import union_all

    named = _named_bearings(ctx.plan)
    authored = {el.tag: el for el in ctx.plan.all_elements()}
    walls = [w for w in ctx.model.walls if w.tag in named
             and not isinstance(authored.get(w.tag), FoundationWall)]
    slabs = [(s, Polygon(s.outline)) for s in slabs_on_grade(ctx.model) if len(s.outline) >= 3]
    supports = [s for s in ctx.model.solids
                if s.category in ("footing", "pad") and len(s.outline) >= 3]

    out: list[Finding] = []
    for wall in sorted(walls, key=lambda w: w.tag):
        axis = LineString(wall.axis)
        on = [s.tag for s, poly in slabs
              if abs(s.z1_m - wall.z0_m) <= _Z_TOL_M and poly.buffer(1e-6).intersects(axis)]
        if not on:
            continue
        members = [m for m in wall.members if m.category in _BEARING_MEMBERS
                   and abs(m.p0[0] - m.p1[0]) < 1e-9 and abs(m.p0[1] - m.p1[1]) < 1e-9]
        if not members:
            out.append(unknown(_CID, f"{wall.tag} is a bearing wall on {', '.join(on)} but "
                               "resolved no studs, so its bearing points cannot be located",
                               (wall.tag, *on), code=_CODE))
            continue
        under = [s for s in supports if abs(s.z1_m - wall.z0_m) <= _Z_TOL_M]
        ground = union_all([Polygon(s.outline) for s in under]) if under else None
        footing_tags = sorted(s.tag for s in under
                              if Polygon(s.outline).intersects(axis.buffer(0.2)))
        out.append(_grade_wall(wall, on, members, ground, footing_tags))
    if not out:
        out.append(not_applicable(
            _CID, f"{len(walls)} framed walls are named as bearings and none stands on a "
            "slab-on-grade — each bears on a foundation wall, a floor or a beam",
            code=_CODE))
    return out
