"""A door's girt sill course carries its approach on its blocks' screws (owner, 2026-11-14).

The screws cross the sheathing into the floor's edge member. At an I-joist they would cross
the web and nothing else, so an SPF backer goes on each face of the web, ripped to the
recess, and becomes derived floor framing here. The grade is
``engineering.exterior_door_support.girt_course_connection_report``; the oracle is
``notes/exterior_door_structural_mount.md``, "Girt sill course connection".
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.engineering.exterior_door_support import girt_course_connection_report
from typehaus.resolve.framing.girt_sill_course import sill_block_prefix, sill_block_screws
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.truss_girts import OUTER, truss_girt_bands
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.model import FramedMember

_IN = 0.0254
_TOL = _IN / 16
_EDGE_CATEGORIES = ("joist", "rim", "sister_joist", "trimmer", "blocking", "band")
#: Main-member penetration the authored wet lateral value was worked at (the note's basis).
_BASIS_PENETRATION_IN = 1.5
_BACKER_KEY = "girt-sill-backer-"


def girt_sill_connection(model, wall, opening, placement, course: FramedMember):
    """``(report fields, unknown, conflicts)`` for one door's girt sill course."""
    bands = truss_girt_bands(model.plan, wall.assembly)
    framing = bands[1].framing if bands else None
    spec = framing.sill_course if framing is not None else None
    capacity = framing.standoff_fastener_wet_lateral_lb if framing is not None else None
    if spec is None or capacity is None or framing.standoff_fastener_diameter_in is None:
        return _unknown("its screws have no authored sill-course fastening or lateral value")
    index = int(course.child_key.rsplit("-", 1)[-1])
    blocks = [m for m in wall.members if m.child_key.startswith(sill_block_prefix(OUTER, index))]
    if not blocks:
        return _unknown("no blocks under it")
    frame = _CourseFrame(wall, opening, placement, course)
    block = blocks[0]
    block_t = cross_section(block.profile).width_m
    sheathing_out = frame.depth(block.p0) - block_t / 2
    sheathing_t = sum(layer.thickness_m for layer in wall.depth_layers()
                      if layer.function == "sheathing")
    through = frame.girt_t + block_t + sheathing_t
    length = spec.fastener_length_in * _IN
    found = _edge_member(model, frame, block, sheathing_out, sheathing_out + block_t + frame.girt_t
                         - length)
    if found is None:
        return _unknown("no floor member behind its screws")
    floor_index, member = found
    section = cross_section(member.profile)
    conflicts = []
    if section.shape == "i_joist":
        flange_bottom = member.z1_m - section.flange_thickness_m
        if block.z0_m >= flange_bottom - _TOL:
            return _unknown(f"its blocks sit wholly opposite {member.child_key}'s flange")
        recess = (section.flange_width_m - section.web_thickness_m) / 2
        thread_start = length - (framing.standoff_fastener_thread_in or 0.0) * _IN
        if length < through + section.flange_width_m - _TOL:
            conflicts.append(f"{spec.fastener_part} stops short of the backer pair behind the "
                             "girt sill course")
        if thread_start < through + recess + section.web_thickness_m - _TOL:
            conflicts.append(f"{spec.fastener_part}'s thread stands in the clamped stack at "
                             "the girt sill course")
        _add_backers(model, floor_index, member, frame, spec, opening.tag, recess,
                     flange_bottom)
    elif length < through + _BASIS_PENETRATION_IN * _IN - _TOL:
        conflicts.append(f"{spec.fastener_part} enters {member.child_key} short of "
                         f"{_BASIS_PENETRATION_IN:g} in")
    pitch = spec.end_screw_pitch.meters / _IN
    screws = []
    for item in blocks:
        count = sill_block_screws(item) or 1
        station = frame.station(item.p0) / _IN
        screws += [station + (j - (count - 1) / 2) * pitch for j in range(count)]
    height = course.z1_m - course.z0_m
    across = section_across(course, height)
    report = girt_course_connection_report(
        course.length_m / _IN, screws, framing.standoff_fastener_diameter_in,
        spec.course_modulus_psi, (across / _IN) * (height / _IN) ** 3 / 12,
        placement.specification.approach_bearing.concentrated_load_lb, capacity,
        framing.standoff_fastener_wet_lateral_source)
    report.update(girt_course_member=member.child_key, girt_course_fastener=spec.fastener_part)
    if report["connection_status"] == "FAIL":
        demand = report["connection_demand_lb"]
        conflicts.append(f"girt sill course: worst screw share {demand:.1f} lb exceeds its "
                         f"{capacity:g} lb lateral value")
    unknown = ([] if report["connection_status"] != "UNKNOWN"
               else ["girt sill course: its screws leave the course unstable"])
    return report, unknown, conflicts


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


def _add_backers(model, floor_index, member, frame, spec, tag, recess, flange_bottom):
    """The backer pair in the joist's web recesses, the course's length (idempotent)."""
    floor = model.floors[floor_index]
    keys = {m.child_key for m in floor.members}
    stock = cross_section(spec.backer_stock)
    centre = frame.depth(member.p0)
    offset = (cross_section(member.profile).web_thickness_m + recess) / 2
    new = []
    for side, sign in (("out", 1.0), ("in", -1.0)):
        key = f"{_BACKER_KEY}{tag}-{side}"
        if key in keys:
            continue
        depth = centre + sign * offset
        new.append(FramedMember(
            floor.uid, key, "blocking", f"{recess / _IN:.5f}x{stock.depth_m / _IN:.4f}",
            frame.point(0.0, depth), frame.point(frame.span, depth),
            flange_bottom - stock.depth_m, flange_bottom, frame.span,
            material=spec.backer_material_ref, stock_profile=spec.backer_stock))
    if new:
        model.floors[floor_index] = replace(floor, members=(*floor.members, *new))


def _unknown(reason):
    return (dict(connection_status="UNKNOWN", connection_demand_lb=None,
                 connection_capacity_lb=None, connection_dcr=None),
            [f"girt sill course: {reason}; its connection is ungraded"], [])
