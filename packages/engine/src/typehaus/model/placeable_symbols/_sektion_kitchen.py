"""Configured SEKTION casework: nominal frame envelopes, AXSTAD faces outside them.

The existing catalog depth is a frame/rail datum. Doors project 3/4 inch beyond it;
BAGGANÄS projects beyond the doors. Neither changes a cabinet's installation footprint.
"""

from math import atan2, cos, degrees, radians, sin

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import box, line, polygon, prism, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._sektion import _inset_l, sektion_corner_points
from typehaus.model.placeable_symbols._sektion_corner_wall import sektion_corner_wall_points
from typehaus.model.placeable_symbols._sektion_frames import (
    sektion_carcass,
    sektion_leveling_legs,
    sektion_plinth,
)
from typehaus.model.placeable_symbols._sektion_fronts import (
    DOOR_THICKNESS_M,
    HARDWARE_EDGE_OFFSET_M,
    REVEAL_M,
    axstad_front,
    bagganas_knob,
    bagganas_pull,
)
from typehaus.model.placeable_symbols._sektion_layout import (
    DRAWER_STACK_COUNT,
    SektionCabinetConfiguration,
    front_layout,
    fronts_across,
)
from typehaus.quantities import inch

BASE_SUPPORT_M = inch(3.5).meters
BASE_FRAME_M = inch(30).meters
COUNTER_M = inch(1.181).meters
TOE_RECESS_M = inch(3).meters
CORNER_LEG_M = inch(24).meters
INCH_M = inch(1).meters
SINK_OPENING_WIDTH_RATIO = 0.83
SINK_OPENING_DEPTH_RATIO = 0.78


def _doors(
    width, front, thickness, bottom, top, *, hinge_right=False, lift=False, knob_at_bottom=True
):
    count = fronts_across(width / INCH_M)
    parts = []
    for index in range(count):
        nominal_width = width / count
        face_width = nominal_width - min(REVEAL_M, nominal_width / 20)
        x = -width / 2 + nominal_width * (index + 0.5)
        parts.extend(axstad_front(face_width, front, thickness, bottom, top, center_x=x))
        offset = min(HARDWARE_EDGE_OFFSET_M, face_width / 4, (top - bottom) / 4)
        opening_sign = (-1 if hinge_right else 1) if count == 1 else (1 if index == 0 else -1)
        knob_x = x if lift else x + opening_sign * (face_width / 2 - offset / 2)
        knob_z = bottom + offset if lift or knob_at_bottom else top - offset
        parts.extend(
            bagganas_knob(
                knob_x,
                front,
                knob_z,
                min(1.0, face_width / inch(6).meters, (top - bottom) / inch(6).meters),
            )
        )
    return parts


def _counter(width, depth, bottom, top, sink=False):
    if not sink:
        return [box(0, 0, bottom, top, width, depth, "counter")]
    opening_w, opening_d = width * SINK_OPENING_WIDTH_RATIO, depth * SINK_OPENING_DEPTH_RATIO
    side = (width - opening_w) / 2
    end = (depth - opening_d) / 2
    return [
        *(
            box(sign * (opening_w + side) / 2, 0, bottom, top, side, depth, "counter")
            for sign in (-1, 1)
        ),
        *(
            box(0, sign * (opening_d + end) / 2, bottom, top, opening_w, end, "counter")
            for sign in (-1, 1)
        ),
    ]


