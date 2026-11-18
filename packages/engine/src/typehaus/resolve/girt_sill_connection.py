"""A door's girt sill beam carries its approach on its two end seats' screws.

The screws cross the sheathing into the floor's edge member, an LSL rim board
(``JoistSpec.edge_rims``), and on into the wood nailed behind it (a backer); an I-joist there
is refused, its web is no screw target. The screw is graded on what ESR-1078 and the house's
NDS basis ask (``notes/exterior_door_sill_beam.md`` §3): plain shank across the clamped stack
(the sheathing is nailed to the rim, ``catlin_truss_engineering.md`` §3.1), embedded thread
and penetration in the wood contiguous from the rim's face, Table 5 spacing by each member's
specific gravity; the share is ``engineering.exterior_door_support``'s spring beam, and the
seat's rotation ``engineering.sill_seat_rotation``'s NDS 12.4.1 grade.
"""

from __future__ import annotations

import math

from typehaus.engineering.exterior_door_support import (
    girt_course_connection_report,
    screw_force_matrix,
    screw_spacing_failures,
    sill_beam_report,
)
from typehaus.engineering.sill_seat_rotation import seat_rotation_report
from typehaus.hardware.catalog import screw_by_part_number
from typehaus.resolve.framing.girt_sill_course import sill_block_prefix
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.truss_girts import OUTER, truss_girt_bands
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.model import FramedMember

_IN = 0.0254
_TOL = _IN / 16
_EDGE_CATEGORIES = ("joist", "rim", "sister_joist", "trimmer", "blocking", "band")
#: NDS §12.1.4.6 minimum penetration, in diameters (``catlin_truss_engineering.md`` §3.3).
_MIN_PENETRATION_D = 6
#: ESR-1078 Table 5 splits its columns at this specific gravity.
_DENSE_G = 0.50
#: An unmaterialled LSL rim board: ESR-1387's equivalent SG for fasteners in its face.
_LSL_RIM_G = 0.50


