"""Selected wall-light silhouettes, scaled from product inches.

References: waclighting.com/product/{roland,tube-2}/;
modernforms.com/product/bantam/; hinkley.com/50910bk.html;
Livex's 4451/4452 installation drawing and 4451-04 catalog photo.
Overall envelopes and Roland/Bantam canopies follow published drawings. Curves,
wall thicknesses, arms and small hardware are photo estimates, not fabrication data.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import circle, line, rect
from typehaus.model.placeable_symbols._sconce_geometry import BLACK, SconceFrame

ROLAND_SIZE = (4.5, 2.5, 12.0)
BANTAM_SIZE = (9.0, 4.0, 3.5)
SOREN_SIZE = (5.0, 4.8, 14.3)
TUBE_SIZE = (4.5, 5.0, 5.0)
CANDLE_SIZE = (4.25, 7.75, 11.25)
CANDLE_ARM_STEPS = 24


def roland_sconce(width: float, depth: float, height: float) -> Geometry:
    frame = SconceFrame(width, depth, height, ROLAND_SIZE)
    # Roland is an etched acrylic blade with a horizontal black belt, not a black box
    # with end slots. The square driver canopy sits behind the middle of the blade.
    parts = (frame.block(0, .5, 3.75, 8.25, 4.5, 1),
             frame.block(0, 1.65, 5.55, 6.45, 1.0, 1.3),
             frame.block(0, 2.35, 0, 5.3, 4.5, .30, "lamp"),
             frame.block(0, 2.35, 6.7, 12, 4.5, .30, "lamp"),
             frame.block(0, 2.325, 5.3, 6.7, 4.5, .35))
    strokes = (rect(0, depth * .3, width, depth * .4, fill=BLACK),
               rect(0, -depth * .44, width, depth * .12, fill="lamp"))
    return strokes, parts


def bantam_sconce(width: float, depth: float, height: float) -> Geometry:
    frame = SconceFrame(width, depth, height, BANTAM_SIZE)
    # A continuous stepped extrusion; only the horizontal shelf's top is luminous.
    parts = (frame.block(0, .75, 0, 3.5, 9, 1.5),
             frame.block(0, 2.75, 0, 1.4, 9, 2.5),
             frame.block(0, 2.75, 1.4, 1.5, 8.5, 2.1, "lamp"))
    strokes = (rect(0, 0, width, depth, fill=BLACK),
               rect(0, -depth * .1875, width * 8.5 / 9, depth * 2.1 / 4, fill="lamp"))
    return strokes, parts


def soren_sconce(width: float, depth: float, height: float) -> Geometry:
    frame = SconceFrame(width, depth, height, SOREN_SIZE)
    projection = 3.3
    parts = [frame.wall_plate(.25, 11.8, 2.5, 2.5, .5),
             frame.block(0, 1.9, 11.55, 11.95, .55, 3.1),
             frame.turned(projection, ((.24, 10.4), (.24, 13.7))),
             frame.turned(projection, ((1.5, 8.2), (1.5, 9.7), (1.46, 10.0),
                                       (1.3, 10.35), (.95, 10.65), (.4, 10.85))),
             # Inner return and annular end faces leave the bottom genuinely open.
             frame.turned(projection, ((1.42, 0), (1.42, 8.25),
                                       (1.36, 8.25), (1.36, 0)),
                          "clear-glass", hollow=True, fluting_depth=.025),
             frame.turned(projection, ((.5, 7.35), (.5, 8.25))),
             # The selected lamp is an A19, rather than the product photo's T lamp.
             frame.turned(projection, ((.42, 7.4), (.5, 6.9), (.85, 6.5), (1.12, 6.0),
                                       (1.18, 5.5), (1.1, 5.05), (.7, 4.7), (.15, 4.6)),
                          "lamp")]
    strokes = (rect(0, depth * (.5 - .25 / 4.8), width, depth * .5 / 4.8, fill=BLACK),
               circle(0, depth * (.5 - projection / 4.8),
                      min(width * 1.5 / 5, depth * 1.5 / 4.8), fill="glass"))
    return strokes, tuple(parts)


def tube_wall_sconce(width: float, depth: float, height: float) -> Geometry:
    frame = SconceFrame(width, depth, height, TUBE_SIZE)
    projection, radius = 2.75, 2.25
    parts = (frame.block(0, .20, .4, 4.6, 4.2, .4),
             frame.block(0, .65, 1.9, 3.1, 1.2, .6),
             # Return up the inner bore to keep a black cutoff lip around the lens.
             frame.turned(projection, ((radius, 0), (radius, .25), (2.22, .27),
                                       (2.22, .29), (radius, .31), (radius, 5), (2.0, 5),
                                       (2.0, .3), (1.9, .3), (1.9, 0)), hollow=True),
             frame.turned(projection, ((2.0, .3), (2.0, .36)), "lamp"),
             frame.turned(projection, ((2.0, 4.85), (2.0, 5))))
    strokes = (rect(0, depth * .46, width * 4.2 / 4.5, depth * .08, fill=BLACK),
               circle(0, -depth * .05, min(width / 2, depth * radius / 5), fill=BLACK))
    return strokes, parts


def candle_wall_sconce(width: float, depth: float, height: float) -> Geometry:
    frame = SconceFrame(width, depth, height, CANDLE_SIZE)
    projection = 5.625
    # A U-shaped arm is the characteristic Heritage silhouette. A cubic follows the
    # photo's smooth bend without disconnected cylinders or a decorative gothic scroll.
    control = ((.45, 4.8), (2.0, 4.8), (2.8, -5.4), (projection, 4.35))
    path = []
    for index in range(CANDLE_ARM_STEPS + 1):
        t = index / CANDLE_ARM_STEPS
        weights = ((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3)
        path.append(tuple(sum(weight * p[axis] for weight, p in zip(weights, control, strict=True))
                          for axis in range(2)))
    # Lift the curve's low point to leave a little metal below the oval backplate.
    minimum_z = min(z for _, z in path)
    path = tuple((p, .15 + (z - minimum_z) * 4.65 / (4.8 - minimum_z)) for p, z in path)
    parts = [frame.wall_plate(.18, 4.25, 2.0, 3.0, .36),
             frame.wall_plate(.39, 4.25, 1.8, 2.8, .10),
             frame.bent_rod(path, .13),
             frame.turned(projection, ((.25, 4.35), (.7, 4.45), (1.5, 4.7),
                                       (2.125, 4.9), (2.125, 5.0))),
             frame.turned(projection, ((.55, 5), (.55, 5.35))),
             frame.turned(projection, ((.43, 5.35), (.43, 8.45)), "cabinet-cream"),
             frame.turned(projection, ((.20, 8.45), (.40, 8.7), (.58, 9.2), (.6, 9.65),
                                       (.5, 10.2), (.3, 10.75), (.025, 11.25)), "lamp")]
    for x in (-1.6, 1.6):
        # Small ball nuts on either side of the arm's wall connection.
        # An anisotropically scaled sphere is unnecessary at this size; shallow bosses
        # preserve the hardware silhouette in both exports and the plan view.
        parts.append(frame.block(x, .49, 4.1, 4.4, .30, .18))
    strokes = (rect(0, depth * (.5 - .18 / 7.75), width * 4 / 4.25,
                    depth * .36 / 7.75, fill=BLACK),
               line(frame.point(0, .45, 0)[:2], frame.point(0, projection, 0)[:2]),
               circle(0, depth * (.5 - projection / 7.75),
                      min(width / 2, depth * 2.125 / 7.75), fill=BLACK))
    return strokes, tuple(parts)
