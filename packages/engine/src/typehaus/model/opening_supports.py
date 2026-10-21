"""Explicit wall supports for the ends of a nonbearing pocket-door frame."""

from pydantic import model_validator

from typehaus.model.base import HausModel


class OpeningFrameEndSupports(HausModel):
    """Supports at the low/high stations of the complete frame, including its pocket.

    A reference requests a geometrically validated connection, not permission to omit
    framing. Unspecified ends keep their conventional king/jack packs.
    """

    start_wall_ref: str | None = None
    end_wall_ref: str | None = None

    @model_validator(mode="after")
    def _require_support_reference(self):
        if not self.start_wall_ref and not self.end_wall_ref:
            raise ValueError("frame_end_supports must name at least one support wall")
        for reference in (self.start_wall_ref, self.end_wall_ref):
            if reference is not None and not reference.strip():
                raise ValueError("frame end support wall references cannot be blank")
        return self
