"""Dimensioned exposed metal skins, shared by model.json and glTF.

The profiles here follow MBCI's BBD75-1212 and Metal Sales' PBR and 7/8 inch Corrugated
section drawings. The nominal envelope is measured from the support; concealed fastening
legs and screws are omitted. Horizontal panel joint design is separate.

References:
- https://www.mbci.com/products/board-and-batten-bbd75-1212-wall-panel/
- https://www.metalsales.us.com/wp-content/uploads/2026/02/PBR-Panel-Installation-Guide-02-2026.pdf
- https://www.metalsales.us.com/wp-content/uploads/2026/03/78-Corrugated_3-2026.pdf
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.geometry_prims import (
    _arch_soffit_sample,
    _arch_soffit_segment_count,
    arch_soffit_circle,
)
from typehaus.resolve.geometry_walls import cuts_layer, wall_top_at
from typehaus.resolve.panel_support import panel_support_clearance_m
from typehaus.resolve.surface_clipping import (
    CLIP_TOLERANCE_M,
    clip_faces,
    mesh_from_faces,
    subtract_convex,
)
from typehaus.triangulation import planar_ring_triangles


@dataclass(frozen=True)
class MetalSkinProfile:
    key: str
    pitch_m: float
    depth_m: float
    sheet_thickness_m: float
    section_points_m: tuple[tuple[float, float], ...]
    crown_width_m: float | None = None


INCH_M = 0.0254
SHEET_24_GA_M = 0.00060706  # nominal 24 ga base steel, .0239 inch
PROFILE_DEPTH_TOLERANCE_M = 1e-6
SECTION_MITER_TOLERANCE = 1e-8
MAX_SECTION_MITER_RATIO = 4.0
CORRUGATED_SEGMENTS_PER_WAVE = 24


def _board_batten_profile() -> MetalSkinProfile:
    pitch, depth, crown, sheet = 0.3048, 0.01905, 0.0508, SHEET_24_GA_M
    return MetalSkinProfile(
        "board-and-batten",
        pitch,
        depth,
        sheet,
        (
            (-pitch / 2, sheet),
            (-crown / 2, sheet),
            (-crown / 2, depth),
            (crown / 2, depth),
            (crown / 2, sheet),
            (pitch / 2, sheet),
        ),
        crown,
    )


BBD75_PROFILE = _board_batten_profile()


def _pbr_section() -> tuple[tuple[float, float], ...]:
    """Trace the scaled PBR cross-section drawing, including its two minor ribs per pan."""
    pitch, depth, sheet = 12 * INCH_M, 1.25 * INCH_M, SHEET_24_GA_M
    # The current profile sheet dimensions the 12 inch major-rib rhythm and 1-1/4 inch
    # height. Crown/base widths and the minor ribs' roughly 1/4 inch rise are traced
    # proportionally from its section drawing; those smaller features have no callouts.
    features = []
    for center in (-4 * INCH_M, 0.0, 4 * INCH_M):
        major = center == 0.0
        base_half = (1.5 if major else 0.5) * INCH_M
        crown_half = (0.5 if major else 0.1875) * INCH_M
        height = depth if major else sheet + 0.25 * INCH_M
        features.extend(
            (
                (center - base_half, sheet),
                (center - crown_half, height),
                (center + crown_half, height),
                (center + base_half, sheet),
            )
        )
    points = [(-pitch / 2, sheet), *features, (pitch / 2, sheet)]
    return tuple(sorted(points))


PBR_PROFILE = MetalSkinProfile(
    "ribbed-panel",
    12 * INCH_M,
    1.25 * INCH_M,
    SHEET_24_GA_M,
    _pbr_section(),
)


def _corrugated_section() -> tuple[tuple[float, float], ...]:
    """Sample the manufacturer's sinusoidal 7/8 inch wall profile at a named resolution."""
    pitch, depth, sheet = (8 / 3 * INCH_M, 7 / 8 * INCH_M, SHEET_24_GA_M)
    return tuple(
        (
            -pitch / 2 + pitch * index / CORRUGATED_SEGMENTS_PER_WAVE,
            sheet
            + (depth - sheet)
            * (1 + math.cos(2 * math.pi * (index / CORRUGATED_SEGMENTS_PER_WAVE - 0.5)))
            / 2,
        )
        for index in range(CORRUGATED_SEGMENTS_PER_WAVE + 1)
    )


