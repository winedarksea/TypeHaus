"""Minnesota UPC 707.4 sanitary cleanout locations and 707.9 access."""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import Point, Polygon

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_queries import pipe_elevations_at
from typehaus.resolve.mep_tie_ins import drain_tie_ins

_CODE_LOCATION = "MN Plumbing Code (ch. 4714) 707.4"
_CODE_CLEARANCE = "2020 MN Plumbing Code (2018 UPC) 707.9"
_FT_M = 0.3048
_SHORT_LINE_M = 5 * _FT_M
_SPACING_M = 100 * _FT_M
_TURN_LIMIT_DEG = 135.0
_LOCATION_TOLERANCE_M = 1 * _FT_M
_TERMINAL_TOLERANCE_M = 4 * _FT_M
# A one-fifth bend is within 72 degrees of vertical, or at least tan(18) rise/run.
_MIN_VERTICAL_SLOPE = math.tan(math.radians(18))


@dataclass(frozen=True)
class CleanoutRequirement:
    pipe_ref: str
    point: tuple[float, float]
    reason: str
    z_m: float | None = None


def _horizontal_segments(run):
    if run.z_m is None:
        return []
    segments = []
    for index, (a, b) in enumerate(zip(run.path, run.path[1:], strict=False)):
        plan = math.dist(a, b)
        rise = abs(run.z_m[index + 1] - run.z_m[index])
        if plan > 1e-6 and rise / plan < _MIN_VERTICAL_SLOPE:
            segments.append((index, a, b, plan))
    return segments


def _segment_lengths(run):
    return [math.hypot(math.dist(a, b), run.z_m[i + 1] - run.z_m[i])
            for i, (a, b) in enumerate(zip(run.path, run.path[1:], strict=False))]


def _tie_station(parent, child):
    """Developed distance to a child's arrival on its downstream parent."""
    point = child.path[-1]
    candidates = []
    walked = 0.0
    lengths = _segment_lengths(parent)
    for index, (a, b) in enumerate(zip(parent.path, parent.path[1:], strict=False)):
        segment = lengths[index]
        vx, vy = b[0] - a[0], b[1] - a[1]
        plan_sq = vx * vx + vy * vy
        if plan_sq > 1e-12:
            fraction = max(0.0, min(1.0, ((point[0] - a[0]) * vx
                                              + (point[1] - a[1]) * vy) / plan_sq))
            projected = (a[0] + vx * fraction, a[1] + vy * fraction)
            if math.dist(point, projected) < 1e-5:
                z = parent.z_m[index] + (parent.z_m[index + 1] - parent.z_m[index]) * fraction
                candidates.append((abs(z - child.z_m[-1]), walked + segment * fraction))
        walked += segment
    return min(candidates)[1] if candidates else None


def _point_at_station(run, station):
    walked = 0.0
    for index, segment in enumerate(_segment_lengths(run)):
        if walked + segment >= station - 1e-7 and segment > 1e-9:
            fraction = max(0.0, min(1.0, (station - walked) / segment))
            a, b = run.path[index:index + 2]
            return ((a[0] + (b[0] - a[0]) * fraction,
                     a[1] + (b[1] - a[1]) * fraction),
                    run.z_m[index] + (run.z_m[index + 1] - run.z_m[index]) * fraction)
        walked += segment
    return run.path[-1], run.z_m[-1]


def _distance_to_axis(point, axis):
    a, b = axis
    dx, dy = b[0] - a[0], b[1] - a[1]
    span_sq = dx * dx + dy * dy
    if span_sq <= 1e-12:
        return math.dist(point, a)
    fraction = max(0.0, min(1.0, ((point[0] - a[0]) * dx
                                      + (point[1] - a[1]) * dy) / span_sq))
    return math.dist(point, (a[0] + fraction * dx, a[1] + fraction * dy))


def _continuous_parts(start, first_segment, drains, ties):
    """Run intervals from a horizontal terminal through its downstream tie-ins."""
    parts = []
    current = start
    start_station = sum(_segment_lengths(start)[:first_segment])
    seen = set()
    while current.tag not in seen:
        seen.add(current.tag)
        total = sum(_segment_lengths(current))
        parts.append((current, start_station, total))
        parent = drains.get(ties.get(current.tag))
        if parent is None:
            break
        tie_station = _tie_station(parent, current)
        if tie_station is None:
            break
        current, start_station = parent, tie_station
    return parts


def _spacing_requirements(parts):
    requirements = []
    distance = 0.0
    next_station = _SPACING_M
    for run, start_at, end_at in parts:
        span = end_at - start_at
        while distance + span > next_station + 1e-6:
            point, z = _point_at_station(run, start_at + next_station - distance)
            requirements.append(CleanoutRequirement(run.tag, point, "100 ft spacing", z))
            next_station += _SPACING_M
        distance += span
    return requirements


