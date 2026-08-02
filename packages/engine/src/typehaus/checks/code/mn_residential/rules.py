"""R305 ceiling height and R401.3 lot drainage (→ 12).

Every rule is tri-state (#32): a rule that cannot evaluate reports UNKNOWN with the reason
and is counted separately, never as a pass.

This module used to hold every MN residential rule — nine hundred lines across seven
unrelated articles. The rest now live in topic modules beside it (``egress``, ``stairs``,
``fall_protection``, ``alarms``, ``circulation``, ``fire_separation``, ``ventilation``,
``attic``), all sharing :mod:`._common`.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import (_fail, _foundation_footprint,
                                                         _pass, _room_storey, _unknown)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.model.refs import FollowRoof
from typehaus.quantities import ft
from typehaus.resolve.roof_geometry import roof_headroom_areas

_MIN_CEILING = ft(7)
_MIN_SLOPED_CEILING = ft(5)
_MIN_SLOPED_CEILING_FRACTION = 0.5

# R401.3 lot drainage: grade must fall away from the foundation within the first 10'. Pervious
# ground needs 5% (6" per 10'), measured from spot elevations (code.R401_3_grading). Impervious
# surfaces (walks, patios, driveways, slabs abutting the house) need only 2%, evaluated from the
# authored ImperviousSurface hardscapes (code.R401_3_impervious).
_GRADING_BAND = ft(10)
_MIN_GROUND_SLOPE = 0.05  # 6" per 10' away from the foundation (pervious ground)
_MIN_IMPERVIOUS_SLOPE = 0.02  # 2% away from the foundation (walks/patios/slabs)
_SLOPE_EPS = 1e-3


@check(Tier.CODE, "code.R305_ceiling_height")
def ceiling_height(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room" or room.occupancy is Occupancy.UNCONDITIONED:
            continue
        if room.ceiling is None:
            storey = _room_storey(ctx, room.tag)
            h = storey.default_ceiling_height if storey else None
        elif hasattr(room.ceiling, "meters"):
            h = room.ceiling
        elif isinstance(room.ceiling, FollowRoof):
            out.append(_follow_roof_ceiling_finding(ctx, room))
            continue
        if h is None:
            out.append(_unknown("code.R305_ceiling_height", "no ceiling height",
                                (room.tag,), "R305.1"))
        elif h < _MIN_CEILING:
            out.append(_fail("code.R305_ceiling_height",
                             f"{room.tag} ceiling {h.fmt()} < 7'-0\" minimum", (room.tag,),
                             "R305.1"))
        else:
            out.append(_pass("code.R305_ceiling_height", f"{room.tag} ceiling ok", "R305.1"))
    return out


def _follow_roof_ceiling_finding(ctx: CheckContext, room) -> Finding:
    roof = next((item for item in ctx.model.roofs if item.tag == room.ceiling.roof_ref), None)
    resolved_room = next((item for item in ctx.model.rooms if item.tag == room.tag), None)
    storey = _room_storey(ctx, room.tag)
    if roof is None or resolved_room is None or storey is None:
        return _unknown("code.R305_ceiling_height", "unresolved roof-following ceiling",
                        (room.tag,), "R305.1")
    area, at_seven = roof_headroom_areas(
        resolved_room.clear_face, roof, storey.elevation.meters, _MIN_CEILING.meters,
    )
    _, at_five = roof_headroom_areas(
        resolved_room.clear_face, roof, storey.elevation.meters, _MIN_SLOPED_CEILING.meters,
    )
    if area <= 1e-9:
        return _unknown("code.R305_ceiling_height", "room has no area beneath referenced roof",
                        (room.tag,), "R305.1")
    fraction = at_seven / area
    if at_five + 1e-9 < area or fraction + 1e-9 < _MIN_SLOPED_CEILING_FRACTION:
        return _fail(
            "code.R305_ceiling_height",
            f"{room.tag} has {fraction:.0%} of floor at or above 7'-0\"; "
            "R305.1 requires at least 50% with no habitable area below 5'-0\"",
            (room.tag,), "R305.1",
        )
    return _pass("code.R305_ceiling_height",
                 f"{room.tag} follows {roof.tag}: {fraction:.0%} of floor at or above 7'-0\"",
                 "R305.1")


@check(Tier.CODE, "code.R401_3_grading")
def foundation_grading(ctx: CheckContext) -> list[Finding]:
    """R401.3 lot drainage — grade must fall away from the foundation within 10 feet.

    The primary building footprint is reconstructed from the foundation walls; every spot
    elevation outside it and within 10' is a drainage station, and the shallowest measured
    slope must reach 5% (6" per 10'). Impervious-surface grading (2%) is the sibling
    requirement asserted separately by ``code.R401_3_impervious``.
    """
    from shapely.geometry import Point

    site = ctx.plan.project.site
    if site.grade is None:
        return [_unknown("code.R401_3_grading", "no average-grade datum on the site",
                         (), "R401.3")]
    if not site.spot_elevations:
        return [_unknown("code.R401_3_grading",
                         "no spot elevations to measure grade slope", (), "R401.3")]
    if not any(wall.is_foundation for wall in ctx.model.walls):
        return [_unknown("code.R401_3_grading", "no foundation walls to grade around",
                         (), "R401.3")]
    footprint = _foundation_footprint(ctx)
    if footprint is None:
        return [_unknown("code.R401_3_grading",
                         "could not reconstruct a foundation footprint", (), "R401.3")]
    boundary = footprint.exterior

    grade_m = site.grade.meters
    band_m = _GRADING_BAND.meters
    worst: tuple[float, float, float] | None = None  # (slope, distance_m, elevation_m)
    stations = 0
    for spot in site.spot_elevations:
        point = Point(spot.position.xy_m)
        if footprint.covers(point):
            continue  # interior grade point, not a perimeter drainage station
        distance_m = boundary.distance(point)
        if distance_m <= 1e-6 or distance_m > band_m + 1e-9:
            continue
        stations += 1
        elevation_m = spot.elevation.meters
        slope = (grade_m - elevation_m) / distance_m  # positive = falls away from the wall
        if worst is None or slope < worst[0]:
            worst = (slope, distance_m, elevation_m)
    if worst is None:
        return [_unknown("code.R401_3_grading",
                         "no spot elevations within 10' of the building foundation",
                         (), "R401.3")]
    slope, distance_m, elevation_m = worst
    if slope + _SLOPE_EPS < _MIN_GROUND_SLOPE:
        fall_in = (grade_m - elevation_m) / 0.0254
        run_ft = distance_m / 0.3048
        return [_fail("code.R401_3_grading",
                      f"grade only falls {slope * 100:.1f}% away from the foundation "
                      f"({fall_in:+.1f}\" over {run_ft:.1f}'); R401.3 requires "
                      f"{_MIN_GROUND_SLOPE * 100:.0f}% (6\" within 10')", (), "R401.3")]
    return [_pass("code.R401_3_grading",
                  f"grade falls at least {_MIN_GROUND_SLOPE * 100:.0f}% away from the foundation "
                  f"at all {stations} station(s) within 10' (shallowest {slope * 100:.1f}%)",
                  "R401.3")]


@check(Tier.CODE, "code.R401_3_impervious")
def impervious_surface_grading(ctx: CheckContext) -> list[Finding]:
    """R401.3 — impervious surfaces abutting the house must slope >= 2% away from the foundation.

    Each authored ``ImperviousSurface`` (walk/patio/driveway/slab) whose nearest edge lies within
    10' of the primary foundation footprint is a station. The run away from the foundation comes
    from the outline (far-edge reach minus near-edge reach), the fall from the authored near/far
    grade elevations, and the shallowest surface slope must reach 2%. Mirrors
    ``code.R401_3_grading`` and emits one finding for the worst surface.
    """
    from shapely.geometry import Point

    site = ctx.plan.project.site
    surfaces = getattr(site, "impervious_surfaces", ())
    if not surfaces:
        return []  # no impervious surfaces modeled abutting the foundation; rule does not apply
    footprint = _foundation_footprint(ctx)
    if footprint is None:
        return [_unknown("code.R401_3_impervious",
                         "no foundation footprint to grade impervious surfaces against",
                         (), "R401.3")]
    boundary = footprint.exterior
    band_m = _GRADING_BAND.meters
    worst: tuple[float, str, float, float] | None = None  # (slope, label, run_m, drop_m)
    stations = 0
    for surface in surfaces:
        verts = [p.xy_m for p in surface.outline]
        if len(verts) < 2:
            continue
        dists = [boundary.distance(Point(v)) for v in verts]
        near_i = min(range(len(verts)), key=dists.__getitem__)
        far_i = max(range(len(verts)), key=dists.__getitem__)
        if dists[near_i] > band_m + 1e-9:
            continue  # surface lies entirely beyond 10' of the foundation
        run_m = dists[far_i] - dists[near_i]
        if run_m <= _SLOPE_EPS:
            continue  # degenerate outline with no reach away from the foundation
        stations += 1
        drop_m = surface.near_elevation.meters - surface.far_elevation.meters
        slope = drop_m / run_m  # positive = falls away from the foundation
        if worst is None or slope < worst[0]:
            worst = (slope, surface.label, run_m, drop_m)
    if worst is None:
        return []  # no impervious surface within 10' of the foundation to grade
    slope, label, run_m, drop_m = worst
    if slope + _SLOPE_EPS < _MIN_IMPERVIOUS_SLOPE:
        fall_in = drop_m / 0.0254
        run_ft = run_m / 0.3048
        return [_fail("code.R401_3_impervious",
                      f"impervious surface '{label}' only falls {slope * 100:.1f}% away from the "
                      f"foundation ({fall_in:+.1f}\" over {run_ft:.1f}'); R401.3 requires "
                      f"{_MIN_IMPERVIOUS_SLOPE * 100:.0f}% for walks/patios/slabs", (), "R401.3")]
    return [_pass("code.R401_3_impervious",
                  f"impervious surfaces slope at least {_MIN_IMPERVIOUS_SLOPE * 100:.0f}% away "
                  f"from the foundation at all {stations} surface(s) within 10' "
                  f"(shallowest {slope * 100:.1f}% at '{label}')", "R401.3")]