CORRUGATED_PROFILE = MetalSkinProfile(
    "corrugated",
    8 / 3 * INCH_M,
    7 / 8 * INCH_M,
    SHEET_24_GA_M,
    _corrugated_section(),
)

PANEL_PROFILES = {
    profile.key: profile for profile in (BBD75_PROFILE, PBR_PROFILE, CORRUGATED_PROFILE)
}
PROFILE_DEPTH_LABELS = {
    "board-and-batten": "3/4 inch",
    "ribbed-panel": "1-1/4 inch",
    "corrugated": "7/8 inch",
}


def _polygon_planes(ring):
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1], strict=True))
    ring = ring if area > 0 else list(reversed(ring))
    return [
        (b[1] - a[1], a[0] - b[0], 0.0, (b[1] - a[1]) * a[0] + (a[0] - b[0]) * a[1])
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True)
    ]


def _convex_footprints(ring):
    planes = _polygon_planes(ring)
    if all(all(a * x + b * y <= d + CLIP_TOLERANCE_M for x, y in ring) for a, b, _, d in planes):
        return [planes]
    return [
        _polygon_planes([ring[i] for i in tri])
        for tri in planar_ring_triangles([(x, y, 0.0) for x, y in ring])
    ]


def _opening_planes(wall, opening, project):
    (ax, ay), (bx, by) = wall.axis
    length = math.hypot(bx - ax, by - ay)
    center = project(
        (
            ax + (bx - ax) * opening.center_along_m / length,
            ay + (by - ay) * opening.center_along_m / length,
        )
    )[0]
    half = opening.width_m / 2
    bottom = wall.base_ref_z_m + opening.sill_m
    top = bottom + opening.height_m
    rise = opening.arch_rise_m
    ring = [(center - half, bottom), (center + half, bottom)]
    if rise > CLIP_TOLERANCE_M:
        spring = top - rise
        radius, angle, depth = arch_soffit_circle(half, rise)
        count = _arch_soffit_segment_count(radius, angle)
        ring.extend(
            (center + offset, spring + height)
            for offset, height in (
                _arch_soffit_sample(i, count, radius, angle) for i in range(count, -1, -1)
            )
        )
    else:
        ring.extend(((center + half, top), (center - half, top)))
    # The polygon lives in along/elevation, with no restriction across the skin.
    return [(a, 0.0, b, d) for a, b, _, d in _polygon_planes(ring)]


def _section_ribbon_faces(a, b, inner_a, inner_b, z0, z1):
    """The two sheet faces for one straight section span.

    Adjacent section spans share their fold edge. Closing a prism around every span
    duplicates those internal edges throughout the export; clipping adds the small cut faces
    where an opening, rake, or footprint actually exposes the sheet thickness.
    """
    ao, bo, ai, bi = a, b, inner_a, inner_b
    a0, a1 = (*ao, z0), (*ao, z1)
    b0, b1 = (*bo, z0), (*bo, z1)
    ia0, ia1 = (*ai, z0), (*ai, z1)
    ib0, ib1 = (*bi, z0), (*bi, z1)
    return [
        [a0, a1, b1, b0],  # exposed face
        [ia0, ib0, ib1, ia1],  # reverse face
    ]


def _inset_section(points, thickness):
    segment_normals = []
    for a, b in zip(points, points[1:], strict=False):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= CLIP_TOLERANCE_M:
            raise ValueError("Metal panel profile contains a zero-length section")
        segment_normals.append((-dy / length, dx / length))
    inset = []
    for index, point in enumerate(points):
        if index == 0:
            normal = segment_normals[0]
        elif index == len(points) - 1:
            normal = segment_normals[-1]
        else:
            before, after = segment_normals[index - 1], segment_normals[index]
            total = (before[0] + after[0], before[1] + after[1])
            magnitude = math.hypot(*total)
            if magnitude <= SECTION_MITER_TOLERANCE:
                normal = after
            else:
                bisector = (total[0] / magnitude, total[1] / magnitude)
                projection = bisector[0] * after[0] + bisector[1] * after[1]
                miter_ratio = min(
                    MAX_SECTION_MITER_RATIO, 1 / max(projection, SECTION_MITER_TOLERANCE)
                )
                normal = (bisector[0] * miter_ratio, bisector[1] * miter_ratio)
        inset.append((point[0] - thickness * normal[0], point[1] - thickness * normal[1]))
    return inset


