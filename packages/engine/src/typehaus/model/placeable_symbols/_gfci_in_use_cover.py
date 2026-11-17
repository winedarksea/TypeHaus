"""Closed Leviton 5980-UCL cover over a vertical SmartlockPro GFCI.

Envelope: https://leviton.com/products/5980-ucl (5980 dimensional drawing).
Hood taper, wall thickness, hardware and cord exits approximate the product photos;
these details are visual geometry, not a manufacturer fabrication model. Local +Y
is the mounting plane. The clear hood encloses an empty plug cavity.
"""

import math
from dataclasses import dataclass

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import triangulate

from typehaus.model.placeable_symbols._frame import box, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.model.placeable_symbols.receptacles import (
    _clipped_outline,
    _depth_extrusion,
    _face,
)


@dataclass(frozen=True)
class InUseCoverGeometryConfig:
    width_in: float = 3.63
    depth_in: float = 3.08
    height_in: float = 6.69
    shell_thickness_in: float = 0.08
    adapter_depth_in: float = 0.25
    body_bottom_in: float = 0.80
    body_top_in: float = 5.90
    corner_fraction: float = 0.08
    hood_taper_in: float = 0.24
    cord_exit_radius_in: float = 0.29
    cord_exit_spacing_in: float = 1.36
    cord_exit_front_setback_in: float = 0.65
    cord_exit_segments: int = 12
    hinge_radius_in: float = 0.16
    hinge_width_in: float = 2.10
    latch_width_in: float = 0.60
    latch_bottom_in: float = 0.20
    latch_top_in: float = 0.95
    latch_projection_in: float = 0.60
    face_width_in: float = 1.29
    face_height_in: float = 2.70
    face_projection_20a_in: float = 0.10
    face_projection_15a_in: float = 0.03
    maximum_parts: int = 36
    maximum_triangles: int = 1200


IN_USE_COVER_GEOMETRY = InUseCoverGeometryConfig()
COVER_COLOR = "weatherproof-cover"


def _closed_panel(outer, inner):
    """A thin closed quad, with both faces retained for transparent exports."""
    vertices = [*outer, *inner]
    triangles = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6)]
    for index in range(4):
        following = (index + 1) % 4
        triangles.extend(((index, index + 4, following + 4),
                          (index, following + 4, following)))
    return mesh_part(vertices, outward(vertices, triangles), "clear-glass")


def _cord_exit_panel(outline, holes, bottom, thickness):
    """A bottom sheet with two actual open cord ports and closed port walls."""
    polygon = Polygon(outline, holes)
    vertices, triangles = [], []

    def triangle(points):
        offset = len(vertices)
        vertices.extend(points)
        triangles.append((offset, offset + 1, offset + 2))

    for face in triangulate(polygon):
        if not polygon.covers(face):
            continue
        points = list(face.exterior.coords)[:3]
        triangle([(x, y, bottom) for x, y in reversed(points)])
        triangle([(x, y, bottom + thickness) for x, y in points])
    # Orient hole rings opposite to the outer boundary so their normals face the void.
    polygon = orient(polygon)
    for ring in (polygon.exterior, *polygon.interiors):
        for (x, y), (xx, yy) in zip(ring.coords[:-1], ring.coords[1:], strict=True):
            a, b = (x, y, bottom), (xx, yy, bottom)
            c, d = (xx, yy, bottom + thickness), (x, y, bottom + thickness)
            triangle((a, b, c))
            triangle((a, c, d))
    part = mesh_part(vertices, outward(vertices, triangles), "clear-glass")
    return {**part, "role": "in-use-cover:cord-exits"}


