"""A two-wheeled roll-out refuse cart: tapered body, overhanging lid, handle and wheels at -y.

Local -y is the handle side, the one a person grabs to roll it out; the footprint is the
cart's published overall plan size.
"""

from typehaus.model.placeable_symbols._frame import box, line, prism, rect

LID_THICKNESS_RATIO = 0.04
WHEEL_HEIGHT_RATIO = 0.22
WHEEL_WIDTH_RATIO = 0.14
HANDLE_DEPTH_RATIO = 0.08
BODY_TAPER_RATIO = 0.88  # the bottom is narrower than the lid, so carts nest


def rolling_cart(width: float, depth: float, height: float):
    lid_bottom = height * (1 - LID_THICKNESS_RATIO)
    handle_d = depth * HANDLE_DEPTH_RATIO
    body_front = -depth / 2 + handle_d
    wheel_h = height * WHEEL_HEIGHT_RATIO
    wheel_w = width * WHEEL_WIDTH_RATIO
    half_w, half_bottom = width / 2, width * BODY_TAPER_RATIO / 2
    strokes = (rect(0, handle_d / 2, width, depth - handle_d, fill="nordvalla-gray"),
               rect(0, -depth / 2 + handle_d / 2, width, handle_d, fill="metal-black"),
               line((-half_w, body_front + handle_d), (half_w, body_front + handle_d)))
    # Body: a plan ring swept up; the taper reads in elevation as two stacked prisms.
    back_bottom = depth / 2 * BODY_TAPER_RATIO
    lower = ((-half_bottom, body_front), (half_bottom, body_front),
             (half_bottom, back_bottom), (-half_bottom, back_bottom))
    upper = ((-half_w, body_front), (half_w, body_front), (half_w, depth / 2),
             (-half_w, depth / 2))
    parts = [prism(lower, wheel_h / 3, lid_bottom / 2, "nordvalla-gray"),
             prism(upper, lid_bottom / 2, lid_bottom, "nordvalla-gray"),
             box(0, 0, lid_bottom, height, width, depth, "nordvalla-gray-seam"),
             box(0, -depth / 2 + handle_d / 2, lid_bottom - handle_d, lid_bottom,
                 width * 0.8, handle_d, "metal-black")]
    for sign in (-1, 1):
        parts.append(box(sign * (half_bottom - wheel_w / 2), body_front + wheel_h / 2,
                         0, wheel_h, wheel_w, wheel_h, "metal-black"))
    return strokes, tuple(parts)
