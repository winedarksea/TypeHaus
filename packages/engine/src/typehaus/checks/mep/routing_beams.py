"""Does a pipe, duct or raceway pass straight through a beam.

``mep.run_member_crossing`` grades floor joists and rims, and only legs that cross them. A
leg running ALONG a bay crosses no joist — and on catlin two 4" ERV returns rode their bays
east at ``_BAY_Z`` clean through the flush BM-M-HALL LVL with no finding anywhere. A beam
is a carrier, not a member of a floor's field, so no floor window applies: any real overlap
of the run's surface with the beam's section is a FAIL. Engineered beams take holes only
off the manufacturer's chart, and this engine holds none.

``Tier.STRUCTURAL``, no ``PermitItemSpec`` — same footing as ``mep.run_member_crossing``.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.mep.routing_geometry import run_polylines, run_radii
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.run_through_beam"
#: Framed-member categories that are carriers rather than a floor's field.
_BEAM_MEMBER_CATEGORIES = ("beam", "girder", "ridge_beam")
#: Overlap below this is a drawing tangency, not a hole.
_TOLERANCE_M = 0.125 * M_PER_IN


def _beams(ctx: CheckContext) -> list[tuple[str, object, float, float]]:
    """``(tag, plan polygon, z0, z1)`` for every beam solid and beam framed member."""
    from shapely.geometry import MultiPoint, Polygon

    from typehaus.resolve.geometry_members import member_box

    out = []
    for solid in ctx.model.solids:
        if solid.category == "beam" and len(solid.outline) >= 3:
            out.append((solid.tag, Polygon(solid.outline), solid.z0_m, solid.z1_m))
    for member in ctx.model.all_members():
        if member.category not in _BEAM_MEMBER_CATEGORIES:
            continue
        box = member_box(member)
        if box is None:
            continue
        corners = [*box.corners_bottom, *box.corners_top]
        footprint = MultiPoint([(x, y) for x, y, _ in corners]).convex_hull
        if footprint.area <= 0:
            continue
        out.append((f"{member.parent_uid}:{member.child_key}", footprint,
                    min(c[2] for c in corners), max(c[2] for c in corners)))
    return out


def _leg_overlap(a, b, za: float, zb: float, radius: float, footprint,
                 z0: float, z1: float) -> float:
    """How deep the leg's surface stands inside the beam, in metres (<= 0 is clear)."""
    from shapely.geometry import LineString, Point

    if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
        if not Point(a).buffer(radius).intersects(footprint):
            return 0.0
        lo, hi = min(za, zb), max(za, zb)
    else:
        leg = LineString([a, b])
        # Clip the centreline to the beam grown by the radius: the stretch whose surface is
        # over the beam in plan. Its z range is what meets the section.
        clipped = leg.intersection(footprint.buffer(radius))
        if clipped.is_empty:
            return 0.0
        ts = [leg.project(Point(xy)) / leg.length
              for geom in getattr(clipped, "geoms", [clipped]) for xy in geom.coords]
        zs = [za + (zb - za) * t for t in ts]
        lo, hi = min(zs), max(zs)
    return min(hi + radius, z1) - max(lo - radius, z0)


@check(Tier.STRUCTURAL, _CID)
def run_through_beam(ctx: CheckContext) -> list[Finding]:
    """A run's surface may not occupy a beam's section. One finding per (run, beam) met."""
    beams = _beams(ctx)
    runs = run_polylines(ctx)
    if not beams:
        return [_na(_CID, "this model resolves no beams for a run to pass through")]
    radii = run_radii(ctx)
    out: list[Finding] = []
    for kind, tag, path, z in runs:
        if len(path) < 2 or len(z) != len(path):
            continue
        radius = radii.get(tag, 0.0)
        for beam_tag, footprint, z0, z1 in beams:
            depth = max(_leg_overlap(path[i], path[i + 1], z[i], z[i + 1], radius,
                                     footprint, z0, z1)
                        for i in range(len(path) - 1))
            if depth > _TOLERANCE_M:
                out.append(_fail(
                    _CID,
                    f"{kind} {tag} passes through beam {beam_tag}: its "
                    f"{2 * radius / M_PER_IN:.3f}\" outside stands "
                    f"{depth / M_PER_IN:.3f}\" into the beam's section",
                    (tag, beam_tag),
                    fix=("reroute the run to cross the beam's line beyond its ends (through "
                         "the bearing wall's blocking), or drop it below the beam's soffit "
                         "in a soffit; a hole in an engineered beam needs the maker's chart")))
    if not out:
        return [_pass(_CID, f"{len(runs)} routed run(s) checked against {len(beams)} "
                            "beam(s); no run's surface enters a beam's section")]
    return out
