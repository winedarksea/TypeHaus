"""Generated massing for a raised, inside-mount cellular window blind."""

from __future__ import annotations

from typehaus.model.placeable_symbols._frame import Part, Stroke, box, line, rect
from typehaus.quantities import inch

HEADRAIL_HEIGHT_M = inch(1.5).meters
BOTTOM_RAIL_HEIGHT_M = inch(1.0).meters
SIDE_CLEARANCE_M = inch(0.25).meters
PLEAT_SPACING_M = inch(1.5).meters
PLEAT_FACE_HEIGHT_M = inch(0.10).meters
PLEAT_FACE_DEPTH_M = inch(0.08).meters
SHADE_FABRIC_DEPTH_M = inch(0.04).meters
RAISED_FABRIC_HEIGHT_M = inch(1.5).meters
MIN_VISIBLE_PLEAT_COUNT = 1


def cellular_blind(width: float, depth: float, height: float
                   ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    """A headrail, folded honeycomb shade and bottom rail at the top of the opening.

    The catalog height remains the full window drop so the headrail stays at the window head.
    Compress the fabric and its pleats beneath it, leaving the glass below the stack clear.
    All pieces stay inside the catalog type's envelope.
    """
    headrail_height = min(HEADRAIL_HEIGHT_M, height * 0.15)
    bottom_rail_height = min(BOTTOM_RAIL_HEIGHT_M,
                             max(0.0, height - headrail_height) * 0.15)
    shade_top = height - headrail_height
    extended_fabric_height = shade_top - bottom_rail_height
    shade_bottom = shade_top - min(RAISED_FABRIC_HEIGHT_M, extended_fabric_height)
    shade_height = shade_top - shade_bottom
    side_clearance = min(SIDE_CLEARANCE_M, width * 0.08)
    shade_width = width - 2 * side_clearance
    rail_width = width - side_clearance
    front_y = -depth / 2
    fabric_depth = min(SHADE_FABRIC_DEPTH_M, depth / 8)
    rib_depth = min(PLEAT_FACE_DEPTH_M, depth / 8)
    parts: list[Part] = [
        box(0.0, 0.0, height - headrail_height, height,
            rail_width, depth, "appliance-white"),
        box(0.0, 0.0, shade_bottom, shade_top,
            shade_width, fabric_depth, "appliance-white"),
        box(0.0, 0.0, shade_bottom - bottom_rail_height, shade_bottom,
            rail_width, depth, "appliance-white"),
    ]
    rib_count = max(MIN_VISIBLE_PLEAT_COUNT, int(extended_fabric_height / PLEAT_SPACING_M))
    spacing = shade_height / rib_count
    rib_height = min(PLEAT_FACE_HEIGHT_M, spacing / 2)
    for rib_index in range(rib_count):
        center_z = shade_bottom + (rib_index + 0.5) * spacing
        # Alternating shallow offsets suggest the folded cell profile in elevation and side view.
        offset = rib_depth / 2 if rib_index % 2 else rib_depth
        parts.append(box(0.0, front_y + offset, center_z - rib_height / 2,
                         center_z + rib_height / 2, shade_width, rib_depth,
                         "casework-shadow"))
    strokes = (
        rect(0.0, 0.0, width, depth),
        line((-width / 2, 0.0), (width / 2, 0.0)),
    )
    return strokes, tuple(parts)
