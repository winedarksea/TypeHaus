"""CD08210-style bathroom fan heater; discharge faces local -y.

Appearance follows Lasko's CD08210 product photographs (lasko.com, November 2026).
The caller owns the planning envelope; these proportions do not assert a purchased SKU.
The grille is a shallow bowed guard over a dark recess, without an energized glow.
"""

from typehaus.model.placeable_symbols._families import Geometry, _rounded_rectangle_points
from typehaus.model.placeable_symbols._frame import Part, box, circle, prism, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

GRILLE_SEGMENTS = 12
GRILLE_COLUMNS = 19
GRILLE_ROWS = 17
INTAKE_ROWS = 12
GRILLE_HALF_WIDTH_RATIO = 0.43
GRILLE_FRONT_RATIO = -0.485
GRILLE_BOW_RATIO = 0.12


def _grille_depth(x_fraction: float) -> float:
    return GRILLE_FRONT_RATIO + GRILLE_BOW_RATIO * x_fraction**2


def _bowed_strip(width: float, depth: float, height: float, bottom: float, top: float,
                 inset: float, thickness: float, color: str) -> Part:
    """Closed curved strip, with thickness extending toward the heater's back."""
    positions = []
    for segment in range(GRILLE_SEGMENTS + 1):
        fraction = 2 * segment / GRILLE_SEGMENTS - 1
        x = width * GRILLE_HALF_WIDTH_RATIO * fraction
        y = depth * (_grille_depth(fraction) + inset)
        positions.extend(((x, y, height * bottom), (x, y, height * top),
                          (x, y + depth * thickness, height * top),
                          (x, y + depth * thickness, height * bottom)))
    triangles = [(0, 2, 1), (0, 3, 2)]
    for segment in range(GRILLE_SEGMENTS):
        for edge in range(4):
            a, b = 4 * segment + edge, 4 * segment + (edge + 1) % 4
            triangles.extend(((a, b, b + 4), (a, b + 4, a + 4)))
    end = GRILLE_SEGMENTS * 4
    triangles.extend(((end, end + 1, end + 2), (end, end + 2, end + 3)))
    return mesh_part(positions, outward(positions, triangles), color)


def ceramic_fan_heater(width: float, depth: float, height: float) -> Geometry:
    outline = _rounded_rectangle_points(width, depth, min(width, depth) * 0.15)
    top_outline = tuple((x, y * 0.98) for x, y in outline)
    rear_outline = tuple((x, y + depth * 0.15) for x, y in _rounded_rectangle_points(
        width * 0.94, depth * 0.66, min(width, depth) * 0.12))
    strokes = (rect(0, 0, width, depth, fill="appliance-white"),
               circle(0, 0, min(width, depth) * 0.12),
               rect(0, -depth * 0.43, width * 0.8, depth * 0.06, fill="metal"))
    parts = [
        prism(outline, 0, height * 0.15, "appliance-white"),
        prism(top_outline, height * 0.84, height * 0.985, "appliance-white"),
        # The rear shell stops behind the guard so it cannot conceal the grille recess.
        prism(rear_outline, height * 0.15, height * 0.84, "appliance-white"),
        _bowed_strip(width, depth, height, 0.15, 0.84, 0.014, 0.025, "screen"),
    ]
    for sign in (-1, 1):
        parts.append(box(sign * width * 0.465, 0, height * 0.15, height * 0.84,
                         width * 0.07, depth * 0.68, "appliance-white"))
    for column in range(GRILLE_COLUMNS):
        fraction = 2 * column / (GRILLE_COLUMNS - 1) - 1
        parts.append(box(width * GRILLE_HALF_WIDTH_RATIO * fraction,
                         depth * (_grille_depth(fraction) + 0.004),
                         height * 0.155, height * 0.835,
                         width * 0.006, depth * 0.008, "metal"))
    for row in range(GRILLE_ROWS):
        bottom = 0.16 + row * 0.67 / (GRILLE_ROWS - 1)
        parts.append(_bowed_strip(width, depth, height, bottom, bottom + 0.005,
                                  0, 0.008, "metal"))
    for row in range(INTAKE_ROWS):
        bottom = 0.19 + row * 0.60 / (INTAKE_ROWS - 1)
        parts.append(box(0, depth * 0.487, height * bottom, height * (bottom + 0.018),
                         width * 0.74, depth * 0.012, "screen"))
    # Top touch button and discrete mode marks, rather than invented thermostat dials.
    button_radius = min(width, depth) * 0.11
    parts.append(prism(circle(0, 0, button_radius)["points"],
                       height * 0.985, height, "metal"))
    for fraction in (-0.18, 0, 0.18):
        parts.append(box(width * fraction, -depth * 0.22, height * 0.985, height * 0.99,
                         width * 0.055, depth * 0.018, "screen"))
    parts.append(box(0, -depth * 0.492, height * 0.88, height * 0.92,
                     width * 0.11, depth * 0.014, "metal-black"))
    return strokes, tuple(parts)
