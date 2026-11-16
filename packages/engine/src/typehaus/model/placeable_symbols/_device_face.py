"""Layered relief shared by wiring-device faces (see switches.py for the contract).

Layers, back to front: the face slab on the plate, a dark reveal, then each actuator.
Depths are shares of the projection so every layer stays inside the envelope at any size.
"""

from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import box


@dataclass(frozen=True)
class FaceLayerConfig:
    slab_fraction: float = 0.50
    reveal_fraction: float = 0.05
    actuator_fraction: float = 0.45  # a proud paddle or lever reaches the envelope front
    pressed_fraction: float = 0.25   # the pressed half of a rocker
    button_fraction: float = 0.25
    reveal_margin_fraction: float = 0.02  # of the face's smaller side, each side of an actuator


FACE_LAYERS = FaceLayerConfig()


@dataclass(frozen=True)
class FaceLayers:
    """Local-Y positions (metres) of the layers for one projection."""

    slab_depth: float
    slab_front: float
    reveal_depth: float
    actuator_reach: float
    pressed_reach: float
    button_reach: float
    reveal_margin: float


def layers(depth: float, face_extent: float = 0.0) -> FaceLayers:
    """``face_extent`` is the face's smaller side, which sizes the reveal margin."""
    cfg = FACE_LAYERS
    return FaceLayers(
        slab_depth=depth * cfg.slab_fraction,
        slab_front=depth / 2 - depth * cfg.slab_fraction,
        reveal_depth=depth * cfg.reveal_fraction,
        actuator_reach=depth * cfg.actuator_fraction,
        pressed_reach=depth * cfg.pressed_fraction,
        button_reach=depth * cfg.button_fraction,
        reveal_margin=face_extent * cfg.reveal_margin_fraction)


def slab(width: float, depth: float, height: float, face: FaceLayers,
         color: str = "device-face"):
    """The device face standing on the plate: back at +depth/2."""
    return box(0, depth / 2 - face.slab_depth / 2, 0, height, width, face.slab_depth, color)


def reveal_box(parts: list, face: FaceLayers, center_x: float, z0: float, z1: float,
               width: float) -> None:
    """The dark gap an actuator sits in."""
    margin = face.reveal_margin
    parts.append(box(center_x, face.slab_front - face.reveal_depth / 2, z0 - margin,
                     z1 + margin, width + 2 * margin, face.reveal_depth, "device-slot"))


def pad(parts: list, face: FaceLayers, center_x: float, z0: float, z1: float, width: float,
        reach: float, *, color: str = "device-face", reveal: bool = True) -> None:
    """An actuator on the slab, with a dark reveal behind it."""
    if reveal:
        reveal_box(parts, face, center_x, z0, z1, width)
    front = face.slab_front - face.reveal_depth
    parts.append(box(center_x, front - reach / 2, z0, z1, width, reach, color))
