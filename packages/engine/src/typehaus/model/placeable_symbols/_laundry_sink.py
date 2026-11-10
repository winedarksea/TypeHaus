"""Cabinet utility tub with an open stainless basin and representative flex-neck faucet.

The 34-inch rim and 43-inch overall envelope follow the catalog convention. Bowl size
uses the QL039 sibling of the selected QL033Y; cabinet and faucet profiles are illustrative.
"""

from math import cos, pi, sin

from typehaus.model.placeable_symbols._basin import rectangular_basin
from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, circle, line, rect
from typehaus.model.placeable_symbols._sektion_fronts import round_bar

INCH_M = 0.0254
LAUNDRY_TUB_DECK_FRACTION = 34.0 / 43.0
LAUNDRY_TUB_BASIN_IN = (22.31, 19.5)
LAUNDRY_TUB_BASIN_DEPTH_M = 9.0 * INCH_M
RIM_THICKNESS_M = 0.0625 * INCH_M
BASIN_WALL_THICKNESS_M = 0.125 * INCH_M
CABINET_WALL_THICKNESS_M = 0.625 * INCH_M
DOOR_REVEAL_M = 0.125 * INCH_M
FAUCET_BEND_SEGMENTS = 12


def _utility_faucet(width, depth, deck, height, basin_y):
    faucet_height = height - deck
    radius = min(0.5 * INCH_M, width * 0.025, faucet_height * 0.06, depth * 0.025)
    faucet_y = depth * 0.42
    spout_y = basin_y + depth * 0.10
    bend_height = min(faucet_height * 0.35, (faucet_y - spout_y) / 2)
    bend_base = height - radius - bend_height
    bend_center_y = (faucet_y + spout_y) / 2
    bend_reach = (faucet_y - spout_y) / 2
    points = [
        (0, bend_center_y + bend_reach * cos(pi * step / FAUCET_BEND_SEGMENTS),
         bend_base + bend_height * sin(pi * step / FAUCET_BEND_SEGMENTS))
        for step in range(FAUCET_BEND_SEGMENTS + 1)
    ]
    parts = [
        round_bar((0, faucet_y, deck), (0, faucet_y, deck + radius), radius * 1.8, "metal"),
        round_bar((0, faucet_y, deck), points[0], radius, "metal"),
        *(round_bar(start, end, radius, "metal")
          for start, end in zip(points, points[1:], strict=False)),
        round_bar(points[-1], (0, spout_y, bend_base - faucet_height * 0.20),
                  radius * 1.4, "metal"),
        round_bar((radius, faucet_y, deck + faucet_height * 0.18),
                  (radius * 3, faucet_y, deck + faucet_height * 0.18), radius * 0.6, "metal"),
        round_bar((radius * 3, faucet_y, deck + faucet_height * 0.18),
                  (radius * 3, faucet_y, deck + faucet_height * 0.42), radius * 0.4, "metal"),
    ]
    return parts


def laundry_tub() -> Builder:
    """Leave the entire bowl void clear through both the rim and the cabinet."""

    def build(width: float, depth: float, height: float) -> Geometry:
        deck = height * LAUNDRY_TUB_DECK_FRACTION
        rim_thickness = min(RIM_THICKNESS_M, deck * 0.02)
        kick = min(0.09, deck * 0.12)
        cabinet_wall = min(CABINET_WALL_THICKNESS_M, width * 0.02, depth * 0.02)
        basin_width = min(LAUNDRY_TUB_BASIN_IN[0] * INCH_M, width * 0.94)
        # Reserve a front lip and a wider rear faucet deck inside the declared footprint.
        basin_depth = min(LAUNDRY_TUB_BASIN_IN[1] * INCH_M, depth * 0.80)
        basin_y = -depth * 0.05
        bowl_top = deck - rim_thickness
        bowl_bottom = max(kick, bowl_top - min(LAUNDRY_TUB_BASIN_DEPTH_M,
                                               (bowl_top - kick) * 0.9))
        basin_wall = min(BASIN_WALL_THICKNESS_M, min(basin_width, basin_depth) * 0.02)
        strokes = [rect(0, 0, width, depth, fill="counter"),
                   rect(0, basin_y, basin_width, basin_depth, weight=DETAIL_WEIGHT),
                   circle(0, basin_y, min(basin_width, basin_depth) * 0.06,
                          weight=DETAIL_WEIGHT),
                   line((-width * 0.07, depth * 0.38), (width * 0.07, depth * 0.38))]
        parts = [
            box(0, 0, 0, kick, width * 0.96, depth * 0.90, "cabinet-cream-dark"),
            box(0, 0, kick, kick + cabinet_wall, width, depth, "cabinet-cream"),
            box(0, depth / 2 - cabinet_wall / 2, kick, bowl_top,
                width, cabinet_wall, "cabinet-cream"),
        ]
        for sign in (-1, 1):
            parts.append(box(sign * (width / 2 - cabinet_wall / 2), 0, kick, bowl_top,
                             cabinet_wall, depth, "cabinet-cream"))
            side_rim = (width - basin_width) / 2
            parts.append(box(sign * (width / 2 - side_rim / 2), 0, bowl_top, deck,
                             side_rim, depth, "appliance-steel"))
        for low, high in ((-depth / 2, basin_y - basin_depth / 2),
                          (basin_y + basin_depth / 2, depth / 2)):
            parts.append(box(0, (low + high) / 2, bowl_top, deck,
                             basin_width, high - low, "appliance-steel"))
        reveal = min(DOOR_REVEAL_M, width * 0.01)
        door_width = width / 2 - reveal
        for sign in (-1, 1):
            door_x = sign * width / 4
            front_y = -depth / 2 + cabinet_wall * 1.2
            parts.append(box(door_x, front_y, kick + reveal, bowl_top,
                             door_width, cabinet_wall, "cabinet-cream"))
            pull_y = -depth / 2 + cabinet_wall * 0.5
            parts.append(round_bar((door_x - door_width * 0.18, pull_y, bowl_bottom - cabinet_wall),
                                   (door_x + door_width * 0.18, pull_y, bowl_bottom - cabinet_wall),
                                   cabinet_wall * 0.20, "metal"))
        parts.extend(rectangular_basin(0, basin_y, basin_width, basin_depth,
                                       bowl_bottom, bowl_top, basin_wall, "appliance-steel"))
        drain_radius = min(basin_width, basin_depth) * 0.045
        parts.append(round_bar((0, basin_y, bowl_bottom + basin_wall),
                               (0, basin_y, bowl_bottom + basin_wall * 1.5),
                               drain_radius, "metal"))
        parts.extend(_utility_faucet(width, depth, deck, height, basin_y))
        return tuple(strokes), tuple(parts)

    return build