def girt_sill_connection(model, wall, opening, placement, course: FramedMember):
    """``(report fields, unknown, conflicts)`` for one door's girt sill beam."""
    bands = truss_girt_bands(model.plan, wall.assembly)
    framing = bands[1].framing if bands else None
    spec = framing.sill_course if framing is not None else None
    if spec is None:
        return _unknown("its screws have no authored sill-course fastening")
    capacity, source = spec.lateral_wet_lb, spec.lateral_source
    item, _, thread_in = screw_by_part_number(spec.fastener_part)
    index = int(course.child_key.rsplit("-", 1)[-1])
    seats = [m for m in wall.members if m.child_key.startswith(sill_block_prefix(OUTER, index))]
    if len(seats) != 2 or thread_in is None or None in (item.spacing, item.spacing_dense):
        return _unknown("it has no seat at each end" if len(seats) != 2 else
                        f"{spec.fastener_part}'s thread length or published spacing is unread")
    frame = _CourseFrame(wall, opening, placement, course)
    block = seats[0]
    sheathing_out = frame.depth(block.p0) - cross_section(block.profile).width_m / 2
    sheathing_t = sum(layer.thickness_m for layer in wall.depth_layers()
                      if layer.function == "sheathing")
    clamped = frame.course_depth + frame.girt_t / 2 - sheathing_out
    length, thread = spec.fastener_length_in * _IN, thread_in * _IN
    found = _edge_member(model, frame, block, sheathing_out, sheathing_out + clamped - length)
    if found is None:
        return _unknown("no floor member behind its screws")
    member = found
    section = cross_section(member.profile)
    if section.shape == "i_joist":
        return _unknown(f"its screws land in {member.child_key}'s web: lay the edge line as "
                        "a rim board (JoistSpec.edge_rims)")
    conflicts = []
    through = clamped + sheathing_t
    wood = _wood_behind(model, frame, member, length - thread - through, length - through)
    rules = (_rule(model, item, course.material), _rule(model, item, block.material),
             _rule(model, item, member.material, _LSL_RIM_G))
    backers = [(name, s0, s1, z0, z1, _rule(model, item, material, _LSL_RIM_G))
               for _, _, name, s0, s1, z0, z1, material in wood[1:]]
    screws = _screws(spec, rules, course, seats, frame, member, backers, conflicts)
    joint = _screw_fit(spec, item, length, thread, clamped, through, section.width_m,
                       wood, screws)
    conflicts += joint.pop("conflicts")
    height = course.z1_m - course.z0_m
    across = section_across(course, height)
    load = placement.specification.approach_bearing.concentrated_load_lb
    stations = [s for s, _, _ in screws]
    inertia = (across / _IN) * (height / _IN) ** 3 / 12
    report = girt_course_connection_report(
        course.length_m / _IN, stations, spec.fastener_diameter_in, spec.course_modulus_psi,
        inertia, load, capacity, source)
    report.update(girt_course_member=member.child_key, girt_course_fastener=spec.fastener_part,
                  **joint)
    ranges = [tuple(sorted((frame.station(b.p0), frame.station(b.p1)))) for b in seats]
    centroids = [sum(group) / len(group) for group in
                 ([s for s, _, _ in screws if lo / _IN <= s <= hi / _IN] for lo, hi in ranges)]
    report.update(sill_beam_report(
        abs(centroids[1] - centroids[0]), across / _IN, height / _IN, spec.course_modulus_psi,
        spec.course_bending_psi, spec.course_shear_psi, load,
        spec.course_deflection_limit.meters / _IN))
    report.update(seat_width_in=spec.seat_width.meters / _IN,
                  seat_screws=[(round(s, 4), round(z, 4)) for s, z, _ in screws])
    unknown = []
    solved = screw_force_matrix(course.length_m / _IN, stations, spec.fastener_diameter_in,
                                spec.course_modulus_psi, inertia, load)
    if solved is not None:
        withdrawal = spec.withdrawal_lb_per_in * report["screw_embedded_thread_in"]
        columns = [(label, min(withdrawal, lb * spec.pull_through_wet_factor))
                   for label, lb in spec.pull_through_lb]
        groups = [([i for i, (_, _, row) in enumerate(screws) if row[0] == str(k)],
                   seat.z0_m / _IN, seat.z1_m / _IN) for k, seat in enumerate(seats)]
        report.update(seat_rotation_report(
            *solved, [(s, z) for s, z, _ in screws], groups,
            (through - frame.girt_t / 2) / _IN, spec.seat_bearing_inset.meters / _IN,
            capacity, columns), seat_rotation_source=spec.axial_source)
        if report["seat_rotation_status"] == "FAIL":
            conflicts.append(f"girt sill seat rotation: a screw's combined lateral and "
                             f"withdrawal is {report['seat_rotation_dcr']:.3f} of NDS 12.4.1's "
                             "allowable")
    if report["member_status"] == "FAIL":
        conflicts.append("girt sill beam exceeds its bending, shear or deflection limit")
    if report["connection_status"] == "FAIL":
        demand = report["connection_demand_lb"]
        conflicts.append(f"girt sill beam: worst seat screw share {demand:.1f} lb exceeds its "
                         f"{capacity:g} lb lateral value")
    if report["connection_status"] == "UNKNOWN":
        unknown.append("girt sill beam: its screws leave the beam unstable")
    return report, unknown, conflicts


def _rule(model, item, material, default_g=None):
    """ESR-1078 Table 5's column for a member, by its specific gravity."""
    found = model.plan.library.material(material) if material else None
    gravity = getattr(found, "specific_gravity", None) or default_g or 0.0
    return item.spacing_dense if gravity >= _DENSE_G - 1e-9 else item.spacing


