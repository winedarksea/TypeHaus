"""A width x height pair for a rough opening (plans/door-sizing.md)."""

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class OpeningSize(HausModel):
    """A rough opening, framing to framing; the floor end is the subfloor."""

    width: Length
    height: Length

    @model_validator(mode="after")
    def _positive(self):
        if self.width.meters <= 0 or self.height.meters <= 0:
            raise ValueError("an opening size must be positive")
        return self