def profile_mesh(
    wall,
    polygon,
    z0,
    z1,
    datum,
    *,
    openings=(),
    layer_name=None,
    lower_at=None,
    upper_at=None,
    height_breakpoints=(),
    profile=BBD75_PROFILE,
    support_clearance_m=0.0,
) -> GMesh:
    """Fold and clip a skin in a facade's stable (along, outward, elevation) frame."""
    if z1 - z0 <= CLIP_TOLERANCE_M:
        return GMesh((), (), ())
    if len(polygon) < 3:
        raise ValueError(f"{wall.tag}: invalid siding footprint")
    (ox, oy), (ex, ey) = datum
    run = math.hypot(ex - ox, ey - oy)
    if run <= CLIP_TOLERANCE_M:
        raise ValueError(f"{wall.tag}: degenerate siding datum")
    ux, uy = (ex - ox) / run, (ey - oy) / run
    nx, ny = -uy, ux
    # The stack, rather than the run's direction, determines the exterior side.
    inner, outer = wall.layers[0].polygon, wall.layers[-1].polygon

    def mean_across(ring):
        return sum((x - ox) * nx + (y - oy) * ny for x, y in ring) / len(ring)

    if mean_across(outer) < mean_across(inner):
        nx, ny = -nx, -ny

    def project(p):
        return ((p[0] - ox) * ux + (p[1] - oy) * uy, (p[0] - ox) * nx + (p[1] - oy) * ny)

    def world(p):
        return (ox + ux * p[0] + nx * p[1], oy + uy * p[0] + ny * p[1], p[2])

    ring = [project(p) for p in polygon]
    low, high = min(s for s, _ in ring), max(s for s, _ in ring)
    support = min(n for _, n in ring)
    crown = max(n for _, n in ring)
    if abs(crown - support - profile.depth_m) > PROFILE_DEPTH_TOLERANCE_M:
        raise ValueError(
            f"{wall.tag}: {profile.key} skin envelope must be "
            f"{PROFILE_DEPTH_LABELS.get(profile.key, f'{profile.depth_m:.6f} m')} deep"
        )
    footprints = _convex_footprints(ring)
    holes = [
        _opening_planes(wall, op, project) for op in openings if cuts_layer(wall, layer_name, op)
    ]
    stations = sorted(
        {low, high, *(project(p)[0] for p in height_breakpoints if low < project(p)[0] < high)}
    )
    height_regions = []
    for start, end in zip(stations[:-1], stations[1:], strict=True):
        planes = [(1.0, 0.0, 0.0, end), (-1.0, 0.0, 0.0, -start)]
        for at, lower in ((lower_at, True), (upper_at, False)):
            if at is None:
                continue
            a, b = world((start, 0.0, 0.0)), world((end, 0.0, 0.0))
            za, zb = at(a[0], a[1]), at(b[0], b[1])
            slope = (zb - za) / (end - start)
            plane = (-slope, 0.0, 1.0, za - slope * start)
            planes.append(tuple(-v for v in plane) if lower else plane)
        height_regions.append(planes)
    pieces = []
    relief_depth = profile.depth_m - profile.sheet_thickness_m
    if not 0 <= support_clearance_m < relief_depth:
        raise ValueError(f"{wall.tag}: concealed flashing exceeds the {profile.key} skin envelope")
    # Thin sheet seats over the concealed laps. Relieve the shallow folds continuously
    # through wall and closure, keeping the crown and the nominal stack depth fixed.
    section = tuple(
        (s, depth + support_clearance_m * (profile.depth_m - depth) / relief_depth)
        for s, depth in profile.section_points_m
    )
    inset = _inset_section(section, profile.sheet_thickness_m)
    half = profile.pitch_m / 2
    for station in range(
        math.floor((low - half) / profile.pitch_m), math.ceil((high + half) / profile.pitch_m) + 1
    ):
        center = station * profile.pitch_m
        for index, (a, b) in enumerate(zip(section, section[1:], strict=False)):
            s0, s1 = center + a[0], center + b[0]
            if s1 <= low or s0 >= high:
                continue
            outer_a, outer_b = (s0, support + a[1]), (s1, support + b[1])
            inner_a = (center + inset[index][0], support + inset[index][1])
            inner_b = (center + inset[index + 1][0], support + inset[index + 1][1])
            for footprint in footprints:
                for height_planes in height_regions:
                    faces = _section_ribbon_faces(
                        outer_a,
                        outer_b,
                        inner_a,
                        inner_b,
                        z0,
                        z1,
                    )
                    for plane in footprint + height_planes:
                        faces = clip_faces(faces, plane)
                        if not faces:
                            break
                    fragments = [faces] if faces else []
                    for hole in holes:
                        fragments = [
                            part
                            for fragment in fragments
                            for part in subtract_convex(fragment, hole)
                        ]
                    pieces.extend(fragments)
    return mesh_from_faces(pieces, world, ux * ny - uy * nx < 0)


