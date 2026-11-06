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
class ReturnPiece:
    """One cut piece of a fabricated return, with its glued-on front lap strip."""

    edge: str  # "jamb-left" | "jamb-right" | "head"
    length_m: float
    depth_m: float  # finished face to the window frame
    strip_length_m: float = 0.0
    strip_width_m: float = 0.0


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
    # A stool's authored picture frame (``WindowStool.return_material_ref``): no beads, and
    # the pieces bill with the countertops when a top shares the material.
    fabricated: bool = False
    pieces: tuple[ReturnPiece, ...] = ()
