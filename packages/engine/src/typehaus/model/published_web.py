"""``PublishedWebOpenings`` — what an open-web floor-truss maker publishes about its webs.

A sibling of ``PublishedSpan`` / ``PublishedHole``, carried on ``JoistSpec.web_openings``.
A published opening chart is a prescriptive read: the maker draws which openings exist and
what each takes, and ``resolve/open_web.py`` places them on every truss and grades a run
against the one it lands in. **What the maker does not publish stays flagged**: the panel
pitch is the shop layout's, so ``panel_pitch_assumed`` says the pitch is this house's
working figure until the layout arrives, and the end-diagonal that absorbs the stock
remainder is the resolver's assumption (``OpenWebShape.assumptions``).
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class PublishedWebOpenings(HausModel):
    """The openings, trim and stock a truss maker publishes for one floor-truss product."""

    #: The document, edition and page, enough for a reviewer to open it.
    source: str
    #: The chart and column actually read, in the chart's own words.
    table: str
    #: The member the row is for, spelled as the model spells the profile (retype guard).
    member: str
    #: ``D``: the largest ROUND hole through a web opening.
    round_diameter: Length
    #: ``R1``: the rectangular chase (width along the truss, height), and where it may sit.
    r1_width: Length | None = None
    r1_height: Length | None = None
    #: True where the chart allows R1 only at the centreline of the STOCK length.
    r1_at_stock_centreline: bool = False
    #: The framed duct chase R1 sits in (verticals at its edges); defaults to ``r1_width``.
    chase_width: Length | None = None
    #: ``R2``: the small rectangle ("for small pipe and wire").
    r2_width: Length | None = None
    r2_height: Length | None = None
    #: The OSB TrimEnd block each stock end carries, and so how much may be cut off it.
    trim_end: Length | None = None
    #: Stock comes in multiples of this, between ``stock_min`` and ``stock_max``.
    stock_increment: Length | None = None
    stock_min: Length | None = None
    stock_max: Length | None = None
    #: Centre-to-centre of the Warren panel points along a chord. Not published for the
    #: products on file: ``panel_pitch_assumed`` says so until the shop layout is in hand.
    panel_pitch: Length
    panel_pitch_assumed: bool = True
    #: Conditions the chart states and this engine does not check.
    condition: str = ""

    @model_validator(mode="after")
    def _row_is_readable(self) -> PublishedWebOpenings:
        for name in ("source", "table", "member"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"PublishedWebOpenings.{name} must name what was read")
        if self.round_diameter.meters <= 0.0 or self.panel_pitch.meters <= 0.0:
            raise ValueError("PublishedWebOpenings round_diameter and panel_pitch must be positive")
        for pair in (("r1_width", "r1_height"), ("r2_width", "r2_height")):
            given = [getattr(self, name) for name in pair]
            if any(v is not None for v in given) and not all(v is not None for v in given):
                raise ValueError(f"PublishedWebOpenings: state {pair[0]} and {pair[1]} together")
            if any(v is not None and v.meters <= 0.0 for v in given):
                raise ValueError(f"PublishedWebOpenings.{pair[0]}/{pair[1]} must be positive")
        if self.r1_at_stock_centreline and self.r1_width is None:
            raise ValueError("PublishedWebOpenings.r1_at_stock_centreline needs an R1 size")
        if self.chase_width is not None and (
                self.r1_width is None or self.chase_width.meters < self.r1_width.meters):
            raise ValueError("PublishedWebOpenings.chase_width must hold the R1 opening")
        stock = (self.stock_increment, self.stock_min, self.stock_max)
        if self.trim_end is not None:
            if self.trim_end.meters <= 0.0:
                raise ValueError("PublishedWebOpenings.trim_end must be positive")
            if any(v is None for v in stock):
                raise ValueError("a trimmable truss needs stock_increment, stock_min and stock_max")
        elif any(v is not None for v in stock):
            raise ValueError("stock sizes are read only where the row has a trim_end")
        return self

    @property
    def chase(self) -> float | None:
        """The framed chase width in metres, or None where the row has no R1."""
        if self.r1_width is None:
            return None
        return (self.chase_width or self.r1_width).meters
