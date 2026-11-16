"""Generic digital thermostat; the display faces the room along local -Y."""

from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import box, rect
from typehaus.model.placeable_symbols._mesh import mesh_part


@dataclass(frozen=True)
class ThermostatGeometryConfig:
    corner_fraction: float = 0.08
    face_inset_fraction: float = 0.025
    housing_front_depth_fraction: float = 0.16
    bevel_depth_fraction: float = 0.18
    relief_depth_fraction: float = 0.025
    screen_width_fraction: float = 0.76
    screen_bottom_fraction: float = 0.36
    screen_top_fraction: float = 0.84
    digit_width_fraction: float = 0.17
    digit_height_fraction: float = 0.29
    digit_center_fraction: float = 0.115
    digit_bottom_fraction: float = 0.45
    segment_thickness_fraction: float = 0.025
    button_width_fraction: float = 0.23
    button_height_fraction: float = 0.13
    button_center_fraction: float = 0.22
    button_bottom_fraction: float = 0.13
    button_mark_fraction: float = 0.085


THERMOSTAT_GEOMETRY = ThermostatGeometryConfig()
# A fixed illustrative reading, not simulated room temperature. Segments: top clockwise,
# then middle; using geometry keeps the digits legible in both the viewer and GLB export.
DISPLAY_DIGIT_SEGMENTS = ((0, 1, 2), (0, 1, 6, 4, 3))  # 72


def _housing(width, depth, height):
    config = THERMOSTAT_GEOMETRY
    corner = min(width, height) * config.corner_fraction
    inset = min(width, height) * config.face_inset_fraction
    outline = ((-width / 2 + corner, 0), (width / 2 - corner, 0),
               (width / 2, corner), (width / 2, height - corner),
               (width / 2 - corner, height), (-width / 2 + corner, height),
               (-width / 2, height - corner), (-width / 2, corner))
    front = -depth / 2 + depth * config.housing_front_depth_fraction
    positions = []
    for y, margin in ((depth / 2, 0),
                      (front + depth * config.bevel_depth_fraction, 0), (front, inset)):
        positions.extend((x * (1 - 2 * margin / width), y,
                          margin + z * (1 - 2 * margin / height)) for x, z in outline)
    triangles = [(0, index + 1, index) for index in range(1, 7)]
    triangles.extend((16, 16 + index, 17 + index) for index in range(1, 7))
    for ring in (0, 8):
        for index in range(8):
            following = (index + 1) % 8
            triangles.extend(((ring + index, ring + following, ring + 8 + following),
                              (ring + index, ring + 8 + following, ring + 8 + index)))
    return mesh_part(positions, triangles, "plastic-white"), front


def thermostat(width, depth, height):
    config = THERMOSTAT_GEOMETRY
    housing, front = _housing(width, depth, height)
    relief = depth * config.relief_depth_fraction
    parts = [housing]

    def face_box(x, bottom, top, face_width, color, layer=0):
        parts.append(box(x, front - relief * (layer + 0.5), bottom, top,
                         face_width, relief, color))

    face_box(0, height * config.screen_bottom_fraction, height * config.screen_top_fraction,
             width * config.screen_width_fraction, "screen")
    digit_width = width * config.digit_width_fraction
    digit_height = height * config.digit_height_fraction
    thickness = min(width, height) * config.segment_thickness_fraction
    for center, segments in zip((-width * config.digit_center_fraction,
                                 width * config.digit_center_fraction),
                                DISPLAY_DIGIT_SEGMENTS, strict=True):
        bottom = height * config.digit_bottom_fraction
        for segment in segments:
            if segment in (0, 3, 6):
                z = bottom + {0: digit_height, 3: 0, 6: digit_height / 2}[segment]
                face_box(center, z - thickness / 2, z + thickness / 2,
                         digit_width, "plastic-white", layer=1)
            else:
                x = center + (digit_width - thickness) / 2 * (1 if segment in (1, 2) else -1)
                z = bottom + (digit_height / 2 if segment in (1, 5) else 0)
                face_box(x, z + thickness / 2, z + digit_height / 2 - thickness / 2,
                         thickness, "plastic-white", layer=1)
    # Two separate buttons and raised marks read at room scale without texture assets.
    bottom = height * config.button_bottom_fraction
    top = bottom + height * config.button_height_fraction
    for direction in (-1, 1):
        x = direction * width * config.button_center_fraction
        face_box(x, bottom, top, width * config.button_width_fraction, "screen")
        face_box(x, (bottom + top - thickness) / 2, (bottom + top + thickness) / 2,
                 width * config.button_mark_fraction, "plastic-white", layer=1)
        if direction == 1:
            mark_height = height * config.button_mark_fraction
            face_box(x, (bottom + top - mark_height) / 2, (bottom + top + mark_height) / 2,
                     thickness, "plastic-white", layer=2)
    return (rect(0, 0, width, depth),), tuple(parts)