def _screw_fit(spec, item, length, thread, clamped, through, rim_width, wood, screws):
    """Shank, thread and embedment of the screws (depths in metres past the head): the thread
    counts in wood contiguous from the rim's face (rim, then any backer nailed behind it), the
    least over every screw."""
    conflicts = []
    shank = length - thread
    if shank < clamped - _TOL:
        conflicts.append(f"{spec.fastener_part}'s thread stands in the clamped stack at the "
                         "girt sill beam")
    start, end = shank - through, length - through
    reaches = [_contiguous(wood, station * _IN, z * _IN) for station, z, _ in screws]
    reach = min(reaches) if reaches else rim_width
    embedded = max(0.0, min(end, reach) - max(start, 0.0))
    penetration = min(end, reach)
    minimum = item.spacing.min_embedded_thread * _IN
    if embedded < minimum - _TOL:
        conflicts.append(f"{spec.fastener_part} embeds {embedded / _IN:.2f}\" of thread in the "
                         f"edge rim and its backer, under {minimum / _IN:g}\"")
    if penetration < _MIN_PENETRATION_D * spec.fastener_diameter_in * _IN - _TOL:
        conflicts.append(f"{spec.fastener_part} penetrates the edge rim "
                         f"{penetration / _IN:.2f}\", under {_MIN_PENETRATION_D}D")
    return dict(conflicts=conflicts, screw_clamped_stack_in=clamped / _IN,
                screw_shank_in=shank / _IN, screw_penetration_in=penetration / _IN,
                screw_embedded_thread_in=embedded / _IN,
                screw_tip_past_rim_in=max(0.0, end - rim_width) / _IN,
                screw_backers=sorted({w[2] for w in wood[1:]}))


def _contiguous(wood, station, z):
    """How deep wood runs unbroken from the rim's face along a screw at ``station``/``z``."""
    reach = 0.0
    for lo, hi, _, s0, s1, z0, z1, _ in sorted(wood):
        if s0 - _TOL <= station <= s1 + _TOL and z0 - _TOL <= z <= z1 + _TOL:
            if lo > reach + _TOL:
                break
            reach = max(reach, hi)
    return reach


def _wood_behind(model, frame, rim, depth, end):
    """``(lo, hi, name, s0, s1, z0, z1, material)`` in metres: the rim (first) and each member
    of its floor parallel behind it that the thread, ``depth``..``end`` in from the rim's face,
    could enter; ``lo``/``hi`` inward from that face, stations along the course."""
    half = cross_section(rim.profile).width_m / 2
    face = frame.depth(rim.p0) + half
    out = []
    for floor in model.floors:
        if not any(member is rim for member in floor.members):
            continue
        for member in floor.members:
            if member is not rim and member.category not in _EDGE_CATEGORIES:
                continue
            dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
            run = math.hypot(dx, dy)
            if run < _TOL or abs(dx * frame.along[1] - dy * frame.along[0]) > 1e-3 * run:
                continue
            width = cross_section(member.profile).width_m / 2
            lo = face - (frame.depth(member.p0) + width)
            hi = lo + 2 * width
            if member is not rim and (lo < -_TOL or lo > end + _TOL or hi < depth):
                continue
            s0, s1 = sorted((frame.station(member.p0), frame.station(member.p1)))
            out.append((lo, hi, member.child_key, s0, s1, member.z0_m, member.z1_m,
                        member.material))
    out.sort(key=lambda w: (w[2] != rim.child_key, w[0]))
    return out


