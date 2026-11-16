"""Wall-switch faces: only what stands in front of the wall plate.

Contract (shared with receptacles.py and ``_device_face.py``):

* Local frame as every symbol: local -Y faces the room; the back face (local +Y = +depth/2)
  sits ON the plate face. ``resolve`` offsets the device out by the plate thickness.
* ``footprint`` = (face width, projection past the plate); ``height`` = face height. Parts
  stay inside that envelope.
* Draw the face and its actuators only. The plate and the box are derived ``resolve`` solids
  and the body behind the plate is never modelled, so nothing here goes behind the plate.
* Colour roles: ``device-face`` (a type recolours it through ``material_refs``),
  ``device-slot`` (reveals, channels), ``device-accent`` (lens, LEDs, small buttons).
"""

from dataclasses import dataclass

from typehaus.model.placeable_symbols._device_face import FaceLayers, layers, pad, reveal_box, slab
from typehaus.model.placeable_symbols._frame import box, rect


@dataclass(frozen=True)
class SwitchGeometryConfig:
    """Depth shares are of the projection; width and height shares of the face."""

    toggle_width_fraction: float = 0.20
    toggle_bottom_fraction: float = 0.38
    toggle_top_fraction: float = 0.62
    rocker_width_fraction: float = 0.86
    rocker_bottom_fraction: float = 0.05
    rocker_top_fraction: float = 0.95
    rocker_split_fraction: float = 0.50  # paddle tilt: upper half proud, lower half pressed
    dimmer_paddle_center_fraction: float = -0.17
    dimmer_paddle_width_fraction: float = 0.58
    dimmer_slider_center_fraction: float = 0.33
    dimmer_slider_width_fraction: float = 0.13
    dimmer_slider_bottom_fraction: float = 0.12
    dimmer_slider_top_fraction: float = 0.88
    dimmer_knob_bottom_fraction: float = 0.50
    dimmer_knob_top_fraction: float = 0.60
    dimmer_knob_depth_fraction: float = 0.30
    keypad_width_fraction: float = 0.86
    keypad_large_zone: tuple[float, float] = (0.52, 0.95)  # one large button (Zooz ZEN32)
    keypad_small_zone: tuple[float, float] = (0.05, 0.46)
    keypad_small_count: int = 4
    keypad_gap_fraction: float = 0.02
    occupancy_lens_zone: tuple[float, float] = (0.80, 0.96)
    occupancy_lens_width_fraction: float = 0.60
    occupancy_lens_depth_fraction: float = 0.30
    occupancy_rocker_top_fraction: float = 0.72
    timer_led_zone: tuple[float, float] = (0.88, 0.94)
    timer_led_count: int = 3
    timer_led_width_fraction: float = 0.14
    timer_led_depth_fraction: float = 0.12
    timer_button_zone: tuple[float, float] = (0.08, 0.80)
    timer_button_count: int = 3


SWITCH_GEOMETRY = SwitchGeometryConfig()


def _toggle(width, depth, height):
    cfg, face = SWITCH_GEOMETRY, layers(depth, min(width, height))
    parts = [slab(width, depth, height, face)]
    pad(parts, face, 0, cfg.toggle_bottom_fraction * height, cfg.toggle_top_fraction * height,
        cfg.toggle_width_fraction * width, face.actuator_reach)
    return (rect(0, 0, width, depth),), tuple(parts)


def _paddle(parts, face: FaceLayers, center_x, z_bottom, z_top, width):
    """A rocker: upper half proud, lower half pressed in, one dark reveal around both."""
    cfg = SWITCH_GEOMETRY
    split = z_bottom + (z_top - z_bottom) * cfg.rocker_split_fraction
    reveal_box(parts, face, center_x, z_bottom, z_top, width)
    pad(parts, face, center_x, split, z_top, width, face.actuator_reach, reveal=False)
    pad(parts, face, center_x, z_bottom, split, width, face.pressed_reach, reveal=False)


def _rocker(width, depth, height):
    cfg, face = SWITCH_GEOMETRY, layers(depth, min(width, height))
    parts = [slab(width, depth, height, face)]
    _paddle(parts, face, 0, cfg.rocker_bottom_fraction * height,
            cfg.rocker_top_fraction * height, cfg.rocker_width_fraction * width)
    return (rect(0, 0, width, depth),), tuple(parts)


