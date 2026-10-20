"""Immutable installed window-return quantities, shared by geometry and takeoff."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowReturnLayer:
    name: str
    material_ref: str
    thickness_m: float
    area_m2: float
    coating: bool


@dataclass(frozen=True)
class ResolvedWindowReturn:
    uid: str
    tag: str
    window_ref: str
    wall_tag: str
    storey: str
    layers: tuple[WindowReturnLayer, ...]
    exposed_area_m2: float
    bead_length_m: float
    derived_paint: bool
