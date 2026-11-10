"""Representative air-terminal metal, separate from conservative fit envelopes.

Local coordinates are face-across, face-up, and depth into the cavity. Catalog dimensions
bound the drawing; blade spacing and metal thickness are visualization defaults only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import triangulate

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes, transform_mesh
from typehaus.resolve.geometry_ir import GMesh


@dataclass(frozen=True)
class TerminalVisualization:
    sheet_m: float = 0.0006
    frame_m: float = 0.0127
    blade_pitch_m: float = 0.0254
    blade_chord_m: float = 0.0127
    blade_angle_degrees: float = 35.0
    disc_radius_ratio: float = 0.76
    facets: int = 48


VISUALIZATION = TerminalVisualization()


def rectangle(width, height):
    return ((-width / 2, -height / 2), (width / 2, -height / 2),
            (width / 2, height / 2), (-width / 2, height / 2))


def circle(diameter, centre=(0.0, 0.0)):
    return tuple((centre[0] + diameter / 2 * math.cos(i * 2 * math.pi / VISUALIZATION.facets),
                  centre[1] + diameter / 2 * math.sin(i * 2 * math.pi / VISUALIZATION.facets))
                 for i in range(VISUALIZATION.facets))


def panel(outer, holes, bottom, top):
    """Closed sheet extrusion with real openings, in metres."""
    polygon = Polygon(outer)
    for hole in holes:
        polygon = polygon.difference(Polygon(hole))
    if not polygon.is_valid or top <= bottom:
        raise ValueError("terminal panel must have valid rings and positive thickness")
    if polygon.is_empty:
        return GMesh(positions=(), triangles=())
    if polygon.geom_type == "MultiPolygon":
        return combine_meshes(*(panel(tuple(p.exterior.coords)[:-1],
                                     tuple(tuple(r.coords)[:-1] for r in p.interiors),
                                     bottom, top) for p in polygon.geoms))
    polygon = orient(polygon, sign=1.0)
    positions, triangles = [], []
    for triangle in triangulate(polygon):
        if not polygon.covers(triangle):
            continue
        corners = tuple(orient(triangle, sign=1.0).exterior.coords)[:3]
        start = len(positions)
        positions.extend((x, y, z) for z in (bottom, top) for x, y in corners)
        triangles.extend(((start, start + 2, start + 1),
                          (start + 3, start + 4, start + 5)))
    for boundary in (polygon.exterior, *polygon.interiors):
        ring = tuple(boundary.coords)[:-1]
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            start = len(positions)
            positions.extend((x, y, z) for (x, y), z in
                             ((a, bottom), (b, bottom), (b, top), (a, top)))
            triangles.extend(((start, start + 1, start + 2),
                              (start, start + 2, start + 3)))
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def block(x0, y0, z0, x1, y1, z1):
    return box_mesh(tuple(v / M_PER_IN for v in (x0, y0, z0)),
                    tuple(v / M_PER_IN for v in (x1, y1, z1)))


def tube(width, height, depth, section):
    thickness = min(VISUALIZATION.sheet_m, width / 4, height / 4)
    outer = circle(width) if section == "round" else rectangle(width, height)
    inner = (circle(width - 2 * thickness) if section == "round"
             else rectangle(width - 2 * thickness, height - 2 * thickness))
    return panel(outer, (inner,), 0, depth)


def shell(width, height, depth, section, inlet=None):
    if section == "round" or inlet is None:
        return tube(width, height, depth, section)
    # A dimensioned inlet pierces the appropriate side; no inferred connection mouths.
    t = min(VISUALIZATION.sheet_m, width / 4, height / 4, depth / 4)
    parts = []
    px, py, pz = inlet[0]
    normal, opening = inlet[1:]
    for axis, extent, transverse in ((0, width, height), (1, height, width)):
        for sign in (-1, 1):
            holes = ()
            if normal[axis] * sign > 0.99:
                along = py if axis == 0 else px
                holes = (tuple((a + along, b + pz - depth / 2) for a, b in opening),)
            sheet = panel(rectangle(transverse, depth), holes, 0, t)
            origin = [0.0, 0.0, depth / 2]
            origin[axis] = extent / 2 - t if sign > 0 else -extent / 2
            axes = (((0, 1, 0), (0, 0, 1), (1, 0, 0)) if axis == 0
                    else ((1, 0, 0), (0, 0, 1), (0, 1, 0)))
            parts.append(transform_mesh(sheet, tuple(origin), *axes))
    # A dimensioned side entry defines a boot: close its back and leave its face open.
    # Plain necks with no authored inlet stay open-ended sleeves.
    if abs(normal[2]) < 0.99:
        parts.append(panel(rectangle(width, height), (), depth - t, depth))
    for sign, z in ((-1, 0), (1, depth - t)):
        if normal[2] * sign > 0.99:
            holes = (tuple((a + px, b + py) for a, b in opening),)
            parts.append(panel(rectangle(width, height), holes, z, z + t))
    return combine_meshes(*parts)


def face_mesh(width, height, depth, style, double_deflection, opening=None):
    frame = min(VISUALIZATION.frame_m, width / 8, height / 8)
    thickness = min(VISUALIZATION.sheet_m, depth / 4)
    if style == "disc_valve":
        diameter = min(width, height)
        rim = panel(circle(diameter), (circle(diameter - 2 * frame),), 0, thickness)
        disc = panel(circle(diameter * VISUALIZATION.disc_radius_ratio), (),
                     depth - thickness, depth)
        # A central stem supports the disc while leaving the annular passage visible.
        stem = block(-thickness, -thickness, 0, thickness, thickness, depth)
        return combine_meshes(rim, disc, stem)
    inner_width, inner_height = opening or (width - 2 * frame, height - 2 * frame)
    if not (0 < inner_width < width and 0 < inner_height < height):
        raise ValueError("grille opening must fit inside its face")
    parts = [panel(rectangle(width, height), (rectangle(inner_width, inner_height),),
                   0, min(frame, depth))]
    angle = math.radians(VISUALIZATION.blade_angle_degrees)
    chord = min(VISUALIZATION.blade_chord_m, inner_height / 4,
                (depth - thickness) / math.sin(angle) / (2 if double_deflection else 1))
    for vertical in ((False, True) if double_deflection else (False,)):
        span, extent = ((inner_height, inner_width) if vertical else (inner_width, inner_height))
        count = max(1, int(extent / VISUALIZATION.blade_pitch_m))
        blade = block(-span / 2, -chord / 2, -thickness / 2,
                      span / 2, chord / 2, thickness / 2)
        for i in range(count):
            position = -extent / 2 + extent * (i + 0.5) / count
            z = depth * (0.75 if vertical else 0.25 if double_deflection else 0.5)
            axes = (((0, 1, 0), (math.cos(angle), 0, math.sin(angle)),
                     (-math.sin(angle), 0, math.cos(angle))) if vertical
                    else ((1, 0, 0), (0, math.cos(angle), math.sin(angle)),
                          (0, -math.sin(angle), math.cos(angle))))
            parts.append(transform_mesh(blade, (position if vertical else 0,
                                                0 if vertical else position, z), *axes))
    return combine_meshes(*parts)


def terminal_frame(model, obj):
    from typehaus.resolve.terminal_necks import _back, _face_offset, _rotate

    if obj.mount is None or obj.body_z0_m is None or obj.body_z1_m is None:
        return None
    across = (*_rotate((1.0, 0.0), obj.rotation_degrees), 0)
    other = (*_rotate((0.0, 1.0), obj.rotation_degrees), 0)
    kind = obj.mount.kind.value
    if kind == "wall":
        back = _back(model, obj, other[:2])
        if back is None:
            return None
        distance = _face_offset(obj, back)
        origin = (obj.position[0] + back[0] * distance,
                  obj.position[1] + back[1] * distance,
                  (obj.body_z0_m + obj.body_z1_m) / 2)
        return origin, across, (0, 0, 1), (*back, 0)
    origin = (*obj.position, obj.body_z0_m if kind == "ceiling" else obj.body_z1_m)
    return origin, across, other, (0, 0, 1 if kind == "ceiling" else -1)


def resolve_terminal_faces(model):
    types = {t.tag: t for t in model.plan.library.register_types}
    for index, obj in enumerate(model.canvas_objects):
        catalog = types.get(obj.type_ref) if obj.kind == "Register" else None
        if catalog is None or catalog.face_style is None:
            continue
        frame = terminal_frame(model, obj)
        if frame is None:
            continue
        wall = obj.mount.kind.value == "wall"
        width = catalog.footprint[0].meters
        height = catalog.height.meters if wall else catalog.footprint[1].meters
        depth = catalog.footprint[1].meters if wall else catalog.height.meters
        mesh = face_mesh(width, height, depth, catalog.face_style,
                         catalog.double_deflection,
                         tuple(v.meters for v in catalog.face_opening)
                         if catalog.face_opening is not None else None)
        if wall:
            mesh = transform_mesh(mesh, (0, 0, -depth))
        model.canvas_objects[index] = replace(obj, body_mesh=transform_mesh(mesh, *frame))


def neck_mesh(model, obj, neck):
    frame = terminal_frame(model, obj)
    if frame is None or neck.section is None:
        return None
    inlet = None
    if neck.inlet is not None:
        authored = neck.inlet
        position = tuple(v.meters for v in authored.position)
        normal = (*authored.normal, 0)
        if obj.mount.kind.value == "wall":
            position = (position[0], position[2], position[1])
            normal = (authored.normal[0], 0, authored.normal[1])
        opening = (circle(authored.width.meters) if authored.section == "round"
                   else rectangle(authored.width.meters, authored.height.meters))
        inlet = position, normal, opening
    mesh = shell(neck.width.meters, neck.height.meters, neck.depth.meters, neck.section, inlet)
    return transform_mesh(mesh, *frame)
