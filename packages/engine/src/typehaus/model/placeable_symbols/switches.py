"""Wall-switch relief; local -Y faces the room, matching wall receptacles."""

from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import box, rect


@dataclass(frozen=True)
class SwitchGeometryConfig:
    plate_depth_fraction: float = 0.08
    maximum_plate_depth_m: float = 0.004
    control_depth_fraction: float = 0.20
    maximum_control_depth_m: float = 0.010
    recess_depth_fraction: float = 0.02
    maximum_recess_control_fraction: float = 0.10
    maximum_recess_face_fraction: float = 0.01
    recess_width_fraction: float = 0.30
    recess_height_fraction: float = 0.34
    toggle_width_fraction: float = 0.12
    toggle_bottom_fraction: float = 0.48
    toggle_top_fraction: float = 0.66
    rocker_width_fraction: float = 0.58
    rocker_bottom_fraction: float = 0.22
    rocker_top_fraction: float = 0.78
    rocker_lower_depth_fraction: float = 0.55


SWITCH_GEOMETRY = SwitchGeometryConfig()


def _switch(width, depth, height, *, rocker=False):
    config = SWITCH_GEOMETRY
    control_depth = min(depth * config.control_depth_fraction, config.maximum_control_depth_m)
    plate_depth = min(depth * config.plate_depth_fraction, config.maximum_plate_depth_m)
    control_front = -depth / 2
    plate_front = control_front + control_depth
    plate_back = plate_front + plate_depth
    parts = [
        box(0, (plate_back + depth / 2) / 2, 0, height,
            width, depth / 2 - plate_back, "electrical-orange"),
        box(0, (plate_front + plate_back) / 2, 0, height,
            width, plate_depth, "electrical-plate"),
    ]
    control_width = width * (config.rocker_width_fraction if rocker
                             else config.recess_width_fraction)
    bottom = height * (config.rocker_bottom_fraction if rocker
                       else (1 - config.recess_height_fraction) / 2)
    top = height - bottom
    recess_depth = min(depth * config.recess_depth_fraction,
                       control_depth * config.maximum_recess_control_fraction,
                       min(width, height) * config.maximum_recess_face_fraction)
    parts.append(box(0, plate_front - recess_depth / 2, bottom, top,
                     control_width, recess_depth, "electrical-recess"))
    # A dark reveal outlines the actuator; its relief stays within the device envelope.
    if rocker:
        rocker_width = control_width - 2 * recess_depth
        for lower, upper, projection in (
            (bottom + recess_depth, height / 2, config.rocker_lower_depth_fraction),
            (height / 2 + recess_depth, top - recess_depth, 1.0),
        ):
            back = plate_front - recess_depth
            front = plate_front - control_depth * projection
            parts.append(box(0, (front + back) / 2, lower, upper,
                             rocker_width, back - front, "electrical-orange"))
    else:
        parts.append(box(0, (control_front + plate_front - recess_depth) / 2,
                         height * config.toggle_bottom_fraction,
                         height * config.toggle_top_fraction,
                         width * config.toggle_width_fraction,
                         control_depth - recess_depth, "electrical-orange"))
    return (rect(0, 0, width, depth),), tuple(parts)


def _rocker(width, depth, height):
    return _switch(width, depth, height, rocker=True)


SWITCH_SYMBOLS = {"wall-switch-toggle": _switch, "wall-switch-rocker": _rocker}
