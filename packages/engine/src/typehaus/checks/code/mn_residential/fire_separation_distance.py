"""R302.1 — exterior walls, openings and projections against fire separation distance.

FSD is measured from each exterior wall's outside face along its outward normal, cast from
both ends and the midpoint, to every parcel edge; the shortest hit governs. A face whose
normals reach no edge runs perpendicular to it, which R202's definition exempts. Lot lines
stand in for a street centreline, which is conservative. The exterior face is
``EnvelopeGeometry.exterior_face_probe``; projections are roof footprints (eaves and rakes).

Table R302.1(1), 2018 IRC: a wall at 5 ft or more needs no rating; under 5 ft it needs a
1-hour rating this model does not carry (UNKNOWN). Openings are not allowed under 3 ft and
are capped at 25% of the wall face from 3 to 5 ft. Projections are not allowed under 2 ft;
from 2 to 5 ft their underside needs a rating (UNKNOWN). Separation between two buildings on
the same lot (an imaginary line) is not graded.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Polygon

from typehaus.checks._authoring import failed, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve.envelope_geometry import _INTERIOR_PROBE_OFFSET_M, envelope_geometry

_CID, _CODE = "code.R302_1_exterior_walls", "R302.1"
_FT = 0.3048
_WALL_FT, _OPENING_FT, _PROJECTION_FT = 5.0, 3.0, 2.0
_MAX_OPENING_SHARE = 0.25
_REACH_M = 1000.0


def _fsd_m(probe: LineString, axis_mid: tuple[float, float],
           edges: list[LineString]) -> float | None:
    """Shortest outward-normal distance from the face behind ``probe`` to a lot line."""
    (ax, ay), (bx, by) = probe.coords[0], probe.coords[-1]
    run = math.hypot(bx - ax, by - ay)
    if run <= 1e-9:
        return None
    nx, ny = -(by - ay) / run, (bx - ax) / run
    mx, my = (ax + bx) / 2, (ay + by) / 2
    if (mx - axis_mid[0]) * nx + (my - axis_mid[1]) * ny < 0:
        nx, ny = -nx, -ny
    best = None
    for px, py in ((ax, ay), (mx, my), (bx, by)):
        ray = LineString([(px, py), (px + nx * _REACH_M, py + ny * _REACH_M)])
        for edge in edges:
            hit = ray.intersection(edge)
            if hit.is_empty:
                continue
            dist = ray.project(hit.representative_point()) + _INTERIOR_PROBE_OFFSET_M
            best = dist if best is None else min(best, dist)
    return best


def _opening_share(model, wall) -> float:
    face = math.dist(*wall.axis) * max(wall.z1_m - wall.z0_m, 1e-9)
    return sum(o.width_m * o.height_m for o in model.openings
               if o.host_wall == wall.tag) / face


@check(Tier.CODE, _CID)
def exterior_walls_fsd(ctx: CheckContext) -> list[Finding]:
    """Exterior walls, their openings and roof projections against Table R302.1(1)."""
    parcel = [p.xy_m for p in ctx.plan.project.site.parcel]
    if len(parcel) < 3:
        return [unknown(_CID, "no parcel ring to measure fire separation distance to",
                        code=_CODE)]
    edges = [LineString([parcel[i], parcel[(i + 1) % len(parcel)]])
             for i in range(len(parcel))]
    envelope = envelope_geometry(ctx.model)
    out: list[Finding] = []
    closest: tuple[float, str] | None = None
    for wall in ctx.model.walls:
        probe = envelope.exterior_face_probe(wall)
        if probe is None:
            continue
        mid = tuple((a + b) / 2 for a, b in zip(*wall.axis, strict=True))
        fsd = _fsd_m(probe, mid, edges)
        if fsd is None:
            continue
        feet = fsd / _FT
        closest = (feet, wall.tag) if closest is None or feet < closest[0] else closest
        if feet >= _WALL_FT:
            continue
        out.append(unknown(_CID, f"{wall.tag} is {feet:.1f} ft from a lot line: under 5 ft "
                           "it must be 1-hour rated, and walls carry no rating here",
                           (wall.tag,), code=_CODE))
        share = _opening_share(ctx.model, wall)
        if share > 0 and (feet < _OPENING_FT or share > _MAX_OPENING_SHARE):
            out.append(failed(_CID, f"{wall.tag} at {feet:.1f} ft carries openings on "
                              f"{share:.0%} of its face; none allowed under 3 ft, 25% to "
                              "5 ft", (wall.tag,), code=_CODE,
                              fix="Remove or shrink the openings, or move the wall."))
    for roof in ctx.model.roofs:
        if len(roof.footprint) < 3:
            continue
        feet = min(Polygon(roof.footprint).distance(edge) for edge in edges) / _FT
        if feet < _PROJECTION_FT:
            out.append(failed(_CID, f"{roof.tag} projects to {feet:.1f} ft of a lot line; "
                              "none allowed under 2 ft", (roof.tag,), code=_CODE,
                              fix="Shorten the overhang."))
        elif feet < _WALL_FT:
            out.append(unknown(_CID, f"{roof.tag} projects to {feet:.1f} ft of a lot line: "
                               "2-5 ft needs a 1-hour underside, which is not modelled",
                               (roof.tag,), code=_CODE))
        else:
            out.append(passed(_CID, f"{roof.tag} projections stay {feet:.1f} ft off every "
                              "lot line", (roof.tag,), code=_CODE))
    if closest is None:
        out.append(unknown(_CID, "no exterior wall faces a lot line", code=_CODE))
    elif closest[0] >= _WALL_FT:
        out.append(passed(_CID, f"every exterior wall is 5 ft or more from the lot lines "
                          f"(closest {closest[1]} at {closest[0]:.1f} ft)", code=_CODE))
    return out
