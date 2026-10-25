"""Rivelia-style automatic espresso machine, with its front toward local -y.

The catalog supplies the assembled envelope. Internal proportions approximate the
manufacturer photograph; the attached carafe and side tank stay inside that envelope.
"""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, circle, prism, rect

HOUSING_TOP_RATIO = 0.76
HOPPER_BASE_RATIO = 0.80
HOPPER_LID_RATIO = 0.97


def espresso_machine(width: float, depth: float, height: float) -> Geometry:
    housing_center_x = -width * 0.11
    hopper = circle(housing_center_x, depth * 0.20,
                    min(width * 0.23, depth * 0.17), fill="glass")
    tank = rect(width * 0.39, depth * 0.12, width * 0.22, depth * 0.66, fill="glass")
    carafe = rect(-width * 0.32, -depth * 0.37,
                  width * 0.22, depth * 0.24, fill="glass")
    screen = rect(housing_center_x, -depth * 0.15,
                  width * 0.64, depth * 0.16, fill="screen")
    strokes = (
        rect(0, 0, width, depth, fill="appliance-white"), tank,
        rect(housing_center_x, depth * 0.12, width * 0.78, depth * 0.76,
             fill="appliance-white"),
        rect(housing_center_x, -depth * 0.37, width * 0.78, depth * 0.24,
             fill="appliance-steel"),
        carafe, screen, hopper,
    )
    parts = [
        box(housing_center_x, 0, 0, height * 0.05,
            width * 0.78, depth, "appliance-white"),
        box(housing_center_x, depth * 0.12, height * 0.05, height * HOUSING_TOP_RATIO,
            width * 0.78, depth * 0.76, "appliance-white"),
        # The dark front panel sits behind the dispensing head and the removable carafe.
        box(width * 0.06, -depth * 0.263, height * 0.10, height * 0.64,
            width * 0.40, depth * 0.006, "metal-black"),
        box(housing_center_x, -depth * 0.37, height * 0.05, height * 0.065,
            width * 0.75, depth * 0.24, "appliance-steel"),
        box(width * 0.06, -depth * 0.30, height * 0.37, height * 0.65,
            width * 0.24, depth * 0.08, "appliance-steel"),
        box(width * 0.06, -depth * 0.30, height * 0.65, height * 0.67,
            width * 0.26, depth * 0.09, "metal-black"),
        prism(tank["points"], height * 0.08, height * 0.62, "glass"),
        prism(tank["points"], height * 0.62, height * 0.65, "appliance-white"),
        prism(carafe["points"], height * 0.065, height * 0.43, "glass"),
        prism(carafe["points"], height * 0.43, height * 0.50, "metal-black"),
        box(-width * 0.17, -depth * 0.37, height * 0.40, height * 0.43,
            width * 0.10, depth * 0.04, "metal-black"),
        prism(screen["points"], height * HOUSING_TOP_RATIO, height * 0.765, "screen"),
        prism(hopper["points"], height * HOUSING_TOP_RATIO,
              height * HOPPER_BASE_RATIO, "metal-black"),
        prism(hopper["points"], height * HOPPER_BASE_RATIO,
              height * HOPPER_LID_RATIO, "glass"),
        prism(hopper["points"], height * HOPPER_LID_RATIO, height, "appliance-white"),
    ]
    for spout_center_ratio in (0.0, 0.12):
        parts.append(box(width * spout_center_ratio, -depth * 0.32,
                         height * 0.33, height * 0.37,
                         width * 0.045, depth * 0.04, "metal-black"))
    for slot_center_ratio in (-0.09, 0.01, 0.11, 0.21):
        parts.append(box(width * slot_center_ratio, -depth * 0.39,
                         height * 0.065, height * 0.067,
                         width * 0.025, depth * 0.15, "metal-black"))
    return strokes, tuple(parts)
