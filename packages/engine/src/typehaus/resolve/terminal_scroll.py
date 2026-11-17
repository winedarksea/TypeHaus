"""Representative openings of the Reggio 412 cast scroll grille."""
from __future__ import annotations

from shapely.geometry import Point

# One quadrant of the 12 x 3.5 in face, simplified from the 412 spec drawing.
# The apertures are mirrored so the center web and both ends cast in one piece.
_QUADRANT_IN = (
    ((.39, .89), (1.14, .89), (1.54, .48), (1.36, .39), (1.22, .17),
     (1.01, .43), (.91, .38), (.74, .48), (.52, .51), (.48, .72)),
    ((1.46, .89), (1.94, .89), (1.70, .62)),
    ((1.86, .48), (2.26, .89), (3.01, .89), (2.91, .69), (2.88, .51),
     (2.65, .48), (2.52, .39), (2.42, .43), (2.18, .17), (2.05, .37)),
    ((3.42, .89), (3.42, .13), (3.26, .17), (3.12, .32), (3.22, .47),
     (3.22, .60), (3.13, .78), (3.30, .89)),
    ((3.62, .89), (3.84, .89), (3.84, .75), (4.30, .75), (4.30, .41),
     (3.85, .41), (3.85, .10), (3.62, .10), (3.62, .48), (3.75, .48),
     (3.75, .69), (3.62, .69)),
    ((4.56, .68), (4.81, .68), (4.81, .89), (4.56, .89)),
)
_MIDLINE_IN = (
    ((.98, 0), (.80, .16), (.64, .26), (.48, .28), (.35, .23), (.24, .16),
     (.14, .24), (.23, .36), (.29, .52), (.29, .67), (.21, .81), (.11, .89)),
    ((3.23, 0), (3.05, .19), (2.96, .26), (2.82, .27), (2.70, .22),
     (2.61, .13), (2.54, .17), (2.35, 0)),
    ((4.81, 0), (4.81, .47), (4.56, .47), (4.56, .17), (4.10, .17), (4.10, 0)),
)


def scroll_openings(width, height):
    # The central scroll holes straddle the horizontal axis.
    midline = tuple(upper + tuple((x, -y) for x, y in reversed(upper) if y)
                    for upper in _MIDLINE_IN)
    x_scale, y_scale = width / 12, height / 3.5
    shaped = [tuple((sx * x * x_scale, sy * y * y_scale) for x, y in ring)
              for sx in (-1, 1) for sy in (-1, 1) for ring in _QUADRANT_IN]
    shaped.extend(tuple((sx * x * x_scale, y * y_scale) for x, y in ring)
                  for sx in (-1, 1) for ring in midline)
    shaped.extend(tuple((sx * (x + dx) * x_scale, dy * y_scale) for dx, dy in
                        Point(0, 0).buffer(diameter / 2, quad_segs=6).exterior.coords[:-1])
                  for sx in (-1, 1) for x, diameter in ((1.70, .58), (5.5, .19)))
    return tuple(shaped)