def _screws(spec, rules, course, seats, frame, rim, backers, conflicts):
    """Each seat's rows laid out from its outer end, every other row half a pitch along so
    neighbours are staggered, rows centred in the band every member's edge distances leave,
    then graded against the published minima (rows by the rim's column, ESR-1078 Table 5
    "perp to grain of MM")."""
    beam_rule, seat_rule, rim_rule = rules
    span = frame.span / _IN
    members = [("beam", 0.0, span, course.z0_m / _IN, course.z1_m / _IN, "top", beam_rule),
               ("edge rim", -1e9, 1e9, rim.z0_m / _IN, rim.z1_m / _IN, "bottom", rim_rule)]
    members += [(name, s0 / _IN, s1 / _IN, z0 / _IN, z1 / _IN, "bottom", rule)
                for name, s0, s1, z0, z1, rule in backers]
    for k, seat in enumerate(seats):
        s0, s1 = sorted((frame.station(seat.p0) / _IN, frame.station(seat.p1) / _IN))
        members.append((f"seat {k}", s0, s1, seat.z0_m / _IN, seat.z1_m / _IN, "top",
                        seat_rule))
    lows = [z0 + (r.unloaded_edge if loaded == "top" else r.loaded_edge)
            for _, _, _, z0, _, loaded, r in members]
    highs = [z1 - (r.loaded_edge if loaded == "top" else r.unloaded_edge)
             for _, _, _, _, z1, loaded, r in members]
    mid = (max(lows) + min(highs)) / 2
    rows = [mid + (r - (spec.seat_rows - 1) / 2) * rim_rule.row_spacing
            for r in range(spec.seat_rows)][::-1]
    end = max(beam_rule.end_distance, seat_rule.end_distance)
    screws = []
    for k, seat in enumerate(seats):
        s0, s1 = sorted((frame.station(seat.p0) / _IN, frame.station(seat.p1) / _IN))
        outer, sign = (s0, 1.0) if abs(s0) < abs(span - s1) else (s1, -1.0)
        for r, z in enumerate(rows):
            for j in range(spec.screws_per_row):
                offset = end + (j + (r % 2) / 2) * rim_rule.in_row_spacing
                screws.append((outer + sign * offset, z, f"{k}{r}"))
    misses = screw_spacing_failures(screws, members, rim_rule)
    conflicts.extend(f"girt sill seat screws: {miss} (ESR-1078 Table 5)" for miss in misses)
    return screws


def section_across(member: FramedMember, height: float) -> float:
    """A member's thickness through the wall, given its vertical extent."""
    section = cross_section(member.profile)
    return section.width_m if abs(height - section.depth_m) < _TOL else section.depth_m


class _CourseFrame:
    """Stations along the course and depths outward-positive from the opening's centre."""

    def __init__(self, wall, opening, placement, course):
        _, _, normal, _ = wall_frame(wall)
        self.center = opening_center(wall, opening)
        self.out = (placement.outward_sign * normal[0], placement.outward_sign * normal[1])
        dx, dy = course.p1[0] - course.p0[0], course.p1[1] - course.p0[1]
        run = math.hypot(dx, dy)
        self.along, self.origin = (dx / run, dy / run), course.p0
        self.span = run
        self.course_depth = self.depth(course.p0)
        self.girt_t = section_across(course, course.z1_m - course.z0_m)

    def depth(self, point):
        return ((point[0] - self.center[0]) * self.out[0]
                + (point[1] - self.center[1]) * self.out[1])

    def station(self, point):
        return ((point[0] - self.origin[0]) * self.along[0]
                + (point[1] - self.origin[1]) * self.along[1])

    def point(self, station, depth):
        offset = depth - self.course_depth
        return (self.origin[0] + self.along[0] * station + self.out[0] * offset,
                self.origin[1] + self.along[1] * station + self.out[1] * offset)


def _edge_member(model, frame, block, sheathing_out, tip):
    """The first floor member the screws enter, if any."""
    best = None
    for floor in model.floors:
        for member in floor.members:
            if member.category not in _EDGE_CATEGORIES:
                continue
            if member.z1_m <= block.z0_m or member.z0_m >= block.z1_m:
                continue
            dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
            run = math.hypot(dx, dy)
            if run < _TOL or abs(dx * frame.along[1] - dy * frame.along[0]) > 1e-3 * run:
                continue
            s0, s1 = sorted((frame.station(member.p0), frame.station(member.p1)))
            if s0 > _TOL or s1 < frame.span - _TOL:
                continue
            half = cross_section(member.profile).width_m / 2
            centre = frame.depth(member.p0)
            outboard = centre + half
            if centre - half >= sheathing_out or outboard <= tip:
                continue
            if best is None or outboard > best[0]:
                best = (outboard, member)
    return None if best is None else best[1]


def _unknown(reason):
    return (dict(connection_status="UNKNOWN", connection_demand_lb=None,
                 connection_capacity_lb=None, connection_dcr=None),
            [f"girt sill beam: {reason}; its connection is ungraded"], [])
