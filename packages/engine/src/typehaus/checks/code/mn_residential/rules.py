"""MN residential code rules — a few high-value ones (R305/R310/R311.7/R311.6, → 12).

Every rule is tri-state (#32): a rule that cannot evaluate reports UNKNOWN with the reason
and is counted separately, never as a pass.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import SLEEPING_OCCUPANCIES, Occupancy
from typehaus.model.enums import AlarmKind
from typehaus.quantities import ft, inch
from typehaus.model.refs import FollowRoof
from typehaus.resolve.roof_geometry import roof_headroom_areas

_MIN_CEILING = ft(7)
_MIN_SLOPED_CEILING = ft(5)
_MIN_SLOPED_CEILING_FRACTION = 0.5
_MIN_EGRESS_WIDTH = inch(20)
_MIN_EGRESS_HEIGHT = inch(24)
_MAX_EGRESS_SILL = inch(44)
_MIN_EGRESS_AREA_SF = 5.7  # grade-floor 5.0; upper 5.7 (R310.2.1)
_MIN_DOOR_CLEAR = inch(31.75)  # 32" nominal clear (R311.2)

# R401.3 lot drainage: grade must fall >= 6" within the first 10' from the foundation
# (5% for pervious ground; impervious surfaces need only 2%, but those are not separately
# modeled). We evaluate the pervious ground slope from spot elevations.
_GRADING_BAND = ft(10)
_MIN_GROUND_SLOPE = 0.05  # 6" per 10' away from the foundation
_SLOPE_EPS = 1e-3


def _pass(cid: str, msg: str, code: str) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, code_ref=code,
                   result=Result.PASS)


def _fail(cid: str, msg: str, tags: tuple[str, ...], code: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=cid, message=msg, element_tags=tags,
                   code_ref=code, result=Result.FAIL)


def _unknown(cid: str, reason: str, tags: tuple[str, ...], code: str) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {reason}",
                   element_tags=tags, code_ref=code, result=Result.UNKNOWN)


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


@check(Tier.CODE, "code.R310_egress")
def egress_windows(ctx: CheckContext) -> list[Finding]:
    """Every sleeping room needs a compliant emergency escape opening (R310)."""
    from shapely.geometry import Point, Polygon

    out: list[Finding] = []
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room" or room.occupancy not in SLEEPING_OCCUPANCIES:
            continue
        resolved_room = next((item for item in ctx.model.rooms if item.tag == room.tag), None)
        wins = _room_windows(ctx, resolved_room, Point, Polygon)
        best = None
        for op in wins:
            area = op.width_m * op.height_m * 10.7639
            if (op.width_m >= _MIN_EGRESS_WIDTH.meters
                    and op.height_m >= _MIN_EGRESS_HEIGHT.meters
                    and area >= _MIN_EGRESS_AREA_SF
                    and op.sill_m <= _MAX_EGRESS_SILL.meters):
                best = op
                break
        if best is not None:
            out.append(_pass("code.R310_egress",
                             f"{room.tag} has egress window {best.tag}", "R310.1"))
        elif not wins:
            out.append(_fail("code.R310_egress",
                             f"sleeping room {room.tag} has no egress window", (room.tag,),
                             "R310.1"))
        else:
            out.append(_fail("code.R310_egress",
                             f"sleeping room {room.tag} window fails egress dimensions",
                             (room.tag,), "R310.2"))
    return out


def _room_windows(ctx: CheckContext, room, point_type, polygon_type) -> list:
    """Find windows on the room's bounding wall, not any window in the building."""
    if room is None or not room.clear_face:
        return []
    face = polygon_type(room.clear_face)
    # Wall axes normally lie just beyond the clear-face polygon.  The generous 12" band
    # reaches the wall's exterior centerline without accidentally claiming a window in a
    # neighboring room separated by an interior partition.
    boundary_band = face.boundary.buffer(inch(12).meters)
    windows = []
    for opening in ctx.model.openings:
        if opening.is_door or opening.type_ref is None:
            continue
        wall = ctx.model.wall(opening.host_wall)
        if wall is None or wall.storey != room.storey:
            continue
        (sx, sy), (ex, ey) = wall.axis
        axis_length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
        if axis_length <= 1e-9:
            continue
        fraction = opening.center_along_m / axis_length
        center = point_type(sx + (ex - sx) * fraction, sy + (ey - sy) * fraction)
        if boundary_band.covers(center):
            windows.append(opening)
    return windows


