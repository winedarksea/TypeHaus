"""A door's girt sill beam carries its approach on its two end seats' screws.

The screws cross the sheathing into the floor's edge member. At an I-joist they would cross
the web and nothing else, so an SPF backer goes on each face of the web behind each seat,
ripped to the recess, and becomes derived floor framing here. The screw is graded on what
ESR-1078 and the house's own basis ask (``notes/exterior_door_sill_beam.md`` §3): plain
shank across the clamped stack (the sheathing is nailed to the edge member,
``catlin_truss_engineering.md`` §3.1), thread inside the edge member, embedded thread and
penetration minima, the published spacing; the share is
``engineering.exterior_door_support``'s spring beam.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.engineering.exterior_door_support import (
    girt_course_connection_report,
    screw_spacing_failures,
    sill_beam_report,
)
from typehaus.hardware.catalog import screw_by_part_number
from typehaus.resolve.framing.girt_sill_course import sill_block_prefix
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.truss_girts import OUTER, truss_girt_bands
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.model import FramedMember

_IN = 0.0254
_TOL = _IN / 16
_EDGE_CATEGORIES = ("joist", "rim", "sister_joist", "trimmer", "blocking", "band")
_BACKER_KEY = "girt-sill-backer-"
#: NDS §12.1.4.6 minimum penetration, in diameters (``catlin_truss_engineering.md`` §3.3).
_MIN_PENETRATION_D = 6
#: Width of TJ-4000 p.6's published flange-thickness band (``framing/profiles._TJI_SERIES_IN``
#: models its low end): a backer tight under a thick flange sits this much lower.
_FLANGE_BAND_IN = 0.125


def girt_sill_connection(model, wall, opening, placement, course: FramedMember):
    """``(report fields, unknown, conflicts)`` for one door's girt sill beam."""
    bands = truss_girt_bands(model.plan, wall.assembly)
    framing = bands[1].framing if bands else None
    spec = framing.sill_course if framing is not None else None
    if spec is None or framing.standoff_fastener_diameter_in is None:
        return _unknown("its screws have no authored sill-course fastening")
    capacity, source = spec.lateral_wet_lb, spec.lateral_source
    item, _, thread_in = screw_by_part_number(spec.fastener_part)
    index = int(course.child_key.rsplit("-", 1)[-1])
    seats = [m for m in wall.members if m.child_key.startswith(sill_block_prefix(OUTER, index))]
    if len(seats) != 2 or thread_in is None or item.spacing is None:
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
    floor_index, member = found
    section = cross_section(member.profile)
    unknown, conflicts = [], []
    ranges = [tuple(sorted((frame.station(b.p0), frame.station(b.p1)))) for b in seats]
    # The edge member's wood, depth past its face (the sheathing's back): an I-joist's web
    # is a gap between its two backers.
    wood = [(0.0, section.width_m)]
    backer_z = None
    if section.shape == "i_joist":
        flange_bottom = member.z1_m - section.flange_thickness_m
        if block.z0_m >= flange_bottom - _TOL:
            return _unknown(f"its seats sit wholly opposite {member.child_key}'s flange")
        recess = (section.flange_width_m - section.web_thickness_m) / 2
        wood = [(0.0, recess), (recess + section.web_thickness_m, section.flange_width_m)]
        backer_z = _add_backers(model, floor_index, member, frame, spec, opening.tag, recess,
                                flange_bottom, ranges)
        unknown.append("girt sill beam: the edge TJI's backer blocks (TJ-4000 p.28 size and "
                       "nailing) are unread; the backer attachment is ungraded")
    joint = _screw_fit(spec, item, length, thread, clamped, clamped + sheathing_t, wood,
                       framing.standoff_fastener_diameter_in)
    conflicts += joint.pop("conflicts")
    screws = _screws(spec, item.spacing, course, seats, frame, backer_z, conflicts, unknown)
    height = course.z1_m - course.z0_m
    across = section_across(course, height)
    load = placement.specification.approach_bearing.concentrated_load_lb
    report = girt_course_connection_report(
        course.length_m / _IN, [s for s, _, _ in screws], framing.standoff_fastener_diameter_in,
        spec.course_modulus_psi, (across / _IN) * (height / _IN) ** 3 / 12, load, capacity,
        source)
    report.update(girt_course_member=member.child_key, girt_course_fastener=spec.fastener_part,
                  **joint)
    centroids = [sum(group) / len(group) for group in
                 ([s for s, _, _ in screws if lo / _IN <= s <= hi / _IN] for lo, hi in ranges)]
    report.update(sill_beam_report(
        abs(centroids[1] - centroids[0]), across / _IN, height / _IN, spec.course_modulus_psi,
        spec.course_bending_psi, spec.course_shear_psi, load,
        spec.course_deflection_limit.meters / _IN))
    report.update(seat_width_in=spec.seat_width.meters / _IN,
                  seat_screws=[(round(s, 4), round(z, 4)) for s, z, _ in screws])
    if report["member_status"] == "FAIL":
        conflicts.append("girt sill beam exceeds its bending, shear or deflection limit")
    if report["connection_status"] == "FAIL":
        demand = report["connection_demand_lb"]
        conflicts.append(f"girt sill beam: worst seat screw share {demand:.1f} lb exceeds its "
                         f"{capacity:g} lb lateral value")
    if report["connection_status"] == "UNKNOWN":
        unknown.append("girt sill beam: its screws leave the beam unstable")
    return report, unknown, conflicts