def sektion_axstad_cabinet(configuration: SektionCabinetConfiguration) -> Builder:
    def build(width: float, depth: float, height: float) -> Geometry:
        installed_base = configuration.installation == "base"
        installed_tall = configuration.installation == "tall"
        support_height = inch(configuration.support_height_in).meters
        nominal = inch(36 if installed_base else 83.5).meters + support_height - BASE_SUPPORT_M
        scale = min(1.0, height / nominal) if installed_base or installed_tall else 1.0
        base = support_height * scale if installed_base or installed_tall else 0.0
        top = base + BASE_FRAME_M * scale if installed_base else height
        thickness = min(DOOR_THICKNESS_M, depth / 8)
        front = -depth / 2 - thickness
        reveal = min(REVEAL_M, width / 20, (top - base) / 20)
        sink = configuration.fronts == "sink"
        garage = configuration.fronts == "garage"
        shelves = (
            () if sink or garage or configuration.fronts == "drawers"
            else (base + (top - base) / 2,)
        )
        parts = sektion_carcass(
            width, depth, base, top, -depth / 2, shelves, include_top=not installed_base,
            include_bottom=not garage,
        )
        if base:
            support_builder = (
                sektion_leveling_legs if configuration.leveling_legs else sektion_plinth
            )
            parts.extend(support_builder(width, depth, base, recess=min(TOE_RECESS_M, depth / 4)))
        if installed_base:
            counter_bottom = height - min(COUNTER_M, (height - top) / 2)
            # Substrate and frame-top rails leave the sink opening clear as well.
            substrate = _counter(width, depth, top, counter_bottom, sink)
            parts.extend({**part, "color": "appliance-white"} for part in substrate)
            parts.extend(_counter(width, depth, counter_bottom, height, sink))
        if configuration.fronts == "drawers":
            for index in range(DRAWER_STACK_COUNT):
                bottom = base + (top - base) * index / DRAWER_STACK_COUNT + reveal / 2
                upper = base + (top - base) * (index + 1) / DRAWER_STACK_COUNT - reveal / 2
                parts.extend(axstad_front(width - reveal, front, thickness, bottom, upper))
                parts.extend(
                    bagganas_pull(
                        0,
                        front,
                        (bottom + upper) / 2,
                        min(1.0, width / inch(8).meters, (upper - bottom) / inch(3).meters),
                    )
                )
        elif configuration.fronts == "garage":
            # A lift-up front preserves headroom without an internal tambour coil.
            parts.extend(
                _doors(
                    width, front, thickness, base + reveal / 2, top - reveal / 2,
                    lift=True,
                )
            )
        else:
            divisions = (base, top)
            if installed_tall:
                # The bill's rows (front_layout); a scaled-down glyph keeps the 50" lower door
                # scaled, and authored fronts split the span in proportion.
                rows = front_layout(configuration, width / INCH_M, height / INCH_M).rows
                if configuration.tall_front_heights_in:
                    total_in = sum(row.height_in for row in rows)
                    divisions = (base,)
                    for row in rows:
                        divisions += (divisions[-1] + (top - base) * row.height_in / total_in,)
                else:
                    divisions = (base, base + inch(rows[0].height_in).meters * scale, top)
            for bottom, upper in zip(divisions, divisions[1:], strict=False):
                parts.extend(
                    _doors(
                        width,
                        front,
                        thickness,
                        bottom + reveal / 2,
                        upper - reveal / 2,
                        hinge_right=configuration.hinge_right,
                        lift=configuration.fronts == "lift",
                        knob_at_bottom=not installed_base and (not installed_tall or bottom > base),
                    )
                )
        strokes = (
            rect(0, 0, width, depth, fill="appliance-white"),
            line((-width / 2, -depth / 2), (width / 2, -depth / 2)),
        )
        return strokes, tuple(parts)

    return build


def _place_front_parts(parts, x, y, angle):
    """Rotate front meshes onto a notch or diagonal without renderer-specific geometry."""
    c, s = cos(radians(angle)), sin(radians(angle))
    result = []
    for part in parts:
        positions = [
            (x + c * px - s * py, y + s * px + c * py, pz)
            for px, py, pz in part["mesh"]["positions"]
        ]
        result.append(mesh_part(positions, list(part["mesh"]["triangles"]), part["color"]))
    return result


