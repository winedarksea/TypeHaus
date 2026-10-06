"""Framing and fastening recipes for a diaphragm's collector and neighbouring deck."""

from typing import Literal

from pydantic import Field, field_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length, inch


class CollectorBlocking(HausModel):
    """Solid raised-heel blocks, cut from stock to the deck, between truss faces."""

    collector: str
    stock: str
    material: str
    #: ``inboard``: one face flush with the collector's face toward the roof's centre, where
    #: the plates go, so a block narrower than the beam still backs them.
    flush: Literal["centre", "inboard"] = "centre"
    end_tie: str = "LS30Z"
    end_ties_each_end: int = Field(default=1, ge=1)
    fastening: str


class PanelEdgeBlocking(HausModel):
    """On-edge blocks under every sheet edge between trusses, set out from the ridge.

    ``module`` is the horizontal plan module; its pitched length must fit the sheet.
    """

    stock: str
    material: str
    module: Length
    toenails_each_end: int = Field(default=3, ge=1)
    fastening: str

    @field_validator("module")
    @classmethod
    def positive_module(cls, value: Length) -> Length:
        if value.meters <= 0:
            raise ValueError("panel module must be positive")
        return value


class JointNailing(HausModel):
    """Longitudinal nailers in the bays on either side of the receiving gable truss.

    Only the outer strap holes are used: the un-nailed middle crosses the gable chord.
    The installed strap rating is reduced for the specified nail count. A multi-ply
    stock ("2-2x6") is laminated at ``lamination_spacing``, two nails near each end.
    """

    stock: str
    material: str
    continuous_deck: bool
    strap_nails_each_end: int = Field(ge=1)
    rated_strap_nails_each_end: int = Field(ge=1)
    nail_group_inset: Length
    minimum_end_distance: Length = inch(2.375)
    minimum_edge_distance: Length = inch(0.75)
    deck_edge_distance: Length = inch(0.375)
    deck_nail_spacing: Length = inch(3)
    deck_nail_rows: int = Field(default=2, ge=1)
    #: The deck nail itself, read nail by nail (NDS 12.3.1): 8d common by default.
    deck_nail_diameter: Length = inch(0.131)
    deck_nail_length: Length = inch(2.5)
    #: NDS Table I1 bending yield, psi, for 0.099in < D <= 0.142in.
    deck_nail_fyb_psi: float = Field(default=100_000.0, gt=0)
    lamination_spacing: Length = inch(12)
    end_tie: str = "LS30Z"
    fastening: str
    source: str

    @field_validator("nail_group_inset", "minimum_end_distance", "minimum_edge_distance",
                     "deck_edge_distance", "deck_nail_spacing", "lamination_spacing",
                     "deck_nail_diameter", "deck_nail_length")
    @classmethod
    def positive_nailing_dimensions(cls, value: Length) -> Length:
        if value.meters <= 0:
            raise ValueError("nailing distances and spacing must be positive")
        return value
