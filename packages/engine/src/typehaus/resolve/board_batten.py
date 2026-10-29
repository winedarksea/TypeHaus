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
from dataclasses import replace
from functools import lru_cache

from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.geometry_prims import (
    _arch_soffit_sample,
    _arch_soffit_segment_count,
    arch_soffit_circle,
)
from typehaus.resolve.geometry_walls import body_top_at, cuts_layer

# Re-export existing names for downstream panel callers.
from typehaus.resolve.metal_skin_profiles import (  # noqa: F401 — compatibility exports
    BBD75_PROFILE,
    CORRUGATED_PROFILE,
    INCH_M,
    PANEL_PROFILES,
    PBR_PROFILE,
    PROFILE_DEPTH_LABELS,
    PROFILE_DEPTH_TOLERANCE_M,
    SHEET_24_GA_M,
    MetalSkinProfile,
    _inset_section,
    _section_ribbon_faces,
)
from typehaus.resolve.panel_support import panel_support_clearance_m
from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate
from typehaus.resolve.surface_clipping import (
    CLIP_TOLERANCE_M,
    clip_faces,
    mesh_from_faces,
    subtract_convex,
)
from typehaus.triangulation import planar_ring_triangles


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


def _opening_cut(wall, opening, project):
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
    planes = [(a, 0.0, b, d) for a, b, _, d in _polygon_planes(ring)]
    return planes, (center - half, center + half, bottom, top)


def _straddled(planes, corners):
    """The planes that cut a ribbon, or None when one misses it entirely.

    A ribbon's faces have only its eight corners for vertices, so a plane every corner is
    inside leaves ``clip_faces`` returning the faces unchanged, and one every corner is
    outside empties them: only the straddlers need clipping.
    """
    cuts = []
    for plane in planes:
        a, b, c, d = plane
        signed = [a * x + b * y + c * z - d for x, y, z in corners]
        if min(signed) > CLIP_TOLERANCE_M:
            return None
        if max(signed) > CLIP_TOLERANCE_M:
            cuts.append(plane)
    return cuts


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
        _opening_cut(wall, op, project)
        for op in openings
        if cuts_layer(wall, layer_name, op)
    ]
    stations = sorted(
        {low, high, *(project(p)[0] for p in height_breakpoints if low < project(p)[0] < high)}
    )
    height_regions = []
    for start, end in zip(stations[:-1], stations[1:], strict=True):
        planes = [(1.0, 0.0, 0.0, end), (-1.0, 0.0, 0.0, -start)]
        uppers = upper_at if isinstance(upper_at, tuple) else (upper_at,)
        for at, lower in ((lower_at, True), *((at, False) for at in uppers)):
            if at is None:
                continue
            a, b = world((start, support, 0.0)), world((end, support, 0.0))
            za, zb = at(a[0], a[1]), at(b[0], b[1])
            slope = (zb - za) / (end - start)
            # The fall across the skin's depth too: an eave closure's top follows the pitch.
            c = world((start, crown, 0.0))
            fall = (at(c[0], c[1]) - za) / (crown - support)
            plane = (-slope, -fall, 1.0, za - slope * start - fall * support)
            planes.append(tuple(-v for v in plane) if lower else plane)
        height_regions.append(planes)
    relief_depth = profile.depth_m - profile.sheet_thickness_m
    if not 0 <= support_clearance_m < relief_depth:
        raise ValueError(f"{wall.tag}: concealed flashing exceeds the {profile.key} skin envelope")
    # Thin sheet seats over the concealed laps. Relieve the shallow folds continuously
    # through wall and closure, keeping the crown and the nominal stack depth fixed.
    section = tuple(
        (s, depth + support_clearance_m * (profile.depth_m - depth) / relief_depth)
        for s, depth in profile.section_points_m
    )
    return _fold(
        tuple(tuple(planes) for planes in footprints),
        tuple(tuple(planes) for planes in height_regions),
        tuple((tuple(planes), box) for planes, box in holes),
        section, profile.sheet_thickness_m, profile.pitch_m,
        low, high, support, z0, z1, (ox, oy, ux, uy, nx, ny),
    )


