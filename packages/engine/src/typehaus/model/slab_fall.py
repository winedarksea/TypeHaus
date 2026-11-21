"""A pour slab that falls to drain: the plane its top (and, constant thickness, its bottom)
follows (decision #138), or a local dish to a floor drain inside a level rim (#148).

``Slab.top_elevation`` stays the top at the LOW edge, so every flat reader of the slab's
``z1_m`` sees its lowest point; the readers that must follow the floor read
``resolve/slab_fall.slab_top_at``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, Point2D


class SlabFall(HausModel):
    """The slab's top falls ``rate_in_per_ft`` toward ``toward``, reaching
    ``Slab.top_elevation`` at ``low_edge``: the y of an east-west line (north/south), else
    the x of a north-south one. The top rises away from that line; the plane is not
    clamped, so the outline should lie wholly on its uphill side."""

    toward: Literal["north", "south", "east", "west"]
    rate_in_per_ft: float
    low_edge: Length

    @model_validator(mode="after")
    def _positive_rate(self) -> SlabFall:
        if not 0 < self.rate_in_per_ft <= 1.0:
            raise ValueError("SlabFall.rate_in_per_ft must be in (0, 1] (in/ft)")
        return self


class DrainDish(HausModel):
    """Inside ``outline`` the pour's top dishes to the floor drain ``drain_ref`` at no less
    than ``rate_in_per_ft``; the rim stays at the slab's top. The slab keeps its thickness, so
    whatever is under it dishes too (``resolve/slab_dish.py``). The outline must be
    star-shaped from the drain."""

    drain_ref: str
    outline: tuple[Point2D, ...]
    rate_in_per_ft: float

    @model_validator(mode="after")
    def _valid(self) -> DrainDish:
        if not 0 < self.rate_in_per_ft <= 1.0:
            raise ValueError("DrainDish.rate_in_per_ft must be in (0, 1] (in/ft)")
        if len(self.outline) < 3:
            raise ValueError("DrainDish.outline needs at least three points")
        return self


register_constructor("SlabFall", SlabFall)
register_constructor("DrainDish", DrainDish)
