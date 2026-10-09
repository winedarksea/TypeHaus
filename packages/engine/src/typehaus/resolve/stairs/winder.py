"""Finished winder panels and their complete structural platform boxes."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.common import (
    _notch_z,
    _riser_member,
    _spacing,
    _stringer_offsets,
    _tread_board_profile,
    _tread_risers,
    _tread_thickness,
)
from typehaus.resolve.stairs.winder_framing import departing_rim_members, winder_box_framing
from typehaus.resolve.stairs.winder_geometry import (
    WinderLayout,
    balanced_winder_turn,
    layout_from_spec,
    physical_nosing_line,
    polygon_ring,
    shifted_line,
)


def local_winder_layout(stair: Stair, nosing_m: float) -> WinderLayout:
    spec = stair.winder_turn or balanced_winder_turn(
        stair.width.meters, stair.winder_count, nosing_m)
    return layout_from_spec(spec, stair.winder_count, stair.width.meters)


def winder_transform(stair: Stair, minx: float, miny: float):
    origin = stair.start.xy_m if stair.start else (minx, miny)
    sign = -1.0 if stair.run_reversed else 1.0
    turn = -1.0 if stair.turn_direction == "right" else 1.0
    run = (sign, 0.0) if stair.run_direction == "x" else (0.0, sign)
    cross = (0.0, turn) if stair.run_direction == "x" else (turn, 0.0)

    def vector(value):
        a, b = value
        return run[0] * a + cross[0] * b, run[1] * a + cross[1] * b

    def point(value):
        x, y = vector(value)
        return origin[0] + x, origin[1] + y

    return point, vector


def resolved_winder_layout(stair: Stair, minx: float, miny: float,
                           nosing_m: float) -> WinderLayout:
    layout = local_winder_layout(stair, nosing_m)
    point, vector = winder_transform(stair, minx, miny)
    return WinderLayout(tuple(point(p) for p in layout.footprint),
                        tuple(point(p) for p in layout.inner_boundary),
                        tuple(tuple(point(p) for p in line) for line in layout.riser_lines),
                        tuple(vector(n) for n in layout.normals))


def _winder_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                          risers: int, riser: float, tread: float,
                          tread_depth: float, nosing: float,
                          supporting_floor_m: float | None = None) -> tuple[FramedMember, ...]:
    layout = local_winder_layout(stair, nosing)
    point, vector = winder_transform(stair, minx, miny)
    width, thickness = stair.width.meters, _tread_thickness(stair)
    straight_treads = risers - 1 - stair.winder_count
    if straight_treads < 0:
        raise ValueError("winder count exceeds the stair's tread budget")
    inside, outside = layout.riser_lines[-1]
    boxes = winder_box_framing(stair, layout, z0, riser, thickness, supporting_floor_m)
    departing_rim = departing_rim_members(
        boxes, layout, stair.winder_count - 1, stair.winder_framing.departing_rim_plies,
        cross_section(stair.winder_framing.rim_profile).width_m)[0].child_key
    out = []
    spring = _notch_z(z0 + riser * (stair.winder_count + 1), thickness)
    arrival = _notch_z(z0 + riser * risers, thickness)
    depth = cross_section(stair.stringer_profile).depth_m
    for index, cross in enumerate(_stringer_offsets(
            width, _spacing(stair), cross_section(stair.stringer_profile).width_m)):
        a = (inside[0], inside[1] + cross)
        b = (a[0] + tread * straight_treads, a[1])
        if straight_treads:
            out.append(FramedMember(
                stair.uid, f"stringer-{index}", "stringer", stair.stringer_profile,
                a, b, spring - depth, spring, math.hypot(tread, riser) * straight_treads,
                z0_end_m=arrival - depth, z1_end_m=arrival,
                connection=f"winder-box-rim:{departing_rim}",
                start_connection=f"winder-box-rim:{departing_rim}"))
    rim = next(m for m in boxes if m.child_key == departing_rim)
    steel_thickness = .125 * .0254
    stringer_width = cross_section(stair.stringer_profile).width_m
    for member in tuple(out):
        bottom, top = max(member.z0_m, rim.z0_m), min(member.z1_m, rim.z1_m)
        if top <= bottom:
            raise ValueError("straight stringer has no attachment depth at the departing rim")
        a = (member.p0[0] + steel_thickness / 2, member.p0[1] - stringer_width / 2)
        b = (a[0], member.p0[1] + stringer_width / 2)
        out.append(FramedMember(
            stair.uid, f"hanger-winder-{member.child_key}", "hanger",
            f"0.125x{(top - bottom) / .0254:g}", a, b, bottom, top, stringer_width,
            material="steel", connection=f"winder-box-rim:{departing_rim}"))
    rear_fit = stair.riser_thickness.meters if stair.riser_thickness else 0.0
    for index in range(stair.winder_count):
        top = z0 + riser * (index + 1)
        leading = layout.riser_lines[index]
        nose = shifted_line(leading, layout.normals[index], -nosing)
        panel = layout.panel(index, nosing, rear_fit)
        # Extend the edge to its physical wall/well intersections after the nose shift.
        nose = physical_nosing_line(panel, layout.normals[index])
        out.append(FramedMember(
            stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
            *leading, top - thickness, top, math.dist(*leading),
            plan_outline=polygon_ring(panel), riser_line=leading, nosing_line=nose))
        riser_member = _riser_member(
            stair, f"riser-winder-{index:03d}", leading, layout.normals[index],
            z0 + riser * index, top - thickness)
        if riser_member:
            out.append(riser_member)
    profile = _tread_board_profile(tread_depth, thickness)
    for index in range(straight_treads):
        centre = inside[0] + tread * index + (tread - nosing) / 2
        top = z0 + riser * (index + stair.winder_count + 1)
        face = ((inside[0] + tread * index, inside[1]),
                (outside[0] + tread * index, outside[1]))
        out.append(FramedMember(
            stair.uid, f"tread-{index:03d}", "tread", profile,
            (centre, inside[1]), (centre, outside[1]), top - thickness, top, width,
            riser_line=face, nosing_line=shifted_line(face, (1.0, 0.0), -nosing)))
    out.extend(_tread_risers(stair, [member for member in out if member.category == "tread"],
                              riser, tread))
    if not straight_treads:
        end = _riser_member(stair, "riser-winder-head", layout.riser_lines[-1],
                            layout.normals[-1], z0 + riser * stair.winder_count,
                            z0 + riser * risers - thickness)
        if end:
            out.append(end)
    out.extend(boxes)
    post_section = cross_section(stair.newel_profile)
    # The post stands beside the departing lane, with both faces outside clear width.
    # It attaches to the departing rim; it never substitutes for the well boundary.
    post = (inside[0] + post_section.width_m / 2,
            inside[1] - post_section.depth_m / 2)
    post_top = z0 + riser * stair.winder_count
    post_base = z0 if supporting_floor_m is None else supporting_floor_m
    out.append(FramedMember(
        stair.uid, "newel-000", "newel", stair.newel_profile, post, post,
        post_base, post_top, post_top - post_base, orient=(1.0, 0.0),
        connection=f"winder-box-rim:{departing_rim}"))
    return tuple(replace(
        member, p0=point(member.p0), p1=point(member.p1),
        orient=vector(member.orient) if member.orient else None,
        plan_outline=[point(p) for p in member.plan_outline] if member.plan_outline else None,
        riser_line=tuple(point(p) for p in member.riser_line) if member.riser_line else None,
        nosing_line=tuple(point(p) for p in member.nosing_line) if member.nosing_line else None,
    ) for member in out)