@check(Tier.CODE, "code.R311_door_width")
def egress_door_width(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for door in (e for e in ctx.plan.all_elements() if e.element_kind == "Door"):
        dt = next((t for t in ctx.plan.library.door_types if t.tag == door.type_ref), None)
        if dt is None:
            out.append(_unknown("code.R311_door_width", "unknown door type",
                                (door.tag,), "R311.2"))
            continue
        if dt.exterior and dt.width < _MIN_DOOR_CLEAR:
            out.append(_fail("code.R311_door_width",
                             f"egress door {door.tag} width {dt.width.fmt()} < 32\" clear",
                             (door.tag,), "R311.2"))
        else:
            out.append(_pass("code.R311_door_width", f"door {door.tag} width ok", "R311.2"))
    return out


def _room_storey(ctx: CheckContext, room_tag: str):
    for storey in ctx.plan.storeys:
        if any(e.tag == room_tag for e in ctx.plan.storey_elements(storey.tag)):
            return storey
    return None


@check(Tier.CODE, "code.R314_R315_alarms")
def smoke_and_co_alarm_placement(ctx: CheckContext) -> list[Finding]:
    """Require a bedroom alarm and one alarm outside sleeping areas on each sleeping storey."""
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        elements = ctx.plan.storey_elements(storey.tag)
        bedrooms = [element for element in elements
                    if element.element_kind == "Room" and element.occupancy in SLEEPING_OCCUPANCIES]
        if not bedrooms:
            continue
        alarms = [element for element in elements if element.element_kind == "Alarm"]
        for bedroom in bedrooms:
            alarm = next((item for item in alarms if item.room == bedroom.tag
                          and item.kind in (AlarmKind.SMOKE, AlarmKind.COMBO)), None)
            if alarm is None:
                out.append(_fail("code.R314_R315_alarms",
                                 f"bedroom {bedroom.tag} has no smoke alarm", (bedroom.tag,),
                                 "R314.3"))
            else:
                out.append(_pass("code.R314_R315_alarms",
                                 f"{bedroom.tag} has bedroom smoke alarm {alarm.tag}", "R314.3"))
        non_sleeping_rooms = [element for element in elements if element.element_kind == "Room"
                              and element.tag not in {bedroom.tag for bedroom in bedrooms}]
        shared = next((item for item in alarms
                       if item.kind in (AlarmKind.SMOKE, AlarmKind.COMBO)
                       and item.room in {room.tag for room in non_sleeping_rooms}), None)
        if not non_sleeping_rooms:
            out.append(_unknown("code.R314_R315_alarms",
                                f"no modeled area outside sleeping rooms on storey {storey.tag}",
                                tuple(bedroom.tag for bedroom in bedrooms), "R314.3"))
            continue
        if shared is None:
            out.append(_fail("code.R314_R315_alarms",
                             f"storey {storey.tag} has no smoke alarm outside sleeping areas",
                             tuple(bedroom.tag for bedroom in bedrooms), "R314.3"))
        else:
            out.append(_pass("code.R314_R315_alarms",
                             f"{storey.tag} has outside-sleeping smoke alarm {shared.tag}", "R314.3"))
    return out


@check(Tier.CODE, "code.R401_3_grading")
def foundation_grading(ctx: CheckContext) -> list[Finding]:
    """R401.3 lot drainage — grade must fall away from the foundation within 10 feet.

    The primary building footprint is reconstructed from the foundation walls; every spot
    elevation outside it and within 10' is a drainage station, and the shallowest measured
    slope must reach 5% (6" per 10'). Impervious-surface grading (2%) is a documented
    sibling requirement but is not separately modeled, so it is not asserted here.
    """
    from shapely.geometry import LineString, Point
    from shapely.ops import polygonize, unary_union

    site = ctx.plan.project.site
    if site.grade is None:
        return [_unknown("code.R401_3_grading", "no average-grade datum on the site",
                         (), "R401.3")]
    if not site.spot_elevations:
        return [_unknown("code.R401_3_grading",
                         "no spot elevations to measure grade slope", (), "R401.3")]
    segments = [LineString([wall.axis[0], wall.axis[1]])
                for wall in ctx.model.walls if wall.is_foundation]
    if not segments:
        return [_unknown("code.R401_3_grading", "no foundation walls to grade around",
                         (), "R401.3")]
    faces = list(polygonize(unary_union(segments)))
    if not faces:
        return [_unknown("code.R401_3_grading",
                         "could not reconstruct a foundation footprint", (), "R401.3")]
    merged = unary_union(faces)
    polys = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
    footprint = max(polys, key=lambda poly: poly.area)  # primary (largest) enclosure
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
