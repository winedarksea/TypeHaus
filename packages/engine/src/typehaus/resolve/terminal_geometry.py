"""Representative air-terminal metal, separate from conservative fit envelopes.

Faces and sheet primitives live here; a neck's closed box is ``resolve/neck_solids``.

Local coordinates are face-across, face-up, and depth into the cavity. Catalog dimensions
bound the drawing; blade spacing and metal thickness are visualization defaults only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes, transform_mesh
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_panel import panel
from typehaus.resolve.terminal_scroll import scroll_openings


@dataclass(frozen=True)
class TerminalVisualization:
    sheet_m: float = 0.0006
    frame_m: float = 0.0127
    blade_pitch_m: float = 0.0254
    blade_chord_m: float = 0.0127
    blade_angle_degrees: float = 35.0
    disc_diameter_ratio: float = 0.60
    facets: int = 48


VISUALIZATION = TerminalVisualization()


def rectangle(width, height):
    return ((-width / 2, -height / 2), (width / 2, -height / 2),
            (width / 2, height / 2), (-width / 2, height / 2))


def circle(diameter, centre=(0.0, 0.0)):
    return tuple((centre[0] + diameter / 2 * math.cos(i * 2 * math.pi / VISUALIZATION.facets),
                  centre[1] + diameter / 2 * math.sin(i * 2 * math.pi / VISUALIZATION.facets))
                 for i in range(VISUALIZATION.facets))


def block(x0, y0, z0, x1, y1, z1):
    return box_mesh(tuple(v / M_PER_IN for v in (x0, y0, z0)),
                    tuple(v / M_PER_IN for v in (x1, y1, z1)))


def tube(width, height, depth, section, sheet_m=None):
    """An open sleeve: a round collar or a rectangular damper box."""
    thickness = min(sheet_m or VISUALIZATION.sheet_m, width / 4, height / 4)
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


def _revolve(profile):
    """Spin a closed (radius, depth) section, with single vertices at the poles."""
    positions, rings, triangles = [], [], []
    for radius, depth in profile:
        ring = circle(2 * radius) if radius else ((0, 0),)
        indices = tuple(range(len(positions), len(positions) + len(ring)))
        positions.extend((x, y, depth) for x, y in ring)
        rings.append(indices if radius else indices * VISUALIZATION.facets)
    for front, back in zip(rings, rings[1:] + rings[:1], strict=True):
        for i in range(VISUALIZATION.facets):
            j = (i + 1) % VISUALIZATION.facets
            if front[i] != front[j]:
                triangles.append((front[i], front[j], back[j]))
            if back[i] != back[j]:
                triangles.append((front[i], back[j], back[i]))
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def _disc_valve(diameter, depth, disc_diameter):
    # Piecewise sections approximate the pressed steel profiles. The raised center
    # and the turned inner edge leave a continuous annular opening around the baffle.
    radius = diameter / 2
    disc = (disc_diameter or diameter * VISUALIZATION.disc_diameter_ratio) / 2
    if not 0 < disc < radius:
        raise ValueError("valve disc must fit inside its casing")
    span = radius - disc
    throat = disc + 0.26 * span
    rear = disc + 0.44 * span
    rim = _revolve(((throat, depth * 0.67), (disc + 0.55 * span, depth * 0.49),
                    (disc + 0.82 * span, depth * 0.42), (radius, depth * 0.56),
                    (radius, depth), (rear, depth), (throat, depth * 0.81)))
    spindle = min(VISUALIZATION.sheet_m * 2, disc / 4)
    centre = _revolve(((0, 0), (disc * 0.55, depth * 0.02),
                       (disc * 0.87, depth * 0.08), (disc, depth * 0.19),
                       (disc, depth * 0.28), (spindle, depth * 0.28),
                       (spindle, depth), (0, depth)))
    return combine_meshes(rim, centre)


def face_mesh(width, height, depth, style, double_deflection, opening=None,
              disc_diameter=None):
    if style == "disc_valve":
        return _disc_valve(min(width, height), depth, disc_diameter)
    if style == "cast_scroll_grille":
        return panel(rectangle(width, height), scroll_openings(width, height), 0, depth,
                     constrained=True)
    frame = min(VISUALIZATION.frame_m, width / 8, height / 8)
    thickness = min(VISUALIZATION.sheet_m, depth / 4)
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
        # The face plane also locates the neck. Keep it fixed and draw authored
        # trim into the room, independently of the legacy fit envelope.
        projection = catalog.face_projection
        if projection is not None:
            depth = projection.meters
        disc_diameter = catalog.disc_diameter
        mesh = face_mesh(width, height, depth, catalog.face_style,
                         catalog.double_deflection,
                         tuple(v.meters for v in catalog.face_opening)
                         if catalog.face_opening is not None else None,
                         disc_diameter.meters if disc_diameter is not None else None)
        if wall or projection is not None:
            mesh = transform_mesh(mesh, (0, 0, -depth))
        model.canvas_objects[index] = replace(obj, body_mesh=transform_mesh(mesh, *frame))


def neck_mesh(model, obj, neck):
    """A neck's sheet metal: ``resolve/neck_solids``."""
    from typehaus.resolve.neck_solids import neck_mesh as _neck_mesh

    return _neck_mesh(model, obj, neck)