def _turn_requirements(parts):
    requirements = []
    previous = None
    cumulative = 0.0
    for run, start_at, end_at in parts:
        walked = 0.0
        for index, segment in enumerate(_segment_lengths(run)):
            lower = max(start_at, walked)
            upper = min(end_at, walked + segment)
            if upper - lower > 1e-8 and segment > 1e-9:
                a, b = run.path[index:index + 2]
                first = (lower - walked) / segment
                last = (upper - walked) / segment
                dx, dy = (b[0] - a[0]) * (last - first), (b[1] - a[1]) * (last - first)
                horizontal_length = math.hypot(dx, dy)
                dz = (run.z_m[index + 1] - run.z_m[index]) * (last - first)
                if horizontal_length < 1e-6 or abs(dz) / horizontal_length >= _MIN_VERTICAL_SLOPE:
                    previous, cumulative = None, 0.0
                else:
                    vector = (dx / horizontal_length, dy / horizontal_length)
                    if previous is not None:
                        dot = max(-1.0, min(1.0, previous[0] * vector[0]
                                             + previous[1] * vector[1]))
                        cumulative += math.degrees(math.acos(dot))
                        if cumulative > _TURN_LIMIT_DEG + 1e-6:
                            point = (a[0] + (b[0] - a[0]) * first,
                                     a[1] + (b[1] - a[1]) * first)
                            z = (run.z_m[index]
                                 + (run.z_m[index + 1] - run.z_m[index]) * first)
                            requirements.append(CleanoutRequirement(
                                run.tag, point, "cumulative turns >135 deg", z))
                            cumulative = 0.0
                    previous = vector
            walked += segment
    return requirements


def required_cleanout_locations(model) -> list[CleanoutRequirement]:
    """Requirements on connected fixture waste, after Minnesota's four exceptions.

    Runs above the lowest floor are exempt except the building drain, its direct
    horizontal branches, and kitchen sink lines. Unconnected indirect waste and relief
    discharges are excluded by the authored ``sanitary`` flag.
    """
    drains = {r.tag: r for r in model.pipe_runs if r.system == "drain" and r.sanitary}
    if not drains:
        return []
    ties = drain_tie_ins(list(drains.values()))
    building = next((r for r in drains.values() if r.tag.endswith("MAIN-DRAIN")), None)
    lowest_floor = min(s.elevation.meters for s in model.plan.storeys)
    requirements = []
    for run in drains.values():
        segments = _horizontal_segments(run)
        if not segments:
            continue  # exception 2: vertical or one-fifth-bend piping
        horizontal_length = sum(segment[3] for segment in segments)
        sink = any("SINK" in tag for tag in run.serves)
        kitchen_sink = any("KITCH" in tag and "SINK" in tag for tag in run.serves)
        eligible = (run is building or (building is not None and ties.get(run.tag) == building.tag)
                    or kitchen_sink or min(run.z_m or ()) <= lowest_floor + M_PER_IN)
        if not eligible:
            continue  # exception 3: piping above the lowest floor
        if horizontal_length < _SHORT_LINE_M and not sink:
            continue  # exception 1: short non-sink lines
        requirements.append(CleanoutRequirement(
            run.tag, segments[0][1], "upper terminal", run.z_m[segments[0][0]]))

        parts = _continuous_parts(run, segments[0][0], drains, ties)
        requirements.extend(_spacing_requirements(parts))
        requirements.extend(_turn_requirements(parts))
    return list(dict.fromkeys(requirements))


