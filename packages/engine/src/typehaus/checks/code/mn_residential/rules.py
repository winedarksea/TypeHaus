"""MN residential code rules — a few high-value ones (R305/R310/R311.7/R311.6, → 12).

Every rule is tri-state (#32): a rule that cannot evaluate reports UNKNOWN with the reason
and is counted separately, never as a pass.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import SLEEPING_OCCUPANCIES, Occupancy
from typehaus.model.enums import AlarmKind
from typehaus.quantities import ft, inch
from typehaus.model.refs import FollowRoof
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.roof_geometry import roof_headroom_areas, roof_underside_at

_MIN_CEILING = ft(7)
_MIN_SLOPED_CEILING = ft(5)
_MIN_SLOPED_CEILING_FRACTION = 0.5
_MIN_EGRESS_WIDTH = inch(20)
_MIN_EGRESS_HEIGHT = inch(24)
_MAX_EGRESS_SILL = inch(44)
_MIN_EGRESS_AREA_SF = 5.7  # grade-floor 5.0; upper 5.7 (R310.2.1)
_MIN_DOOR_CLEAR = inch(31.75)  # 32" nominal clear (R311.2)
_MAX_STAIR_RISER = inch(7.75)
_MIN_STAIR_GOING = inch(10)
_MIN_STAIR_HEADROOM = ft(6, 8)
_MIN_STAIR_WIDTH = inch(36)  # R311.7.1, above the handrail / between finished walls
_MIN_STAIR_LANDING_DEPTH = inch(36)  # R311.7.6, in the direction of travel
_MIN_HANDRAIL_RISERS = 4  # R311.7.8: required on flights with four or more risers
# Plumb-clearance sampling along the sloped nosing line: plan step between samples, and
# where across the flight each station is probed (both edges + centre — the worst point
# under a raking well header is at one side, not the middle).
_HEADROOM_SAMPLE_STEP_M = 0.05
_HEADROOM_LATERAL_FRACTIONS = (0.0, 0.5, 1.0)
# An obstruction must clear the walking surface by at least this to count as *overhead*
# rather than the surface's own construction.
_HEADROOM_OVERHEAD_EPS_M = 0.001
# Floor/soffit cover shrinks by this before containment: stair edges are authored on the
# well's edges, so boundary samples otherwise flip between in-void and under-deck on
# float summation error. 5 mm decides no real header.
_HEADROOM_PLAN_EPS_M = 0.005

# R401.3 lot drainage: grade must fall away from the foundation within the first 10'. Pervious
# ground needs 5% (6" per 10'), measured from spot elevations (code.R401_3_grading). Impervious
# surfaces (walks, patios, driveways, slabs abutting the house) need only 2%, evaluated from the
# authored ImperviousSurface hardscapes (code.R401_3_impervious).
_GRADING_BAND = ft(10)
_MIN_GROUND_SLOPE = 0.05  # 6" per 10' away from the foundation (pervious ground)
_MIN_IMPERVIOUS_SLOPE = 0.02  # 2% away from the foundation (walks/patios/slabs)
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


@check(Tier.CODE, "code.R311_7_stair_geometry")
def stair_geometry(ctx: CheckContext) -> list[Finding]:
    """Verify the built walking sequence reaches the next finished floor with code geometry.

    The resolver owns the exact opening and roof geometry.  This check intentionally measures
    its output rather than re-solving it from authored inputs, catching a dropped/level tread
    even when the design rise and riser count still look mathematically consistent.
    """
    if not ctx.model.stairs:
        return [_unknown("code.R311_7_stair_geometry", "no resolved stairs", (), "R311.7")]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        source = ctx.plan.storey(stair.storey)
        target = ctx.plan.storey(stair.to_storey)
        if source is None or target is None:
            out.append(_unknown("code.R311_7_stair_geometry", "unresolved stair storey",
                                (stair.tag,), "R311.7"))
            continue
        walking = sorted(member.z1_m for member in stair.members
                         if member.category in {"tread", "winder", "landing"})
        arrival = target.elevation.meters
        expected = [source.elevation.meters + stair.riser_height_m * step
                    for step in range(1, stair.riser_count)]
        # Headroom is NOT this check's business: it is a plumb measurement against the
        # overhead structure, made by code.R311_7_2_stair_headroom. Reporting the arrival
        # storey's nominal ceiling height here — as this check once did — is not headroom.
        valid = (
            stair.riser_height_m <= _MAX_STAIR_RISER.meters + 1e-9
            and stair.going_depth_m >= _MIN_STAIR_GOING.meters - 1e-9
            and len(walking) == len(expected)
            and all(abs(actual - wanted) <= 1e-6 for actual, wanted in zip(walking, expected))
            and abs(source.elevation.meters + stair.riser_count * stair.riser_height_m - arrival) <= 1e-6
        )
        if valid:
            out.append(_pass("code.R311_7_stair_geometry",
                             f"{stair.tag} reaches {stair.to_storey} with "
                             f"{stair.riser_count} built risers at "
                             f"{stair.riser_height_m / .0254:.2f}\" on a "
                             f"{stair.going_depth_m / .0254:.1f}\" going", "R311.7"))
        else:
            out.append(_fail("code.R311_7_stair_geometry",
                             f"{stair.tag} fails built rise or going",
                             (stair.tag,), "R311.7"))
    return out


def _flight_stations(stair) -> dict[str, list[tuple[tuple[float, float],
                                                    tuple[float, float], float]]]:
    """Per flight, the nosing stations of the sloped walking line, in climb order.

    A station is ``(a, b, z)``: the riser-face segment (a winder's fan line) at its
    tread's finished walking elevation. R311.7.2 measures plumb from the sloped line
    adjoining the nosings, so the line to sample is the interpolation between
    consecutive stations of one flight — never across flights, whose runs occupy
    different lanes.
    """
    flights: dict[str, list] = {}
    for member in stair.members:
        if member.category == "winder":
            flights.setdefault("winder", []).append((member.p0, member.p1, member.z1_m))
        elif member.category == "tread" and member.riser_line is not None:
            a, b = member.riser_line
            key = member.child_key.rsplit("-", 1)[0]
            flights.setdefault(key, []).append((a, b, member.z1_m))
        elif member.category == "landing":
            # A landing's walking surface: its two end edges at the deck face, swept from
            # the member axis by the profile's true half-width.
            (x0, y0), (x1, y1) = member.p0, member.p1
            run = math.hypot(x1 - x0, y1 - y0)
            if run < 1e-9:
                continue
            ux, uy = (x1 - x0) / run, (y1 - y0) / run
            half = cross_section(member.profile).width_m / 2.0
            px, py = -uy * half, ux * half
            flights[member.child_key] = [
                ((x0 - px, y0 - py), (x0 + px, y0 + py), member.z1_m),
                ((x1 - px, y1 - py), (x1 + px, y1 + py), member.z1_m),
            ]
    for key, stations in flights.items():
        stations.sort(key=lambda station: station[2])
        # Extend a straight flight one station past its top riser: the sloped line runs
        # to the edge it arrives at (the landing zone or the arrival deck), one going
        # beyond and one riser above the last nosing. Only tread flights extend — a
        # landing's stations already are its edges, and a winder fan's continuation is
        # the straight flight itself (its first riser line lies on the turn's departing
        # edge).
        if key.startswith("tread") and len(stations) >= 2:
            (a0, b0, z0), (a1, b1, z1) = stations[-2], stations[-1]
            stations.append(((2 * a1[0] - a0[0], 2 * a1[1] - a0[1]),
                             (2 * b1[0] - b0[0], 2 * b1[1] - b0[1]), 2 * z1 - z0))
    return flights


def _walk_samples(stations):
    """Points ``(x, y, z)`` densely covering the sloped walking line between stations."""
    for (a0, b0, z0), (a1, b1, z1) in zip(stations, stations[1:]):
        span = max(math.hypot(a1[0] - a0[0], a1[1] - a0[1]),
                   math.hypot(b1[0] - b0[0], b1[1] - b0[1]))
        steps = max(1, math.ceil(span / _HEADROOM_SAMPLE_STEP_M))
        for step in range(steps + 1):
            t = step / steps
            ax, ay = a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t
            bx, by = b0[0] + (b1[0] - b0[0]) * t, b0[1] + (b1[1] - b0[1]) * t
            z = z0 + (z1 - z0) * t
            for u in _HEADROOM_LATERAL_FRACTIONS:
                yield (ax + (bx - ax) * u, ay + (by - ay) * u, z)


@check(Tier.CODE, "code.R311_7_2_stair_headroom")
def stair_headroom(ctx: CheckContext) -> list[Finding]:
    """Measure the plumb clearance from the sloped nosing line to the structure above.

    This is the measurement ``code.R311_7_stair_geometry`` used to *claim*: it reported
    the arrival storey's nominal ceiling height, which is not headroom over any tread.
    Here every flight's nosing line is sampled and probed plumb against the resolved
    overhead structure: floor decks (outside their stair-well voids) down to their
    deepest framing, roof planes at their structural underside, and soffit faces.
    Structure only — ceiling finishes, freestanding beams and ducts are not modeled
    against the walk — and never PASS by absence: a stair with no resolved structure
    overhead reports UNKNOWN.
    """
    cid, code = "code.R311_7_2_stair_headroom", "R311.7.2"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    floors = []
    for floor in ctx.model.floors:
        if not floor.deck_outline:
            continue
        underside = min([member.z0_m for member in floor.members] + [floor.deck_z0_m])
        cover = Polygon(floor.deck_outline,
                        holes=[list(void) for void in floor.deck_voids]
                        ).buffer(-_HEADROOM_PLAN_EPS_M)
        if not cover.is_empty:
            floors.append((cover, underside, floor.tag))
    roofs = [(Polygon(roof.footprint), roof) for roof in ctx.model.roofs if roof.footprint]
    soffits = []
    for soffit in ctx.model.soffits:
        if not soffit.outline:
            continue
        cover = Polygon(soffit.outline).buffer(-_HEADROOM_PLAN_EPS_M)
        if not cover.is_empty:
            soffits.append((cover, soffit.z0_m, soffit.tag))
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        worst: tuple[float, tuple[float, float], str] | None = None
        for stations in _flight_stations(stair).values():
            for x, y, z in _walk_samples(stations):
                point = Point(x, y)
                lowest: tuple[float, str] | None = None
                for polygon, underside, tag in floors:
                    if underside > z + _HEADROOM_OVERHEAD_EPS_M and polygon.contains(point):
                        if lowest is None or underside < lowest[0]:
                            lowest = (underside, tag)
                for polygon, roof in roofs:
                    if polygon.contains(point):
                        underside = roof_underside_at(ctx.model, roof, (x, y))
                        if underside > z + _HEADROOM_OVERHEAD_EPS_M and (
                                lowest is None or underside < lowest[0]):
                            lowest = (underside, roof.tag)
                for polygon, underside, tag in soffits:
                    if underside > z + _HEADROOM_OVERHEAD_EPS_M and polygon.contains(point):
                        if lowest is None or underside < lowest[0]:
                            lowest = (underside, tag)
                if lowest is None:
                    continue
                clearance = lowest[0] - z
                if worst is None or clearance < worst[0]:
                    worst = (clearance, (x, y), lowest[1])
        if worst is None:
            out.append(_unknown(cid, f"{stair.tag}: no resolved structure overhead of "
                                "the walking line (floors, roofs, soffits)",
                                (stair.tag,), code))
            continue
        clearance, (x, y), tag = worst
        where = (f"{clearance / .3048:.2f}' plumb under {tag} at "
                 f"({x / .3048:.1f}', {y / .3048:.1f}')")
        if clearance >= _MIN_STAIR_HEADROOM.meters - 1e-9:
            out.append(_pass(cid, f"{stair.tag} headroom {where} (>= 6'-8\"; structure "
                             "only, finishes unmodeled)", code))
        else:
            out.append(_fail(cid, f"{stair.tag} headroom {where} < 6'-8\"",
                             (stair.tag, tag), code))
    return out


@check(Tier.CODE, "code.R311_7_1_stair_width")
def stair_width(ctx: CheckContext) -> list[Finding]:
    """Built flight width from the tread boards themselves (R311.7.1: 36" minimum).

    Handrails are unmodeled (see code.R311_7_8_handrail), so this is the width between
    finished walls — the 36" number — not the 31.5"/27" clear-past-handrail rules, which
    cannot be measured until a handrail exists to project into the flight. The winder
    turn is excluded: its width is the turn square's by construction, and its own code
    minimums are the narrow-end and walk-line checks.
    """
    cid, code = "code.R311_7_1_stair_width", "R311.7.1"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        widths = [member.length_m for member in stair.members
                  if member.category == "tread"]
        if not widths:
            out.append(_unknown(cid, f"{stair.tag} has no tread boards to measure",
                                (stair.tag,), code))
            continue
        width = min(widths)
        if width >= _MIN_STAIR_WIDTH.meters - 1e-9:
            out.append(_pass(cid, f"{stair.tag} flight width {width / .0254:.2f}\" "
                             ">= 36\" (handrail projection unmodeled)", code))
        else:
            out.append(_fail(cid, f"{stair.tag} flight width {width / .0254:.2f}\" "
                             "< 36\"", (stair.tag,), code))
    return out


@check(Tier.CODE, "code.R311_7_6_landing_depth")
def stair_landing_depth(ctx: CheckContext) -> list[Finding]:
    """Built landing platforms measured off the members (R311.7.6).

    Two numbers, on two axes: 36" in the direction of travel (the deck member's run),
    and never narrower than the stairway served (its swept width against the widest
    tread). The resolver *floors* authored depths at 36", but this measures what was
    built — the doctrine that caught the stretched first risers is measure-the-output,
    not trust-the-generator. Stairs without landing members (a straight or winder run
    between floors) have nothing to measure: the floors they arrive at serve as the
    R311.7.6 landing.
    """
    cid, code = "code.R311_7_6_landing_depth", "R311.7.6"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        stair_width_m = max([member.length_m for member in stair.members
                             if member.category == "tread"], default=0.0)
        for member in stair.members:
            if member.category != "landing":
                continue
            depth = member.length_m
            width = cross_section(member.profile).width_m
            if depth < _MIN_STAIR_LANDING_DEPTH.meters - 1e-9:
                out.append(_fail(cid, f"{stair.tag} {member.child_key} runs "
                                 f"{depth / .0254:.2f}\" in the direction of travel "
                                 "< 36\"", (stair.tag,), code))
            elif width < stair_width_m - 1e-9:
                out.append(_fail(cid, f"{stair.tag} {member.child_key} is "
                                 f"{width / .0254:.2f}\" wide, narrower than the "
                                 f"{stair_width_m / .0254:.2f}\" stairway it serves",
                                 (stair.tag,), code))
            else:
                out.append(_pass(cid, f"{stair.tag} {member.child_key} "
                                 f"{depth / .0254:.2f}\" deep x {width / .0254:.2f}\" "
                                 "wide", code))
    return out


@check(Tier.CODE, "code.R311_7_8_handrail")
def stair_handrail(ctx: CheckContext) -> list[Finding]:
    """R311.7.8: a flight with four or more risers needs a handrail 34"-38" above the
    nosings, continuous and graspable.

    Nothing in the model *is* a handrail: ``Railing`` elements are guards — plan-outline
    solids with a height, no graspability, continuity or role semantics — so presence
    cannot be measured yet. This reports the gap as UNKNOWN rather than staying silent;
    the permit checklist claimed headroom it did not measure once already. Authoring a
    handrail role on ``Railing`` is the follow-up recorded in plans/TODO.md.
    """
    cid, code = "code.R311_7_8_handrail", "R311.7.8"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        if stair.riser_count < _MIN_HANDRAIL_RISERS:
            out.append(_pass(cid, f"{stair.tag} has {stair.riser_count} risers — no "
                             "handrail required", code))
            continue
        out.append(_unknown(cid, f"{stair.tag} ({stair.riser_count} risers) requires a "
                            "handrail; none is modeled — Railing carries no handrail "
                            "role/graspability semantics", (stair.tag,), code))
    return out


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


# How close a habitable room has to be to a garage before R315.2.2's garage-adjacency CO rule
# is in play. A garage sharing a wall is the obvious case; this house's is *freestanding*, 4'
# north, joined door-to-door by an enclosed breezeway — which is the same exposure path a
# common wall gives you, so the rule has to reach it. Beyond this band the garage is genuinely
# detached and the rule reports UNKNOWN rather than passing on a technicality.
_GARAGE_ADJACENCY = ft(12)


@check(Tier.CODE, "code.R315_garage_alarms")
def garage_heat_and_co_alarms(ctx: CheckContext) -> list[Finding]:
    """A garage wants a heat detector, and the dwelling beside it wants CO coverage.

    Neither half was covered. ``code.R314_R315_alarms`` filters on (SMOKE, COMBO) and only
    looks at storeys with bedrooms on them, so the garage storey was invisible to it.

    A garage gets a *heat* detector rather than a smoke alarm: exhaust, dust and a space that
    runs to outdoor temperature would nuisance-trip a smoke head, which is why the code asks
    for CO coverage on the dwelling side instead of a smoke alarm inside the garage.
    """
    from shapely.geometry import Polygon

    cid = "code.R315_garage_alarms"
    out: list[Finding] = []
    alarms = [element for element in ctx.plan.all_elements()
              if element.element_kind == "Alarm"]
    garages = [room for room in ctx.model.rooms if room.occupancy == Occupancy.GARAGE.value]
    if not garages:
        return [_unknown(cid, "no garage modelled", (), "R315.2.2")]

    for garage in garages:
        detector = next((item for item in alarms
                         if item.room == garage.tag and item.kind is AlarmKind.HEAT), None)
        if detector is None:
            out.append(_fail(cid, f"garage {garage.tag} has no heat detector", (garage.tag,),
                             "R315.2.2"))
        else:
            out.append(_pass(cid, f"{garage.tag} has heat detector {detector.tag}",
                             "R315.2.2"))

    # CO coverage on the dwelling side. Adjacency is measured between the resolved room
    # faces, so a breezeway-connected garage counts the same as a shared-wall one.
    garage_tags = {room.tag for room in garages}
    band = [Polygon(room.clear_face).buffer(_GARAGE_ADJACENCY.meters)
            for room in garages if len(room.clear_face) >= 3]
    neighbours = [room for room in ctx.model.rooms
                  if room.tag not in garage_tags and len(room.clear_face) >= 3
                  and any(zone.intersects(Polygon(room.clear_face)) for zone in band)]
    if not neighbours:
        out.append(_unknown(cid, "no habitable room within "
                                 f"{_GARAGE_ADJACENCY.feet:g}' of a garage — detached, so the "
                                 "garage-adjacency CO rule does not apply",
                            tuple(sorted(garage_tags)), "R315.2.2"))
        return out
    covered = [item for item in alarms
               if item.kind in (AlarmKind.CO, AlarmKind.COMBO)
               and item.room in {room.tag for room in neighbours}]
    if not covered:
        out.append(_fail(cid, "no CO alarm in any room adjacent to the garage",
                         tuple(sorted(room.tag for room in neighbours)), "R315.2.2"))
    else:
        out.append(_pass(cid, f"{len(covered)} CO alarm(s) cover the rooms adjacent to the "
                              f"garage ({covered[0].tag})", "R315.2.2"))
    return out


@check(Tier.CODE, "code.R401_3_grading")
def foundation_grading(ctx: CheckContext) -> list[Finding]:
    """R401.3 lot drainage — grade must fall away from the foundation within 10 feet.

    The primary building footprint is reconstructed from the foundation walls; every spot
    elevation outside it and within 10' is a drainage station, and the shallowest measured
    slope must reach 5% (6" per 10'). Impervious-surface grading (2%) is the sibling
    requirement asserted separately by ``code.R401_3_impervious``.
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


def _foundation_footprint(ctx: CheckContext):
    """Largest foundation-wall enclosure (the primary building), or None if unavailable."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union

    segments = [LineString([wall.axis[0], wall.axis[1]])
                for wall in ctx.model.walls if wall.is_foundation]
    if not segments:
        return None
    faces = list(polygonize(unary_union(segments)))
    if not faces:
        return None
    merged = unary_union(faces)
    polys = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
    return max(polys, key=lambda poly: poly.area)


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


# --- R312.1 guards at stair-well openings ----------------------------------------------
_GUARD_MIN_HEIGHT = inch(36)  # R312.1.2, at open sides of walking surfaces
_GUARD_GAP_TOL_M = 0.05       # uncovered slivers under ~2" are corner laps, not open sides
_GUARD_PLANE_TOL_M = 0.15     # a railing path within 6" of the well edge guards that edge
_GUARD_WALL_FACE_TOL_M = 0.05  # the void is cut to the finished well, i.e. the wall face
_GUARD_BASE_TOL_M = 0.15      # railing base matched to the walking surface (deck_guard's tol)
_GUARD_THROAT_Z_WINDOW_M = 0.5  # only treads arriving at this surface open a throat
_GUARD_THROAT_REACH_M = 0.45   # stretch the arrival quad ~a tread to the finished edge


def _edge_cover_intervals(edge_across: float, along0: float, along1: float, across: int,
                          along: int, walls, railings, stair_quads):
    """(covered, short_guards): interval cover along one well edge, and any railing that
    runs the edge but is too short to be a guard."""
    from shapely.geometry import LineString

    from typehaus.resolve.floors import _wall_footprint_span

    covered: list[tuple[float, float]] = []
    short: list = []
    used: set[str] = set()
    for wall in walls:
        span_across = _wall_footprint_span(wall, across)
        span_along = _wall_footprint_span(wall, along)
        if span_across is None or span_along is None:
            continue
        if not (span_across[0] - _GUARD_WALL_FACE_TOL_M <= edge_across
                <= span_across[1] + _GUARD_WALL_FACE_TOL_M):
            continue
        covered.append(span_along)
    for railing, tall_enough in railings:
        for p, q in zip(railing.path, railing.path[1:]):
            pa, qa = p.xy_m, q.xy_m
            if (abs(pa[across] - edge_across) > _GUARD_PLANE_TOL_M
                    or abs(qa[across] - edge_across) > _GUARD_PLANE_TOL_M):
                continue
            lo, hi = sorted((pa[along], qa[along]))
            if tall_enough:
                covered.append((lo, hi))
                used.add(railing.tag)
            else:
                short.append(railing)
    edge_line = LineString([(edge_across, along0), (edge_across, along1)]
                           if across == 0 else
                           [(along0, edge_across), (along1, edge_across)])
    for quad in stair_quads:
        inter = edge_line.intersection(quad)
        if inter.is_empty or getattr(inter, "length", 0.0) <= 1e-6:
            continue
        values = [pt[along] for geom in getattr(inter, "geoms", [inter])
                  for pt in geom.coords]
        covered.append((min(values), max(values)))
    return covered, short, used


@check(Tier.CODE, "code.R312_1_guard")
def stairwell_guard(ctx: CheckContext) -> list[Finding]:
    """R312.1 — every open side of a stair well's walking surface carries a guard.

    Each STAIR floor opening's four edges are classified against the resolved geometry:
    an edge is covered where a wall's plan footprint stands at it full guard height,
    where an authored Railing runs along it at >= 36" with its base on the walking
    surface, or where the stair itself enters (the throat — that side is the stairway,
    R311's problem, not an open side). Whatever length remains is an open side with no
    guard: a FAIL naming the edge and the uncovered interval. A railing that runs an
    edge under 36" fails on height rather than counting as coverage, and a house with
    no stair wells reports UNKNOWN — never PASS by absence.
    """
    from shapely.geometry import Polygon as _ShapelyPolygon

    from typehaus.model.floors import FloorOpening, FloorOpeningPurpose, FloorSystem
    from typehaus.model.structure import Railing
    from typehaus.resolve.floors import (_rectangular_opening_box, _subtract_interval,
                                         _wall_footprint_span)

    cid, code = "code.R312_1_guard", "R312.1"
    openings_by_tag = {e.tag: e for e in ctx.plan.all_elements()
                       if isinstance(e, FloorOpening)}
    hosts = [(fs, opening_tag) for fs in ctx.plan.all_elements()
             if isinstance(fs, FloorSystem) for opening_tag in fs.openings]
    wells = [(fs, openings_by_tag[tag]) for fs, tag in hosts
             if tag in openings_by_tag
             and openings_by_tag[tag].purpose is FloorOpeningPurpose.STAIR]
    if not wells:
        return [_unknown(cid, "no stair floor openings in the plan", (), code)]

    all_railings = [e for e in ctx.plan.all_elements() if isinstance(e, Railing)]
    out: list[Finding] = []
    for fs, opening in wells:
        floor = next((f for f in ctx.model.floors if f.tag == fs.tag), None)
        if floor is None or not floor.deck_outline:
            out.append(_unknown(cid, f"{opening.tag}: host floor {fs.tag} resolved no "
                                "deck to measure a walking surface from",
                                (opening.tag, fs.tag), code))
            continue
        box = _rectangular_opening_box(opening)
        if box is None:
            out.append(_unknown(cid, f"{opening.tag}: outline is not an axis-aligned "
                                "rectangle", (opening.tag,), code))
            continue
        minx, maxx, miny, maxy = box
        surface = floor.deck_z1_m
        walls = [w for w in ctx.model.walls
                 if w.storey == floor.storey
                 and w.z0_m <= surface + 0.1
                 and w.z1_m >= surface + _GUARD_MIN_HEIGHT.meters - 0.02]
        railings = [(r, r.height.meters + 1e-9 >= _GUARD_MIN_HEIGHT.meters)
                    for r in all_railings
                    if abs(r.base_elevation.meters - surface) < _GUARD_BASE_TOL_M]
        stair_quads = []
        for stair in ctx.model.stairs:
            for stations in _flight_stations(stair).values():
                pairs = list(zip(stations, stations[1:]))
                for index, ((a0, b0, z0), (a1, b1, z1)) in enumerate(pairs):
                    if max(z0, z1) < surface - _GUARD_THROAT_Z_WINDOW_M:
                        continue
                    if index == len(pairs) - 1:
                        # The nosing line's extrapolated arrival station lands a tread
                        # short of the finished well edge (the void is cut to the
                        # trimmer, not to the top nosing); stretch the final quad along
                        # the travel direction so the throat actually reaches the edge
                        # it enters through. Along travel only — never sideways, which
                        # would eat into genuinely open sides beside the flight.
                        run = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
                        if run > 1e-9:
                            ux, uy = (a1[0] - a0[0]) / run, (a1[1] - a0[1]) / run
                            reach = _GUARD_THROAT_REACH_M
                            a1 = (a1[0] + ux * reach, a1[1] + uy * reach)
                            b1 = (b1[0] + ux * reach, b1[1] + uy * reach)
                    quad = _ShapelyPolygon([a0, b0, b1, a1])
                    if quad.is_valid and quad.area > 1e-6:
                        stair_quads.append(quad)

        edges = (("west", 0, minx, miny, maxy), ("east", 0, maxx, miny, maxy),
                 ("south", 1, miny, minx, maxx), ("north", 1, maxy, minx, maxx))
        gaps: list[str] = []
        short_guards: list = []
        guarding_tags: set[str] = set()
        for name, across, edge_across, along0, along1 in edges:
            along = 1 - across
            covered, short, used = _edge_cover_intervals(
                edge_across, along0, along1, across, along, walls, railings, stair_quads)
            short_guards.extend(short)
            guarding_tags |= used
            remaining = [(along0, along1)]
            for lo, hi in covered:
                remaining = _subtract_interval(remaining, lo, hi)
            for lo, hi in remaining:
                if hi - lo > _GUARD_GAP_TOL_M:
                    gaps.append(f"{name} edge {lo / .3048:.2f}'..{hi / .3048:.2f}' "
                                f"({(hi - lo) / .3048:.2f}')")
        if gaps:
            out.append(_fail(cid, f"{opening.tag}: open side(s) with no guard, wall or "
                             f"stair entry — {'; '.join(gaps)}",
                             (opening.tag, fs.tag), code))
        elif short_guards:
            names = sorted({r.tag for r in short_guards})
            worst = min(r.height.inches for r in short_guards)
            out.append(_fail(cid, f"{opening.tag}: guard(s) {', '.join(names)} run the "
                             f"well edge at {worst:.0f}\", under the 36\" R312.1.2 "
                             "minimum", (opening.tag, *names), code))
        else:
            out.append(_pass(cid, f"{opening.tag}: every open side is guarded "
                             f"({', '.join(sorted(guarding_tags)) or 'walls'} and the "
                             "stair throat close the well)", code))
    return out
