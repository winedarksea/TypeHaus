"""Shared AXSTAD faces and BAGGANÄS hardware, facing local -y.

Overall sizes are IKEA US dimensions. Rail width and the softened inner profile are
visual approximations, not manufacturing profiles or drilling templates.
"""

from math import cos, pi, sin

from typehaus.model.placeable_symbols._frame import Part
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.quantities import inch

DOOR_THICKNESS_M = inch(0.75).meters
DOOR_BORDER_M = inch(2).meters
PANEL_RECESS_M = inch(0.25).meters
PROFILE_WIDTH_M = inch(0.25).meters
PROFILE_STEPS = 4
REVEAL_M = inch(0.125).meters
KNOB_DIAMETER_M = inch(13 / 16).meters
KNOB_PROJECTION_M = inch(15 / 16).meters
PULL_LENGTH_M = inch(5.625).meters
PULL_HOLE_SPACING_M = inch(5.0625).meters
PULL_PROJECTION_M = inch(1.25).meters
PULL_DIAMETER_M = inch(0.375).meters
# Washer diameter and thickness are visual estimates; mounting spacing is published.
WASHER_DIAMETER_M = inch(0.5).meters
WASHER_THICKNESS_M = inch(0.0625).meters
ROUND_SEGMENTS = 16
HARDWARE_EDGE_OFFSET_M = inch(2).meters


def axstad_front(
    width: float,
    front: float,
    thickness: float,
    bottom: float,
    top: float,
    *,
    center_x: float = 0.0,
) -> list[Part]:
    """A closed face with an eased inner transition and a recessed panel."""
    border = min(DOOR_BORDER_M, width / 4, (top - bottom) / 4)
    recess = min(PANEL_RECESS_M, thickness / 2)
    profile = min(PROFILE_WIDTH_M, border / 3)
    rings = [(0.0, 0.0), (border - profile, 0.0)]
    for step in range(1, PROFILE_STEPS + 1):
        angle = pi / 2 * step / PROFILE_STEPS
        rings.append((border - profile + profile * sin(angle), recess * (1 - cos(angle))))
    vertices = []
    for inset, y in rings:
        vertices.extend(
            (
                (center_x - width / 2 + inset, front + y, bottom + inset),
                (center_x + width / 2 - inset, front + y, bottom + inset),
                (center_x + width / 2 - inset, front + y, top - inset),
                (center_x - width / 2 + inset, front + y, top - inset),
            )
        )
    triangles = []
    for ring in range(len(rings) - 1):
        for side in range(4):
            a, b = ring * 4 + side, ring * 4 + (side + 1) % 4
            c, d = a + 4, b + 4
            triangles.extend(((a, b, d), (a, d, c)))
    last = (len(rings) - 1) * 4
    triangles.extend(((last, last + 1, last + 2), (last, last + 2, last + 3)))
    back = len(vertices)
    vertices.extend((x, front + thickness, z) for x, _, z in vertices[:4])
    triangles.extend(((back, back + 2, back + 1), (back, back + 3, back + 2)))
    for side in range(4):
        following = (side + 1) % 4
        triangles.extend(
            ((side, back + following, following), (side, back + side, back + following))
        )
    return [mesh_part(vertices, triangles, "appliance-white")]


def round_bar(start: tuple, end: tuple, radius: float, color: str = "metal-black") -> Part:
    """Closed round stock along either a horizontal pull or a projecting stem."""
    direction = tuple(end[i] - start[i] for i in range(3))
    length = sum(value * value for value in direction) ** 0.5
    axis = tuple(value / length for value in direction)
    reference = (0, 0, 1) if abs(axis[2]) < 0.9 else (1, 0, 0)
    first = (
        axis[1] * reference[2] - axis[2] * reference[1],
        axis[2] * reference[0] - axis[0] * reference[2],
        axis[0] * reference[1] - axis[1] * reference[0],
    )
    norm = sum(value * value for value in first) ** 0.5
    first = tuple(value / norm for value in first)
    second = (
        axis[1] * first[2] - axis[2] * first[1],
        axis[2] * first[0] - axis[0] * first[2],
        axis[0] * first[1] - axis[1] * first[0],
    )
    vertices = [
        tuple(
            center[i]
            + radius
            * (
                first[i] * cos(2 * pi * n / ROUND_SEGMENTS)
                + second[i] * sin(2 * pi * n / ROUND_SEGMENTS)
            )
            for i in range(3)
        )
        for center in (start, end)
        for n in range(ROUND_SEGMENTS)
    ]
    vertices.extend((start, end))
    triangles = []
    for n in range(ROUND_SEGMENTS):
        following = (n + 1) % ROUND_SEGMENTS
        triangles.extend(
            (
                (n, following, following + ROUND_SEGMENTS),
                (n, following + ROUND_SEGMENTS, n + ROUND_SEGMENTS),
                (2 * ROUND_SEGMENTS, following, n),
                (2 * ROUND_SEGMENTS + 1, n + ROUND_SEGMENTS, following + ROUND_SEGMENTS),
            )
        )
    return mesh_part(vertices, triangles, color)


def bagganas_knob(x: float, front: float, z: float, scale: float = 1.0) -> list[Part]:
    diameter, projection = KNOB_DIAMETER_M * scale, KNOB_PROJECTION_M * scale
    head_depth = diameter / 4
    return [
        round_bar((x, front, z), (x, front - projection + head_depth, z), diameter / 5),
        round_bar(
            (x, front - projection + head_depth, z), (x, front - projection, z), diameter / 2
        ),
    ]


def bagganas_pull(x: float, front: float, z: float, scale: float = 1.0) -> list[Part]:
    radius = PULL_DIAMETER_M * scale / 2
    projection = PULL_PROJECTION_M * scale
    length = PULL_LENGTH_M * scale
    spacing = PULL_HOLE_SPACING_M * scale
    washer = WASHER_THICKNESS_M * scale
    bar_y = front - projection + radius
    parts = [round_bar((x - length / 2, bar_y, z), (x + length / 2, bar_y, z), radius)]
    for sign in (-1, 1):
        mount_x = x + sign * spacing / 2
        parts.extend(
            (
                round_bar(
                    (mount_x, front, z), (mount_x, front - washer, z), WASHER_DIAMETER_M * scale / 2
                ),
                round_bar((mount_x, front - washer, z), (mount_x, bar_y, z), radius),
            )
        )
    return parts
