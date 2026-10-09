"""Dimensioned winder plan, platform framing, and a cut through the departing rim."""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.checks.code.mn_residential.stair_winders import winder_measurements
from typehaus.emit.draw.scene import ArchDimension, NamedPoint, Polyline, SceneBuilder, Text
from typehaus.emit.draw.section_clip import clip_polygon
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import CutPlane, slice_solid


def emit_winder_framing(builder, stair, transform=lambda p: tuple(v / M_PER_IN for v in p),
                        tier=None):
    """Actual panel seams and fitted framing outlines, with selectable box tiers."""
    for member in stair.members:
        if member.category not in {"stair_subdeck", "landing_framing", "stringer", "newel"}:
            continue
        if tier is not None and not (member.child_key.startswith(
                (f"stair-subdeck-{tier:03d}-", f"landing-rim-winder{tier}-",
                 f"landing-joist-winder{tier}-"))):
            continue
        from typehaus.resolve.framing.footprint import member_footprint

        ring = member_footprint(member)[0]
        builder.add(Polyline(points=tuple(transform(p) for p in ring), closed=True,
                             layer="S-FRAM", lineweight=.13 if member.category
                             == "stair_subdeck" else .25,
                             linetype="DASHED" if member.category == "stair_subdeck"
                             else "CONTINUOUS", uid=stair.uid, tag=member.child_key))


def build_winder_detail(model, stair_tag):
    stair = next(s for s in model.stairs if s.tag == stair_tag)
    layout = stair.winder_turn
    measured = winder_measurements(stair)
    origin = layout.riser_lines[0][1]
    run, cross = layout.normals[-1], layout.normals[0]

    def local(point, offset=(0.0, 0.0)):
        x, y = point[0] - origin[0], point[1] - origin[1]
        return (offset[0] + (x * run[0] + y * run[1]) / M_PER_IN,
                offset[1] + (x * cross[0] + y * cross[1]) / M_PER_IN)

    b = SceneBuilder(name=f"winder-{stair.tag}", units="in")
    winders = sorted((m for m in stair.members if m.category == "winder"),
                     key=lambda m: m.z1_m)
    extent = max(local(p)[0] for p in layout.footprint)
    pitch = extent + 18
    for member in winders:
        ring = tuple(local(p) for p in member.plan_outline)
        b.add(Polyline(points=ring, closed=True, layer="A-STAIR", uid=stair.uid,
                       tag=member.child_key))
        centroid = Polygon(ring).centroid
        index = winders.index(member)
        b.add(Text(anchor=(centroid.x, centroid.y), content=f"W{index + 1}", height=2,
                   align="center"))
    points = measured.walkline_points
    centre = local(measured.centre)
    angles = [math.atan2(local(p)[1] - centre[1], local(p)[0] - centre[0]) for p in points]
    # Unwrap the turn so the walkline draws one continuous concentric arc.
    for index in range(1, len(angles)):
        while angles[index] - angles[index - 1] > math.pi:
            angles[index] -= 2 * math.pi
        while angles[index] - angles[index - 1] < -math.pi:
            angles[index] += 2 * math.pi
    radius = measured.radius_m / M_PER_IN
    arc = tuple((centre[0] + radius * math.cos(angles[0] + (angles[-1] - angles[0]) * i / 60),
                 centre[1] + radius * math.sin(angles[0] + (angles[-1] - angles[0]) * i / 60))
                for i in range(61))
    b.add(Polyline(points=arc, layer="A-ANNO-DIMS", linetype="DASHED"))
    for index, (a, c) in enumerate(zip(points, points[1:], strict=False)):
        p0, p1 = local(a), local(c)
        b.add(ArchDimension(kind="aligned", ends=(NamedPoint(xy=p0), NamedPoint(xy=p1)),
                            p0=p0, p1=p1, offset=3,
                            text=f'W{index + 1} '
                                 f'{measured.walkline_depths_m[index] / M_PER_IN:.3f}"'))
    b.add(Text(anchor=(0, extent + 6), content=f"{stair.tag} — FINISHED OAK / 12-INCH WALKLINE",
               height=2))
    b.add(Text(anchor=(0, -8), content="W1–W3: " + ", ".join(
        f'{v / M_PER_IN:.3f}"' for v in measured.walkline_depths_m), height=1.5))
    b.add(Text(anchor=(0, -12), content="MINIMUM CLEAR DEPTH: " + ", ".join(
        f'{v / M_PER_IN:.3f}"' for v in measured.narrow_depths_m), height=1.5))
    for tier in range(stair.winder_count):
        offset = (pitch if tier == 0 else (tier - 1) * pitch,
                  0 if tier == 0 else -pitch - 12)
        emit_winder_framing(b, stair, lambda p, offset=offset: local(p, offset), tier)
        b.add(Text(anchor=(offset[0], offset[1] + extent + 6),
                   content=f"BOX {tier + 1}: RIMS / BLOCKING / PLYWOOD SEAM", height=2))
    # The section uses the shared 3D member solids, including the straight-stringer seat.
    final = layout.riser_lines[-1]
    midpoint = tuple((a + c) / 2 for a, c in zip(*final, strict=True))
    direction = "x" if abs(run[0]) > .5 else "y"
    plane = CutPlane(axis=direction, station_m=midpoint[1 if direction == "x" else 0])
    station_origin = midpoint[0 if direction == "x" else 1]
    for member in stair.members:
        solid = member_solid(member)
        if solid is None:
            continue
        for profile in slice_solid(solid, plane):
            ring = clip_polygon(profile.outline,
                                ((station_origin - 24 * M_PER_IN,
                                  stair.base_elevation_m - M_PER_IN),
                                 (station_origin + extent * M_PER_IN,
                                  stair.base_elevation_m + 45 * M_PER_IN)))
            if ring:
                b.add(Polyline(points=tuple((pitch * 2 + 24 + (u - station_origin) / M_PER_IN,
                                             (z - stair.base_elevation_m) / M_PER_IN)
                                            for u, z in ring), closed=True, layer="S-FRAM"))
    b.add(Text(anchor=(pitch * 2 - 24, -8), content="DEPARTING RIM / STRINGER CONNECTION",
               height=2))
    b.add(Text(anchor=(0, -pitch - 30), content='1" OAK; 3/4" STRUCTURAL PLYWOOD; '
               'RIPPED 2x8; SUPPORTS ≤16"; DOUBLE DEPARTING RIM', height=1.5))
    b.add(Text(anchor=(0, -pitch - 34), content="UPPER BOXES BEAR ON PLYWOOD; "
               "FIRST BOX / NEWEL BEAR ON REINFORCED FLOOR", height=1.5))
    return b.build()
