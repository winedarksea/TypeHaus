"""Receptacle faces: only what stands in front of the wall plate.

Same contract as switches.py: local -Y faces the room, the back face (+depth/2) sits on the
plate face, ``footprint`` = (face width, projection), ``height`` = face height, and nothing is
drawn behind the plate. The plate and box are derived ``resolve`` solids. Roles: ``device-face``
(recolourable through ``material_refs``), ``device-slot``, ``device-accent``.

Keys: receptacle-duplex / -single-120 (Decora), -gfci (slots + TEST/RESET), -blank-gfci
(TEST/RESET only), -combined (5-20R + 6-20R), -quad (two duplexes), -240 (6-20R),
-240-four-wire (generic rectangular 4-wire), -round-30 (14-30R), -round-50 (14-50R),
-floor, and device-blank (an unmarked face, e.g. a data jack).
"""

import math

from typehaus.model.placeable_symbols._device_face import FaceLayers, layers, pad, slab
from typehaus.model.placeable_symbols._frame import box, circle, prism, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._receptacle_config import (
    GROUND_LAYOUTS,
    INCH,
    SLOT_LAYOUTS,
)
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


def _slot_marks(center_x, center_z, scale, front, back, configuration):
    """Dark slots on a socket face; ``front``..``back`` is their depth span."""
    unit = scale * INCH
    parts = [box(center_x + dx * unit, (front + back) / 2, center_z + dz * unit - h * unit / 2,
                 center_z + dz * unit + h * unit / 2, w * unit, back - front, "device-slot")
             for dx, dz, w, h in SLOT_LAYOUTS[configuration]]
    dx, dz, ground_width, ground_height = GROUND_LAYOUTS[configuration]
    x, z = center_x + dx * unit, center_z + dz * unit
    width, height = ground_width * unit, ground_height * unit
    # A flat bottom and faceted arch read as a ground opening without a boolean hole.
    outline = [(x + px * width, z + pz * height)
               for px, pz in ((-.5, -.5), (.5, -.5), (.5, 0), (.25, .5), (-.25, .5), (-.5, 0))]
    parts.append(_depth_extrusion(outline, front, back, "device-slot"))
    return parts


def _orient_face_detail(part, face_height, housing_height):
    """Rotate a detail 90 degrees from the face frame, preserving relief and mesh normals."""
    def position(point):
        x, y, z = point
        return (z - face_height / 2, y, housing_height / 2 - x)

    result = {**part, "center": position(part["center"])}
    width, depth, height = part["size"]
    result["size"] = (height, depth, width)
    if "mesh" in part:
        mesh = part["mesh"]
        result["mesh"] = {
            **mesh, "positions": tuple(position(point) for point in mesh["positions"]),
            "normals": tuple((z, y, -x) for x, y, z in mesh["normals"]),
        }
    return result


def _rows(count, pitch_in, scale, height):
    """Socket-centre heights for ``count`` stacked sockets, top first."""
    return [height / 2 + ((count - 1) / 2 - index) * pitch_in * scale * INCH
            for index in range(count)]


def _buttons(parts, face: FaceLayers, center_x, center_z, scale, count, pitch_in, width_in,
             height_in, horizontal_run=True):
    """TEST/RESET buttons: ``count`` accent pads in a row (or a column) about a centre."""
    for index in range(count):
        offset = (index - (count - 1) / 2) * pitch_in * scale * INCH
        x, z = (center_x + offset, center_z) if horizontal_run else (center_x, center_z - offset)
        pad(parts, face, x, z - height_in * scale * INCH / 2, z + height_in * scale * INCH / 2,
            width_in * scale * INCH, face.button_reach, color="device-accent")