def _dimmer(width, depth, height):
    """Rocker plus a slim slider: a dark channel with a raised knob."""
    cfg, face = SWITCH_GEOMETRY, layers(depth, min(width, height))
    parts = [slab(width, depth, height, face)]
    _paddle(parts, face, cfg.dimmer_paddle_center_fraction * width,
            cfg.rocker_bottom_fraction * height, cfg.rocker_top_fraction * height,
            cfg.dimmer_paddle_width_fraction * width)
    slider_x = cfg.dimmer_slider_center_fraction * width
    slider_width = cfg.dimmer_slider_width_fraction * width
    z0 = cfg.dimmer_slider_bottom_fraction * height
    z1 = cfg.dimmer_slider_top_fraction * height
    parts.append(box(slider_x, face.slab_front - face.reveal_depth / 2, z0, z1,
                     slider_width, face.reveal_depth, "device-slot"))
    knob_depth = cfg.dimmer_knob_depth_fraction * depth
    parts.append(box(slider_x, face.slab_front - face.reveal_depth - knob_depth / 2,
                     cfg.dimmer_knob_bottom_fraction * height,
                     cfg.dimmer_knob_top_fraction * height,
                     slider_width * 0.8, knob_depth, "device-accent"))
    return (rect(0, 0, width, depth),), tuple(parts)


def _stack_zones(zone, count, gap):
    """``count`` equal (bottom, top) spans filling ``zone`` (face-height fractions)."""
    low, high = zone
    each = (high - low - gap * (count - 1)) / count
    return [(low + index * (each + gap), low + index * (each + gap) + each)
            for index in range(count)]


def _keypad(width, depth, height):
    """One large button over a column of small ones."""
    cfg, face = SWITCH_GEOMETRY, layers(depth, min(width, height))
    parts = [slab(width, depth, height, face)]
    zones = [*_stack_zones(cfg.keypad_small_zone, cfg.keypad_small_count,
                           cfg.keypad_gap_fraction), cfg.keypad_large_zone]
    for bottom, top in zones:
        pad(parts, face, 0, bottom * height, top * height,
            cfg.keypad_width_fraction * width, face.actuator_reach)
    return (rect(0, 0, width, depth),), tuple(parts)


def _occupancy(width, depth, height):
    """Rocker below a sensor lens across the top."""
    cfg, face = SWITCH_GEOMETRY, layers(depth, min(width, height))
    parts = [slab(width, depth, height, face)]
    _paddle(parts, face, 0, cfg.rocker_bottom_fraction * height,
            cfg.occupancy_rocker_top_fraction * height, cfg.rocker_width_fraction * width)
    z0, z1 = (fraction * height for fraction in cfg.occupancy_lens_zone)
    lens_depth = cfg.occupancy_lens_depth_fraction * depth
    parts.append(box(0, face.slab_front - lens_depth / 2, z0, z1,
                     cfg.occupancy_lens_width_fraction * width, lens_depth, "device-accent"))
    return (rect(0, 0, width, depth),), tuple(parts)


def _timer(width, depth, height):
    """Status LEDs over a column of buttons."""
    cfg, face = SWITCH_GEOMETRY, layers(depth, min(width, height))
    parts = [slab(width, depth, height, face)]
    led_width = cfg.timer_led_width_fraction * width
    led_depth = cfg.timer_led_depth_fraction * depth
    z0, z1 = (fraction * height for fraction in cfg.timer_led_zone)
    for index in range(cfg.timer_led_count):
        x = (index - (cfg.timer_led_count - 1) / 2) * led_width * 1.8
        parts.append(box(x, face.slab_front - led_depth / 2, z0, z1, led_width, led_depth,
                         "device-accent"))
    for bottom, top in _stack_zones(cfg.timer_button_zone, cfg.timer_button_count,
                                    cfg.keypad_gap_fraction):
        pad(parts, face, 0, bottom * height, top * height,
            cfg.keypad_width_fraction * width, face.button_reach)
    return (rect(0, 0, width, depth),), tuple(parts)


SWITCH_SYMBOLS = {
    "wall-switch-toggle": _toggle,      # traditional toggle, any plain 120V switch
    "wall-switch-rocker": _rocker,      # Decora paddle
    "wall-switch-dimmer": _dimmer,      # paddle + slider (Diva/Decora dimmers)
    "wall-switch-keypad": _keypad,      # 1 large + 4 small buttons (Zooz ZEN32 style)
    "wall-switch-occupancy": _occupancy,  # paddle + sensor lens
    "wall-switch-timer": _timer,        # LEDs + buttons (timer, smart timer)
}
