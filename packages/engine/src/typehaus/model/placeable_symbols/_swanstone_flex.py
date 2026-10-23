"""Swanstone pan, stock Flex front and separately supported custom north glass.

The front is a stock-size design intent, not an approved hybrid installation. A glazier
must size the post/connections and confirm the door-to-post and pane-to-channel details.
"""

from math import cos, pi, sin

from typehaus.model.placeable_symbols._frame import Part, box, circle, prism, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._swanstone_flex_config import BATH2_SHOWER


def front_opening_limits(width: float) -> tuple[float, float]:
    """Local x of the post's inside face and the finished south wall, metres."""
    dimensions = BATH2_SHOWER
    scale = width / dimensions.pan_width
    return (-width / 2,
            width / 2 - dimensions.wall_panel_thickness * scale)


def door_swing_outline(width: float, depth: float) -> tuple[tuple[float, float], ...]:
    """Conservative outward 90° leaf sweep; includes the projecting handle."""
    dimensions = BATH2_SHOWER
    sx, sy = width / dimensions.pan_width, depth / dimensions.pan_depth
    _, south = front_opening_limits(width)
    pivot = south - dimensions.rail_width * sx
    front = -depth / 2 + dimensions.threshold_depth * sy / 2
    radius = (dimensions.door_swing_radius + dimensions.handle_projection) * sx
    return ((pivot, front), *(
        (pivot - radius * cos(pi * i / (2 * dimensions.swing_segments)),
         front - radius * sin(pi * i / (2 * dimensions.swing_segments)))
        for i in range(dimensions.swing_segments + 1)))


def swanstone_flex(width: float, depth: float, height: float):
    dimensions = BATH2_SHOWER
    sx, sy, sz = (width / dimensions.pan_width, depth / dimensions.pan_depth,
                  height / dimensions.model_height)
    parts: list[Part] = []

    def solid(x, y, z0, z1, w, d, role, material=None):
        part = box(x * sx, y * sy, z0 * sz, z1 * sz, w * sx, d * sy, role)
        if material:
            part["material_ref"] = material
        parts.append(part)

    half_width, half_depth = dimensions.pan_width / 2, dimensions.pan_depth / 2
    rear = dimensions.pan_depth - dimensions.interior_depth - dimensions.threshold_depth
    basin_offset = (dimensions.threshold_depth - rear) / 2
    pan_material = "solid-surface-panel"
    solid(0, 0, 0, dimensions.floor_thickness, dimensions.pan_width, dimensions.pan_depth, "carrara", pan_material)
    # These four closed wedges give the basin a visible depression without pretending
    # the plumbing's authored 2 5/8-inch offset is a different molded drain position.
    vertices = []
    for index in range(dimensions.basin_segments):
        angle = 2 * pi * index / dimensions.basin_segments
        dx, dy = cos(angle), sin(angle)
        radius = min(dimensions.interior_width / 2 / max(abs(dx), 1e-9),
                     dimensions.interior_depth / 2 / max(abs(dy), 1e-9))
        vertices.extend((
            (radius * dx * sx, (radius * dy + basin_offset) * sy,
             dimensions.basin_edge_height * sz),
            (dimensions.drain_diameter / 2 * dx * sx,
             dimensions.drain_diameter / 2 * dy * sy, dimensions.drain_floor_height * sz),
            (radius * dx * sx, (radius * dy + basin_offset) * sy, dimensions.floor_thickness * sz),
            (dimensions.drain_diameter / 2 * dx * sx,
             dimensions.drain_diameter / 2 * dy * sy, dimensions.floor_thickness * sz)))
    triangles = []
    for index in range(dimensions.basin_segments):
        a, b = index * 4, ((index + 1) % dimensions.basin_segments) * 4
        triangles.extend(((a, b, b + 1), (a, b + 1, a + 1),
                          (a + 2, a + 3, b + 3), (a + 2, b + 3, b + 2),
                          (a, a + 2, b + 2), (a, b + 2, b),
                          (a + 1, b + 1, b + 3), (a + 1, b + 3, a + 3)))
    basin = mesh_part(vertices, triangles, "carrara")
    basin["material_ref"] = pan_material
    parts.append(basin)
    solid(0, -half_depth + dimensions.threshold_depth / 2, dimensions.floor_thickness,
          dimensions.threshold_height, dimensions.pan_width, dimensions.threshold_depth, "carrara", pan_material)
    side = (dimensions.pan_width - dimensions.interior_width) / 2
    for x in (-half_width + side / 2, half_width - side / 2):
        solid(x, 0, dimensions.floor_thickness, dimensions.pan_height,
              side, dimensions.pan_depth, "carrara", pan_material)
    solid(0, half_depth - rear / 2, dimensions.floor_thickness, dimensions.pan_height,
          dimensions.interior_width, rear, "carrara", pan_material)
    parts.append(prism(circle(0, 0, dimensions.drain_diameter * sx / 2)["points"],
                       dimensions.floor_thickness * sz,
                       dimensions.drain_floor_height * sz, "chrome"))

    front = -half_depth + dimensions.threshold_depth / 2
    post = -half_width - dimensions.post_width / 2
    deck = dimensions.deck_datum - dimensions.finished_floor_datum
    solid(post, front, deck, dimensions.model_height,
          dimensions.post_width, dimensions.post_width, "chrome")
    north, south = (value / sx for value in front_opening_limits(width))
    rail = dimensions.rail_width
    z0 = dimensions.threshold_height
    z1 = z0 + dimensions.front_height
    for x in (north + rail / 2, south - rail / 2):
        solid(x, front, z0, z1, rail, rail, "chrome")
    for z in (z0, z1 - rail):
        solid((north + south) / 2, front, z, z + rail, south - north, rail, "chrome")
    pivot = south - rail
    meeting = pivot - dimensions.door_swing_radius
    for left, right in ((north + rail, meeting), (meeting, pivot)):
        solid((left + right) / 2, front, z0 + rail, z1 - rail,
              right - left, dimensions.front_glass_thickness, "glass")
    solid(meeting, front, z0 + rail, z1 - rail,
          dimensions.seal_width, rail, "seal")
    solid((meeting + pivot) / 2, front, z0 + rail, z0 + rail + dimensions.seal_width,
          pivot - meeting, rail, "seal")
    handle_z = z0 + dimensions.handle_center_height
    solid(meeting + rail, front - dimensions.handle_projection,
          handle_z - dimensions.handle_height / 2, handle_z + dimensions.handle_height / 2,
          dimensions.seal_width * 2, dimensions.seal_width * 2, "chrome")
    for z in (handle_z - dimensions.handle_height / 2, handle_z + dimensions.handle_height / 2):
        solid(meeting + rail, front - dimensions.handle_projection / 2,
              z, z + dimensions.seal_width, dimensions.seal_width * 2,
              dimensions.handle_projection, "chrome")
    # The return starts on Corian, not on the pan, and has its own three-sided support.
    channel = dimensions.channel_width
    back = half_depth - dimensions.wall_panel_thickness
    solid(post, (front + back) / 2, deck, dimensions.model_height,
          dimensions.north_glass_thickness, back - front, "glass")
    for z in (deck, dimensions.model_height - channel):
        solid(post, (front + back) / 2, z, z + channel,
              channel, back - front, "chrome")
    solid(post, back - channel / 2, deck, dimensions.model_height,
          channel, channel, "chrome")
    strokes = (rect(0, 0, width, depth, fill="carrara"),
               circle(0, 0, dimensions.drain_diameter * sx / 2))
    return strokes, tuple(parts)
