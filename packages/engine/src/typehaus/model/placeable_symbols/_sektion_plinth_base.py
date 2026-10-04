"""A stock 30-inch wall frame installed on the living run's anchored plinth."""

from typehaus.model.placeable_symbols._families import Geometry, case
from typehaus.model.placeable_symbols._frame import box
from typehaus.quantities import inch

PLINTH_HEIGHT_M = inch(3.5).meters
FRAME_HEIGHT_M = inch(30).meters
SUBTOP_THICKNESS_M = inch(0.5).meters
INSTALLED_HEIGHT_M = inch(36).meters


def sektion_plinth_wall_base(width: float, depth: float, height: float) -> Geometry:
    # Preview symbols also accept smaller arbitrary boxes; preserve the stock ratios
    # while the catalog's actual 36-inch installed type retains its exact courses.
    scale = min(1.0, height / INSTALLED_HEIGHT_M)
    plinth_height = PLINTH_HEIGHT_M * scale
    strokes, frame_parts = case(rows=1, cols=1, pulls=False,
                               color="cabinet-cream", face_color="cabinet-cream-dark")(
                                   width, depth, FRAME_HEIGHT_M * scale)
    raised_parts = tuple({**part, "center": (part["center"][0], part["center"][1],
                                           part["center"][2] + plinth_height)}
                         for part in frame_parts)
    frame_top = plinth_height + FRAME_HEIGHT_M * scale
    subtop_top = frame_top + SUBTOP_THICKNESS_M * scale
    setback = min(inch(1).meters, depth / 4)
    return strokes, (*raised_parts,
                     box(0, setback, 0, plinth_height,
                         width, depth - 2 * setback, "cabinet-cream-dark"),
                     box(0, 0, frame_top, subtop_top, width, depth, "cabinet-cream"),
                     box(0, 0, subtop_top, height, width, depth, "counter"))
