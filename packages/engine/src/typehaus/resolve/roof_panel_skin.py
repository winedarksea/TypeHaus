"""Fold declared roof panels in a shared ridge datum, then clip their sheet edges."""

import math
from dataclasses import replace
from functools import lru_cache

from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_roofs import _face_normal, layer_inset_rect, plane_triangles
from typehaus.resolve.metal_skin_profiles import (
    PANEL_PROFILES,
    PROFILE_DEPTH_TOLERANCE_M,
    _inset_section,
    _section_ribbon_faces,
)
from typehaus.resolve.roof_image_ii_pan_end import (
    image_ii_pan_ends,
    wrapped_eave_skin_setbacks,
)
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.roof_panel_hem import roof_pan_hems
from typehaus.resolve.surface_clipping import clip_faces, cross, dot, mesh_from_faces


def profiled_roof_layers(roof, model):
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    setbacks = {entry["layer"]: entry for entry in roof.layer_edge_setbacks}
    finishes = {material.tag: material.finish for material in model.plan.library.materials}
    base = 0.0
    for layer in above_structure_layers(assembly):
        profile = PANEL_PROFILES.get(finishes.get(layer.material_ref))
        if profile is not None:
            entry = setbacks.get(layer.name, {})
            if profile.key == "standing-seam":
                entry = wrapped_eave_skin_setbacks(model, roof, entry)
            rect = layer_inset_rect(roof, entry, base)
            yield layer, base, rect, profile
        base += layer.thickness.meters


def panel_stations(low, high, pitch):
    """Seams share the rectangle centre datum on both slopes, including partial end pans."""
    center = (low + high) / 2
    return tuple(
        center + index * pitch
        for index in range(
            math.ceil((low - center) / pitch), math.floor((high - center) / pitch) + 1
        )
    )


def seam_stations(roof, model) -> tuple[float, ...]:
    for _, _, rect, profile in profiled_roof_layers(roof, model):
        low, high = rect[:2] if roof.ridge_direction == "x" else rect[2:]
        return panel_stations(low, high, profile.pitch_m)
    return ()


def roof_profile_mesh(roof, rect, base, profile):
    """Local coordinates are (along ridge, normal depth, fall-line distance)."""
    along_x = roof.ridge_direction == "x"
    low, high = rect[:2] if along_x else rect[2:]
    triangles = tuple(tuple(tuple(p) for p in tri) for tri in plane_triangles(roof, rect))
    ridge = None
    if roof.form != "shed":
        across = 1 if along_x else 0
        ridge = (
            min(p[across] for p in roof.footprint) + max(p[across] for p in roof.footprint)
        ) / 2
    positions, faces, normals = [], [], []
    # Two triangles describe each rectangular plane; never split a seam on their diagonal.
    for triangle_index in range(0, len(triangles), 2):
        mesh = _roof_plane_mesh(triangles[triangle_index : triangle_index + 2], along_x,
                                low, high, base, ridge, profile.section_points_m,
                                profile.sheet_thickness_m, profile.pitch_m)
        offset = len(positions)
        positions.extend(mesh.positions)
        normals.extend(mesh.normals)
        faces.extend(tuple(offset + i for i in tri) for tri in mesh.triangles)
    return GMesh(tuple(positions), tuple(faces), tuple(normals))


@lru_cache(maxsize=64)
def _roof_plane_mesh(pair, along_x, low, high, base, ridge, section, sheet_thickness_m,
                     pitch_m) -> GMesh:
    """One roof plane's folded sheet, a pure function of numbers (→ board_batten._fold)."""
    along = (1.0, 0.0, 0.0) if along_x else (0.0, 1.0, 0.0)
    anchor = (low + high) / 2
    triangle = pair[0]
    normal = _face_normal(triangle)
    fall = cross(along, normal)
    if fall[2] > 0:
        fall = tuple(-v for v in fall)
    origin = triangle[0]

    def world(point):
        u, depth, v = point
        return tuple(
            origin[i]
            + along[i] * (u - dot(origin, along))
            + normal[i] * (base + depth)
            + fall[i] * v
            for i in range(3)
        )

    # Vertical rake/ridge planes and deck-normal eave planes match the band perimeter.
    corners = {p for tri in pair for p in tri}
    fall_values = [dot(tuple(p[i] - origin[i] for i in range(3)), fall) for p in corners]
    v_low, v_high = min(fall_values), max(fall_values)
    planes = [
        (1.0, 0.0, 0.0, high),
        (-1.0, 0.0, 0.0, -low),
        (0.0, 0.0, 1.0, v_high),
        (0.0, 0.0, -1.0, -v_low),
    ]
    if ridge is not None:
        across = 1 if along_x else 0
        sign = 1.0 if normal[across] < 0 else -1.0
        # Replace the high-end plane with a vertical ridge cut through the miter.
        ridge_plane = (
            0.0,
            sign * normal[across],
            sign * fall[across],
            sign * (ridge - origin[across] - normal[across] * base),
        )
        planes = [*planes[:3], ridge_plane]
    inset = _inset_section(section, sheet_thickness_m)
    pieces = []
    for station in range(
        math.floor((low - anchor) / pitch_m) - 1,
        math.ceil((high - anchor) / pitch_m) + 1,
    ):
        center = anchor + station * pitch_m
        for index, (a, b) in enumerate(zip(section, section[1:], strict=False)):
            if center + b[0] < low or center + a[0] > high:
                continue
            ao, bo = (center + a[0], a[1]), (center + b[0], b[1])
            ai, bi = (
                (center + inset[index][0], inset[index][1]),
                (center + inset[index + 1][0], inset[index + 1][1]),
            )
            ribbon = _section_ribbon_faces(ao, bo, ai, bi, v_low - 1, v_high + 1)
            for plane in planes:
                ribbon = clip_faces(ribbon, plane)
            if ribbon:
                pieces.append(ribbon)
    return mesh_from_faces(pieces, world, dot(cross(along, normal), fall) < 0)


def resolve_profiled_roof_surfaces(model):
    for index, roof in enumerate(model.roofs):
        meshes = []
        hems = ()
        for layer, base, rect, profile in profiled_roof_layers(roof, model):
            if abs(layer.thickness.meters - profile.depth_m) > PROFILE_DEPTH_TOLERANCE_M:
                raise ValueError(
                    f"{roof.tag}: {profile.key} roofing envelope must match profile depth"
                )
            meshes.append((layer.name, roof_profile_mesh(roof, rect, base, profile)))
            if profile.key == "standing-seam":
                wrapped, ends = image_ii_pan_ends(model, roof, rect, profile, layer.material_ref)
                hems += roof_pan_hems(roof, rect, base, profile, layer.material_ref,
                                      skip=wrapped) + ends
        model.roofs[index] = replace(roof, layer_surface_meshes=tuple(meshes),
                                     members=roof.members + hems)