def _face(width, depth, height, columns, band=None):
    """A flat face of ``columns`` Decora-pitch columns of sockets, optionally with a GFCI band."""
    cols = len(columns)
    horizontal = cols == 1 and len(columns[0]) == 2 and width > height and band is None
    face_width, face_height = (height, width) if horizontal else (width, height)
    face = layers(depth, min(face_width, face_height))
    scale = min(face_width / cols / (CFG.face_width_in * INCH),
                face_height / (CFG.face_height_in * INCH))
    unit = scale * INCH
    socket_front = face.slab_front - CFG.socket_depth_fraction * depth
    mark_front = socket_front - CFG.mark_depth_fraction * depth
    pitch = CFG.gfci_row_pitch_in if band == "gfci" else CFG.duplex_row_pitch_in
    socket_height = (CFG.gfci_socket_height_in if band == "gfci" else CFG.socket_height_in) * unit
    details = []
    for column_index, sockets in enumerate(columns):
        center_x = (column_index - (cols - 1) / 2) * face_width / cols
        for center_z, configuration in zip(_rows(len(sockets), pitch, scale, face_height),
                                           sockets, strict=True):
            details.append(_depth_extrusion(
                _clipped_outline(center_x, center_z, CFG.socket_width_in * unit, socket_height,
                                 CFG.socket_corner_fraction),
                socket_front, face.slab_front, "device-face"))
            details.extend(_slot_marks(center_x, center_z, scale, mark_front, socket_front,
                                       configuration))
        if band == "gfci":
            _buttons(details, face, center_x, face_height / 2, scale, 2,
                     CFG.gfci_button_pitch_in, CFG.gfci_button_width_in,
                     CFG.gfci_button_height_in)
        elif band == "blank-gfci":
            _buttons(details, face, center_x, face_height / 2, scale, 2,
                     CFG.blank_gfci_button_pitch_in, CFG.blank_gfci_button_width_in,
                     CFG.blank_gfci_button_height_in, horizontal_run=False)
    if horizontal:
        details = [_orient_face_detail(part, face_height, height) for part in details]
    return (rect(0, 0, width, depth),), (slab(width, depth, height, face), *details)


def _round(configuration):
    """A round 240V face (14-30R / 14-50R): a disc with its slots, scaled to the footprint."""
    def build(width, depth, height):
        diameter = min(width, height)
        scale = diameter / (CFG.round_diameter_in * INCH)
        outline = [(diameter / 2 * math.cos(2 * math.pi * i / CFG.round_segments),
                    height / 2 + diameter / 2 * math.sin(2 * math.pi * i / CFG.round_segments))
                   for i in range(CFG.round_segments)]
        mark_depth = CFG.round_mark_depth_fraction * depth
        parts = [_depth_extrusion(outline, -depth / 2 + mark_depth, depth / 2, "device-face")]
        parts.extend(_slot_marks(0, height / 2, scale, -depth / 2, -depth / 2 + mark_depth,
                                 configuration))
        return (rect(0, 0, width, depth),), tuple(parts)
    return build


def _blank(width, depth, height):
    face = layers(depth, min(width, height))
    return (rect(0, 0, width, depth),), (slab(width, depth, height, face),)


def _floor_box(width, depth, height):
    """A floor receptacle's lid: only the flange proud of the floor, with its slots."""
    mark_height = height * CFG.mark_depth_fraction
    flange = circle(0, 0, min(width, depth) / 2)["points"]
    parts = [prism(flange, 0, height - mark_height, "device-face")]
    for y in (-depth * CFG.floor_socket_offset_fraction, depth * CFG.floor_socket_offset_fraction):
        for x in (-width * CFG.floor_blade_spacing_fraction,
                  width * CFG.floor_blade_spacing_fraction):
            parts.append(box(x, y, height - mark_height, height,
                             width * CFG.floor_blade_width_fraction,
                             depth * CFG.floor_blade_length_fraction, "device-slot"))
        parts.append(box(0, y - depth * CFG.floor_blade_spacing_fraction,
                         height - mark_height, height,
                         width * CFG.floor_ground_size_fraction,
                         depth * CFG.floor_ground_size_fraction, "device-slot"))
    return (rect(0, 0, width, depth),), tuple(parts)


def _of(*columns, band=None):
    return lambda width, depth, height: _face(width, depth, height, columns, band)


RECEPTACLE_SYMBOLS = {
    "receptacle-duplex": _of(("120", "120")),
    "receptacle-single-120": _of(("120-20",)),
    "receptacle-gfci": _of(("120", "120"), band="gfci"),
    "receptacle-blank-gfci": _of((), band="blank-gfci"),
    "receptacle-combined": _of(("120-20",), ("240",)),
    "receptacle-quad": _of(("120-20", "120-20"), ("120-20", "120-20")),
    "receptacle-240": _of(("240",)),
    "receptacle-240-four-wire": _of(("240-four-wire",)),
    "receptacle-round-30": _round("round-30"),
    "receptacle-round-50": _round("round-50"),
    "receptacle-floor": _floor_box,
    "device-blank": _blank,
}
