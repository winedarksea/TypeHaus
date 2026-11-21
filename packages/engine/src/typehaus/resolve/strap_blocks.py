"""A through-panel pipe strap's laminated cellular-PVC block (decision #142).

The block bears on the pan (between battens, behind the crowns), ``StrapBlockRow.width``
wide, and stands out to the held pipe's back: its depth is the row's, or less where the pipe
sits closer to the wall (a leader 2 1/2" off the crowns). It sits level on the girt course it
reaches; one whose top would reach the wall's top line is cut parallel to it, under the rake
trim's hem.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.resolve.mount_blocks import (
    ResolvedMountBlock,
    _xy,
    station_of,
    wall_face_frame,
)

#: Least block worth laminating: one ply of the sheet.
_MIN_DEPTH_M = 0.75 * 0.0254


def strap_blocks(model: Any, standard: Any) -> list[ResolvedMountBlock]:
    from typehaus.model.enums import ConnectorKind
    from typehaus.resolve.framing.furring import STRAPPING_CATEGORY
    from typehaus.resolve.geometry_walls import body_top_at
    from typehaus.resolve.panel_flats import cladding_layer, panel_profile

    row = standard.strap_block
    if row is None:
        return []
    out = []
    for el in model.plan.all_elements():
        if el.element_kind != "Connector" or el.kind != ConnectorKind.PIPE_STRAP:
            continue
        wall = next((model.wall(ref) for ref in el.connects if model.wall(ref) is not None
                     and cladding_layer(model, model.wall(ref)) is not None), None)
        if wall is None or el.position is None or el.elevation is None:
            continue
        origin, tangent, normal = wall_face_frame(wall)
        profile = panel_profile(model, wall)
        back = -(profile.depth_m - profile.sheet_thickness_m)
        xy = el.position.xy_m
        centre_n = (xy[0] - origin[0]) * normal[0] + (xy[1] - origin[1]) * normal[1]
        radius = held_radius(model, el, normal)
        depth = row.depth.meters
        if radius is not None:
            depth = max(_MIN_DEPTH_M, min(depth, centre_n - radius - back))
        station = station_of(wall, xy)
        z = el.elevation.meters
        half, height = row.max_width.meters / 2, row.height.meters
        lo, hi = station - half, station + half
        z0 = z - height / 2
        # Level on the girt course it reaches: its bottom on the course's.
        course = next((m for m in wall.members if m.category == STRAPPING_CATEGORY
                       and m.z0_m - 1e-6 <= z <= m.z0_m + height - 0.0127
                       and m.z0_m >= z - height), None)
        if course is not None:
            z0 = course.z0_m
        z1 = z0 + height
        drop = row.rake_hem_drop.meters + row.rake_clearance.meters
        cut = tuple(body_top_at(wall, *_xy(origin, tangent, s)) - drop for s in (lo, hi))
        top_z = cut if min(cut) < z1 else None
        out.append(ResolvedMountBlock(
            uid=f"{el.uid}-block", tag=f"MB-{el.tag}", kind="strap_block",
            wall_tag=wall.tag, storey=wall.storey, holds=(el.tag,), station_lo_m=lo,
            station_hi_m=hi, z0_m=z0, z1_m=max(top_z) if top_z else z1, depth_m=depth,
            origin=origin, tangent=tangent, normal=normal, product=row.product_ref,
            material=row.material_ref, top_z=top_z, back_n_m=back))
    return out


def held_radius(model: Any, connector: Any, normal: tuple[float, float]) -> float | None:
    """Half the held pipe's depth off the wall: the nearest run's OD, else its solid's."""
    from typehaus.resolve.mep_envelopes import run_polylines, run_radii

    held = connector.connects[0] if connector.connects else None
    if held is None:
        return None
    xy = connector.position.xy_m
    near = [(min(math.dist(xy, p) for p in path), tag)
            for _kind, tag, path, _z in run_polylines(model)
            if (tag == held or tag.startswith(f"{held}-")) and path]
    if near:
        return run_radii(model)[min(near)[1]]
    solid = next((s for s in model.solids if s.tag == held and s.outline), None)
    if solid is None:
        return None
    across = [x * normal[0] + y * normal[1] for x, y in solid.outline]
    return (max(across) - min(across)) / 2
