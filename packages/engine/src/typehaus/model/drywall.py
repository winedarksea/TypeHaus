"""Drywall accessories, declared once and derived from the host faces (decision #103).

The ``TrimStandard`` / ``BoxStandard`` pattern: one house-level element names the bead for
each kind of board edge, ``resolve/drywall_trims.py`` finds the edges, and
``takeoff/drywall_trims.py`` bills them by the LF. Inside corners are paper tape and stay in
the board's labour rate, so they have no field here.
"""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, ft

_BOARD_MATCH_M = 0.001


class TerminationBead(HausModel):
    """The J-bead for one board thickness: a 1/2" J does not seat on 5/8" board."""

    board_thickness: Length
    material_ref: str


class ShadowGapProfile(HausModel):
    """An LED shadow gap at the wall-ceiling edge: the ceiling (or soffit) board stops
    ``reveal`` short of the washed wall, a Z shadow bead lines the board's edge and the
    reveal's back, and bare tape stuck to that back faces down and washes the wall.

    ``depth`` is the bead's reveal depth, the board's thickness, so nothing rises past the
    board into what it is fastened to; ``flange`` is its mudded leg on the board face.
    ``wall_offset_max`` bounds how far an authored run may stand off its wall: the resolver
    moves each leg onto the reveal's centre, ``reveal / 2`` off the finished face.
    """

    material_ref: str
    reveal: Length
    depth: Length
    flange: Length
    wall_offset_max: Length


@register_element
class DrywallStandard(Element):
    """The house's drywall accessories, one material per edge kind (decision #103).

    One per plan (a second is an ``integrity.drywall_standard`` error). Without one, the
    window returns bill the library's generic beads and nothing else is derived.
    ``led_profile`` puts every light run in a gypsum ceiling or soffit in a shadow gap.
    """

    outside_corner_ref: str
    termination_ref: str
    # Per-thickness J-beads, matched to the board at the edge; any other board takes
    # ``termination_ref``.
    termination_refs: tuple[TerminationBead, ...] = ()
    door_bead_ref: str
    tile_reveal_ref: str
    window_corner_ref: str
    window_frame_ref: str
    # The window-return corner bead's nose radius (a bullnose); None is a square bead. A
    # fabricated stool's shoulder notch takes it, so the stone seats against the bead.
    window_corner_radius: Length | None = None
    led_profile: ShadowGapProfile | None = None
    stock_length: Length = ft(10)
    # GA-214 level of finish (0-5) the board is taped to; None is unstated and the drywall
    # bid summary says so rather than assuming Level 4.
    finish_level: int | None = Field(default=None, ge=0, le=5)

    def termination_for(self, board_thickness_m: float | None) -> str:
        """The J-bead for a board ``board_thickness_m`` thick (within 1 mm)."""
        if board_thickness_m is not None:
            for bead in self.termination_refs:
                if abs(bead.board_thickness.meters - board_thickness_m) < _BOARD_MATCH_M:
                    return bead.material_ref
        return self.termination_ref

    def material_refs(self) -> tuple[str, ...]:
        refs = (self.outside_corner_ref, self.termination_ref,
                *(bead.material_ref for bead in self.termination_refs), self.door_bead_ref,
                self.tile_reveal_ref, self.window_corner_ref, self.window_frame_ref,
                *((self.led_profile.material_ref,) if self.led_profile else ()))
        return tuple(dict.fromkeys(refs))


register_constructor("DrywallStandard", DrywallStandard)
register_constructor("ShadowGapProfile", ShadowGapProfile)
register_constructor("TerminationBead", TerminationBead)
