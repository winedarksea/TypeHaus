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