def _hood(width, front, back, bottom, top, unit):
    cfg = IN_USE_COVER_GEOMETRY
    thickness = cfg.shell_thickness_in * unit
    taper = cfg.hood_taper_in * unit
    rear = _clipped_outline(0, (bottom + top) / 2, width, top - bottom,
                            cfg.corner_fraction)
    nose = _clipped_outline(0, (bottom + top - taper) / 2,
                            width - 2 * taper, top - bottom - taper, cfg.corner_fraction)
    inner_rear = _clipped_outline(0, (bottom + top) / 2, width - 2 * thickness,
                                  top - bottom - 2 * thickness, cfg.corner_fraction)
    inner_nose = _clipped_outline(0, (bottom + top - taper) / 2,
                                  width - 2 * (taper + thickness),
                                  top - bottom - taper - 2 * thickness, cfg.corner_fraction)
    parts = [_depth_extrusion(nose, front, front + thickness, "clear-glass")]
    # The lower straight edge is replaced with the perforated sheet below.
    for index in range(1, len(nose)):
        following = (index + 1) % len(nose)
        outer = [(x, y, z) for outline, y in ((nose, front), (rear, back))
                 for x, z in (outline[index], outline[following])]
        inner = [(x, y, z) for outline, y in ((inner_nose, front + thickness),
                                             (inner_rear, back))
                 for x, z in (outline[index], outline[following])]
        parts.append(_closed_panel([outer[i] for i in (0, 1, 3, 2)],
                                   [inner[i] for i in (0, 1, 3, 2)]))
    holes = []
    for sign in (-1, 1):
        holes.append([(sign * cfg.cord_exit_spacing_in * unit / 2
                       + cfg.cord_exit_radius_in * unit * math.cos(math.tau * i
                                                                / cfg.cord_exit_segments),
                       front + cfg.cord_exit_front_setback_in * unit
                       + cfg.cord_exit_radius_in * unit * math.sin(math.tau * i
                                                                / cfg.cord_exit_segments))
                      for i in range(cfg.cord_exit_segments)])
    parts.append(_cord_exit_panel([(nose[0][0], front), (nose[1][0], front),
                                   (rear[1][0], back), (rear[0][0], back)],
                                  holes, bottom, thickness))
    return parts


def gfci_in_use_cover(width, depth, height, *, amperage=20):
    cfg = IN_USE_COVER_GEOMETRY
    # Uniform scaling preserves small details even in registry size sweeps.
    unit = min(width / cfg.width_in, depth / cfg.depth_in, height / cfg.height_in)
    thickness = cfg.shell_thickness_in * unit
    adapter_depth = cfg.adapter_depth_in * unit
    back = depth / 2
    adapter_front = back - adapter_depth
    hood_front = -depth / 2
    bottom = cfg.body_bottom_in * unit
    top = height - (cfg.height_in - cfg.body_top_in) * unit
    base_outline = _clipped_outline(0, (bottom + top) / 2, width,
                                    top - bottom, cfg.corner_fraction)
    parts = [_depth_extrusion(base_outline, adapter_front, back, COVER_COLOR)]
    face_depth = (cfg.face_projection_20a_in if amperage == 20
                  else cfg.face_projection_15a_in) * unit
    face_height = cfg.face_height_in * unit
    _, face_parts = _face(cfg.face_width_in * unit, face_depth, face_height,
                          (("120-20", "120-20") if amperage == 20 else ("120", "120"),),
                          band="gfci")
    offset_y = adapter_front - face_depth / 2
    offset_z = (height - face_height) / 2
    for part in face_parts:
        x, y, z = part["center"]
        shifted = {**part, "center": (x, y + offset_y, z + offset_z)}
        if "mesh" in part:
            shifted["mesh"] = {**part["mesh"], "positions": tuple(
                (x, y + offset_y, z + offset_z) for x, y, z in part["mesh"]["positions"])}
        parts.append(shifted)
    parts.extend(_hood(width, hood_front, adapter_front, bottom, top, unit))
    hinge_radius = cfg.hinge_radius_in * unit
    parts.append(box(0, back - adapter_depth / 2, top, height - 2 * hinge_radius,
                     cfg.hinge_width_in * unit, adapter_depth, COVER_COLOR))
    parts.append(round_cylinder((0, back - hinge_radius, height - hinge_radius),
                                hinge_radius, cfg.hinge_width_in * unit,
                                axis=0, color=COVER_COLOR))
    # A U-shaped lock tab leaves a real opening instead of painting a dark dot on a block.
    latch_width = cfg.latch_width_in * unit
    latch_bottom = cfg.latch_bottom_in * unit
    latch_top = cfg.latch_top_in * unit
    latch_depth = cfg.latch_projection_in * unit
    latch_y = adapter_front - latch_depth / 2
    for x in (-(latch_width - thickness) / 2, (latch_width - thickness) / 2):
        parts.append(box(x, latch_y, latch_bottom, latch_top, thickness,
                         latch_depth, COVER_COLOR))
    parts.append(box(0, latch_y, 0, latch_bottom, latch_width, latch_depth, COVER_COLOR))
    return (rect(0, 0, width, depth),), tuple(parts)


def gfci_in_use_cover_15a(width, depth, height):
    return gfci_in_use_cover(width, depth, height, amperage=15)
