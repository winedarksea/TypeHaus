"""Purchased wall-handrail fittings: the bracket, return, end plate and splice a rail buys."""

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class WallMountSpec(HausModel):
    bracket_product: str
    return_product: str | None = None
    end_plate_product: str | None = None
    splice_product: str | None = None
    # Wall finish face to rail centreline. A fixed bracket sets both; unset = unpublished,
    # and the arm is not graded.
    projection_min: Length | None = None
    projection_max: Length | None = None
    # The drawn wall flange; replaces the stock 70 mm when set.
    end_plate_diameter: Length | None = None
    # The field fit (shim, set screw, expander), carried onto the bill.
    fit_note: str | None = None
    source: str

    @model_validator(mode="after")
    def validate_reach(self):
        lo, hi = self.projection_min, self.projection_max
        if (lo is None) != (hi is None):
            raise ValueError("projection_min and projection_max are set together")
        if lo is not None and not 0 < lo.meters <= hi.meters:
            raise ValueError("projection range must be positive and ordered")
        if self.end_plate_diameter is not None and self.end_plate_diameter.meters <= 0:
            raise ValueError("end_plate_diameter must be positive")
        return self