def _screw_fit(spec, item, length, thread, clamped, through, wood, diameter_in):
    """Shank, thread and embedment of one screw (depths in metres past the head)."""
    conflicts = []
    shank = length - thread
    if shank < clamped - _TOL:
        conflicts.append(f"{spec.fastener_part}'s thread stands in the clamped stack at the "
                         "girt sill beam")
    member_width = wood[-1][1]
    start, end = shank - through, length - through
    if end > member_width + _TOL:
        conflicts.append(f"{spec.fastener_part}'s thread runs past the edge member behind the "
                         "girt sill beam")
    embedded = sum(max(0.0, min(end, b) - max(start, a)) for a, b in wood)
    penetration = length - through
    minimum = item.spacing.min_embedded_thread * _IN
    if embedded < minimum - _TOL:
        conflicts.append(f"{spec.fastener_part} embeds {embedded / _IN:.2f}\" of thread in the "
                         f"edge member's wood, under {minimum / _IN:g}\"")
    if penetration < _MIN_PENETRATION_D * diameter_in * _IN - _TOL:
        conflicts.append(f"{spec.fastener_part} penetrates the edge member "
                         f"{penetration / _IN:.2f}\", under {_MIN_PENETRATION_D}D")
    return dict(conflicts=conflicts, screw_clamped_stack_in=clamped / _IN,
                screw_shank_in=shank / _IN, screw_penetration_in=penetration / _IN,
                screw_embedded_thread_in=embedded / _IN)


def _screws(spec, rule, course, seats, frame, backer_z, conflicts, unknown):
    """Each seat's rows laid out from its outer end, every other row half a pitch along so
    neighbours are staggered, rows centred in the band every member's edge distances leave,
    then graded against the published minima."""
    span = frame.span / _IN
    members = [("beam", 0.0, span, course.z0_m / _IN, course.z1_m / _IN, "top")]
    for k, seat in enumerate(seats):
        s0, s1 = sorted((frame.station(seat.p0) / _IN, frame.station(seat.p1) / _IN))
        members.append((f"seat {k}", s0, s1, seat.z0_m / _IN, seat.z1_m / _IN, "top"))
        if backer_z is not None:
            members.append((f"backer {k}", s0, s1, backer_z[0] / _IN, backer_z[1] / _IN,
                            "bottom"))
    lows = [z0 + (rule.unloaded_edge if loaded == "top" else rule.loaded_edge)
            for _, _, _, z0, _, loaded in members]
    highs = [z1 - (rule.loaded_edge if loaded == "top" else rule.unloaded_edge)
             for _, _, _, _, z1, loaded in members]
    mid = (max(lows) + min(highs)) / 2
    rows = [mid + (r - (spec.seat_rows - 1) / 2) * rule.row_spacing
            for r in range(spec.seat_rows)][::-1]
    screws = []
    for k, seat in enumerate(seats):
        s0, s1 = sorted((frame.station(seat.p0) / _IN, frame.station(seat.p1) / _IN))
        outer, sign = (s0, 1.0) if abs(s0) < abs(span - s1) else (s1, -1.0)
        for r, z in enumerate(rows):
            for j in range(spec.screws_per_row):
                offset = rule.end_distance + (j + (r % 2) / 2) * rule.in_row_spacing
                screws.append((outer + sign * offset, z, f"{k}{r}"))
    misses = screw_spacing_failures(screws, members, rule)
    conflicts.extend(f"girt sill seat screws: {miss} (ESR-1078 Table 5)" for miss in misses)
    if backer_z is not None and not misses:
        drop = _FLANGE_BAND_IN
        thick = [(n, s0, s1, z0 - drop, z1 - drop, loaded) if n.startswith("backer") else
                 (n, s0, s1, z0, z1, loaded) for n, s0, s1, z0, z1, loaded in members]
        if screw_spacing_failures(screws, thick, rule):
            unknown.append("girt sill seat screws: they meet ESR-1078 Table 5 under the edge "
                           "TJI's thin-end flange; a flange at the thick end of TJ-4000's band "
                           f"(+{drop:g} in) drops the backers past it, so the delivered flange "
                           "decides")
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
    """``(floor index, member)``: the first floor member the screws enter, if any."""
    best = None
    for floor_index, floor in enumerate(model.floors):
        for member in floor.members:
            if member.category not in _EDGE_CATEGORIES or member.child_key.startswith(
                    _BACKER_KEY):
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
                best = (outboard, floor_index, member)
    return None if best is None else best[1:]


def _add_backers(model, floor_index, member, frame, spec, tag, recess, flange_bottom, ranges):
    """The backer pair in the joist's web recesses over each station range, tight under the
    top flange (idempotent); returns its ``(z0, z1)``."""
    floor = model.floors[floor_index]
    keys = {m.child_key for m in floor.members}
    stock = cross_section(spec.backer_stock)
    z = (flange_bottom - stock.depth_m, flange_bottom)
    centre = frame.depth(member.p0)
    offset = (cross_section(member.profile).web_thickness_m + recess) / 2
    new = []
    for k, (lo, hi) in enumerate(ranges):
        suffix = f"-{k}" if len(ranges) > 1 else ""
        for side, sign in (("out", 1.0), ("in", -1.0)):
            key = f"{_BACKER_KEY}{tag}{suffix}-{side}"
            if key in keys:
                continue
            depth = centre + sign * offset
            new.append(FramedMember(
                floor.uid, key, "blocking", f"{recess / _IN:.5f}x{stock.depth_m / _IN:.4f}",
                frame.point(lo, depth), frame.point(hi, depth), z[0], z[1], hi - lo,
                material=spec.backer_material_ref, stock_profile=spec.backer_stock))
    if new:
        model.floors[floor_index] = replace(floor, members=(*floor.members, *new))
    return z


def _unknown(reason):
    return (dict(connection_status="UNKNOWN", connection_demand_lb=None,
                 connection_capacity_lb=None, connection_dcr=None),
            [f"girt sill beam: {reason}; its connection is ungraded"], [])
