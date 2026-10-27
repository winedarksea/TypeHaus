"""Receptacle faces in the shared local frame, with the wall at positive depth."""

from typehaus.model.placeable_symbols._frame import box, circle, prism, rect


def _receptacle(width, depth, height, configurations):
    # Keep the authored envelope: it controls wall hosting and clash checks. Thin dark
    # marks sit on its front face so the slots remain legible without boolean geometry.
    plate_depth = min(depth * 0.12, 0.006)
    mark_depth = min(depth * 0.015, 0.001)
    front = -depth / 2 + mark_depth
    parts = [box(0, (mark_depth + plate_depth) / 2, 0, height,
                 width, depth - mark_depth - plate_depth,
                 "electrical-orange"),
             box(0, front + plate_depth / 2, 0, height,
                 width * 0.9, plate_depth, "electrical-plate")]
    count = len(configurations)
    for index, configuration in enumerate(configurations):
        quad = count == 4
        x_center = width * (-0.22 if index % 2 == 0 else 0.22) if quad else 0
        z = (height * (0.68 if index < 2 else 0.32) if quad
             else height * (count - index) / (count + 1))
        spacing = width * (0.07 if quad else 0.13)
        slot_width = width * (0.025 if quad else 0.035)
        slot_height = height * (0.09 if count <= 2 else 0.055)
        # 6-20R has horizontal blades, 5-20R one T-shaped blade; simplified
        # marks distinguish the NEMA configurations at room scale.
        for x in (x_center - spacing, x_center + spacing):
            w, h = ((slot_height, slot_width) if configuration == "240"
                    else (slot_width, slot_height))
            parts.append(box(x, -depth / 2 + mark_depth / 2, z - h / 2, z + h / 2,
                             w, mark_depth, "electrical-recess"))
        if configuration == "120-20":
            parts.append(box(x_center - spacing, -depth / 2 + mark_depth / 2,
                             z - slot_width / 2, z + slot_width / 2,
                             slot_height, mark_depth, "electrical-recess"))
        elif configuration == "240":
            parts.append(box(x_center - spacing, -depth / 2 + mark_depth / 2,
                             z - slot_height / 2, z + slot_height / 2,
                             slot_width, mark_depth, "electrical-recess"))
        elif configuration == "240-four-wire":
            parts.append(box(x_center, -depth / 2 + mark_depth / 2,
                             z + slot_height * 0.85, z + slot_height * 1.2,
                             slot_width * 1.5, mark_depth, "electrical-recess"))
        parts.append(box(x_center, -depth / 2 + mark_depth / 2,
                         z - slot_height * 1.2, z - slot_height * 0.85,
                         slot_width * 1.5, mark_depth, "electrical-recess"))
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
    plate_height = min(height * 0.04, 0.005)
    mark_height = min(height * 0.01, 0.001)
    body_top = height - plate_height - mark_height
    flange = circle(0, 0, min(width, depth) / 2)["points"]
    parts = [box(0, 0, 0, body_top, width * 0.65, depth * 0.65, "electrical-orange"),
             prism(flange, body_top, height - mark_height, "electrical-plate")]
    for y in (-depth * 0.16, depth * 0.16):
        for x in (-width * 0.08, width * 0.08):
            parts.append(box(x, y, height - mark_height, height,
                             width * 0.025, depth * 0.075, "electrical-recess"))
        parts.append(box(0, y - depth * 0.08, height - mark_height, height,
                         width * 0.035, depth * 0.035, "electrical-recess"))
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