def resolve_profiled_metal_surfaces(model) -> None:
    """Attach declared panel-profile meshes after openings, bands and roof closures resolve."""
    finishes = {material.tag: material.finish for material in model.plan.library.materials}
    lines = {
        member.wall_tag: (
            line.origin,
            (line.origin[0] + line.direction[0], line.origin[1] + line.direction[1]),
        )
        for line in model.layout_lines
        for member in line.members
    }
    walls = {wall.uid: wall for wall in model.walls}
    support_clearances = {}

    def profile_for(ref):
        return PANEL_PROFILES.get(finishes.get(ref))

    for i, wall in enumerate(model.walls):
        layers = []
        for layer in wall.layers:
            profile = profile_for(layer.material_ref)
            if profile is not None and not layer.is_cavity:
                z0, z1 = layer.band(wall)
                clearance = panel_support_clearance_m(model, wall, layer)
                support_clearances[wall.uid, layer.material_ref] = clearance
                mesh = profile_mesh(
                    wall,
                    layer.polygon,
                    z0,
                    z1,
                    lines.get(wall.tag, wall.axis),
                    openings=[op for op in model.openings if op.host_wall == wall.tag],
                    layer_name=layer.name,
                    upper_at=lambda x, y, w=wall: wall_top_at(w, x, y),
                    height_breakpoints=wall.axis,
                    profile=profile,
                    support_clearance_m=clearance,
                )
                layer = replace(layer, surface_mesh=mesh)
            layers.append(layer)
        model.walls[i] = replace(wall, layers=tuple(layers))
    for i, roof in enumerate(model.roofs):
        members = []
        for member in roof.members:
            wall = walls.get(member.parent_uid)
            profile = profile_for(member.material)
            if wall and member.category == "cladding" and profile is not None:
                box = member_box(member)
                if box is None:
                    raise ValueError(f"{member.child_key}: invalid cladding closure")
                polygon = [(x, y) for x, y, _ in box.corners_bottom]
                dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
                length2 = dx * dx + dy * dy

                def height(x, y, start, end, member=member, dx=dx, dy=dy, length2=length2):
                    t = ((x - member.p0[0]) * dx + (y - member.p0[1]) * dy) / length2
                    return start + t * ((start if end is None else end) - start)

                mesh = profile_mesh(
                    wall,
                    polygon,
                    min(p[2] for p in box.corners_bottom),
                    max(p[2] for p in box.corners_top),
                    lines.get(wall.tag, wall.axis),
                    lower_at=lambda x, y, h=height, m=member: h(x, y, m.z0_m, m.z0_end_m),
                    upper_at=lambda x, y, h=height, m=member: h(x, y, m.z1_m, m.z1_end_m),
                    profile=profile,
                    support_clearance_m=support_clearances[wall.uid, member.material],
                )
                member = replace(member, surface_mesh=mesh)
            members.append(member)
        model.roofs[i] = replace(roof, members=tuple(members))


# Kept as an import alias for the focused BBD75 tests and downstream callers.
resolve_board_batten_surfaces = resolve_profiled_metal_surfaces