@check(Tier.CODE, "mep.drain_cleanouts")
def drain_cleanouts(ctx: CheckContext):
    requirements = required_cleanout_locations(ctx.model)
    cleanouts = ctx.model.drain_cleanouts
    if not requirements and not cleanouts:
        return [not_applicable("mep.drain_cleanouts", "no sanitary horizontal drains",
                               code=_CODE_LOCATION)]
    findings = []
    building = next((r for r in ctx.model.pipe_runs if r.tag.endswith("MAIN-DRAIN")
                     and r.system == "drain" and r.sanitary), None)
    for requirement in requirements:
        # The required fitting may move a few feet down a buried branch when the fixture
        # occupies the terminal's floor footprint; its cap still has to be exposed.
        tolerance = (_TERMINAL_TOLERANCE_M if requirement.reason == "upper terminal"
                     else _LOCATION_TOLERANCE_M)
        direct = [c for c in cleanouts if c.pipe_ref == requirement.pipe_ref
                  and math.dist(c.position, requirement.point) <= tolerance + 1e-6
                  and (requirement.z_m is None
                       or abs(c.fitting_z_m - requirement.z_m) <= 6 * M_PER_IN)]
        substitute = [c for c in cleanouts if building is not None
                      and requirement.pipe_ref == building.tag
                      and requirement.reason == "upper terminal"
                      and c.pipe_ref == building.tag and c.direction == "two_way"
                      and c.access == "grade"
                      and math.dist(c.position, building.path[-1])
                      <= _LOCATION_TOLERANCE_M + 1e-6]
        matched = direct or substitute
        if matched:
            findings.append(passed("mep.drain_cleanouts",
                                   f"{requirement.pipe_ref} {requirement.reason}: "
                                   f"{matched[0].tag}",
                                   (requirement.pipe_ref, matched[0].tag),
                                   code=_CODE_LOCATION))
        else:
            findings.append(failed("mep.drain_cleanouts",
                                   f"{requirement.pipe_ref} missing {requirement.reason} "
                                   f"cleanout at {requirement.point}",
                                   (requirement.pipe_ref,), code=_CODE_LOCATION))
    for cleanout in cleanouts:
        host = next((r for r in ctx.model.pipe_runs if r.tag == cleanout.pipe_ref), None)
        if (host is None or host.system != "drain" or not host.sanitary
            or not any(abs(z - cleanout.fitting_z_m) <= host.diameter_m / 2
                       for z in pipe_elevations_at(host, cleanout.position))):
            findings.append(failed("mep.drain_cleanouts",
                                   f"{cleanout.tag} fitting is not connected to its sanitary "
                                   f"host {cleanout.pipe_ref}", (cleanout.tag,),
                                   code=_CODE_LOCATION))
        if hasattr(ctx.model, "solids"):
            parts = {s.category for s in ctx.model.solids if s.tag == cleanout.tag
                     or s.tag in {cleanout.tag + "-EXT", cleanout.tag + "-CAP"}}
            if parts != {"cleanout_fitting", "cleanout_extension", "cleanout_cap"}:
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} lacks fitting, extension, or cap geometry",
                                       (cleanout.tag,), code=_CODE_LOCATION))
        if cleanout.access == "grade":
            site_grade = ctx.model.plan.project.site.grade
            if (site_grade is None
                or abs(cleanout.cap_z_m - site_grade.meters) > M_PER_IN):
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} cap does not terminate at grade",
                                       (cleanout.tag,), code=_CODE_LOCATION))
        elif cleanout.access == "floor":
            floor = next((s for s in ctx.model.plan.storeys
                          if getattr(s, "tag", cleanout.storey) == cleanout.storey), None)
            if floor is not None and abs(cleanout.cap_z_m - floor.elevation.meters) > M_PER_IN:
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} cap is not flush with its floor",
                                       (cleanout.tag,), code=_CODE_LOCATION))
            for item in getattr(ctx.model, "canvas_objects", ()):
                if (item.storey != cleanout.storey
                    or item.domain not in {"plumbing", "appliance", "furniture"}
                    or not item.footprint or item.body_z1_m < cleanout.cap_z_m):
                    continue
                if Polygon(item.footprint).covers(Point(cleanout.cap_position)):
                    findings.append(failed("mep.drain_cleanouts",
                                           f"{cleanout.tag} floor cap is hidden by {item.tag}",
                                           (cleanout.tag, item.tag), code=_CODE_LOCATION))
        elif cleanout.access == "wall":
            wall = next((w for w in getattr(ctx.model, "walls", ())
                         if w.tag == cleanout.wall_ref), None)
            if (wall is None
                or _distance_to_axis(cleanout.cap_position, wall.axis) > 6 * M_PER_IN
                or not wall.z0_m - M_PER_IN <= cleanout.cap_z_m <= wall.z1_m + M_PER_IN):
                findings.append(failed("mep.drain_cleanouts",
                                       f"{cleanout.tag} wall cap does not reach its "
                                       f"accessible host {cleanout.wall_ref}",
                                       (cleanout.tag,), code=_CODE_LOCATION))
        required_in = 18 if cleanout.diameter_m <= 2 * M_PER_IN else 24
        if not cleanout.accessible:
            findings.append(failed("mep.drain_cleanouts", f"{cleanout.tag} cap is inaccessible",
                                   (cleanout.tag,), code=_CODE_CLEARANCE))
        elif (cleanout.clear_width_m < required_in * M_PER_IN
              or cleanout.clear_depth_m < required_in * M_PER_IN):
            findings.append(failed("mep.drain_cleanouts",
                                   f"{cleanout.tag} needs {required_in} in by {required_in} in "
                                   "clear at its cap", (cleanout.tag,), code=_CODE_CLEARANCE))
        else:
            findings.append(passed("mep.drain_cleanouts",
                                   f"{cleanout.tag} accessible cap has {required_in} in clearance",
                                   (cleanout.tag,), code=_CODE_CLEARANCE))
    return findings
