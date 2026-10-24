"""Illustrative concealed wastes: chrome tubular P-trap or rear-routed white RÄNNILEN.

These silhouettes do not define rough-ins; the FixtureType's ServicePorts own those.
"""

from typehaus.model.placeable_symbols._sektion_fronts import round_bar

TUBE_DIAMETER_IN = 1.25
TRAP_BEND_SEGMENTS = 12


def lav_waste(depth, deck, basin_bottom, basin_y, *, space_saving=False, base_in=None):
    from math import cos, pi, sin

    base_in = (8.375 if space_saving else 0) if base_in is None else base_in
    reference_deck = 36 - base_in
    scale = min(deck / reference_deck, depth / 8)
    radius = TUBE_DIAMETER_IN * scale / 2
    wall_y = depth / 2 - radius
    arm_z = (20 - base_in) * scale
    bend_radius = 2 * scale
    tail_y = wall_y - 5 * scale if space_saving else basin_y
    color = "plastic-white" if space_saving else "chrome"
    tail_top = basin_bottom - radius
    parts = []
    if space_saving:
        parts.append(round_bar((0, basin_y, tail_top), (0, tail_y, tail_top), radius, color))
    parts.append(round_bar((0, tail_y, tail_top), (0, tail_y, arm_z), radius, color))
    # A swept semicircle makes the low U readable through an open cabinet back.
    for index in range(TRAP_BEND_SEGMENTS):
        points = []
        for step in (index, index + 1):
            angle = pi * step / TRAP_BEND_SEGMENTS
            points.append((0, tail_y + bend_radius * (1-cos(angle)),
                           arm_z - bend_radius * sin(angle)))
        parts.append(round_bar(*points, radius, color))
    parts.append(round_bar((0, tail_y + 2*bend_radius, arm_z),
                           (0, wall_y, arm_z), radius, color))
    return parts
