"""A width x height pair for a rough opening (plans/door-sizing.md)."""

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length

# A prehung unit's shim space, per side (and once at the head), that a published RO must
# leave around it — or around the leaf, where no unit is published.
PREHUNG_SHIM_M = 0.25 * 0.0254
FIT_TOLERANCE_M = 1e-5


class OpeningSize(HausModel):
    """A rough opening, framing to framing; the floor end is the subfloor."""

    width: Length
    height: Length

    @model_validator(mode="after")
    def _positive(self):
        if self.width.meters <= 0 or self.height.meters <= 0:
            raise ValueError("an opening size must be positive")
        return self