def sektion_axstad_corner_base(width: float, depth: float, height: float) -> Geometry:
    scale = min(1.0, height / inch(36).meters)
    base, top = BASE_SUPPORT_M * scale, (BASE_SUPPORT_M + BASE_FRAME_M) * scale
    leg = min(CORNER_LEG_M, width * 0.8, depth * 0.8)
    ring = sektion_corner_points(width, depth, leg)
    nx, ny = width / 2 - leg, depth / 2 - leg
    thickness = min(DOOR_THICKNESS_M, depth / 8, width / 8)
    reveal = min(REVEAL_M, height / 40)
    parts = [
        prism(_inset_l(width, depth, leg, thickness), base, top, "appliance-white"),
        prism(_inset_l(width, depth, leg, min(TOE_RECESS_M, leg / 4)), 0, base, "appliance-white"),
        prism(ring, top, height - min(COUNTER_M, (height - top) / 2), "appliance-white"),
        prism(ring, height - min(COUNTER_M, (height - top) / 2), height, "counter"),
    ]
    # Bifold leaves occupy each notch face; one knob opens the coupled pair.
    for leaf_width, x, y, angle, knob in (
        (nx + width / 2, (-width / 2 + nx) / 2, ny, 0, True),
        (ny + depth / 2, nx, (-depth / 2 + ny) / 2, 90, False),
    ):
        face = axstad_front(leaf_width - reveal, 0, thickness, base + reveal / 2, top - reveal / 2)
        if knob:
            face.extend(
                bagganas_knob(
                    -leaf_width / 2 + min(HARDWARE_EDGE_OFFSET_M, leaf_width / 4),
                    0,
                    top - min(HARDWARE_EDGE_OFFSET_M, (top - base) / 4),
                    min(1.0, height / inch(12).meters, leaf_width / inch(6).meters),
                )
            )
        parts.extend(_place_front_parts(face, x, y, angle))
    return (polygon(ring, fill="appliance-white"),), tuple(parts)


def sektion_axstad_corner_wall(width: float, depth: float, height: float) -> Geometry:
    ring = sektion_corner_wall_points(width, depth)
    first, second = ring[:2]
    span = sum((second[i] - first[i]) ** 2 for i in (0, 1)) ** 0.5
    thickness = min(DOOR_THICKNESS_M, depth / 8, width / 8)
    reveal = min(REVEAL_M, height / 20, span / 20)
    door_width = min(inch(14.875).meters, span - reveal)
    # Cheeks remain behind the door's recess, so the relief is visible from the room.
    inset = thickness
    tangent = ((second[0] - first[0]) / span, (second[1] - first[1]) / span)
    inward = (-tangent[1], tangent[0])
    carcass_ring = (
        tuple(first[i] + inward[i] * inset for i in (0, 1)),
        tuple(second[i] + inward[i] * inset for i in (0, 1)),
        *ring[2:],
    )
    parts = [prism(carcass_ring, 0, height, "appliance-white")]
    face = _doors(door_width + reveal, -thickness, thickness, reveal / 2, height - reveal / 2)
    parts.extend(
        _place_front_parts(
            face,
            (first[0] + second[0]) / 2,
            (first[1] + second[1]) / 2,
            degrees(atan2(tangent[1], tangent[0])),
        )
    )
    return (polygon(ring, fill="appliance-white"),), tuple(parts)


# Symbol name -> configuration; the bill (library/placeables/sektion_parts) reads the same.
KITCHEN_SEKTION_CONFIGURATIONS = {
    "sektion-axstad-kitchen-base-door": SektionCabinetConfiguration("base"),
    "sektion-axstad-kitchen-base-door-raised": SektionCabinetConfiguration(
        "base", support_height_in=4.0625, leveling_legs=True),
    "sektion-axstad-kitchen-base-door-right": SektionCabinetConfiguration("base", hinge_right=True),
    "sektion-axstad-kitchen-drawers": SektionCabinetConfiguration("base", "drawers"),
    "sektion-axstad-kitchen-sink": SektionCabinetConfiguration("base", "sink"),
    "sektion-axstad-kitchen-wall": SektionCabinetConfiguration(),
    "sektion-axstad-kitchen-lift": SektionCabinetConfiguration(fronts="lift"),
    "sektion-axstad-kitchen-tall": SektionCabinetConfiguration("tall"),
    "sektion-axstad-kitchen-tall-raised": SektionCabinetConfiguration(
        "tall", support_height_in=6, leveling_legs=True),
    "sektion-axstad-kitchen-tall-aligned": SektionCabinetConfiguration(
        "tall", tall_front_heights_in=(30, 40, 20)),
    "sektion-axstad-kitchen-garage": SektionCabinetConfiguration(fronts="garage"),
}

KITCHEN_SEKTION_SYMBOLS = {
    **{name: sektion_axstad_cabinet(config)
       for name, config in KITCHEN_SEKTION_CONFIGURATIONS.items()},
    "sektion-axstad-kitchen-corner-base": sektion_axstad_corner_base,
    "sektion-axstad-kitchen-corner-wall": sektion_axstad_corner_wall,
}
