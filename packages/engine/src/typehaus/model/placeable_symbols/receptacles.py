"""Receptacle faces in the shared local frame, with the wall at positive depth."""

from typehaus.model.placeable_symbols._frame import box, circle, prism, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._receptacle_config import RECEPTACLE_GEOMETRY as CFG


def _depth_extrusion(outline, front, back, color):
    """Sweep a convex counterclockwise X/Z outline; front normals face local -Y."""
    count = len(outline)
    vertices = [(x, y, z) for y in (front, back) for x, z in outline]
    triangles = []
    for index in range(1, count - 1):
        triangles.extend(((0, index, index + 1),
                          (count, count + index + 1, count + index)))
    for index in range(count):
        following = (index + 1) % count
        triangles.extend(((index, count + index, count + following),
                          (index, count + following, following)))
    return mesh_part(vertices, triangles, color)


def _clipped_outline(center_x, center_z, width, height, corner_fraction):
    half_width, half_height = width / 2, height / 2
    clip = min(width, height) * corner_fraction
    return [(center_x + x, center_z + z) for x, z in (
        (-half_width + clip, -half_height), (half_width - clip, -half_height),
        (half_width, -half_height + clip), (half_width, half_height - clip),
        (half_width - clip, half_height), (-half_width + clip, half_height),
        (-half_width, half_height - clip), (-half_width, -half_height + clip))]


def _housing(width, depth, height, front):
    # Depth remains the authored schematic envelope; later installation modeling can
    # replace this body without changing how the plate and sockets are assembled.
    return box(0, (front + depth / 2) / 2, 0, height,
               width, depth / 2 - front, "electrical-orange")


def _plate(width, height, front, back):
    outline = _clipped_outline(0, height / 2, width * CFG.plate_width_fraction,
                               height * CFG.plate_height_fraction, CFG.plate_corner_fraction)
    return _depth_extrusion(outline, front, back, "electrical-plate")


def _slot_marks(center_x, center_z, width, height, front, back, configuration):
    spacing = width * CFG.blade_spacing_fraction
    blade_width = width * CFG.blade_width_fraction
    blade_height = height * CFG.blade_height_fraction
    parts = []

    def blade(x, z, slot_width, slot_height):
        return box(x, (front + back) / 2, z - slot_height / 2, z + slot_height / 2,
                   slot_width, back - front, "electrical-recess")

    for x in (center_x - spacing, center_x + spacing):
        slot_width, slot_height = ((blade_height, blade_width) if configuration == "240"
                                   else (blade_width, blade_height))
        parts.append(blade(x, center_z, slot_width, slot_height))
    if configuration == "120-20":
        parts.append(blade(center_x - spacing + blade_height / 4, center_z,
                           blade_height / 2, blade_width))
    elif configuration == "240":
        parts.append(blade(center_x - spacing, center_z + blade_height / 4,
                           blade_width, blade_height / 2))
    elif configuration == "240-four-wire":
        parts.append(blade(center_x, center_z + height * CFG.neutral_offset_fraction,
                           blade_width, blade_height))
    ground_width = width * CFG.ground_width_fraction
    ground_height = height * CFG.ground_height_fraction
    ground_center = center_z - height * CFG.ground_offset_fraction
    # A flat bottom and faceted arch read as a ground opening without a boolean hole.
    outline = [(center_x + x * ground_width, ground_center + z * ground_height)
               for x, z in ((-.5, -.5), (.5, -.5), (.5, 0), (.25, .5),
                            (-.25, .5), (-.5, 0))]
    parts.append(_depth_extrusion(outline, front, back, "electrical-recess"))
    return parts


def _socket_face(center_x, center_z, width, height, front, back):
    return _depth_extrusion(
        _clipped_outline(center_x, center_z, width, height, CFG.socket_corner_fraction),
        front, back, "electrical-orange")


def _receptacle(width, depth, height, configurations):
    plate_depth = min(depth * CFG.plate_depth_fraction, CFG.maximum_plate_depth_m)
    socket_depth = min(depth * CFG.socket_depth_fraction, CFG.maximum_socket_depth_m)
    mark_depth = min(depth * CFG.mark_depth_fraction, CFG.maximum_mark_depth_m)
    mark_front = -depth / 2
    socket_front = mark_front + mark_depth
    plate_front = socket_front + socket_depth
    housing_front = plate_front + plate_depth
    parts = [_housing(width, depth, height, housing_front),
             _plate(width, height, plate_front, housing_front)]
    count = len(configurations)
    quad = count == 4
    socket_width = width * (CFG.quad_socket_width_fraction if quad
                            else CFG.socket_width_fraction)
    socket_height = height * (CFG.single_socket_height_fraction if count == 1
                              else CFG.socket_height_fraction)
    for index, configuration in enumerate(configurations):
        center_x = (width * CFG.quad_column_offset_fraction * (-1 if index % 2 == 0 else 1)
                    if quad else 0)
        center_z = (height * (2 if index < 2 else 1) / 3 if quad
                    else height * (count - index) / (count + 1))
        parts.append(_socket_face(center_x, center_z, socket_width, socket_height,
                                  socket_front, plate_front))
        parts.extend(_slot_marks(center_x, center_z, socket_width, socket_height,
                                 mark_front, socket_front, configuration))
    return (rect(0, 0, width, depth),), tuple(parts)


def _duplex(w, d, h):
    return _receptacle(w, d, h, ("120", "120"))


def _single(w, d, h):
    return _receptacle(w, d, h, ("120-20",))


def _combined(w, d, h):
    return _receptacle(w, d, h, ("120-20", "240"))


def _quad(w, d, h):
    return _receptacle(w, d, h, ("120-20",) * 4)


def _240(w, d, h):
    return _receptacle(w, d, h, ("240",))


def _240_four_wire(w, d, h):
    return _receptacle(w, d, h, ("240-four-wire",))


def _floor_box(width, depth, height):
    plate_height = min(height * CFG.floor_plate_height_fraction, CFG.floor_maximum_plate_height_m)
    mark_height = min(height * CFG.floor_mark_height_fraction, CFG.floor_maximum_mark_height_m)
    body_top = height - plate_height - mark_height
    flange = circle(0, 0, min(width, depth) / 2)["points"]
    parts = [box(0, 0, 0, body_top, width * CFG.floor_body_fraction,
                 depth * CFG.floor_body_fraction, "electrical-orange"),
             prism(flange, body_top, height - mark_height, "electrical-plate")]
    for y in (-depth * CFG.floor_socket_offset_fraction, depth * CFG.floor_socket_offset_fraction):
        for x in (-width * CFG.floor_blade_spacing_fraction,
                  width * CFG.floor_blade_spacing_fraction):
            parts.append(box(x, y, height - mark_height, height,
                             width * CFG.floor_blade_width_fraction,
                             depth * CFG.floor_blade_length_fraction, "electrical-recess"))
        parts.append(box(0, y - depth * CFG.floor_blade_spacing_fraction,
                         height - mark_height, height,
                         width * CFG.floor_ground_size_fraction,
                         depth * CFG.floor_ground_size_fraction, "electrical-recess"))
    return (rect(0, 0, width, depth),), tuple(parts)


RECEPTACLE_SYMBOLS = {
    "receptacle-duplex": _duplex,
    "receptacle-single-120": _single,
    "receptacle-combined": _combined,
    "receptacle-quad": _quad,
    "receptacle-240": _240,
    "receptacle-240-four-wire": _240_four_wire,
    "receptacle-floor": _floor_box,
}
