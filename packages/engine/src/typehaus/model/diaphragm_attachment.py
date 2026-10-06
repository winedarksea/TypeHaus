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
    end_tie: Literal["LS30"] = "LS30"
    end_ties_each_end: int = Field(default=1, ge=1)
    fastening: str


class JointNailing(HausModel):
    """Longitudinal nailers in the bays on either side of the receiving gable truss.

    Only the outer strap holes are used: the un-nailed middle crosses the gable chord.
    The installed strap rating is reduced for the specified nail count.
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
    end_tie: Literal["LS30"] = "LS30"
    fastening: str
    source: str

    @field_validator("nail_group_inset", "minimum_end_distance", "minimum_edge_distance",
                     "deck_edge_distance", "deck_nail_spacing")
    @classmethod
    def positive_nailing_dimensions(cls, value: Length) -> Length:
        if value.meters <= 0:
            raise ValueError("nailing distances and spacing must be positive")
        return value
