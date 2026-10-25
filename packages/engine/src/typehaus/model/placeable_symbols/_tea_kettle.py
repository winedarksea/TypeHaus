"""WK 3422 silhouette: glass jug, raised basket, steel bands and open side handle.

Overall dimensions come from the product type; internal proportions approximate the
manufacturer's photograph. Local -y faces the base controls, with the handle at +x.
"""

from typehaus.model.placeable_symbols._frame import box, circle, ellipse, polygon, prism, rect

BASE_HEIGHT_RATIO = 0.12
LOWER_BAND_TOP_RATIO = 0.29
UPPER_BAND_BOTTOM_RATIO = 0.84
LID_HEIGHT_RATIO = 0.98


def tea_kettle(width: float, depth: float, height: float):
    center_x = -width * 0.07
    radius = min(width * 0.33, depth * 0.39)
    base = ellipse(center_x, 0, width * 0.40, depth / 2, fill="appliance-steel")
    jug = circle(center_x, 0, radius, fill="glass")
    basket = circle(center_x, 0, radius * 0.48, fill="metal")
    spout = polygon(((center_x - radius * 0.80, -radius * 0.45),
                     (-width / 2, 0), (center_x - radius * 0.80, radius * 0.45)),
                    fill="appliance-steel")
    strokes = (base, jug, basket, spout,
               rect(width * 0.32, 0, width * 0.36, depth * 0.14, fill="metal-black"),
               rect(center_x, -depth * 0.40, width * 0.20, depth * 0.08, fill="screen"))
    parts = [prism(base["points"], 0, height * BASE_HEIGHT_RATIO, "appliance-steel"),
             prism(jug["points"], height * BASE_HEIGHT_RATIO,
                   height * LOWER_BAND_TOP_RATIO, "appliance-steel"),
             prism(jug["points"], height * LOWER_BAND_TOP_RATIO,
                   height * UPPER_BAND_BOTTOM_RATIO, "clear-glass"),
             prism(jug["points"], height * UPPER_BAND_BOTTOM_RATIO,
                   height * LID_HEIGHT_RATIO, "appliance-steel"),
             prism(circle(center_x, 0, radius * 0.90)["points"],
                   height * LID_HEIGHT_RATIO, height, "metal-black"),
             prism(basket["points"], height * 0.59, height * 0.79, "metal"),
             prism(circle(center_x, 0, radius * 0.06)["points"],
                   height * 0.59, height * LID_HEIGHT_RATIO, "metal-black"),
             prism(spout["points"], height * UPPER_BAND_BOTTOM_RATIO,
                   height * 0.96, "appliance-steel"),
             box(center_x, -depth * 0.40, height * 0.115, height * BASE_HEIGHT_RATIO,
                 width * 0.20, depth * 0.08, "screen")]
    # Three rails leave the grip visibly open in elevation.
    for z0, z1 in ((0.31, 0.38), (0.88, 0.95)):
        parts.append(box(width * 0.32, 0, height * z0, height * z1,
                         width * 0.36, depth * 0.14, "metal-black"))
    parts.append(box(width * 0.46, 0, height * 0.31, height * 0.95,
                     width * 0.08, depth * 0.14, "metal-black"))
    return strokes, tuple(parts)
