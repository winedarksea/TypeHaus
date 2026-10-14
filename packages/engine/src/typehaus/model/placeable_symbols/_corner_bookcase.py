"""Open L-shaped shelving: local backs are +x/+y, access is from the opposite corner."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, polygon, rect

# JW0510 proportions; frame joinery is illustrative rather than fabrication geometry.
SHELF_LEVEL_COUNT = 7
SHELF_DEPTH_FRACTION = 9.45 / 23.62
SHELF_THICKNESS_M = 0.01905
POST_WIDTH_M = 0.0254
POST_INSET_M = 0.00635
LOWEST_SHELF_BOTTOM_FRACTION = 0.05


def corner_bookcase(width: float, depth: float, height: float) -> Geometry:
    """Paired shelves meet at a seam; the frame has no closed back panels."""
    half_width, half_depth = width / 2, depth / 2
    shelf_depth = min(width, depth) * SHELF_DEPTH_FRACTION
    post_width = min(POST_WIDTH_M, shelf_depth / 4)
    post_inset = min(POST_INSET_M, shelf_depth / 8)
    shelf_thickness = min(SHELF_THICKNESS_M, height / (2 * SHELF_LEVEL_COUNT))
    shelf_bottom = height * LOWEST_SHELF_BOTTOM_FRACTION
    level_pitch = (height - shelf_thickness - shelf_bottom) / (SHELF_LEVEL_COUNT - 1)
    outline = (
        (-half_width, half_depth), (half_width, half_depth),
        (half_width, -half_depth), (half_width - shelf_depth, -half_depth),
        (half_width - shelf_depth, half_depth - shelf_depth),
        (-half_width, half_depth - shelf_depth),
    )
    strokes = [polygon(outline, fill="wood-dark")]
    parts = []
    for level in range(SHELF_LEVEL_COUNT):
        bottom = shelf_bottom + level * level_pitch
        parts.extend((
            box(0, half_depth - shelf_depth / 2, bottom, bottom + shelf_thickness,
                width, shelf_depth, "wood-dark"),
            box(half_width - shelf_depth / 2, -shelf_depth / 2,
                bottom, bottom + shelf_thickness,
                shelf_depth, depth - shelf_depth, "wood-dark"),
        ))

    # Inset feet and a raised bottom tier leave room for baseboards behind the open frame.
    # Two posts at each wing end and two at the shared corner carry the shelves.
    post_centres = [
        (x, y)
        for x in (-half_width + post_inset + post_width / 2,
                  half_width - post_inset - post_width / 2)
        for y in (half_depth - shelf_depth + post_inset + post_width / 2,
                  half_depth - post_inset - post_width / 2)
    ]
    post_centres.extend(
        (x, -half_depth + post_inset + post_width / 2)
        for x in (half_width - shelf_depth + post_inset + post_width / 2,
                  half_width - post_inset - post_width / 2)
    )
    for x, y in post_centres:
        strokes.append(rect(x, y, post_width, post_width, fill="metal-black"))
        parts.append(box(x, y, 0, height - shelf_thickness,
                         post_width, post_width, "metal-black"))
    return tuple(strokes), tuple(parts)