@lru_cache(maxsize=256)
def _fold(footprints, height_regions, holes, section, sheet_thickness_m, pitch_m,
          low, high, support, z0, z1, frame) -> GMesh:
    """The folded, clipped skin: a pure function of numbers, so a resolve that leaves a
    facade alone (most edits, most test splices) reuses its mesh rather than refolding it."""
    ox, oy, ux, uy, nx, ny = frame

    def world(p):
        return (ox + ux * p[0] + nx * p[1], oy + uy * p[0] + ny * p[1], p[2])

    pieces = []
    inset = _inset_section(section, sheet_thickness_m)
    half = pitch_m / 2
    for station in range(
        math.floor((low - half) / pitch_m), math.ceil((high + half) / pitch_m) + 1
    ):
        center = station * pitch_m
        for index, (a, b) in enumerate(zip(section, section[1:], strict=False)):
            s0, s1 = center + a[0], center + b[0]
            if s1 <= low or s0 >= high:
                continue
            outer_a, outer_b = (s0, support + a[1]), (s1, support + b[1])
            inner_a = (center + inset[index][0], support + inset[index][1])
            inner_b = (center + inset[index + 1][0], support + inset[index + 1][1])
            base = [(*p, z0) for p in (outer_a, outer_b, inner_a, inner_b)]
            corners = base + [(x, y, z1) for x, y, _ in base]
            # Footprint planes have no z term: the four corners at z0 decide them.
            footprint_cuts = [_straddled(footprint, base) for footprint in footprints]
            height_cuts = [_straddled(planes, corners) for planes in height_regions]
            for cuts in footprint_cuts:
                if cuts is None:
                    continue
                for more in height_cuts:
                    if more is None:
                        continue
                    faces = _section_ribbon_faces(
                        outer_a,
                        outer_b,
                        inner_a,
                        inner_b,
                        z0,
                        z1,
                    )
                    for plane in cuts + more:
                        faces = clip_faces(faces, plane)
                        if not faces:
                            break
                    fragments = [faces] if faces else []
                    for hole, (hole_low, hole_high, hole_bottom, hole_top) in holes:
                        if s1 <= hole_low or s0 >= hole_high or z1 <= hole_bottom or z0 >= hole_top:
                            continue
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

    def joint_cuts(wall, layer_name, profile, z0, z1):
        assembly = model.plan.library.resolve_assembly(wall.assembly) if wall.assembly else None
        authored = next((layer for layer in assembly.layers if layer.name == layer_name), None) \
            if assembly else None
        joints = (authored.panel_joint_elevations if authored is not None
                  and profile.key == "board-and-batten" else ())
        return [z0, *sorted({j.meters for j in joints if z0 < j.meters < z1}), z1]

    for i, wall in enumerate(model.walls):
        layers = []
        for layer in wall.layers:
            profile = profile_for(layer.material_ref)
            if profile is not None and not layer.is_cavity:
                z0, z1 = layer.band(wall)
                clearance = panel_support_clearance_m(model, wall, layer)
                support_clearances[wall.uid, layer.material_ref] = clearance
                cuts = joint_cuts(wall, layer.name, profile, z0, z1)
                meshes = [profile_mesh(
                    wall, layer.polygon, bottom, top, lines.get(wall.tag, wall.axis),
                    openings=[op for op in model.openings if op.host_wall == wall.tag],
                    layer_name=layer.name,
                    upper_at=lambda x, y, w=wall: body_top_at(w, x, y),
                    height_breakpoints=wall.axis, profile=profile,
                    support_clearance_m=clearance,
                ) for bottom, top in zip(cuts, cuts[1:], strict=False)]
                mesh = _join_meshes(meshes)
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

                def upper_height(x, y, h=height, m=member, roof=roof):
                    if m.section_ring:
                        return (roof_plane_z(roof, roof_slope_coordinate(roof, (x, y)))
                                + m.z1_m - roof_plane_z(roof, roof_slope_coordinate(roof, m.p0)))
                    return h(x, y, m.z1_m, m.z1_end_m)

                top_bound = max(p[2] for p in box.corners_top)
                if member.section_ring:
                    top_bound = max(top_bound, member.z0_m + max(z for _, z in member.section_ring))
                layer_name = next(layer.name for layer in wall.layers
                                  if layer.material_ref == member.material
                                  and layer.function == "cladding")
                cuts = joint_cuts(wall, layer_name, profile,
                                  min(p[2] for p in box.corners_bottom), top_bound)
                mesh = _join_meshes([profile_mesh(
                    wall, polygon, bottom, top, lines.get(wall.tag, wall.axis),
                    lower_at=lambda x, y, h=height, m=member: h(x, y, m.z0_m, m.z0_end_m),
                    upper_at=(upper_height, *_deck_cut_at(model, roof, member)),
                    profile=profile,
                    support_clearance_m=support_clearances[wall.uid, member.material],
                ) for bottom, top in zip(cuts, cuts[1:], strict=False)])
                member = replace(member, surface_mesh=mesh)
            members.append(member)
        model.roofs[i] = replace(roof, members=tuple(members))


def _deck_cut_at(model, roof, member) -> tuple:
    """Under a wrapped Image II eave, the deck's square-cut end as a second head line for a
    closure band's skin (it oversails the panel's back); else nothing."""
    from typehaus.resolve.roof_image_ii_eave import HEAD_CLEARANCE_M, wrapped_eave_deck_cut

    dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
    along_ridge = abs(dy if roof.ridge_direction == "y" else dx)
    if (abs(math.hypot(dx, dy) - along_ridge) > 1e-6
            or wrapped_eave_deck_cut(model, roof, member.p0) is None):
        return ()  # only an eave wall's band stands under the deck's cut end

    def at(x, y):
        cut = wrapped_eave_deck_cut(model, roof, (x, y), level_inboard=False)
        return math.inf if cut is None else cut[0] - HEAD_CLEARANCE_M

    return (at,)


# Kept as an import alias for the focused BBD75 tests and downstream callers.
resolve_board_batten_surfaces = resolve_profiled_metal_surfaces


def _join_meshes(meshes: list[GMesh]) -> GMesh:
    """Preserve independently capped panel runs in the layer's shared mesh."""
    positions, triangles, normals = [], [], []
    for mesh in meshes:
        offset = len(positions)
        positions.extend(mesh.positions)
        triangles.extend(tuple(index + offset for index in triangle) for triangle in mesh.triangles)
        normals.extend(mesh.normals or ())
    return GMesh(tuple(positions), tuple(triangles), tuple(normals))
