"""A door's girt sill course carries its approach on its blocks' screws.

The screws cross the sheathing into the floor's edge member. At an I-joist they would cross
the web and nothing else, so an SPF backer goes on each face of the web, ripped to the
recess, and becomes derived floor framing here: the course's length behind blocks, each
seat's length behind end seats. The screw is graded on what ESR-1078 and the house's own
basis ask (``notes/exterior_door_sill_beam.md`` §3): plain shank across the clamped stack
(the sheathing is nailed to the edge member, ``catlin_truss_engineering.md`` §3.1), thread
inside the edge member, embedded thread and penetration minima, the published spacing; the
share is ``engineering.exterior_door_support``'s spring beam.
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
from typehaus.resolve.framing.girt_sill_course import sill_block_prefix, sill_block_screws
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


def girt_sill_connection(model, wall, opening, placement, course: FramedMember):
    """``(report fields, unknown, conflicts)`` for one door's girt sill course."""
    bands = truss_girt_bands(model.plan, wall.assembly)
    framing = bands[1].framing if bands else None
    spec = framing.sill_course if framing is not None else None
    if spec is None or framing.standoff_fastener_diameter_in is None:
        return _unknown("its screws have no authored sill-course fastening")
    seats = spec.layout == "end_seats"
    capacity, source = ((spec.lateral_wet_lb, spec.lateral_source) if seats else
                        (framing.standoff_fastener_wet_lateral_lb,
                         framing.standoff_fastener_wet_lateral_source))
    if capacity is None:
        return _unknown("its screws have no authored lateral value")
    item, _, thread_in = screw_by_part_number(spec.fastener_part)
    index = int(course.child_key.rsplit("-", 1)[-1])
    blocks = [m for m in wall.members if m.child_key.startswith(sill_block_prefix(OUTER, index))]
    if not blocks or thread_in is None:
        return _unknown("no blocks under it" if not blocks else
                        f"{spec.fastener_part}'s thread length is unread")
    frame = _CourseFrame(wall, opening, placement, course)
    block = blocks[0]
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
    ranges = ([(frame.station(b.p0), frame.station(b.p1)) for b in blocks] if seats
              else [(0.0, frame.span)])
    ranges = [tuple(sorted(r)) for r in ranges]
    # The edge member's wood, depth past its face (the sheathing's back): an I-joist's web
    # is a gap between its two backers.
    wood = [(0.0, section.width_m)]
    backer_z = None
    if section.shape == "i_joist":
        flange_bottom = member.z1_m - section.flange_thickness_m
        if block.z0_m >= flange_bottom - _TOL:
            return _unknown(f"its blocks sit wholly opposite {member.child_key}'s flange")
        recess = (section.flange_width_m - section.web_thickness_m) / 2
        wood = [(0.0, recess), (recess + section.web_thickness_m, section.flange_width_m)]
        backer_z = _add_backers(model, floor_index, member, frame, spec, opening.tag, recess,
                                flange_bottom, ranges)
        unknown.append("girt sill course: the edge TJI's backer blocks (TJ-4000 p.28 size and "
                       "nailing) are unread; the backer attachment is ungraded")
    joint = _screw_fit(spec, item, length, thread, clamped, clamped + sheathing_t, wood,
                       framing.standoff_fastener_diameter_in)
    conflicts += joint.pop("conflicts")
    screws = _screws(spec, item, course, blocks, frame, backer_z, conflicts) if seats else \
        _block_screws(spec, blocks, frame)
    height = course.z1_m - course.z0_m
    across = section_across(course, height)
    stations = [s for s, _, _ in screws]
    report = girt_course_connection_report(
        course.length_m / _IN, stations, framing.standoff_fastener_diameter_in,
        spec.course_modulus_psi, (across / _IN) * (height / _IN) ** 3 / 12,
        placement.specification.approach_bearing.concentrated_load_lb, capacity, source)
    report.update(girt_course_member=member.child_key, girt_course_fastener=spec.fastener_part,
                  girt_course_layout=spec.layout, **joint)
    if seats:
        centroids = [sum(s for s, _, _ in screws if lo <= s <= hi) /
                     max(1, sum(1 for s, _, _ in screws if lo <= s <= hi)) for lo, hi in
                     ((r[0] / _IN, r[1] / _IN) for r in ranges)]
        report.update(sill_beam_report(
            abs(centroids[1] - centroids[0]), across / _IN, height / _IN,
            spec.course_modulus_psi, spec.course_bending_psi, spec.course_shear_psi,
            placement.specification.approach_bearing.concentrated_load_lb,
            spec.course_deflection_limit.meters / _IN))
        report.update(seat_width_in=spec.seat_width.meters / _IN,
                      seat_screws=[(round(s, 4), round(z, 4)) for s, z, _ in screws])
        if report["member_status"] == "FAIL":
            conflicts.append("girt sill beam exceeds its bending, shear or deflection limit")
    if report["connection_status"] == "FAIL":
        demand = report["connection_demand_lb"]
        conflicts.append(f"girt sill course: worst screw share {demand:.1f} lb exceeds its "
                         f"{capacity:g} lb lateral value")
    if report["connection_status"] == "UNKNOWN":
        unknown.append("girt sill course: its screws leave the course unstable")
    return report, unknown, conflicts


