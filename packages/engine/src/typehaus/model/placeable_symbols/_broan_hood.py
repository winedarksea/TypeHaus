"""Broan BWP1304SS with ARKBWP recirculation kit; wall at local +y.

Envelope, canopy and flue dimensions: Broan BWP1 spec sheet 99529070B.
https://broan-nutone.com/getmedia/1709a63b-c6a8-4f8b-8122-43d8de532e59/Specification-Sheet-bilingual-BWP1.pdf
Controls, filter mesh and return slots are representative visual details.
"""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, circle, prism, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

WIDTH_IN = 29.5
DEPTH_IN = 19.6875
MIN_HEIGHT_IN = 25.375  # chimney fully collapsed
MAX_HEIGHT_IN = 40.375
CANOPY_HEIGHT_IN = 9.6875
FASCIA_HEIGHT_IN = 1.375
FLUE_WIDTH_IN = 8.75
FLUE_DEPTH_IN = 6.75
FILTER_COUNT = 2
FILTER_MESH_LINES = 15
CONTROL_COUNT = 5
RETURN_SLOT_COUNT = 9


def broan_recirculating_hood(width: float, depth: float, height: float) -> Geometry:
    """The canopy keeps its height; the telescopic chimney takes the rest of ``height``.

    Below the collapsed 25 3/8" the whole body scales down instead.
    """
    inch = 0.0254
    scale = min(1.0, height / (MIN_HEIGHT_IN * inch))
    canopy_top = CANOPY_HEIGHT_IN * inch * scale
    fascia_top = FASCIA_HEIGHT_IN * inch * scale
    flue_width = width * FLUE_WIDTH_IN / WIDTH_IN
    flue_depth = depth * FLUE_DEPTH_IN / DEPTH_IN
    flue_center_y = (depth - flue_depth) / 2
    detail_thickness = min(width, depth, height) * 0.002
    underside_top = fascia_top * 0.10

    # Keep the plan's below-canopy convention, but show the actual paired filters and LEDs.
    strokes = [rect(0, 0, width, depth, fill="appliance-steel")]
    # Inset the front skin so the buttons occupy their own plane within the envelope.
    parts = [box(0, detail_thickness / 2, underside_top, fascia_top,
                 width, depth - detail_thickness, "appliance-steel")]
    for index in range(FILTER_COUNT):
        filter_x = width * (-0.22 + index * 0.44)
        filter_y, filter_width, filter_depth = depth * 0.09, width * 0.41, depth * 0.65
        strokes.append(rect(filter_x, filter_y, filter_width, filter_depth,
                            weight=DETAIL_WEIGHT))
        parts.append(box(filter_x, filter_y, underside_top * 0.25, underside_top,
                         filter_width, filter_depth, "metal"))
        for mesh_index in range(FILTER_MESH_LINES):
            mesh_x = filter_x + filter_width * (
                (mesh_index + 1) / (FILTER_MESH_LINES + 1) - 0.5)
            parts.append(box(mesh_x, filter_y, 0, underside_top * 0.25,
                             detail_thickness, filter_depth * 0.96, "appliance-steel"))
        parts.append(box(filter_x, filter_y - filter_depth * 0.40, 0,
                         underside_top * 0.5, filter_width * 0.12,
                         filter_depth * 0.05, "metal-black"))
        light_x = width * (-0.32 + index * 0.64)
        light_y, light_radius = -depth * 0.36, depth * 0.035
        light_outline = circle(light_x, light_y, light_radius, weight=DETAIL_WEIGHT)
        strokes.append(light_outline)
        parts.append(prism(light_outline["points"], 0, underside_top * 0.5, "lamp"))

    # A closed frustum gives three sloping faces and a vertical back against the wall.
    lower = [(-width / 2, -depth / 2, fascia_top),
             (width / 2, -depth / 2, fascia_top),
             (width / 2, depth / 2, fascia_top),
             (-width / 2, depth / 2, fascia_top)]
    upper = [(-flue_width / 2, depth / 2 - flue_depth, canopy_top),
             (flue_width / 2, depth / 2 - flue_depth, canopy_top),
             (flue_width / 2, depth / 2, canopy_top),
             (-flue_width / 2, depth / 2, canopy_top)]
    vertices = lower + upper
    triangles = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7)]
    for index in range(4):
        following = (index + 1) % 4
        triangles.extend([(index, following, following + 4),
                          (index, following + 4, index + 4)])
    parts.append(mesh_part(vertices, outward(vertices, triangles), "appliance-steel"))

    seam_height = canopy_top + (height - canopy_top) * 0.55
    parts.extend([
        box(0, flue_center_y, canopy_top, seam_height,
            flue_width, flue_depth, "appliance-steel"),
        # The sliding upper cover is inset so its joint survives an oblique view.
        box(0, flue_center_y + detail_thickness, seam_height, height,
            flue_width - 2 * detail_thickness, flue_depth - 2 * detail_thickness,
            "appliance-steel"),
    ])
    # ARKBWP returns air to the room through slots in both sides of the upper cover.
    for side in (-1, 1):
        for index in range(RETURN_SLOT_COUNT):
            slot_y = flue_center_y + flue_depth * (
                (index + 0.5) / RETURN_SLOT_COUNT - 0.5) * 0.62
            parts.append(box(side * (flue_width / 2 - detail_thickness), slot_y,
                             height * 0.91, height * 0.97, detail_thickness,
                             flue_depth * 0.028, "metal-black"))
    for index in range(CONTROL_COUNT):
        parts.append(box((index - (CONTROL_COUNT - 1) / 2) * width * 0.025,
                         -depth / 2 + detail_thickness / 4,
                         fascia_top * 0.35, fascia_top * 0.65,
                         width * 0.018, detail_thickness / 2, "screen"))
    return tuple(strokes), tuple(parts)
