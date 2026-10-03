"""Wall-facing mirror glass and LED bands, in the shared placeable local frame."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import (
    DETAIL_WEIGHT,
    box,
    depth_cylinder,
    rect,
)

MIRROR_EDGE_INSET_M = 0.00635
MIRROR_LIGHT_BAND_WIDTH_M = 0.0127
MIRROR_EDGE_INSET_SHARE = 0.01
MIRROR_LIGHT_BAND_SHARE = 0.025
# Consecutive layers progress from the wall (+y) toward the room (-y). The stepped
# faces expose the outer glass rim and LED band without burying either in the housing.
MIRROR_FACE_LAYERS = (
    (0.5, -0.25, "luminaire-housing"),
    (-0.25, -0.35, "mirror"),
    (-0.35, -0.425, "lamp"),
    (-0.425, -0.5, "mirror"),
)


def mirror_light(*, round_face: bool = False) -> Builder:
    """An integrated mirror with an inset, continuous front-lit perimeter."""

    def build(width: float, depth: float, height: float) -> Geometry:
        smaller_face_dimension = min(width, height)
        edge_inset = min(MIRROR_EDGE_INSET_M,
                         smaller_face_dimension * MIRROR_EDGE_INSET_SHARE)
        light_band_width = min(MIRROR_LIGHT_BAND_WIDTH_M,
                               smaller_face_dimension * MIRROR_LIGHT_BAND_SHARE)
        # Plan symbols describe the shallow wall footprint, regardless of face height.
        strokes = (rect(0, 0, width, depth, fill="luminaire-housing"),
                   rect(0, -depth * 0.4, width * (1 - 2 * MIRROR_EDGE_INSET_SHARE),
                        depth * 0.2, fill="mirror", weight=DETAIL_WEIGHT))
        insets = (0.0, 0.0, edge_inset, edge_inset + light_band_width)
        parts = []
        for (rear, front, color), inset in zip(MIRROR_FACE_LAYERS, insets, strict=True):
            layer_depth = (rear - front) * depth
            layer_y = (rear + front) * depth / 2
            if round_face:
                radius = smaller_face_dimension / 2 - inset
                parts.append(depth_cylinder(0, layer_y, height / 2, radius,
                                            layer_depth, color))
            else:
                parts.append(box(0, layer_y, inset, height - inset,
                                 width - 2 * inset, layer_depth, color))
        return strokes, tuple(parts)

    return build


ARCH_FRAME_DEPTH_M = 0.0254
ARCH_FRAME_BORDER_M = 0.019
ARCH_GLASS_DEPTH_M = 0.004
ARCH_SHELF_THICKNESS_M = 0.019


def arch_shelf_mirror() -> Builder:
    """A plain arched mirror on a metal frame with a full-width shelf along its bottom.

    The frame and glass sit against the wall (+y); only the shelf takes the footprint's
    full depth. The arch is a half-round of the face width.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        frame_depth = min(ARCH_FRAME_DEPTH_M, depth * 0.3)
        glass_depth = min(ARCH_GLASS_DEPTH_M, depth * 0.1)
        shelf = min(ARCH_SHELF_THICKNESS_M, height * 0.1)
        # A face shorter than it is wide takes a smaller round rather than leave the box.
        radius = min(width / 2, (height - shelf) / 2)
        border = min(ARCH_FRAME_BORDER_M, width * 0.1, radius / 2)
        spring = height - radius
        frame_y = depth / 2 - frame_depth / 2
        glass_y = depth / 2 - frame_depth - glass_depth / 2
        strokes = (rect(0, 0, width, depth),
                   rect(0, frame_y, width, frame_depth, fill="brass", weight=DETAIL_WEIGHT))
        parts = (
            box(0, 0, 0.0, shelf, width, depth, "brass"),
            box(0, frame_y, shelf, spring, width, frame_depth, "brass"),
            depth_cylinder(0, frame_y, spring, radius, frame_depth, "brass"),
            box(0, glass_y, shelf + border, spring, width - 2 * border, glass_depth, "mirror"),
            depth_cylinder(0, glass_y, spring, radius - border, glass_depth, "mirror"),
        )
        return strokes, parts

    return build
