"""A curtain track drawn OPEN: the rail plus folded fabric stacks, inside the closed envelope.

Local frame as every symbol: x along the run (run start at -width/2), +y the wall side,
z=0 at the body base (the floor kiss), z=height at the rail top (the ceiling).
"""

from __future__ import annotations

from typing import Any

from typehaus.model.curtain_track import CurtainTrackSpec
from typehaus.model.placeable_symbols._frame import (
    DETAIL_WEIGHT,
    Part,
    Stroke,
    box,
    line,
    rect,
    with_material_refs,
)
from typehaus.model.placeable_symbols._mesh import mesh_part

RAIL_COLOR = "appliance-white"
FABRIC_COLOR = "fabric"
# Fabric drawn as a closed ribbon this thick, so every reader gets a solid, not a sheet.
FABRIC_THICKNESS_M = 0.003


def _quad(a: int, b: int, c: int, d: int) -> list[tuple[int, int, int]]:
    """Two triangles of a quad wound counter-clockwise seen from outside."""
    return [(a, b, c), (a, c, d)]


def _folded_stack(x0: float, width: float, fold_pitch: float, fold_depth: float,
                  z1: float) -> Part:
    """A zig-zag ribbon in plan, swept 0..z1, its y extent exactly ``fold_depth``."""
    folds = max(1, round(width / fold_pitch))
    count = 2 * folds + 1
    thickness = min(FABRIC_THICKNESS_M, fold_depth / 2)
    amplitude = fold_depth - thickness
    front = [(x0 + width * index / (count - 1),
              -fold_depth / 2 + (amplitude if index % 2 else 0.0)) for index in range(count)]
    back = [(x, y + thickness) for x, y in front]
    # Vertex blocks: front bottom, front top, back bottom, back top.
    positions = [(x, y, z) for ring, z in ((front, 0.0), (front, z1), (back, 0.0), (back, z1))
                 for x, y in ring]
    fb, ft, bb, bt = (block * count for block in range(4))
    triangles: list[tuple[int, int, int]] = []
    for i in range(count - 1):
        j = i + 1
        triangles += _quad(fb + i, fb + j, ft + j, ft + i)   # front face, -y
        triangles += _quad(bb + j, bb + i, bt + i, bt + j)   # back face, +y
        triangles += _quad(ft + i, ft + j, bt + j, bt + i)   # top, +z
        triangles += _quad(fb + i, bb + i, bb + j, fb + j)   # bottom, -z
    last = count - 1
    triangles += _quad(fb, ft, bt, bb)                       # run-start end, -x
    triangles += _quad(fb + last, bb + last, bt + last, ft + last)  # run-end end, +x
    return mesh_part(positions, triangles, FABRIC_COLOR)


def curtain_track_geometry(spec: CurtainTrackSpec, width_m: float, depth_m: float,
                           height_m: float) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    """Plan strokes (rail line, stack outlines) and parts (rail box, folded stacks)."""
    del depth_m  # the spec's own check_fits holds rail and folds inside it
    rail_bottom = height_m - spec.rail_height.meters
    strokes: list[Stroke] = [line((-width_m / 2, 0.0), (width_m / 2, 0.0))]
    parts: list[Part] = [box(0.0, 0.0, rail_bottom, height_m, width_m,
                             spec.rail_width.meters, RAIL_COLOR)]
    if not spec.show_curtains:
        return tuple(strokes), tuple(parts)
    fabric_top = rail_bottom + spec.heading_rise.meters
    for stack in spec.stacks:
        x0 = -width_m / 2 + stack.start.meters
        strokes.append(rect(x0 + stack.width.meters / 2, 0.0, stack.width.meters,
                            spec.fold_depth.meters, weight=DETAIL_WEIGHT))
        parts.append(_folded_stack(x0, stack.width.meters, spec.fold_pitch.meters,
                                   spec.fold_depth.meters, fabric_top))
    return tuple(strokes), tuple(parts)


def curtain_track_type_geometry(item: Any) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    """A FurnitureType's curtain geometry, its ``fabric`` named by model_representation."""
    width_m, depth_m = (dimension.meters for dimension in item.footprint)
    strokes, parts = curtain_track_geometry(item.curtain_track, width_m, depth_m,
                                            item.height.meters)
    refs = getattr(getattr(item, "model_representation", None), "material_refs", None)
    return strokes, with_material_refs(parts, refs)