def _screw_fit(spec, item, length, thread, clamped, through, wood, diameter_in):
    """Shank, thread and embedment of one screw (depths in metres past the head)."""
    conflicts = []
    shank = length - thread
    if shank < clamped - _TOL:
        conflicts.append(f"{spec.fastener_part}'s thread stands in the clamped stack at the "
                         "girt sill course")
    member_width = wood[-1][1]
    start, end = shank - through, length - through
    if end > member_width + _TOL:
        conflicts.append(f"{spec.fastener_part}'s thread runs past the edge member behind the "
                         "girt sill course")
    embedded = sum(max(0.0, min(end, b) - max(start, a)) for a, b in wood)
    penetration = length - through
    minimum = item.spacing.min_embedded_thread * _IN if item.spacing else None
    if minimum is not None and embedded < minimum - _TOL:
        conflicts.append(f"{spec.fastener_part} embeds {embedded / _IN:.2f}\" of thread in the "
                         f"edge member's wood, under {minimum / _IN:g}\"")
    if penetration < _MIN_PENETRATION_D * diameter_in * _IN - _TOL:
        conflicts.append(f"{spec.fastener_part} penetrates the edge member "
                         f"{penetration / _IN:.2f}\", under {_MIN_PENETRATION_D}D")
    return dict(conflicts=conflicts, screw_clamped_stack_in=clamped / _IN,
                screw_shank_in=shank / _IN, screw_penetration_in=penetration / _IN,
                screw_embedded_thread_in=embedded / _IN)


def _block_screws(spec, blocks, frame):
    """One row: each block's count along the course at the end-screw pitch."""
    pitch = spec.end_screw_pitch.meters / _IN
    out = []
    for item in blocks:
        count = sill_block_screws(item) or 1
        station = frame.station(item.p0) / _IN
        out += [(station + (j - (count - 1) / 2) * pitch, None, 0) for j in range(count)]
    return out


def _screws(spec, item, course, seats, frame, backer_z, conflicts):
    """Each seat's staggered rows laid out from its outer end, rows centred in the band every
    member's edge distances leave, then graded against the published minima."""
    rule = item.spacing
    if rule is None:
        conflicts.append(f"{spec.fastener_part} has no published spacing to lay the seats out by")
        return []
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
    stagger = rule.in_row_spacing / spec.seat_rows
    screws = []
    for k, seat in enumerate(seats):
        s0, s1 = sorted((frame.station(seat.p0) / _IN, frame.station(seat.p1) / _IN))
        outer, sign = (s0, 1.0) if abs(s0) < abs(span - s1) else (s1, -1.0)
        for r, z in enumerate(rows):
            for j in range(spec.screws_per_row):
                offset = rule.end_distance + j * rule.in_row_spacing + r * stagger
                screws.append((outer + sign * offset, z, f"{k}{r}"))
    conflicts.extend(f"girt sill seat screws: {miss} (ESR-1078 Table 5)"
                     for miss in screw_spacing_failures(screws, members, rule))
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
            [f"girt sill course: {reason}; its connection is ungraded"], [])
